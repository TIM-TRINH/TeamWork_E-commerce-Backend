# Thiết lập Base URL (/v1) & Global Error Handler (Task 9)
# class cha cho việc quy định lỗi.
from fastapi import Request
from fastapi.responses import JSONResponse

class BusinessRuleException(Exception):
    def __init__(self, message: str, error_code: str = "BUSINESS_RULE"):
        self.message = message
        self.error_code = error_code

async def business_rule_exception_handler(request: Request, exc: BusinessRuleException):
    """Bắt lỗi 422 Business Rule chuẩn theo spec của khách hàng."""
    return JSONResponse(
        status_code=422,
        content={"error_code": exc.error_code, "message": exc.message},
    )