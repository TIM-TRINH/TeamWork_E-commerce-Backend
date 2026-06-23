from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from uuid import UUID
from app.core.config import settings

# 1. Cấu hình bcrypt với cost = 12 (Chuẩn bảo mật hiện tại)
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12 
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 2. JWT Token Generator linh hoạt
def create_jwt_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    """
    Tạo token dựa trên payload. Payload nên chứa: user_id, email, role.
    """
    to_encode = data.copy()
    
    # [QUAN TRỌNG]: Ép kiểu UUID thành chuỗi (str) để tránh lỗi JSON Encode
    if "user_id" in to_encode and isinstance(to_encode["user_id"], UUID):
        to_encode["user_id"] = str(to_encode["user_id"])

    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    to_encode.update({
        "iat": now,
        "exp": expire
    })
    
    # Trích xuất chuỗi bí mật thực sự từ Pydantic v2 SecretStr
    secret_key = settings.SECRET_KEY.get_secret_value()
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

# 3. Hàm tạo nhanh Tokens
def create_access_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, expires_delta=timedelta(minutes=15))

def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_jwt_token(data, expires_delta=timedelta(days=7))

# 4. Verify token trả về UUID
def verify_token(token: str) -> Optional[UUID]:
    try:
        # Nhớ trích xuất secret_key khi decode
        secret_key = settings.SECRET_KEY.get_secret_value()
        
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        user_id_str = payload.get("user_id") 
        if not user_id_str:
            return None
            
        return UUID(str(user_id_str)) # Trả về chuẩn đối tượng UUID v4
    except (JWTError, ValueError):
        # JWTError: Token sai chữ ký hoặc đã hết hạn
        # ValueError: UUID format không hợp lệ
        return None