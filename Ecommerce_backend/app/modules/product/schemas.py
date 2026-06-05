from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional

class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    price: int = Field(..., gt=0, description="Giá VND")
    currency: str = "VND"
    category_id: UUID
    images: List[str]

# Schema cho Response
class ProductResponse(ProductBase):
    product_id: UUID
    in_stock: bool # Theo spec, user chỉ thấy boolean này
    rating: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

# Schema chuẩn hóa Query Parameters cho API GET /v1/products
class ProductQueryParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, le=100)
    category_id: Optional[UUID] = None
    q: Optional[str] = None
    sort: Optional[str] = Field(None, pattern="^(price_asc|price_desc|newest|popular)$")
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = None