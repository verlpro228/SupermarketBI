from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageQuery(BaseModel):
    """列表分页查询基类，具体模块继承后追加筛选字段。"""

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=200, description="每页条数")


class PageData(BaseModel, Generic[T]):
    """分页响应数据结构。"""

    items: list[T]
    total: int
    page: int
    page_size: int


class IdsPayload(BaseModel):
    """批量操作入参。"""

    ids: list[int] = Field(..., min_length=1, description="主键集合")
