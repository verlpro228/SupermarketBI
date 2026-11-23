from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InboundOrder(Base):
    __tablename__ = "inbound_order"
    __table_args__ = {"comment": "入库单"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, comment="入库单号"
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True, comment="商品ID"
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, comment="入库数量")
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="入库进价"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, comment="入库金额（后端计算）"
    )
    production_date: Mapped[date] = mapped_column(Date, nullable=False, comment="生产日期")
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, comment="到期日")
    supplier: Mapped[str | None] = mapped_column(String(128), comment="供应商")
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="操作人ID"
    )
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True, comment="创建时间"
    )

    product: Mapped["Product"] = relationship("Product", lazy="joined")
    operator: Mapped["User"] = relationship("User", lazy="joined")
