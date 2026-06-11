from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # [BỔ SUNG] Import CORS

# Import Settings và Exception từ core
from app.core.config import settings
from app.core.exceptions import BusinessRuleException, business_rule_exception_handler
from app.modules.auth.router import router as auth_router

# Chú ý: Nếu module Product và Order chưa code xong router, 
# bạn cần comment lại để app không bị crash khi khởi động.
# from app.modules.order.router import router as order_router
# from app.modules.product.router import router as product_router

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
        allow_origins=["*"], # Frontend domains được phép gọi API (Sửa lại khi lên Production)
        allow_credentials=True,
        allow_methods=["*"], # Cho phép GET, POST, PUT, DELETE...
        allow_headers=["*"], # Cho phép gửi Authorization header
    )

    # 2. Đăng ký Global Error Handler
    app.add_exception_handler(BusinessRuleException, business_rule_exception_handler)

    # 3. Import routers (Không truyền prefix ở đây vì đã khai báo sẵn trong từng router.py)
    app.include_router(auth_router)
    
    # Bỏ comment khi các module sau hoàn thiện:
    # app.include_router(order_router)
    # app.include_router(product_router)

    # 4. Health Check Endpoint
    @app.get("/v1/health", tags=["Health"])
    def health_check() -> dict:
        """
        Endpoint dùng để Load Docker check trạng thái server.
        """
        return {"status": "ok", "message": "Service is running perfectly."}

    return app

app = create_app()