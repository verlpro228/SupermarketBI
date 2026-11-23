from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "product"
    __table_args__ = {"comment": "商品档案"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    barcode: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="条码"
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment="商品名称")
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("category.id"), nullable=False, index=True, comment="分类ID"
    )
    spec: Mapped[str | None] = mapped_column(String(64), comment="规格")
    unit: Mapped[str | None] = mapped_column(String(16), comment="单位")
    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, comment="进价"
    )
    sale_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, comment="售价"
    )
    safe_stock: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=0, comment="安全库存"
    )
    shelf_life_days: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="保质期天数"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, index=True, comment="1 正常 0 已停用"
    )

    category: Mapped["Category"] = relationship("Category", lazy="joined")
