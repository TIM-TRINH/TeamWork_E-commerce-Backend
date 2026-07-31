from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

SQLALCHEMY_DATABASE_URL = str(settings.DATABASE_URL)


def create_database_engine(database_url: str = SQLALCHEMY_DATABASE_URL) -> Engine:
	connect_args = {"connect_timeout": settings.DB_CONNECT_TIMEOUT}

	if settings.DB_POOL_MODE == "null":
		return create_engine(
			database_url,
			poolclass=NullPool,
			pool_pre_ping=True,
			connect_args=connect_args,
		)

	return create_engine(
		database_url,
		pool_pre_ping=True,
		pool_size=settings.DB_POOL_SIZE,
		max_overflow=settings.DB_MAX_OVERFLOW,
		pool_timeout=settings.DB_POOL_TIMEOUT,
		pool_recycle=settings.DB_POOL_RECYCLE,
		connect_args=connect_args,
	)


engine = create_database_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
