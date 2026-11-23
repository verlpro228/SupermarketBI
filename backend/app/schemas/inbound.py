from datetime import date, datetime

from pydantic import BaseModel, Field, field_serializer

from app.schemas.base import PageQuery


class InboundCreate(BaseModel):
    product_id: int = Field(..., description="商品ID")
    quantity: float = Field(..., gt=0, description="入库数量")
    cost_price: float = Field(..., ge=0, description="入库进价")
    production_date: date = Field(..., description="生产日期")
    supplier: str | None = Field(None, max_length=128, description="供应商")
    remark: str | None = Field(None, max_length=255, description="备注")


class InboundQuery(PageQuery):
    keyword: str | None = Field(None, max_length=64, description="商品名称或条码")
    product_id: int | None = Field(None, description="商品ID")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class InboundOut(BaseModel):
    id: int
    order_no: str
    product_id: int
    product_name: str | None = None
    barcode: str | None = None
    unit: str | None = None
    batch_no: str | None = None
    quantity: float
    cost_price: float
    amount: float
    production_date: date
    expiry_date: date
    supplier: str | None = None
    operator_name: str | None = None
    remark: str | None = None
    created_at: datetime | None = None

    @field_serializer("production_date", "expiry_date")
    def _serialize_date(self, value: date | None) -> str | None:
        return value.strftime("%Y-%m-%d") if value else None

    @field_serializer("created_at")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
