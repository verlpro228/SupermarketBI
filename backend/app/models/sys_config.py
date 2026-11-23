from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SysConfig(Base):
    __tablename__ = "sys_config"
    __table_args__ = {"comment": "系统配置项"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="配置键"
    )
    config_value: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="配置值"
    )
    description: Mapped[str | None] = mapped_column(String(255), comment="说明")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
