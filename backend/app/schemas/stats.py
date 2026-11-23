from typing import Literal

from pydantic import BaseModel, Field

TrendGranularity = Literal["day", "month"]


class DashboardKpi(BaseModel):
    product_count: int
    total_stock: float
    stock_value: float | None = Field(None, description="库存货值，仅管理员返回")
    expiry_count: int


class TrendItem(BaseModel):
    label: str
    inbound: float
    outbound: float


class CategoryValue(BaseModel):
    category: str
    value: float


class CategoryFlowItem(BaseModel):
    category: str
    inbound: float
    outbound: float


class ExpiryLevelCount(BaseModel):
    level: str
    count: int


class ProductValueItem(BaseModel):
    name: str
    value: float


class LowStockItem(BaseModel):
    name: str
    gap: float


class DashboardOut(BaseModel):
    kpi: DashboardKpi
    trend: list[TrendItem]
    category_value: list[CategoryValue]
    category_flow: list[CategoryFlowItem]
    expiry_distribution: list[ExpiryLevelCount]
    top_value_products: list[ProductValueItem]
    low_stock_products: list[LowStockItem]


class TrendQuery(BaseModel):
    days: int = Field(30, ge=1, le=365, description="统计天数")
    granularity: TrendGranularity = Field("day", description="day 按日 / month 按月")


class IoTrendItem(BaseModel):
    label: str
    quantity: float
    orders: int


class SupplierRankItem(BaseModel):
    supplier: str
    quantity: float
    orders: int


class CategoryQuantityItem(BaseModel):
    category: str
    quantity: float


class OutboundTypeItem(BaseModel):
    type: str
    quantity: float
    orders: int


class ProductQuantityItem(BaseModel):
    name: str
    quantity: float


class InboundAnalysisOut(BaseModel):
    days: int
    trend: list[IoTrendItem]
    supplier_ranking: list[SupplierRankItem]
    category_distribution: list[CategoryQuantityItem]


class OutboundAnalysisOut(BaseModel):
    days: int
    trend: list[IoTrendItem]
    type_distribution: list[OutboundTypeItem]
    top_products: list[ProductQuantityItem]
