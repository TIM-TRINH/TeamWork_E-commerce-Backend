# app/modules/auth/dependencies.py
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db_session
from app.modules.auth import services
from app.core import security
from app.core.exceptions import BusinessRuleException

# Cấu hình Swagger UI bắt token từ endpoint login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db_session)
):
    """Dependency lấy thông tin User hiện tại từ Token."""
    user_id_str = security.verify_token(token)
    if not user_id_str:
        raise BusinessRuleException(
            message="Token không hợp lệ hoặc đã hết hạn", 
            error_code="INVALID_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED 
        )
    
    # Ép kiểu về UUID và lấy từ DB
    user = services.get_user_by_id(db, UUID(user_id_str))
    if not user:
        raise BusinessRuleException("Tài khoản không tồn tại", "USER_NOT_FOUND", 401)
        
    return user

def get_current_admin(current_user = Depends(get_current_user)):
    """Dependency phân quyền: Chỉ cho phép Admin (RBAC)."""
    if current_user.role != "admin":
        raise BusinessRuleException(
            message="Bạn không có quyền thực hiện hành động này",
            error_code="FORBIDDEN_ACCESS",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user