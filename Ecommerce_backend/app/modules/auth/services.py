import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import Optional
from fastapi import status # Import status để dùng các mã HTTP chuẩn
from redis import Redis
from redis.exceptions import RedisError

from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate
from app.core.security import hash_password, verify_password
from app.core.config import settings
from app.core.exceptions import BusinessRuleException
from app.core import security
from app.modules.auth import token_store

logger = logging.getLogger(__name__)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Hàm helper dùng chung để tìm user theo email"""
    return db.query(User).filter(User.email == email).first()

def register_user(db: Session, user_create: UserCreate) -> User:
    # Check if user exists
    if get_user_by_email(db, user_create.email):
        raise BusinessRuleException(
            message="Email already registered",
            error_code="USER_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT # Báo lỗi trùng lặp dữ liệu
        )
    
    # Create new user
    user = User(
        email=user_create.email,
        name=user_create.name, 
        password_hash=hash_password(user_create.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered user user_id=%s", user.user_id)
    return user
    

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise BusinessRuleException(
            message="Invalid email or password",
            error_code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED # Bắt buộc dùng 401 cho lỗi đăng nhập
        )
    return user

def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def _invalid_refresh_token() -> BusinessRuleException:
    return BusinessRuleException(
        message="Refresh Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
        error_code="INVALID_REFRESH_TOKEN",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def _token_store_unavailable() -> BusinessRuleException:
    return BusinessRuleException(
        message="Dịch vụ xác thực tạm thời không khả dụng.",
        error_code="AUTH_STORE_UNAVAILABLE",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _token_payload(user: User) -> dict:
    return {
        "sub": str(user.user_id),
        "email": user.email,
        "role": user.role,
    }


def _refresh_ttl_seconds() -> int:
    return int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())


def _create_token_pair(user: User, session_id: UUID, refresh_jti: UUID) -> dict:
    token_payload = _token_payload(user)
    return {
        "access_token": security.create_access_token(data=token_payload),
        "refresh_token": security.create_refresh_token(
            data=token_payload,
            session_id=session_id,
            jti=refresh_jti,
        ),
        "token_type": "bearer",
    }


def login_user(
    db: Session,
    email: str,
    password: str,
    redis_client: Redis,
) -> dict:
    user = authenticate_user(db, email, password)
    session_id = uuid4()
    refresh_jti = uuid4()

    try:
        created = token_store.create_session(
            redis_client,
            session_id=session_id,
            user_id=user.user_id,
            refresh_jti=refresh_jti,
            ttl_seconds=_refresh_ttl_seconds(),
        )
    except RedisError:
        logger.exception("Refresh session store unavailable during login")
        raise _token_store_unavailable()

    if not created:
        logger.error("Refresh session identifier collision")
        raise _token_store_unavailable()

    return _create_token_pair(user, session_id, refresh_jti)


def refresh_access_token(
    db: Session,
    refresh_token: str,
    redis_client: Redis,
) -> dict:
    claims = security.decode_token(refresh_token, expected_type="refresh")
    if not claims or not claims.session_id:
        raise _invalid_refresh_token()

    user = get_user_by_id(db, user_id=claims.user_id)
    if not user:
        raise _invalid_refresh_token()

    replacement_jti = uuid4()
    token_pair = _create_token_pair(user, claims.session_id, replacement_jti)

    try:
        rotation_result = token_store.rotate_session(
            redis_client,
            session_id=claims.session_id,
            user_id=claims.user_id,
            presented_jti=claims.jti,
            replacement_jti=replacement_jti,
            ttl_seconds=_refresh_ttl_seconds(),
        )
    except RedisError:
        logger.exception("Refresh session store unavailable during rotation")
        raise _token_store_unavailable()

    if rotation_result != token_store.RotationResult.ROTATED:
        if rotation_result == token_store.RotationResult.REPLAYED:
            logger.warning("Refresh token replay detected session_id=%s", claims.session_id)
        raise _invalid_refresh_token()

    return token_pair


def logout(refresh_token: str, redis_client: Redis) -> dict:
    claims = security.decode_token(refresh_token, expected_type="refresh")
    if not claims or not claims.session_id:
        raise BusinessRuleException(
            message="Refresh Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
            error_code="INVALID_REFRESH_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        token_store.revoke_session(
            redis_client,
            session_id=claims.session_id,
            ttl_seconds=max(
                1,
                claims.expires_at - int(datetime.now(timezone.utc).timestamp()),
            ),
        )
    except RedisError:
        logger.exception("Refresh session store unavailable during logout")
        raise _token_store_unavailable()

    return {"message": "Logged out successfully."}