from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session


def generate_order_no(db: Session, prefix: str, model: type) -> str:
    """生成业务单号：前缀 + yyyyMMdd + 4 位当日流水，如 RK202611230001。"""
    date_str = datetime.now().strftime("%Y%m%d")
    pattern = f"{prefix}{date_str}"

    last_no = db.scalar(
        select(model.order_no)
        .where(model.order_no.like(f"{pattern}%"))
        .order_by(model.order_no.desc())
        .limit(1)
    )

    seq = 1
    if last_no:
        try:
            seq = int(last_no[len(pattern) :]) + 1
        except ValueError:
            seq = 1

    return f"{pattern}{seq:04d}"


def generate_batch_no() -> str:
    """生成批次号，时间前缀便于阅读，随机后缀保证唯一。"""
    return f"B{datetime.now().strftime('%Y%m%d')}{uuid4().hex[:8].upper()}"
