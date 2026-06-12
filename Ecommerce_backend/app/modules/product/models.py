import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Category(Base):
    """
    Model quản lý danh mục sản phẩm.
    Hỗ trợ cấu trúc cây thư mục đa cấp (Self-referential relationship) đáp ứng Max Depth = 3.
    """
    __tablename__ = "categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="SET NULL"), nullable=True)

    # Mối quan hệ tự tham chiếu (Self-referential) để tạo cây danh mục
    parent = relationship("Category", remote_side=[category_id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    
    products = relationship("Product", back_populates="category")


class Product(Base):
    """
    Model quản lý thông tin sản phẩm cốt lõi.
    """
    __tablename__ = "products"

    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(2000), nullable=True)
    price = Column(Integer, nullable=False, index=True)  # Lưu giá trị VND dạng số nguyên
    currency = Column(String(10), default="VND", nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    images = Column(ARRAY(String), nullable=False, default=[]) # Lưu danh sách URL hình ảnh (PostgreSQL specific)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False)
    
    created_at = Column(Column(DateTime(timezone=True), server_default=func.now(), index=True))
    updated_at = Column(Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    category = relationship("Category", back_populates="products")

    @property
    def in_stock(self) -> bool:
        """
        Động toán trạng thái còn hàng/hết hàng dựa trên stock thực tế.
        Giúp Pydantic tự động map vào trường 'in_stock' của ProductResponse.
        """
        return self.stock > 0