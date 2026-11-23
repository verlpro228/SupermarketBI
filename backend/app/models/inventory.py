from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Inventory(Base, TimestampMixin):
    """商品级库存汇总，出库时用条件更新做原子扣减。"""

    __tablename__ = "inventory"
    __table_args__ = {"comment": "商品库存汇总"}

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), primary_key=True, comment="商品ID"
    )
    total_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=0, comment="当前库存总量"
    )


class InventoryBatch(Base, TimestampMixin):
    """批次库存，每次入库新建一条，出库按到期日升序先进先出扣减。"""

    __tablename__ = "inventory_batch"
    __table_args__ = {"comment": "批次库存"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True, comment="商品ID"
    )
    batch_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, comment="批次号"
    )
    inbound_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("inbound_order.id"), index=True, comment="来源入库单ID"
    )
    production_date: Mapped[date] = mapped_column(Date, nullable=False, comment="生产日期")
    expiry_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="到期日"
    )
    qty_initial: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, comment="入库数量"
    )
    qty_remaining: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, comment="剩余数量"
    )
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, comment="批次进价"
    )
    is_promo: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="1 已标记促销"
    )

    product: Mapped["Product"] = relationship("Product", lazy="joined")
