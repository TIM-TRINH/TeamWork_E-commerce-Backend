from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.modules.order.models import Order, OrderItem
from app.modules.order.schemas import OrderCreate, OrderStatusUpdate, OrderStatusEnum
from app.modules.product.models import Product
from app.core.exceptions import BusinessRuleException
from enum import Enum

# Định nghĩa State Machine: {Trạng_thái_hiện_tại: [Danh_sách_trạng_thái_được_phép_chuyển_tới]}
ALLOWED_TRANSITIONS = {
    OrderStatusEnum.PENDING: [OrderStatusEnum.PROCESSING, OrderStatusEnum.CANCELLED],
    OrderStatusEnum.PROCESSING: [OrderStatusEnum.SHIPPED, OrderStatusEnum.CANCELLED],
    OrderStatusEnum.SHIPPED: [OrderStatusEnum.DELIVERED, OrderStatusEnum.CANCELLED],
    OrderStatusEnum.DELIVERED: [], # Trạng thái kết thúc (Terminal state), không được đi đâu nữa
    OrderStatusEnum.CANCELLED: []  # Trạng thái kết thúc
}

def create_order(db: Session, user_id: UUID, order_create: OrderCreate) -> Order:
    """Tạo đơn hàng an toàn với Pessimistic Lock và Rollback."""
    order = Order(user_id=user_id, total_amount=0) # Đã đổi total_price thành total_amount theo schema chuẩn
    db.add(order)
    db.flush() 
    
    total_amount = 0
    
    try:
        # Sắp xếp để chống Deadlock khi khóa nhiều sản phẩm
        sorted_items = sorted(order_create.items, key=lambda x: x.product_id)
        
        for item in sorted_items:
            # 1. Lock dòng sản phẩm bằng with_for_update()
            product = db.query(Product).filter(
                Product.product_id == item.product_id
            ).with_for_update().first()
            
            if not product:
                raise BusinessRuleException(f"Product {item.product_id} not found", "PRODUCT_NOT_FOUND", 404)
            
            # 2. Kiểm tra tồn kho
            if product.stock < item.quantity:
                raise BusinessRuleException(f"Not enough stock for {product.name}", "INSUFFICIENT_STOCK", 409)
            
            # 3. Trừ tồn kho thực tế
            product.stock -= item.quantity
            
            # 4. Tính toán tiền tại server
            total_amount += product.price * item.quantity
            
            # 5. Lưu chi tiết đơn hàng
            order_item = OrderItem(
                order_id=order.order_id,
                product_id=product.product_id,
                quantity=item.quantity,
                price_at_purchase=product.price
            )
            db.add(order_item)
            
        # Chốt tổng tiền và commit
        order.total_amount = total_amount
        db.commit()
        db.refresh(order)
        return order
        
    except Exception as e:
        db.rollback() # Hoàn tác nếu có bất cứ lỗi nào
        raise e

def get_orders(db: Session, user_id: UUID) -> List[Order]:
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()

def get_order_by_id(db: Session, order_id: UUID) -> Order:
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise BusinessRuleException("Order not found", "ORDER_NOT_FOUND", 404)
    return order

def update_order_status(db: Session, order_id: UUID, status_update: OrderStatusUpdate) -> Order:
    # 1. Lấy đơn hàng hiện tại
    order = get_order_by_id(db, order_id)
    current_status = order.status
    new_status = status_update.status
    
    # 2. Bỏ qua nếu trạng thái không thay đổi (Idempotent)
    if current_status == new_status:
        return order
        
    # 3. STATE MACHINE VALIDATION
    allowed_next_states = ALLOWED_TRANSITIONS.get(current_status, [])
    
    if new_status not in allowed_next_states:
        raise BusinessRuleException(
            message=f"Invalid transition from '{current_status}' to '{new_status}'",
            error_code="INVALID_STATUS_TRANSITION",
            status_code=400 # 400 Bad Request
        )
        
    # 4. Thực thi cập nhật
    order.status = new_status
    db.commit()
    db.refresh(order)
    
    return order
