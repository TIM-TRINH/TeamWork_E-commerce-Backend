from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List
from datetime import datetime
from enum import Enum

# 1. Định nghĩa tập hợp các trạng thái đơn hàng hợp lệ
class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# 2. Schema cho API cập nhật trạng thái (Fix lỗi ImportError)
class OrderStatusUpdate(BaseModel):
    status: OrderStatusEnum = Field(..., description="Trạng thái mới của đơn hàng")

# 3. Định nghĩa 1 item trong giỏ hàng/đơn hàng
class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)

# 4. Schema Client gửi lên khi chốt đơn
class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    # Lưu ý: Tuyệt đối không có trường price ở đây. Giá phải tính ở server!

# 5. Schema Item trả về
class OrderItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    price_at_purchase: int # Giá lúc mua (đã chốt)
    
    model_config = ConfigDict(from_attributes=True)

# 6. Schema Đơn hàng trả về
class OrderResponse(BaseModel):
    order_id: UUID
    user_id: UUID
    status: OrderStatusEnum  # <-- Đã đổi từ str thành Enum
    total_amount: int
    items: List[OrderItemResponse]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)