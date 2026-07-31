from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Quản lý cấu hình toàn cục (Global Configuration) cho E-commerce API.
    Các giá trị sẽ được Pydantic tự động đọc từ biến môi trường hoặc file .env.
    """
    PROJECT_NAME: str = "E-Commerce API"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # Dùng kiểu DSN (Data Source Name) để validate format URL chặt chẽ
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    
    # Dùng SecretStr để chống rò rỉ khi print hoặc ghi log
    SECRET_KEY: SecretStr = Field(min_length=32)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    DB_POOL_MODE: Literal["queue", "null"] = "queue"
    DB_POOL_SIZE: int = Field(default=5, gt=0)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_TIMEOUT: int = Field(default=30, gt=0)
    DB_POOL_RECYCLE: int = Field(default=1800, ge=-1)
    DB_CONNECT_TIMEOUT: int = Field(default=5, gt=0)

    REDIS_MAX_CONNECTIONS: int = Field(default=20, gt=0)
    REDIS_CONNECT_TIMEOUT: float = Field(default=2.0, gt=0)
    REDIS_SOCKET_TIMEOUT: float = Field(default=2.0, gt=0)

    # Cú pháp chuẩn của Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Bỏ qua các biến môi trường thừa không khai báo
    )

# Khởi tạo singleton instance để import vào các module khác
settings = Settings()