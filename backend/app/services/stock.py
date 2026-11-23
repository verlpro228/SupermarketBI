from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.crud import inventory as inventory_crud
from app.crud import stock as stock_crud
from app.models.adjust import StockAdjustLog
from app.models.inventory import Inventory
from app.models.user import User
from app.schemas.stock import (
    StockAdjustPayload,
    StockAdminOut,
    StockBatchOut,
    StockChangeRecord,
    StockOut,
    StockQuery,
)


def _get_stock_for_update(db: Session, product_id: int) -> Inventory:
    stmt = select(Inventory).where(Inventory.product_id == product_id).with_for_update()
    inventory = db.scalar(stmt)
    if inventory is None:
        inventory = Inventory(product_id=product_id, total_qty=Decimal("0"))
        db.add(inventory)
        db.flush()
    return inventory


def list_stock(
    db: Session, query: StockQuery, is_admin: bool
) -> tuple[list[StockOut], int]:
    rows, total = stock_crud.list_stock(db, query)
    today = date.today()

    items: list[StockOut] = []
    for row in rows:
        total_qty = float(row["total_qty"])
        safe_stock = float(row["safe_stock"])
        nearest_expiry: date | None = row["nearest_expiry"]
        days_left = (nearest_expiry - today).days if nearest_expiry else None

        base = {
            "product_id": row["product_id"],
            "barcode": row["barcode"],
            "name": row["name"],
            "category_id": row["category_id"],
            "category_name": row["category_name"],
            "unit": row["unit"],
            "total_qty": total_qty,
            "safe_stock": safe_stock,
            "nearest_expiry": nearest_expiry,
            "days_left": days_left,
            "product_status": row["product_status"],
            "is_low_stock": total_qty < safe_stock,
        }

        if is_admin:
            purchase_price = float(row["purchase_price"])
            items.append(
                StockAdminOut(
                    **base,
                    purchase_price=purchase_price,
                    stock_value=round(total_qty * purchase_price, 2),
                )
            )
        else:
            items.append(StockOut(**base))

    return items, total


def list_records(
    db: Session, product_id: int, page: int, page_size: int
) -> tuple[list[StockChangeRecord], int]:
    rows, total = stock_crud.list_records(db, product_id, page, page_size)
    items = [StockChangeRecord(**row) for row in rows]
    return items, total


def list_batches(db: Session, product_id: int) -> list[StockBatchOut]:
    rows = stock_crud.get_batches(db, product_id)
    return [StockBatchOut(**row) for row in rows]


def adjust_stock(db: Session, payload: StockAdjustPayload, operator: User) -> None:
    batch = inventory_crud.get_batch(db, payload.batch_id, for_update=True)
    if batch is None:
        raise BusinessError("批次不存在")
    if batch.product_id != payload.product_id:
        raise BusinessError("批次与商品不匹配")

    before_qty = Decimal(batch.qty_remaining)
    after_qty = Decimal(str(payload.new_qty)).quantize(Decimal("0.001"))
    diff = after_qty - before_qty

    if diff == 0:
        raise BusinessError("调整前后数量相同，无需调整")

    inventory = _get_stock_for_update(db, payload.product_id)
    new_total = Decimal(inventory.total_qty) + diff

    if new_total < 0:
        raise BusinessError("调整后商品库存不能为负数")

    try:
        batch.qty_remaining = after_qty
        inventory.total_qty = new_total

        db.add(
            StockAdjustLog(
                product_id=payload.product_id,
                batch_id=payload.batch_id,
                before_qty=before_qty,
                after_qty=after_qty,
                diff_qty=diff,
                reason=payload.reason.strip(),
                operator_id=operator.id,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
