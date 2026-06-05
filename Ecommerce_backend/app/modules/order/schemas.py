from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List
from datetime import datetime

# Định nghĩa 1 item trong giỏ hàng/đơn hàng
class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)

# Schema Client gửi lên khi chốt đơn
class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    # Lưu ý: Tuyệt đối không có trường price ở đây. Giá phải tính ở server!

# Schema Item trả về
class OrderItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    price_at_purchase: int # Giá lúc mua (đã chốt)
    
    model_config = ConfigDict(from_attributes=True)

# Schema Đơn hàng trả về
class OrderResponse(BaseModel):
    order_id: UUID
    user_id: UUID
    status: str
    total_amount: int
    items: List[OrderItemResponse]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)