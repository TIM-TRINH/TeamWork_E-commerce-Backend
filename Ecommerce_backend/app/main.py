from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # [BỔ SUNG] Import CORS
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

from app.core.exceptions import (
    BusinessRuleException,
    business_rule_exception_handler,
    unhandled_exception_handler,
)
from app.modules.auth.router import router as auth_router
from app.modules.order.router import router as order_router
from app.modules.product.router import router as product_router
from app.db.database import engine
from app.db.redis import redis_client

def create_app() -> FastAPI:
    """
    Factory function để khởi tạo ứng dụng FastAPI.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,  
        version="1.0",
        description="API cho hệ thống E-commerce (MVP hỗ trợ thanh toán tiền mặt)"
    )

    # 1. Cấu hình CORS Middleware (Luôn đặt ở trên cùng)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # 2. Đăng ký Global Error Handler
    app.add_exception_handler(BusinessRuleException, business_rule_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 3. Import routers (Không truyền prefix ở đây vì đã khai báo sẵn trong từng router.py)
    app.include_router(auth_router)
    app.include_router(order_router)
    app.include_router(product_router)

    # 4. Health Check Endpoint
    @app.get("/v1/health", tags=["Health"])
    def health_check() -> dict:
        """
        Endpoint dùng để Load Docker check trạng thái server.
        """
        return {"status": "ok", "message": "Service is running perfectly."}

    @app.get("/v1/ready", tags=["Health"])
    def readiness_check():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            redis_client.ping()
        except (SQLAlchemyError, RedisError):
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready"},
            )

        return {"status": "ready"}

    return app

app = create_app()