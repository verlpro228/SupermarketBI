from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.expiry import ExpiryActionQuery, ExpiryQuery

_LEVEL_CONDITION = {
    "expired": "DATEDIFF(b.expiry_date, CURDATE()) < 0",
    "urgent": "DATEDIFF(b.expiry_date, CURDATE()) BETWEEN 0 AND :urgent_days",
    "warning": (
        "DATEDIFF(b.expiry_date, CURDATE()) > :urgent_days "
        "AND DATEDIFF(b.expiry_date, CURDATE()) <= :warning_days"
    ),
}

_BATCH_BASE = """
SELECT b.id AS batch_id,
       b.batch_no,
       b.product_id,
       p.name AS product_name,
       p.barcode,
       p.unit,
       p.category_id,
       c.name AS category_name,
       p.purchase_price,
       b.production_date,
       b.expiry_date,
       b.qty_remaining,
       b.cost_price,
       b.is_promo,
       DATEDIFF(b.expiry_date, CURDATE()) AS days_left
FROM inventory_batch b
JOIN product p ON p.id = b.product_id
LEFT JOIN category c ON c.id = p.category_id
WHERE b.qty_remaining > 0
  AND b.is_promo = 0
  AND DATEDIFF(b.expiry_date, CURDATE()) <= :warning_days
"""

_ACTION_BASE = """
SELECT l.id,
       l.product_id,
       p.name AS product_name,
       p.barcode,
       l.batch_id,
       b.batch_no,
       l.action,
       l.quantity,
       u.username AS operator_name,
       oo.order_no,
       l.created_at
FROM expiry_action_log l
JOIN product p ON p.id = l.product_id
LEFT JOIN inventory_batch b ON b.id = l.batch_id
LEFT JOIN sys_user u ON u.id = l.operator_id
LEFT JOIN outbound_order oo ON oo.id = l.outbound_id
WHERE 1 = 1
"""


def list_expiry_batches(
    db: Session, query: ExpiryQuery, urgent_days: int, warning_days: int
):
    params: dict = {"urgent_days": urgent_days, "warning_days": warning_days}
    extra = ""

    if query.level:
        extra += f" AND {_LEVEL_CONDITION[query.level]}"
    if query.category_id:
        extra += " AND p.category_id = :category_id"
        params["category_id"] = query.category_id
    if query.keyword:
        extra += " AND (p.name LIKE :keyword OR p.barcode LIKE :keyword)"
        params["keyword"] = f"%{query.keyword.strip()}%"

    total = db.execute(
        text(f"SELECT COUNT(*) FROM ({_BATCH_BASE}{extra}) t"), params
    ).scalar() or 0

    rows = db.execute(
        text(
            _BATCH_BASE
            + extra
            + " ORDER BY days_left ASC, b.expiry_date ASC, b.id ASC"
            + " LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": query.page_size, "offset": (query.page - 1) * query.page_size},
    ).mappings().all()

    return rows, total


def list_action_logs(db: Session, query: ExpiryActionQuery):
    params: dict = {}
    extra = ""

    if query.action:
        extra += " AND l.action = :action"
        params["action"] = query.action
    if query.keyword:
        extra += " AND (p.name LIKE :keyword OR p.barcode LIKE :keyword)"
        params["keyword"] = f"%{query.keyword.strip()}%"

    total = db.execute(
        text(f"SELECT COUNT(*) FROM ({_ACTION_BASE}{extra}) t"), params
    ).scalar() or 0

    rows = db.execute(
        text(
            _ACTION_BASE
            + extra
            + " ORDER BY l.created_at DESC, l.id DESC LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": query.page_size, "offset": (query.page - 1) * query.page_size},
    ).mappings().all()

    return rows, total
