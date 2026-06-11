# Thiết lập Base URL (/v1) & Global Error Handler (Task 9)
# class cha cho việc quy định lỗi.
from fastapi import Request
from fastapi.responses import JSONResponse

class BusinessRuleException(Exception):
    def __init__(self, message: str, error_code: str = "BUSINESS_RULE", status_code: int = 422):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code # Cho phép ghi đè mã HTTP

async def business_rule_exception_handler(request: Request, exc: BusinessRuleException):
    """Bắt lỗi Business Rule chuẩn theo spec 
    Trả về JSON với cấu trúc: {"error_code": "BUSINESS_RULE", "message": "Chi tiết lỗi"}
    """
    return JSONResponse(
        status_code=exc.status_code, # Trả về đúng mã HTTP được truyền vào
        content={"error_code": exc.error_code, "message": exc.message},
    )