from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.stock import StockQuery

_STOCK_BASE = """
SELECT p.id AS product_id,
       p.barcode,
       p.name,
       p.category_id,
       c.name AS category_name,
       p.unit,
       p.safe_stock,
       p.purchase_price,
       p.status AS product_status,
       COALESCE(i.total_qty, 0) AS total_qty,
       nb.nearest_expiry
FROM product p
LEFT JOIN category c ON c.id = p.category_id
LEFT JOIN inventory i ON i.product_id = p.id
LEFT JOIN (
    SELECT product_id, MIN(expiry_date) AS nearest_expiry
    FROM inventory_batch
    WHERE qty_remaining > 0
    GROUP BY product_id
) nb ON nb.product_id = p.id
WHERE 1 = 1
"""

_RECORD_BASE = """
SELECT * FROM (
    SELECT 'inbound' AS record_type,
           io.order_no,
           b.batch_no,
           io.quantity,
           io.amount,
           b.production_date,
           b.expiry_date,
           DATEDIFF(b.expiry_date, CURDATE()) AS days_left,
           io.supplier,
           NULL AS outbound_type,
           io.remark AS reason,
           u.username AS operator_name,
           io.created_at
    FROM inbound_order io
    LEFT JOIN inventory_batch b ON b.inbound_id = io.id
    LEFT JOIN sys_user u ON u.id = io.operator_id
    WHERE io.product_id = :product_id

    UNION ALL

    SELECT 'outbound' AS record_type,
           oo.order_no,
           b.batch_no,
           oi.quantity,
           oi.amount,
           b.production_date,
           b.expiry_date,
           DATEDIFF(b.expiry_date, CURDATE()) AS days_left,
           NULL AS supplier,
           oo.outbound_type,
           oo.reason,
           u.username AS operator_name,
           oo.created_at
    FROM outbound_item oi
    JOIN outbound_order oo ON oo.id = oi.outbound_id
    JOIN inventory_batch b ON b.id = oi.batch_id
    LEFT JOIN sys_user u ON u.id = oo.operator_id
    WHERE oi.product_id = :product_id
) t
"""


def list_stock(db: Session, query: StockQuery):
    where_sql = ""
    params: dict = {}

    if query.keyword:
        where_sql += " AND (p.name LIKE :keyword OR p.barcode LIKE :keyword)"
        params["keyword"] = f"%{query.keyword.strip()}%"
    if query.category_id:
        where_sql += " AND p.category_id = :category_id"
        params["category_id"] = query.category_id
    if query.status is not None:
        where_sql += " AND p.status = :status"
        params["status"] = query.status

    total = db.execute(
        text("SELECT COUNT(*) FROM product p WHERE 1 = 1" + where_sql), params
    ).scalar() or 0

    rows = db.execute(
        text(
            _STOCK_BASE
            + where_sql
            + " ORDER BY p.id DESC LIMIT :limit OFFSET :offset"
        ),
        {
            **params,
            "limit": query.page_size,
            "offset": (query.page - 1) * query.page_size,
        },
    ).mappings().all()

    return rows, total


def list_records(db: Session, product_id: int, page: int, page_size: int):
    total = db.execute(
        text(f"SELECT COUNT(*) FROM ({_RECORD_BASE}) t"), {"product_id": product_id}
    ).scalar() or 0

    rows = db.execute(
        text(
            _RECORD_BASE
            + " ORDER BY t.created_at DESC, t.order_no DESC LIMIT :limit OFFSET :offset"
        ),
        {
            "product_id": product_id,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    ).mappings().all()

    return rows, total


def get_batches(db: Session, product_id: int):
    rows = db.execute(
        text(
            """
            SELECT b.id AS batch_id,
                   b.batch_no,
                   b.production_date,
                   b.expiry_date,
                   b.qty_remaining,
                   b.cost_price,
                   DATEDIFF(b.expiry_date, CURDATE()) AS days_left
            FROM inventory_batch b
            WHERE b.product_id = :product_id AND b.qty_remaining > 0
            ORDER BY b.expiry_date ASC, b.id ASC
            """
        ),
        {"product_id": product_id},
    ).mappings().all()
    return rows
