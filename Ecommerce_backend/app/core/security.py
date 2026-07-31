import bcrypt
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Any, Dict, Literal, Optional
from uuid import UUID, uuid4

from app.core.config import settings

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False

TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class TokenClaims:
    user_id: UUID
    token_type: TokenType
    jti: UUID
    issued_at: int
    expires_at: int
    session_id: Optional[UUID] = None


def create_jwt_token(
    data: Dict[str, Any],
    expires_delta: timedelta,
    token_type: TokenType,
    jti: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
) -> str:
    to_encode = data.copy()

    if "user_id" in to_encode and isinstance(to_encode["user_id"], UUID):
        to_encode["user_id"] = str(to_encode["user_id"])

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    to_encode.update({
        "token_type": token_type,
        "jti": str(jti or uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    })
    if token_type == "refresh":
        to_encode["session_id"] = str(session_id or uuid4())
    else:
        to_encode.pop("session_id", None)

    secret_key = settings.SECRET_KEY.get_secret_value()
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

def create_access_token(data: Dict[str, Any], jti: Optional[UUID] = None) -> str:
    return create_jwt_token(
        data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        jti=jti,
    )

def create_refresh_token(
    data: Dict[str, Any],
    session_id: UUID,
    jti: UUID,
) -> str:
    return create_jwt_token(
        data,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
        jti=jti,
        session_id=session_id,
    )

def decode_token(token: str, expected_type: TokenType) -> Optional[TokenClaims]:
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token[7:].strip()

    try:
        secret_key = settings.SECRET_KEY.get_secret_value()
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])

        if payload.get("token_type") != expected_type:
            return None

        user_id = UUID(str(payload["sub"]))
        token_jti = UUID(str(payload["jti"]))
        issued_at = int(payload["iat"])
        expires_at = int(payload["exp"])
        session_id = None
        if expected_type == "refresh":
            session_id = UUID(str(payload["session_id"]))

        return TokenClaims(
            user_id=user_id,
            token_type=expected_type,
            jti=token_jti,
            issued_at=issued_at,
            expires_at=expires_at,
            session_id=session_id,
        )
    except (JWTError, KeyError, ValueError, TypeError):
        return None