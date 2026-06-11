from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from uuid import UUID
from app.core.config import settings

# 1. Cấu hình bcrypt bắt buộc cost = 12 theo spec
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12 
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 2. JWT Token Generator linh hoạt cho cả Access và Refresh Token
def create_jwt_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    """
    Tạo token dựa trên payload truyền vào. Payload truyền từ service phải chứa đủ: user_id, email, role.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    # Bổ sung thời gian tạo (iat) và thời gian hết hạn (exp) theo spec
    to_encode.update({
        "iat": now,
        "exp": expire
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# 3. Hàm tạo nhanh Access Token (15 phút) và Refresh Token (7 ngày)
def create_access_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, expires_delta=timedelta(minutes=15))

def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, expires_delta=timedelta(days=7))

# 4. Verify token trả về UUID chuẩn xác
def verify_token(token: str) -> Optional[UUID]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        # Đọc theo key 'user_id' thay vì 'sub'
        user_id_str = payload.get("user_id") 
        if user_id_str is None:
            return None
        return UUID(user_id_str) # Trả về chuẩn đối tượng UUID v4
    except (JWTError, ValueError):
        # ValueError bắt lỗi nếu chuỗi user_id không phải là UUID hợp lệ
        return None