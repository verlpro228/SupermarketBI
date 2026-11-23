from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.crud import expiry as expiry_crud
from app.crud import inventory as inventory_crud
from app.crud import outbound as outbound_crud
from app.models.expiry import ExpiryActionLog
from app.models.inventory import Inventory, InventoryBatch
from app.models.outbound import OutboundOrder
from app.models.user import User
from app.schemas.expiry import (
    ExpiryActionLogOut,
    ExpiryActionQuery,
    ExpiryBatchAdminOut,
    ExpiryBatchOut,
    ExpiryLossPayload,
    ExpiryPromoPayload,
    ExpiryQuery,
    ExpiryThresholds,
)
from app.utils.config import get_expiry_thresholds, resolve_expiry_level
from app.utils.order_no import generate_order_no


def _qty(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def list_expiry_batches(
    db: Session, query: ExpiryQuery, is_admin: bool
) -> tuple[list[ExpiryBatchOut], int, ExpiryThresholds]:
    urgent_days, warning_days = get_expiry_thresholds(db)
    rows, total = expiry_crud.list_expiry_batches(db, query, urgent_days, warning_days)

    items: list[ExpiryBatchOut] = []
    for row in rows:
        days_left = int(row["days_left"])
        base = {
            "batch_id": row["batch_id"],
            "batch_no": row["batch_no"],
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "barcode": row["barcode"],
            "unit": row["unit"],
            "category_id": row["category_id"],
            "category_name": row["category_name"],
            "production_date": row["production_date"],
            "expiry_date": row["expiry_date"],
            "days_left": days_left,
            "qty_remaining": float(row["qty_remaining"]),
            "level": resolve_expiry_level(days_left, urgent_days, warning_days),
            "is_promo": row["is_promo"],
        }

        if is_admin:
            cost_price = float(row["purchase_price"])
            items.append(
                ExpiryBatchAdminOut(
                    **base,
                    cost_price=cost_price,
                    stock_value=round(float(row["qty_remaining"]) * cost_price, 2),
                )
            )
        else:
            items.append(ExpiryBatchOut(**base))

    return items, total, ExpiryThresholds(
        urgent_days=urgent_days, warning_days=warning_days
    )


def _lock_inventory(db: Session, product_id: int) -> Inventory:
    inventory = db.scalar(
        select(Inventory).where(Inventory.product_id == product_id).with_for_update()
    )
    if inventory is None:
        raise BusinessError("商品库存记录不存在，请先执行库存巡检")
    return inventory


def _loss_one(
    db: Session,
    batch: InventoryBatch,
    quantity: Decimal,
    reason: str,
    operator: User,
) -> None:
    remaining = Decimal(batch.qty_remaining)
    if quantity > remaining:
        raise BusinessError(
            f"批次 {batch.batch_no} 剩余 {float(remaining)}，不足以报损 {float(quantity)}"
        )

    inventory = _lock_inventory(db, batch.product_id)
    total_qty = Decimal(inventory.total_qty)
    if total_qty < quantity:
        raise BusinessError("商品汇总库存不足，请先执行库存巡检")

    inventory.total_qty = total_qty - quantity
    batch.qty_remaining = remaining - quantity

    order_no = generate_order_no(db, "CK", OutboundOrder)
    amount = _money(quantity * Decimal(batch.cost_price))

    order = outbound_crud.create_order(
        db,
        order_no=order_no,
        outbound_type="loss",
        total_qty=quantity,
        total_amount=amount,
        reason=reason,
        operator_id=operator.id,
        remark="临期处理报损",
    )
    outbound_crud.create_item(
        db,
        outbound_id=order.id,
        product_id=batch.product_id,
        batch_id=batch.id,
        quantity=quantity,
        cost_price=batch.cost_price,
        amount=amount,
    )

    db.add(
        ExpiryActionLog(
            product_id=batch.product_id,
            batch_id=batch.id,
            action="loss",
            quantity=quantity,
            outbound_id=order.id,
            operator_id=operator.id,
        )
    )


def batch_loss(db: Session, payload: ExpiryLossPayload, operator: User) -> int:
    """批量报损，每批次生成一笔报损出库单，同一事务内完成。"""
    reason = payload.reason.strip()

    try:
        # 按批次ID排序，避免并发时锁顺序不一致导致死锁
        for item in sorted(payload.items, key=lambda x: x.batch_id):
            batch = inventory_crud.get_batch(db, item.batch_id, for_update=True)
            if batch is None:
                raise BusinessError("批次不存在")
            _loss_one(db, batch, _qty(item.quantity), reason, operator)

        db.commit()
    except Exception:
        db.rollback()
        raise

    return len(payload.items)


def mark_promo(db: Session, payload: ExpiryPromoPayload, operator: User) -> None:
    batch = inventory_crud.get_batch(db, payload.batch_id, for_update=True)
    if batch is None:
        raise BusinessError("批次不存在")
    if batch.is_promo == 1:
        raise BusinessError("该批次已标记促销")

    try:
        batch.is_promo = 1
        db.add(
            ExpiryActionLog(
                product_id=batch.product_id,
                batch_id=batch.id,
                action="promo",
                quantity=Decimal("0"),
                operator_id=operator.id,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_action_logs(
    db: Session, query: ExpiryActionQuery
) -> tuple[list[ExpiryActionLogOut], int]:
    rows, total = expiry_crud.list_action_logs(db, query)
    items = [
        ExpiryActionLogOut(
            id=row["id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            barcode=row["barcode"],
            batch_id=row["batch_id"],
            batch_no=row["batch_no"],
            action=row["action"],
            quantity=float(row["quantity"]),
            order_no=row["order_no"],
            operator_name=row["operator_name"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return items, total
