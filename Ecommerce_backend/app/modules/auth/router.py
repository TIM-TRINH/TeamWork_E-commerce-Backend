from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from redis import Redis
from sqlalchemy.orm import Session

# Chú ý import thêm models để type hint cho get_me
from app.modules.auth import schemas, services, models
from app.db.database import get_db_session
from app.db.redis import get_redis_client
from app.modules.auth.dependencies import get_current_user

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
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> dict:
    return services.login_user(
        db,
        email=form_data.username,
        password=form_data.password,
        redis_client=redis_client,
    )


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Lấy thông tin user đang đăng nhập."""
    # Nhờ Type Hint `models.User`, gõ current_user. sẽ xổ ra các thuộc tính
    return current_user


@router.post("/refresh-token", response_model=schemas.TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> dict:
    """Cấp lại bộ đôi Access Token và Refresh Token mới."""
    return services.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
        redis_client=redis_client,
    )


@router.post("/logout", response_model=schemas.MessageResponse)
def logout(
    request: schemas.RefreshTokenRequest,
    redis_client: Redis = Depends(get_redis_client),
) -> dict:
    return services.logout(request.refresh_token, redis_client)