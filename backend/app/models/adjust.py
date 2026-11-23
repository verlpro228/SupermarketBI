from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StockAdjustLog(Base):
    __tablename__ = "stock_adjust_log"
    __table_args__ = {"comment": "库存调整日志"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True, comment="商品ID"
    )
    batch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_batch.id"), nullable=False, comment="调整批次ID"
    )
    before_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, comment="调整前数量"
    )
    after_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, comment="调整后数量"
    )
    diff_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, comment="差异数量"
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False, comment="调整原因")
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="操作人ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True, comment="创建时间"
    )

    product: Mapped["Product"] = relationship("Product", lazy="joined")
    batch: Mapped["InventoryBatch"] = relationship("InventoryBatch", lazy="joined")
    operator: Mapped["User"] = relationship("User", lazy="joined")
