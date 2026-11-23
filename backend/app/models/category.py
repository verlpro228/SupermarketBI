from sqlalchemy import BigInteger, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    __tablename__ = "category"
    __table_args__ = {"comment": "商品分类"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="分类名称"
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, comment="排序号"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="1 启用 0 停用"
    )
