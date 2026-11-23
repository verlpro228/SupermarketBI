from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OutboundOrder(Base):
    __tablename__ = "outbound_order"
    __table_args__ = {"comment": "出库单"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, comment="出库单号"
    )
    outbound_type: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="sale 销售 / loss 报损"
    )
    total_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, comment="出库总数量"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0, comment="出库总金额（后端计算）"
    )
    reason: Mapped[str | None] = mapped_column(String(255), comment="报损原因")
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="操作人ID"
    )
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True, comment="创建时间"
    )

    items: Mapped[list["OutboundItem"]] = relationship(
        "OutboundItem", back_populates="order", cascade="all, delete-orphan"
    )
    operator: Mapped["User"] = relationship("User", lazy="joined")


class OutboundItem(Base):
    __tablename__ = "outbound_item"
    __table_args__ = {"comment": "出库明细（按批次拆分）"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    outbound_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("outbound_order.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="出库单ID",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True, comment="商品ID"
    )
    batch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_batch.id"), nullable=False, index=True, comment="批次ID"
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, comment="本批次出库数量"
    )
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, comment="批次进价快照"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0, comment="本批次出库金额"
    )

    order: Mapped["OutboundOrder"] = relationship("OutboundOrder", back_populates="items")
    batch: Mapped["InventoryBatch"] = relationship("InventoryBatch", lazy="joined")
    product: Mapped["Product"] = relationship("Product", lazy="joined")
