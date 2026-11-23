from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.crud import inspection as inspection_crud
from app.models.inspection import InspectionItem
from app.models.user import User
from app.schemas.inspection import (
    InspectionDetailOut,
    InspectionItemOut,
    InspectionItemStatusPayload,
    InspectionOut,
    InspectionQuery,
)
from app.utils.config import get_expiry_thresholds


def _to_out(record, inspector_name: str | None) -> InspectionOut:
    return InspectionOut(
        id=record.id,
        inspector_name=inspector_name,
        hit_count=record.hit_count,
        created_at=record.created_at,
    )


def run_inspection(db: Session, operator: User) -> InspectionDetailOut:
    _, warning_days = get_expiry_thresholds(db)

    low_stock_rows = inspection_crud.scan_low_stock(db)
    near_expiry_rows = inspection_crud.scan_near_expiry(db, warning_days)

    items: list[InspectionItem] = []

    for row in low_stock_rows:
        gap = Decimal(row["safe_stock"]) - Decimal(row["total_qty"])
        items.append(
            InspectionItem(
                product_id=row["product_id"],
                batch_id=None,
                problem_type="low_stock",
                gap_qty=gap if gap > 0 else Decimal("0"),
                days_left=None,
                status="pending",
            )
        )

    for row in near_expiry_rows:
        items.append(
            InspectionItem(
                product_id=row["product_id"],
                batch_id=row["batch_id"],
                problem_type="near_expiry",
                gap_qty=None,
                days_left=row["days_left"],
                status="pending",
            )
        )

    try:
        record = inspection_crud.create_record(db, operator.id, len(items))
        for item in items:
            item.record_id = record.id
        if items:
            inspection_crud.create_items(db, items)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(record)

    return InspectionDetailOut(
        id=record.id,
        inspector_name=operator.real_name or operator.username,
        hit_count=record.hit_count,
        low_stock_count=len(low_stock_rows),
        near_expiry_count=len(near_expiry_rows),
        pending_count=len(items),
        created_at=record.created_at,
        items=[
            InspectionItemOut(
                id=item.id,
                product_id=item.product_id,
                problem_type=item.problem_type,
                gap_qty=float(item.gap_qty) if item.gap_qty is not None else None,
                days_left=item.days_left,
                status=item.status,
            )
            for item in items
        ],
    )


def list_records(db: Session, query: InspectionQuery) -> tuple[list[InspectionOut], int]:
    rows, total = inspection_crud.list_records(db, query)
    items = [
        InspectionOut(
            id=row["id"],
            inspector_name=row["inspector_name"],
            hit_count=row["hit_count"],
            low_stock_count=int(row["low_stock_count"]),
            near_expiry_count=int(row["near_expiry_count"]),
            pending_count=int(row["pending_count"]),
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return items, total


def get_detail(db: Session, record_id: int) -> InspectionDetailOut:
    record = inspection_crud.get_record(db, record_id)
    if record is None:
        raise BusinessError("巡检记录不存在")

    raw_items = inspection_crud.get_items(db, record_id)

    item_outs = [
        InspectionItemOut(
            id=row["id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            barcode=row["barcode"],
            unit=row["unit"],
            batch_id=row["batch_id"],
            batch_no=row["batch_no"],
            problem_type=row["problem_type"],
            gap_qty=float(row["gap_qty"]) if row["gap_qty"] is not None else None,
            days_left=row["days_left"],
            status=row["status"],
            handled_at=row["handled_at"],
        )
        for row in raw_items
    ]

    return InspectionDetailOut(
        id=record.id,
        inspector_name=(
            (record.inspector.real_name or record.inspector.username)
            if record.inspector
            else None
        ),
        hit_count=record.hit_count,
        low_stock_count=sum(1 for i in item_outs if i.problem_type == "low_stock"),
        near_expiry_count=sum(1 for i in item_outs if i.problem_type == "near_expiry"),
        pending_count=sum(1 for i in item_outs if i.status == "pending"),
        created_at=record.created_at,
        items=item_outs,
    )


def update_item_status(db: Session, payload: InspectionItemStatusPayload) -> int:
    items = inspection_crud.get_items_by_ids(db, payload.ids)
    if len(items) != len(set(payload.ids)):
        raise BusinessError("部分巡检明细不存在")

    now = datetime.now()

    try:
        for item in items:
            item.status = payload.status
            item.handled_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise

    return len(items)
