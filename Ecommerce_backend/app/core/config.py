from pydantic import SecretStr, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Quản lý cấu hình toàn cục (Global Configuration) cho E-commerce API.
    Các giá trị sẽ được Pydantic tự động đọc từ biến môi trường hoặc file .env.
    """
    PROJECT_NAME: str = "E-Commerce API"
    
    # Dùng kiểu DSN (Data Source Name) để validate format URL chặt chẽ
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    
    # Dùng SecretStr để chống rò rỉ khi print hoặc ghi log
    SECRET_KEY: SecretStr

    # Cú pháp chuẩn của Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Bỏ qua các biến môi trường thừa không khai báo
    )

# Khởi tạo singleton instance để import vào các module khác
settings = Settings()