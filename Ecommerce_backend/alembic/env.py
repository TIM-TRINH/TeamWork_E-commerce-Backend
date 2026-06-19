from logging.config import fileConfig
import os
import sys
from dotenv import load_dotenv

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Nạp file .env vào môi trường hệ thống
load_dotenv()

# Đưa thư mục gốc của dự án vào sys.path để import được module app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Đối tượng cấu hình của Alembic
config = context.config

# Cấu hình logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base metadata để Alembic so sánh
from app.db.base_class import Base  # noqa: E402

# ====================================================================
# SỬA Ở ĐÂY: IMPORT TẤT CẢ CÁC MODEL CỦA TOÀN BỘ DỰ ÁN
# ====================================================================
from app.modules.auth.models import User 

# Lưu ý: Dựa vào cấu trúc team, thư mục thường là số ít 'product'. 
# Nếu máy bạn dùng số nhiều 'products', hãy thêm 's' vào nhé!
from app.modules.product.models import Product 

# Bổ sung thêm module Order vì bạn đã làm xong
from app.modules.order.models import Order, OrderItem 
# ====================================================================

target_metadata = Base.metadata


def get_url() -> str:
    """Lấy DATABASE_URL từ biến môi trường và validate."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("Biến môi trường DATABASE_URL chưa được thiết lập!")
    return db_url


def run_migrations_offline() -> None:
    """Chạy migrations ở chế độ offline."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migrations ở chế độ online (kết nối trực tiếp DB)."""
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
        
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()