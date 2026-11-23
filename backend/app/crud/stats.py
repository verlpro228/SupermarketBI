from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


def count_products(db: Session) -> int:
    return (
        db.execute(text("SELECT COUNT(*) FROM product WHERE status = 1")).scalar() or 0
    )


def sum_stock(db: Session) -> Decimal:
    value = db.execute(
        text(
            """
            SELECT COALESCE(SUM(i.total_qty), 0)
            FROM inventory i
            JOIN product p ON p.id = i.product_id
            WHERE p.status = 1
            """
        )
    ).scalar()
    return Decimal(value or 0)


def sum_stock_value(db: Session) -> Decimal:
    value = db.execute(
        text(
            """
            SELECT COALESCE(SUM(i.total_qty * p.purchase_price), 0)
            FROM inventory i
            JOIN product p ON p.id = i.product_id
            WHERE p.status = 1
            """
        )
    ).scalar()
    return Decimal(value or 0)


def count_expiry_products(db: Session, warning_days: int) -> int:
    return (
        db.execute(
            text(
                """
                SELECT COUNT(DISTINCT b.product_id)
                FROM inventory_batch b
                JOIN product p ON p.id = b.product_id
                WHERE b.qty_remaining > 0
                  AND p.status = 1
                  AND DATEDIFF(b.expiry_date, CURDATE()) <= :warning_days
                """
            ),
            {"warning_days": warning_days},
        ).scalar()
        or 0
    )


def category_stock_values(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT c.name AS category,
                   SUM(i.total_qty * p.purchase_price) AS value
            FROM product p
            JOIN category c ON c.id = p.category_id
            JOIN inventory i ON i.product_id = p.id
            WHERE p.status = 1 AND i.total_qty > 0
            GROUP BY c.name
            ORDER BY value DESC
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def _trend(
    db: Session, table: str, quantity_column: str, start_date: date, fmt: str
) -> dict[str, Decimal]:
    rows = db.execute(
        text(
            f"""
            SELECT DATE_FORMAT(created_at, :fmt) AS label,
                   SUM({quantity_column}) AS qty
            FROM {table}
            WHERE DATE(created_at) >= :start_date
            GROUP BY label
            """
        ),
        {"fmt": fmt, "start_date": start_date},
    ).mappings().all()
    return {row["label"]: Decimal(row["qty"] or 0) for row in rows}


def inbound_trend(db: Session, start_date: date, fmt: str) -> dict[str, Decimal]:
    return _trend(db, "inbound_order", "quantity", start_date, fmt)


def outbound_trend(db: Session, start_date: date, fmt: str) -> dict[str, Decimal]:
    return _trend(db, "outbound_order", "total_qty", start_date, fmt)


def category_flow(db: Session, start_date: date) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT c.name AS category,
                   SUM(CASE WHEN t.dir = 'in' THEN t.qty ELSE 0 END) AS inbound,
                   SUM(CASE WHEN t.dir = 'out' THEN t.qty ELSE 0 END) AS outbound
            FROM (
                SELECT p.category_id, 'in' AS dir, io.quantity AS qty
                FROM inbound_order io
                JOIN product p ON p.id = io.product_id
                WHERE DATE(io.created_at) >= :start_date

                UNION ALL

                SELECT p.category_id, 'out' AS dir, oo.total_qty AS qty
                FROM outbound_order oo
                JOIN (
                    SELECT outbound_id, MIN(product_id) AS product_id
                    FROM outbound_item
                    GROUP BY outbound_id
                ) oi ON oi.outbound_id = oo.id
                JOIN product p ON p.id = oi.product_id
                WHERE DATE(oo.created_at) >= :start_date
            ) t
            JOIN category c ON c.id = t.category_id
            GROUP BY c.name
            ORDER BY inbound DESC
            """
        ),
        {"start_date": start_date},
    ).mappings().all()
    return [dict(row) for row in rows]


def expiry_distribution(db: Session, urgent_days: int, warning_days: int) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT CASE
                     WHEN DATEDIFF(b.expiry_date, CURDATE()) < 0 THEN 'expired'
                     WHEN DATEDIFF(b.expiry_date, CURDATE()) <= :urgent_days THEN 'urgent'
                     ELSE 'warning'
                   END AS level,
                   COUNT(*) AS count
            FROM inventory_batch b
            JOIN product p ON p.id = b.product_id
            WHERE b.qty_remaining > 0
              AND p.status = 1
              AND DATEDIFF(b.expiry_date, CURDATE()) <= :warning_days
            GROUP BY level
            """
        ),
        {"urgent_days": urgent_days, "warning_days": warning_days},
    ).mappings().all()
    return [dict(row) for row in rows]


