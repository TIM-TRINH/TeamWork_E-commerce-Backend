import os


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://user:pass@localhost:5432/ecommerce_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-bytes")