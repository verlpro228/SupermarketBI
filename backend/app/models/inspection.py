from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InspectionRecord(Base):
    __tablename__ = "inspection_record"
    __table_args__ = {"comment": "库存巡检记录"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inspector_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="执行人ID"
    )
    hit_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="命中条数"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True, comment="巡检时间"
    )

    inspector: Mapped["User"] = relationship("User", lazy="joined")
    items: Mapped[list["InspectionItem"]] = relationship(
        "InspectionItem", back_populates="record", cascade="all, delete-orphan"
    )


class InspectionItem(Base):
    __tablename__ = "inspection_item"
    __table_args__ = {"comment": "巡检问题明细（快照）"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("inspection_record.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="巡检记录ID",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True, comment="商品ID"
    )
    batch_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("inventory_batch.id"), comment="批次ID（低库存为空）"
    )
    problem_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="low_stock 低库存 / near_expiry 临期"
    )
    gap_qty: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3), comment="低库存缺口数量"
    )
    days_left: Mapped[int | None] = mapped_column(Integer, comment="剩余保质期天数快照")
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pending", comment="pending/handled/ignored"
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, comment="处理时间")

    record: Mapped["InspectionRecord"] = relationship(
        "InspectionRecord", back_populates="items"
    )
    product: Mapped["Product"] = relationship("Product", lazy="joined")
    batch: Mapped["InventoryBatch"] = relationship("InventoryBatch", lazy="joined")
