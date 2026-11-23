from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.inspection import InspectionItem, InspectionRecord
from app.schemas.inspection import InspectionQuery

_LIST_BASE = """
SELECT r.id,
       u.username AS inspector_name,
       r.hit_count,
       r.created_at,
       COALESCE(SUM(CASE WHEN i.problem_type = 'low_stock' THEN 1 ELSE 0 END), 0) AS low_stock_count,
       COALESCE(SUM(CASE WHEN i.problem_type = 'near_expiry' THEN 1 ELSE 0 END), 0) AS near_expiry_count,
       COALESCE(SUM(CASE WHEN i.status = 'pending' THEN 1 ELSE 0 END), 0) AS pending_count
FROM inspection_record r
LEFT JOIN sys_user u ON u.id = r.inspector_id
LEFT JOIN inspection_item i ON i.record_id = r.id
WHERE 1 = 1
"""


def scan_low_stock(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT p.id AS product_id,
                   p.safe_stock,
                   COALESCE(i.total_qty, 0) AS total_qty
            FROM product p
            LEFT JOIN inventory i ON i.product_id = p.id
            WHERE p.status = 1
              AND COALESCE(i.total_qty, 0) < p.safe_stock
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def scan_near_expiry(db: Session, warning_days: int) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT b.product_id,
                   b.id AS batch_id,
                   DATEDIFF(b.expiry_date, CURDATE()) AS days_left
            FROM inventory_batch b
            JOIN product p ON p.id = b.product_id
            WHERE b.qty_remaining > 0
              AND p.status = 1
              AND DATEDIFF(b.expiry_date, CURDATE()) <= :warning_days
            """
        ),
        {"warning_days": warning_days},
    ).mappings().all()
    return [dict(row) for row in rows]


def create_record(db: Session, inspector_id: int, hit_count: int) -> InspectionRecord:
    record = InspectionRecord(inspector_id=inspector_id, hit_count=hit_count)
    db.add(record)
    db.flush()
    return record


def create_items(db: Session, items: list[InspectionItem]) -> None:
    db.add_all(items)
    db.flush()


def list_records(db: Session, query: InspectionQuery):
    params: dict = {}
    extra = ""

    if query.start_date:
        extra += " AND DATE(r.created_at) >= :start_date"
        params["start_date"] = query.start_date
    if query.end_date:
        extra += " AND DATE(r.created_at) <= :end_date"
        params["end_date"] = query.end_date

    total = db.execute(
        text("SELECT COUNT(*) FROM inspection_record r WHERE 1 = 1" + extra), params
    ).scalar() or 0

    rows = db.execute(
        text(
            _LIST_BASE
            + extra
            + " GROUP BY r.id, u.username, r.hit_count, r.created_at"
            + " ORDER BY r.created_at DESC, r.id DESC LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": query.page_size, "offset": (query.page - 1) * query.page_size},
    ).mappings().all()

    return rows, total


def get_record(db: Session, record_id: int) -> InspectionRecord | None:
    return db.get(InspectionRecord, record_id)


def get_items(db: Session, record_id: int) -> list[InspectionItem]:
    rows = db.execute(
        text(
            """
            SELECT i.id, i.product_id, p.name AS product_name, p.barcode, p.unit,
                   i.batch_id, b.batch_no, i.problem_type, i.gap_qty, i.days_left,
                   i.status, i.handled_at
            FROM inspection_item i
            JOIN product p ON p.id = i.product_id
            LEFT JOIN inventory_batch b ON b.id = i.batch_id
            WHERE i.record_id = :record_id
            ORDER BY i.problem_type ASC, i.days_left ASC, i.id ASC
            """
        ),
        {"record_id": record_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def get_items_by_ids(db: Session, ids: list[int]) -> list[InspectionItem]:
    return [item for item in (db.get(InspectionItem, item_id) for item_id in ids) if item]
