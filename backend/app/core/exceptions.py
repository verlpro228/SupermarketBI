import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class BusinessError(Exception):
    """业务异常，统一转换为 code != 0 的响应。"""

    def __init__(self, message: str, code: int = 1, http_status: int = 200):
        self.message = message
        self.code = code
        self.http_status = http_status
        super().__init__(message)


class AuthError(BusinessError):
    def __init__(self, message: str = "登录已失效，请重新登录"):
        super().__init__(message, code=401, http_status=401)


class PermissionError_(BusinessError):
    def __init__(self, message: str = "无权限执行该操作"):
        super().__init__(message, code=403, http_status=403)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def _business_error_handler(_: Request, exc: BusinessError):
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_: Request, exc: RequestValidationError):
        raw_errors = exc.errors()
        # 只保留可序列化的字段，避免 model_validator 抛出的原始异常对象进入响应
        errors = [
            {
                "loc": list(item.get("loc", [])),
                "msg": str(item.get("msg", "")),
                "type": str(item.get("type", "")),
            }
            for item in raw_errors
        ]

        detail = errors[0] if errors else {}
        field = ".".join(str(item) for item in detail.get("loc", [])[1:]) or "参数"
        msg = detail.get("msg", "参数校验失败")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]

        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": f"{field}: {msg}", "data": errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error_handler(_: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": str(exc.detail), "data": None},
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("未处理异常 %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )
