from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Chú ý import thêm models để type hint cho get_me
from app.modules.auth import schemas, services, models
from app.db.database import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.core import security

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

# XÓA bỏ dòng khai báo oauth2_scheme thừa ở đây


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_create: schemas.UserCreate, 
    db: Session = Depends(get_db_session)
) -> models.User: # Thêm Return Type
    return services.register_user(db, user_create)


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
) -> dict:
    # 1. Xác thực user
    user = services.authenticate_user(db, form_data.username, form_data.password)
    
    # 2. Chuẩn bị payload (Best Practice: Dùng key 'sub' thay vì 'user_id' cho chuẩn JWT)
    token_payload = {
        "sub": str(user.id), # Đảm bảo truy cập đúng tên cột ID trong model của bạn
        "email": user.email,
        "role": user.role
    }
    
    # 3. Sinh token
    # TODO: Ở giai đoạn Refactor sau MVP, toàn bộ logic từ dòng 1 đến đây nên được 
    # bọc vào 1 hàm `services.login_user_and_create_tokens(db, username, password)`
    access_token = security.create_access_token(data=token_payload)
    refresh_token = security.create_refresh_token(data=token_payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Lấy thông tin user đang đăng nhập."""
    # Nhờ Type Hint `models.User`, gõ current_user. sẽ xổ ra các thuộc tính
    return current_user


@router.post("/refresh-token", response_model=schemas.TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db_session)
) -> dict:
    """Cấp lại bộ đôi Access Token và Refresh Token mới."""
    return services.refresh_access_token(db=db, refresh_token=request.refresh_token)