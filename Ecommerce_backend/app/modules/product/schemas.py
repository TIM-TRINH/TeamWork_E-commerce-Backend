from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    price: int = Field(..., gt=0, description="Giá VND")
    currency: str = "VND"
    category_id: UUID
    images: List[str]

# 1. Schema cho Admin lúc Tạo/Sửa (Cần số lượng stock cụ thể)
class ProductCreate(ProductBase):
    stock: int = Field(..., ge=0, description="Số lượng tồn kho chính xác")

class ProductUpdate(BaseModel):
    # Tất cả đều Optional
    name: Optional[str] = Field(None, max_length=200)
    price: Optional[int] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    # ... (các trường khác)

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    parent_id: Optional[UUID] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: UUID
    created_at: datetime

# 2. Schema cho Response trả về Client
class ProductResponse(ProductBase):
    product_id: UUID
    in_stock: bool # Client chỉ thấy True/False
    rating: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# 3. Schema chuẩn hóa Query Parameters (Cursor Pagination)
class ProductQueryParams(BaseModel):
    # BỎ trường page, thay bằng cursor
    cursor: Optional[datetime] = Field(None, description="Truyền created_at của item cuối cùng ở lần fetch trước")
    limit: int = Field(20, gt=0, le=100)
    
    category_id: Optional[UUID] = None
    q: Optional[str] = None
    sort: Optional[str] = Field(None, pattern="^(price_asc|price_desc|newest|popular)$")
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = None


class ProductSearchParams(ProductQueryParams):
    q: str = Field(..., min_length=2, description="Từ khóa tìm kiếm")
