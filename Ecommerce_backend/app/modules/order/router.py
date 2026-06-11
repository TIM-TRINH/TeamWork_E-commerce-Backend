from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.modules.order import schemas, services
# Giả định bạn đã có dependency lấy DB session và User hiện tại
from app.db.database import get_db_session
# from app.core.security import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    responses={404: {"description": "Not found"}},
)

# --- Mock Auth Dependency (Để code chạy được khi bạn chưa hoàn thiện module Auth) ---
class MockUser:
    import uuid
    id: UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")

def get_current_user():
    return MockUser()
# -----------------------------------------------------------------------------------

@router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Tạo đơn hàng mới (Checkout)."""
    return services.create_order(db=db, user_id=current_user.id, order_create=order_in)

@router.get("/", response_model=List[schemas.OrderResponse])
def list_my_orders(
    db: Session = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Lấy danh sách đơn hàng của user đang đăng nhập."""
    return services.get_orders(db=db, user_id=current_user.id)

@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order_detail(
    order_id: UUID = Path(..., title="The ID of the order to get"),
    db: Session = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Lấy chi tiết một đơn hàng theo ID."""
    # LƯU Ý: Ở production cần kiểm tra xem order này có thuộc về current_user không!
    return services.get_order_by_id(db=db, order_id=order_id)

@router.patch("/{order_id}/status", response_model=schemas.OrderResponse)
def update_status(
    status_in: schemas.OrderStatusUpdate,
    order_id: UUID = Path(...),
    db: Session = Depends(get_db_session),
    # current_user = Depends(get_current_admin) # Chỉ Admin mới được đổi status
):
    """Cập nhật trạng thái đơn hàng (Dành cho Admin)."""
    return services.update_order_status(db=db, order_id=order_id, status_update=status_in)