def top_value_products(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT p.name AS name,
                   ROUND(i.total_qty * p.purchase_price, 2) AS value
            FROM inventory i
            JOIN product p ON p.id = i.product_id
            WHERE p.status = 1 AND i.total_qty > 0
            ORDER BY value DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]


def low_stock_products(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT p.name AS name,
                   ROUND(p.safe_stock - COALESCE(i.total_qty, 0), 3) AS gap
            FROM product p
            LEFT JOIN inventory i ON i.product_id = p.id
            WHERE p.status = 1
              AND COALESCE(i.total_qty, 0) < p.safe_stock
            ORDER BY gap DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]


def inbound_daily(db: Session, start_date: date) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT DATE_FORMAT(created_at, '%Y-%m-%d') AS label,
                   SUM(quantity) AS quantity,
                   COUNT(*) AS orders
            FROM inbound_order
            WHERE DATE(created_at) >= :start_date
            GROUP BY label
            """
        ),
        {"start_date": start_date},
    ).mappings().all()
    return [dict(row) for row in rows]


def outbound_daily(db: Session, start_date: date) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT DATE_FORMAT(created_at, '%Y-%m-%d') AS label,
                   SUM(total_qty) AS quantity,
                   COUNT(*) AS orders
            FROM outbound_order
            WHERE DATE(created_at) >= :start_date
            GROUP BY label
            """
        ),
        {"start_date": start_date},
    ).mappings().all()
    return [dict(row) for row in rows]


def supplier_ranking(db: Session, start_date: date, limit: int = 8) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT COALESCE(NULLIF(TRIM(supplier), ''), '未填写') AS supplier,
                   SUM(quantity) AS quantity,
                   COUNT(*) AS orders
            FROM inbound_order
            WHERE DATE(created_at) >= :start_date
            GROUP BY supplier
            ORDER BY quantity DESC
            LIMIT :limit
            """
        ),
        {"start_date": start_date, "limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]


def category_inbound(db: Session, start_date: date) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT c.name AS category,
                   SUM(io.quantity) AS quantity
            FROM inbound_order io
            JOIN product p ON p.id = io.product_id
            JOIN category c ON c.id = p.category_id
            WHERE DATE(io.created_at) >= :start_date
            GROUP BY c.name
            ORDER BY quantity DESC
            """
        ),
        {"start_date": start_date},
    ).mappings().all()
    return [dict(row) for row in rows]


def outbound_type_distribution(db: Session, start_date: date) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT outbound_type AS type,
                   SUM(total_qty) AS quantity,
                   COUNT(*) AS orders
            FROM outbound_order
            WHERE DATE(created_at) >= :start_date
            GROUP BY outbound_type
            """
        ),
        {"start_date": start_date},
    ).mappings().all()
    return [dict(row) for row in rows]


def top_outbound_products(db: Session, start_date: date, limit: int = 8) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT p.name AS name,
                   SUM(oo.total_qty) AS quantity
            FROM outbound_order oo
            JOIN (
                SELECT outbound_id, MIN(product_id) AS product_id
                FROM outbound_item
                GROUP BY outbound_id
            ) oi ON oi.outbound_id = oo.id
            JOIN product p ON p.id = oi.product_id
            WHERE DATE(oo.created_at) >= :start_date
            GROUP BY p.name
            ORDER BY quantity DESC
            LIMIT :limit
            """
        ),
        {"start_date": start_date, "limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]
