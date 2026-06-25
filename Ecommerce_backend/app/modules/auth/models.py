import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class User(Base):
    """
    Model đại diện cho bảng users trong cơ sở dữ liệu.
    Lưu trữ thông tin xác thực và phân quyền của người dùng.
    """
    __tablename__ = "users"
    # Sử dụng UUID v4 làm khóa chính theo chuẩn spec
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), default="customer", nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    