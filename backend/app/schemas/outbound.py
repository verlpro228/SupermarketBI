from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_serializer, model_validator

from app.schemas.base import PageQuery

OutboundType = Literal["sale", "loss"]


class OutboundCreate(BaseModel):
    product_id: int = Field(..., description="商品ID")
    outbound_type: OutboundType = Field(..., description="sale 销售 / loss 报损")
    quantity: float = Field(..., gt=0, description="出库数量")
    reason: str | None = Field(None, max_length=255, description="报损原因，报损时必填")
    remark: str | None = Field(None, max_length=255, description="备注")

    @model_validator(mode="after")
    def _validate_reason(self):
        if self.outbound_type == "loss" and not (self.reason or "").strip():
            raise ValueError("报损出库必须填写报损原因")
        return self


class OutboundQuery(PageQuery):
    keyword: str | None = Field(None, max_length=64, description="商品名称或条码")
    outbound_type: OutboundType | None = Field(None, description="出库类型")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class OutboundItemOut(BaseModel):
    batch_id: int
    batch_no: str | None = None
    quantity: float
    cost_price: float
    amount: float
    production_date: date | None = None
    expiry_date: date | None = None

    @field_serializer("production_date", "expiry_date")
    def _serialize_date(self, value: date | None) -> str | None:
        return value.strftime("%Y-%m-%d") if value else None


class OutboundOut(BaseModel):
    id: int
    order_no: str
    product_id: int | None = None
    product_name: str | None = None
    barcode: str | None = None
    unit: str | None = None
    outbound_type: str
    total_qty: float
    total_amount: float
    reason: str | None = None
    operator_name: str | None = None
    remark: str | None = None
    created_at: datetime | None = None
    items: list[OutboundItemOut] = Field(default_factory=list)

    @field_serializer("created_at")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
