from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.modules.order import schemas, services
from app.db.database import get_db_session
from app.core.exceptions import BusinessRuleException
from app.modules.auth.dependencies import get_current_user, get_current_admin

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Tạo đơn hàng mới (Checkout)."""
    # LƯU Ý: Đảm bảo model User của bạn dùng trường khóa chính là user_id (không phải id)
    return services.create_order(db=db, user_id=current_user.user_id, order_create=order_in)


@router.get("/", response_model=List[schemas.OrderResponse])
def list_my_orders(
    db: Session = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Lấy danh sách đơn hàng của user đang đăng nhập."""
    return services.get_orders(db=db, user_id=current_user.user_id)


@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order_detail(
    order_id: UUID = Path(..., title="The ID of the order to get"),
    db: Session = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """Lấy chi tiết một đơn hàng theo ID."""
    order = services.get_order_by_id(db=db, order_id=order_id)
    
    # BẢO MẬT CHỐNG IDOR: Chỉ cho phép chủ nhân đơn hàng hoặc Admin được xem
    if order.user_id != current_user.user_id and current_user.role != "admin":
        raise BusinessRuleException(
            message="Bạn không có quyền truy cập đơn hàng này",
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN
        )
        
    return order


@router.patch("/{order_id}/status", response_model=schemas.OrderResponse)
def update_status(
    status_in: schemas.OrderStatusUpdate,
    order_id: UUID = Path(...),
    db: Session = Depends(get_db_session),
    # BẬT PHÂN QUYỀN: Chỉ Admin mới được phép đổi trạng thái
    current_admin = Depends(get_current_admin) 
):
    """Cập nhật trạng thái đơn hàng (Dành cho Admin)."""
    return services.update_order_status(db=db, order_id=order_id, status_update=status_in)