from datetime import datetime

from sqlalchemy import BigInteger, DateTime, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "sys_user"
    __table_args__ = {"comment": "系统用户"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="登录账号"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    real_name: Mapped[str | None] = mapped_column(String(50), comment="姓名")
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="keeper", index=True, comment="admin/keeper"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="1 启用 0 禁用"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后登录时间"
    )
