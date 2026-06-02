# app/main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Import Settings và Exception từ core
from app.core.config import settings
from app.core.exceptions import BusinessRuleException, business_rule_exception_handler
from app.modules.auth.router import router as auth_router

def create_app() -> FastAPI:
    """
    Factory function để khởi tạo ứng dụng FastAPI.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,  # Đọc tên từ config.py
        version="1.0",
        description="API cho hệ thống E-commerce (MVP hỗ trợ thanh toán tiền mặt)"
    )

    # Đăng ký Global Error Handler theo chuẩn spec (Task 9)
    app.add_exception_handler(BusinessRuleException, business_rule_exception_handler)

    # TODO: Import và include routers tại đây
    app.include_router(auth_router, prefix="/v1/auth", tags=["Auth"])

    # Base URL /v1 cho health check
    @app.get("/v1/health", tags=["Health"])
    def health_check() -> dict:
        """
        Endpoint dùng để Load Balancer hoặc Docker check trạng thái server.
        """
        return {"status": "ok", "message": "Service is running perfectly."}

    return app

app = create_app()