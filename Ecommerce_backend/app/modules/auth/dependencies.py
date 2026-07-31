from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db_session
from app.modules.auth import services, models
from app.core import security
from app.core.exceptions import BusinessRuleException

# Cấu hình Swagger UI bắt token từ endpoint login (Phải khớp với file router)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db_session)
) -> models.User:  # [QUAN TRỌNG]: Bổ sung type hint trả về
    """Dependency lấy thông tin User hiện tại từ Token."""
    
    claims = security.decode_token(token, expected_type="access")
    if not claims:
        raise BusinessRuleException(
            message="Token không hợp lệ hoặc đã hết hạn", 
            error_code="INVALID_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED 
        )
    
    # 2. Truyền thẳng user_id (đã là UUID) vào Service
    user = services.get_user_by_id(db, claims.user_id)
    if not user:
        raise BusinessRuleException(
            message="Tài khoản không tồn tại", 
            error_code="USER_NOT_FOUND", 
            status_code=status.HTTP_401_UNAUTHORIZED
        )
        
    return user

def get_current_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Dependency phân quyền: Chỉ cho phép Admin (RBAC)."""
    
    if current_user.role != "admin":
        raise BusinessRuleException(
            message="Bạn không có quyền thực hiện hành động này",
            error_code="FORBIDDEN_ACCESS",
            status_code=status.HTTP_403_FORBIDDEN
        )
        
    return current_user