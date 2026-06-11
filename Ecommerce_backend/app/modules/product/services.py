from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.modules.product.models import Product
from app.modules.product.schemas import ProductCreate, ProductUpdate
from app.core.exceptions import BusinessRuleException

def create_product(db: Session, product_create: ProductCreate) -> Product:
    # BEST PRACTICE: Pydantic v2 dùng model_dump()
    product = Product(**product_create.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def get_products(db: Session, cursor: Optional[datetime] = None, limit: int = 20) -> List[Product]:
    """Phân trang Cursor-based bằng created_at để tối ưu truy vấn lớn."""
    query = db.query(Product)
    
    if cursor:
        # Lấy các sản phẩm cũ hơn mốc thời gian của trang trước
        query = query.filter(Product.created_at < cursor)
        
    # Luôn order_by để cursor hoạt động chính xác
    return query.order_by(Product.created_at.desc()).limit(limit).all()

def get_product_by_id(db: Session, product_id: UUID) -> Product: # Dùng UUID thay cho int
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise BusinessRuleException("Product not found", "PRODUCT_NOT_FOUND", status_code=404)
    return product

def update_product(db: Session, product_id: UUID, product_update: ProductUpdate) -> Product:
    product = get_product_by_id(db, product_id)
    
    # Pydantic v2: model_dump(exclude_unset=True)
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
        
    db.commit()
    db.refresh(product)
    
    # TODO: Gọi hàm Redis Service để xóa (invalidate) cache của product_id này
    
    return product

def delete_product(db: Session, product_id: UUID):
    product = get_product_by_id(db, product_id)
    db.delete(product)
    db.commit()
    
    # TODO: Gọi hàm Redis Service để xóa (invalidate) cache
    
    return {"message": "Product deleted successfully"}