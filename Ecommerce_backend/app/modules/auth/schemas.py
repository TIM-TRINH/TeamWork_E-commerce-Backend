from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

# Base chứa các trường dùng chung
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., max_length=100)

# Schema cho Request Đăng ký (Client gửi lên)
class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8, 
        pattern=r'^(?=.*[A-Z])(?=.*\d).+$',
        description="Password must have at least 8 characters, 1 uppercase, 1 number"
    )

# Schema cho Response (Server trả về) - TUYỆT ĐỐI KHÔNG chứa password
class UserResponse(UserBase):
    user_id: UUID
    role: str
    verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True) # Hỗ trợ map từ SQLAlchemy Model sang Pydantic

# Schema cho Token
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
# Schema cho Request đổi token mới bằng refresh token
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token hợp lệ để đổi token mới")