from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.modules.product.models import Product, Category
from app.modules.product.schemas import ProductCreate, ProductUpdate, CategoryCreate
from app.core.exceptions import BusinessRuleException

def get_category_by_id(db: Session, category_id: UUID) -> Category:
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise BusinessRuleException(
            message="Category not found",
            error_code="CATEGORY_NOT_FOUND",
            status_code=404
        )
    return category


def create_category(db: Session, category_create: CategoryCreate) -> Category:
    existing = db.query(Category).filter(Category.slug == category_create.slug).first()
    if existing:
        raise BusinessRuleException(
            message="Category slug already exists",
            error_code="CATEGORY_ALREADY_EXISTS",
            status_code=409
        )

    category = Category(**category_create.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_product(db: Session, product_create: ProductCreate) -> Product:
    # Validate category exists before inserting product
    get_category_by_id(db, product_create.category_id)

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


def search_products(
    db: Session,
    q: str,
    category_id: Optional[UUID] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    sort: Optional[str] = None,
    limit: int = 20,
) -> List[Product]:
    """Search products by keyword, category, price range, and sort order."""
    query = db.query(Product)

    # Keyword search across name + description
    q_pattern = f"%{q.strip()}%"
    query = query.filter(
        Product.name.ilike(q_pattern) | Product.description.ilike(q_pattern)
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    elif sort == "popular":
        # Placeholder: hiện chưa có dữ liệu rating/sales nên dùng created_at
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    return query.limit(limit).all()

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