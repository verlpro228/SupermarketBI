from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

from app.schemas.base import PageQuery

ExpiryLevel = Literal["expired", "urgent", "warning"]


class ExpiryQuery(PageQuery):
    level: ExpiryLevel | None = Field(None, description="分档筛选")
    category_id: int | None = Field(None, description="分类筛选")
    keyword: str | None = Field(None, max_length=64, description="商品名称或条码")


class ExpiryBatchOut(BaseModel):
    """库管员视图，不含金额。"""

    batch_id: int
    batch_no: str
    product_id: int
    product_name: str
    barcode: str
    unit: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    production_date: date
    expiry_date: date
    days_left: int
    qty_remaining: float
    level: str
    is_promo: int = 0

    @field_serializer("production_date", "expiry_date")
    def _serialize_date(self, value: date | None) -> str | None:
        return value.strftime("%Y-%m-%d") if value else None


class ExpiryBatchAdminOut(ExpiryBatchOut):
    cost_price: float
    stock_value: float


class ExpiryThresholds(BaseModel):
    urgent_days: int
    warning_days: int


class ExpiryLossItem(BaseModel):
    batch_id: int
    quantity: float = Field(..., gt=0, description="报损数量")


class ExpiryLossPayload(BaseModel):
    items: list[ExpiryLossItem] = Field(..., min_length=1, max_length=100)
    reason: str = Field("临期报损", min_length=1, max_length=255)


class ExpiryPromoPayload(BaseModel):
    batch_id: int


class ExpiryActionQuery(PageQuery):
    keyword: str | None = Field(None, max_length=64)
    action: Literal["loss", "promo"] | None = None


class ExpiryActionLogOut(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    barcode: str | None = None
    batch_id: int
    batch_no: str | None = None
    action: str
    quantity: float
    order_no: str | None = None
    operator_name: str | None = None
    created_at: datetime | None = None

    @field_serializer("created_at")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
