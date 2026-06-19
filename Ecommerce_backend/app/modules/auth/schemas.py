from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime

# Base chứa các trường dùng chung
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., max_length=100)

# Schema cho Request Đăng ký (Client gửi lên)
class UserCreate(UserBase):
    # Đã bỏ tham số pattern ở đây
    password: str = Field(
        ..., 
        min_length=8, 
        description="Password must have at least 8 characters, 1 uppercase, 1 number"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Kiểm tra độ mạnh của mật khẩu một cách tường minh."""
        if not any(char.isupper() for char in v):
            raise ValueError("Mật khẩu phải chứa ít nhất 1 chữ cái in hoa.")
        
        if not any(char.isdigit() for char in v):
            raise ValueError("Mật khẩu phải chứa ít nhất 1 chữ số.")
            
        return v

# Schema cho Response (Server trả về) - TUYỆT ĐỐI KHÔNG chứa password
class UserResponse(UserBase):
    user_id: UUID
    role: str
    verified: bool
    created_at: datetime
    
    # Hỗ trợ map trực tiếp từ SQLAlchemy Model sang Pydantic schema
    model_config = ConfigDict(from_attributes=True) 

# Schema cho Token
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
# Schema cho Request đổi token mới bằng refresh token
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token hợp lệ để đổi token mới")