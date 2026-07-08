from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from uuid import UUID
from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()

    if "user_id" in to_encode and isinstance(to_encode["user_id"], UUID):
        to_encode["user_id"] = str(to_encode["user_id"])

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    })

    secret_key = settings.SECRET_KEY.get_secret_value()
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

def create_access_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, expires_delta=timedelta(minutes=15))

def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, expires_delta=timedelta(days=7))

def verify_token(token: str) -> Optional[UUID]:
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token[7:].strip()

    try:
        secret_key = settings.SECRET_KEY.get_secret_value()
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])

        user_id_str = payload.get("sub")
        if not user_id_str:
            return None

        return UUID(str(user_id_str))
    except (JWTError, ValueError, TypeError):
        return None