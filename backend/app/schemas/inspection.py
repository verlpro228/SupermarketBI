from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

from app.schemas.base import PageQuery


class InspectionQuery(PageQuery):
    start_date: str | None = Field(None, description="开始日期 yyyy-MM-dd")
    end_date: str | None = Field(None, description="结束日期 yyyy-MM-dd")


class InspectionItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    barcode: str | None = None
    unit: str | None = None
    batch_id: int | None = None
    batch_no: str | None = None
    problem_type: str
    gap_qty: float | None = None
    days_left: int | None = None
    status: str
    handled_at: datetime | None = None

    @field_serializer("handled_at")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


class InspectionOut(BaseModel):
    id: int
    inspector_name: str | None = None
    hit_count: int
    low_stock_count: int = 0
    near_expiry_count: int = 0
    pending_count: int = 0
    created_at: datetime | None = None

    @field_serializer("created_at")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


class InspectionDetailOut(InspectionOut):
    items: list[InspectionItemOut] = Field(default_factory=list)


class InspectionItemStatusPayload(BaseModel):
    ids: list[int] = Field(..., min_length=1, description="巡检明细ID集合")
    status: Literal["handled", "ignored"] = Field(..., description="已处理 / 已忽略")
