from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExpiryActionLog(Base):
    __tablename__ = "expiry_action_log"
    __table_args__ = {"comment": "临期处理记录"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True, comment="商品ID"
    )
    batch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_batch.id"), nullable=False, index=True, comment="批次ID"
    )
    action: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="loss 报损 / promo 标记促销"
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=0, comment="处理数量"
    )
    outbound_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("outbound_order.id"), comment="关联报损出库单ID"
    )
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="处理人ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True, comment="处理时间"
    )

    product: Mapped["Product"] = relationship("Product", lazy="joined")
    batch: Mapped["InventoryBatch"] = relationship("InventoryBatch", lazy="joined")
    operator: Mapped["User"] = relationship("User", lazy="joined")
