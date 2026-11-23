from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.base import PageQuery


class ProductQuery(PageQuery):
    keyword: str | None = Field(None, max_length=64, description="名称或条码模糊搜索")
    category_id: int | None = Field(None, description="分类筛选")
    status: int | None = Field(None, ge=0, le=1, description="状态筛选")


class ProductCreate(BaseModel):
    barcode: str = Field(..., min_length=1, max_length=64, description="条码")
    name: str = Field(..., min_length=1, max_length=128, description="商品名称")
    category_id: int = Field(..., description="分类ID")
    spec: str | None = Field(None, max_length=64, description="规格")
    unit: str | None = Field(None, max_length=16, description="单位")
    purchase_price: float = Field(0, ge=0, description="进价")
    sale_price: float = Field(0, ge=0, description="售价")
    safe_stock: float = Field(0, ge=0, description="安全库存")
    shelf_life_days: int = Field(0, ge=0, le=3650, description="保质期天数")


class ProductUpdate(BaseModel):
    barcode: str | None = Field(None, min_length=1, max_length=64)
    name: str | None = Field(None, min_length=1, max_length=128)
    category_id: int | None = None
    spec: str | None = Field(None, max_length=64)
    unit: str | None = Field(None, max_length=16)
    purchase_price: float | None = Field(None, ge=0)
    sale_price: float | None = Field(None, ge=0)
    safe_stock: float | None = Field(None, ge=0)
    shelf_life_days: int | None = Field(None, ge=0, le=3650)


class ProductOut(BaseModel):
    """库管员可见字段，不含进价。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    barcode: str
    name: str
    category_id: int
    category_name: str | None = None
    spec: str | None = None
    unit: str | None = None
    sale_price: float
    safe_stock: float
    shelf_life_days: int
    status: int
    created_at: datetime | None = None

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


class ProductAdminOut(ProductOut):
    """管理员可见字段，含进价。"""

    purchase_price: float


class ProductOption(BaseModel):
    """入库、出库等下拉选择用的精简结构。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    barcode: str
    name: str
    spec: str | None = None
    unit: str | None = None
    shelf_life_days: int
    stock_qty: float = 0
    purchase_price: float | None = Field(
        None, description="商品当前进价，仅管理员返回，用于入库表单预填"
    )
