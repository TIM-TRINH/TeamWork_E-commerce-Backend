import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base 

class Category(Base):
    """Model quản lý danh mục. Tự động có created_at và updated_at từ Base."""
    
    # Ghi đè tự động hóa của Base để ép tên bảng thành SỐ NHIỀU
    __tablename__ = "categories"  

    category_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.category_id", ondelete="SET NULL")
    )

    parent: Mapped["Category"] = relationship("Category", remote_side=[category_id], back_populates="children")
    children: Mapped[list["Category"]] = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class Product(Base):
    """Model quản lý sản phẩm. Tự động có created_at và updated_at từ Base."""
    
    # Ghi đè tự động hóa của Base để ép tên bảng thành SỐ NHIỀU
    __tablename__ = "products"  

    product_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(2000))
    price: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="VND", nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    images: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.category_id", ondelete="RESTRICT")
    )
    
    category: Mapped["Category"] = relationship("Category", back_populates="products")

    @property
    def in_stock(self) -> bool:
        return self.stock > 0