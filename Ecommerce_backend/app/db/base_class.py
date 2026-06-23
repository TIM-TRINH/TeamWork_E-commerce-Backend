from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

class Base(DeclarativeBase):
    """
    Class Base chuẩn cho SQLAlchemy 2.x.
    Tất cả các model kế thừa class này sẽ tự động có tên bảng và 2 cột lưu vết thời gian.
    """
    
    # 1. Tự động sinh tên bảng (VD: class 'Product' -> table 'product')
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # 2. Tự động thêm trường created_at và updated_at cho MỌI bảng
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )