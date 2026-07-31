import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class BusinessRuleException(Exception):
    def __init__(self, message: str, error_code: str = "BUSINESS_RULE", status_code: int = 422):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code # Cho phép ghi đè mã HTTP

async def business_rule_exception_handler(request: Request, exc: BusinessRuleException):
    """Bắt lỗi Business Rule chuẩn theo spec 
    Trả về JSON với cấu trúc: {"error_code": "BUSINESS_RULE", "message": "Chi tiết lỗi"}
    """
    logger.warning(
        "Business rule rejected request method=%s path=%s status=%s code=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.error_code,
    )
    return JSONResponse(
        status_code=exc.status_code, # Trả về đúng mã HTTP được truyền vào
        content={"error_code": exc.error_code, "message": exc.message},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled request error method=%s path=%s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
        },
    )