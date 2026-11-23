from datetime import date, datetime

from pydantic import BaseModel, Field, field_serializer

from app.schemas.base import PageQuery


class StockQuery(PageQuery):
    keyword: str | None = Field(None, max_length=64, description="商品名称或条码")
    category_id: int | None = Field(None, description="分类筛选")
    status: int | None = Field(None, ge=0, le=1, description="商品状态筛选")


class StockOut(BaseModel):
    """库管员视图，不含任何金额字段。"""

    product_id: int
    barcode: str
    name: str
    category_id: int
    category_name: str | None = None
    unit: str | None = None
    total_qty: float
    safe_stock: float
    nearest_expiry: date | None = None
    days_left: int | None = None
    product_status: int
    is_low_stock: bool = False

    @field_serializer("nearest_expiry")
    def _serialize_date(self, value: date | None) -> str | None:
        return value.strftime("%Y-%m-%d") if value else None


class StockAdminOut(StockOut):
    """管理员视图，含进价与库存货值。"""

    purchase_price: float
    stock_value: float


class StockChangeRecord(BaseModel):
    """入库 / 出库流水记录，统一结构。"""

    record_type: str = Field(..., description="inbound / outbound")
    order_no: str
    batch_no: str | None = None
    quantity: float
    amount: float
    production_date: date | None = None
    expiry_date: date | None = None
    days_left: int | None = None
    supplier: str | None = None
    outbound_type: str | None = None
    reason: str | None = None
    operator_name: str | None = None
    created_at: datetime | None = None

    @field_serializer("production_date", "expiry_date")
    def _serialize_date(self, value: date | None) -> str | None:
        return value.strftime("%Y-%m-%d") if value else None

    @field_serializer("created_at")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


class StockBatchOut(BaseModel):
    """库存调整时可选的批次明细。"""

    batch_id: int
    batch_no: str
    production_date: date
    expiry_date: date
    qty_remaining: float
    cost_price: float
    days_left: int

    @field_serializer("production_date", "expiry_date")
    def _serialize_date(self, value: date | None) -> str | None:
        return value.strftime("%Y-%m-%d") if value else None


class StockAdjustPayload(BaseModel):
    product_id: int
    batch_id: int
    new_qty: float = Field(..., ge=0, description="调整后数量")
    reason: str = Field(..., min_length=1, max_length=255, description="调整原因")
