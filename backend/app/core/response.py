from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应体：code=0 表示成功，非 0 表示业务失败。"""

    code: int = 0
    message: str = "ok"
    data: T | None = None


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def fail(code: int = 1, message: str = "操作失败", data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}
