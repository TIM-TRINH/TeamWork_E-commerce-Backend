from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from fastapi import status # Import status để dùng các mã HTTP chuẩn

from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate
from app.core.security import hash_password, verify_password
from app.core.exceptions import BusinessRuleException
from app.core import security

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
    print("PASSWORD RAW:", user_create.password)
    print("PASSWORD LENGTH:", len(user_create.password.encode("utf-8")))
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

def get_user_by_id(db: Session, user_id: UUID) -> User:
    return db.query(User).filter(User.user_id == user_id).first()

def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """
    Xử lý nghiệp vụ xoay vòng token (Token Rotation).
    """
    # 1. Giải mã và xác thực Refresh Token
    user_id = security.verify_token(refresh_token)
    if not user_id:
        raise BusinessRuleException(
            message="Refresh Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
            error_code="INVALID_REFRESH_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # 2. Lấy thông tin user (để đảm bảo user chưa bị xóa hoặc khóa tài khoản)
    user = get_user_by_id(db, user_id=user_id)
    
    # 3. Chuẩn bị lại Payload chuẩn
    token_payload = {
        "sub": str(user.user_id),
        "email": user.email,
        "role": user.role
    }
    
    # 4. Ký phát cặp Token MỚI (Token Rotation)
    new_access_token = security.create_access_token(data=token_payload)
    new_refresh_token = security.create_refresh_token(data=token_payload)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }