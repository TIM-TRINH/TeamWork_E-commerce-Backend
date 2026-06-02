from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce API"
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()