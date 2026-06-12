from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import get_current_user
from app.db.database import get_db_session
from app.modules.auth import schemas, services
from app.core import security
from app.core.exceptions import BusinessRuleException

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

# Khai báo scheme này để FastAPI tự động vẽ ổ khóa trên Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_create: schemas.UserCreate, db: Session = Depends(get_db_session)):
    return services.register_user(db, user_create)


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), # Hỗ trợ Form-Data cho Swagger
    db: Session = Depends(get_db_session)
):
    # Xác thực user
    user = services.authenticate_user(db, form_data.username, form_data.password)
    
    # Chuẩn bị payload chuẩn
    token_payload = {
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role
    }
    
    # Cấp phát 2 loại token đúng thời hạn (15 phút và 7 ngày)
    access_token = security.create_access_token(data=token_payload)
    refresh_token = security.create_refresh_token(data=token_payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user = Depends(get_current_user)):
    """Lấy thông tin user đang đăng nhập."""
    # FastAPI sẽ tự động chạy hàm get_current_user, giải mã token, 
    # lấy user từ DB và ném thẳng vào biến current_user này.
    return current_user

# Bổ sung API xoay vòng token (Token Rotation) theo spec
@router.post("/refresh-token", response_model=schemas.TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db_session)
):
    """
    Cấp lại bộ đôi Access Token và Refresh Token mới.
    API này không yêu cầu Header Authorization (Bearer token).
    """
    return services.refresh_access_token(db=db, refresh_token=request.refresh_token)