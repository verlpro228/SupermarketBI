from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sys_config import SysConfig

EXPIRY_URGENT_KEY = "expiry_urgent_days"
EXPIRY_WARNING_KEY = "expiry_warning_days"

DEFAULT_URGENT_DAYS = 7
DEFAULT_WARNING_DAYS = 30


def get_config_int(db: Session, key: str, default: int) -> int:
    value = db.scalar(select(SysConfig.config_value).where(SysConfig.config_key == key))
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_expiry_thresholds(db: Session) -> tuple[int, int]:
    """返回 (紧急阈值, 预警阈值)，默认 7 天与 30 天。"""
    urgent = get_config_int(db, EXPIRY_URGENT_KEY, DEFAULT_URGENT_DAYS)
    warning = get_config_int(db, EXPIRY_WARNING_KEY, DEFAULT_WARNING_DAYS)
    if warning < urgent:
        warning = urgent
    return urgent, warning


def resolve_expiry_level(days_left: int, urgent_days: int, warning_days: int) -> str:
    if days_left < 0:
        return "expired"
    if days_left <= urgent_days:
        return "urgent"
    if days_left <= warning_days:
        return "warning"
    return "normal"
