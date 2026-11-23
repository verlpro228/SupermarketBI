from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.crud import outbound as outbound_crud
from app.crud import product as product_crud
from app.models.inventory import Inventory, InventoryBatch
from app.models.outbound import OutboundOrder
from app.models.user import User
from app.schemas.outbound import (
    OutboundCreate,
    OutboundItemOut,
    OutboundOut,
    OutboundQuery,
)
from app.utils.order_no import generate_order_no


def _qty(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _batch_item(item) -> OutboundItemOut:
    return OutboundItemOut(
        batch_id=item.batch_id,
        batch_no=item.batch.batch_no if item.batch else None,
        quantity=float(item.quantity),
        cost_price=float(item.cost_price),
        amount=float(item.amount),
        production_date=item.batch.production_date if item.batch else None,
        expiry_date=item.batch.expiry_date if item.batch else None,
    )


def create_outbound(db: Session, payload: OutboundCreate, operator: User) -> OutboundOut:
    product = product_crud.get_by_id(db, payload.product_id)
    if product is None:
        raise BusinessError("商品不存在")
    if product.status != 1:
        raise BusinessError("商品已停用，无法出库")

    quantity = _qty(payload.quantity)

    try:
        # 1. 锁定商品库存汇总，校验并扣减，杜绝负库存
        inventory = db.scalar(
            select(Inventory)
            .where(Inventory.product_id == product.id)
            .with_for_update()
        )
        available = Decimal(inventory.total_qty) if inventory else Decimal("0")
        if available < quantity:
            raise BusinessError(
                f"库存不足，当前库存 {float(available)}，无法出库 {float(quantity)}"
            )

        inventory.total_qty = available - quantity

        # 2. 按到期日升序锁定批次，先进先出扣减
        batches = list(
            db.scalars(
                select(InventoryBatch)
                .where(
                    InventoryBatch.product_id == product.id,
                    InventoryBatch.qty_remaining > 0,
                )
                .order_by(InventoryBatch.expiry_date.asc(), InventoryBatch.id.asc())
                .with_for_update()
            ).all()
        )

        remaining = quantity
        allocations: list[tuple[InventoryBatch, Decimal]] = []

        for batch in batches:
            if remaining <= 0:
                break
            batch_qty = Decimal(batch.qty_remaining)
            take = min(batch_qty, remaining)
            if take <= 0:
                continue
            batch.qty_remaining = batch_qty - take
            remaining -= take
            allocations.append((batch, take))

        if remaining > 0:
            raise BusinessError("批次可用数量不足，库存数据异常，请先执行库存巡检")

        # 3. 写出库单与明细
        order_no = generate_order_no(db, "CK", OutboundOrder)
        total_amount = _money(
            sum((take * Decimal(batch.cost_price) for batch, take in allocations), Decimal("0"))
        )

        order = outbound_crud.create_order(
            db,
            order_no=order_no,
            outbound_type=payload.outbound_type,
            total_qty=quantity,
            total_amount=total_amount,
            reason=payload.reason.strip() if payload.reason else None,
            operator_id=operator.id,
            remark=payload.remark,
        )

        item_outs: list[OutboundItemOut] = []
        for batch, take in allocations:
            amount = _money(take * Decimal(batch.cost_price))
            outbound_crud.create_item(
                db,
                outbound_id=order.id,
                product_id=product.id,
                batch_id=batch.id,
                quantity=take,
                cost_price=batch.cost_price,
                amount=amount,
            )
            item_outs.append(
                OutboundItemOut(
                    batch_id=batch.id,
                    batch_no=batch.batch_no,
                    quantity=float(take),
                    cost_price=float(batch.cost_price),
                    amount=float(amount),
                    production_date=batch.production_date,
                    expiry_date=batch.expiry_date,
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return OutboundOut(
        id=order.id,
        order_no=order.order_no,
        product_id=product.id,
        product_name=product.name,
        barcode=product.barcode,
        unit=product.unit,
        outbound_type=order.outbound_type,
        total_qty=float(order.total_qty),
        total_amount=float(order.total_amount),
        reason=order.reason,
        operator_name=operator.real_name or operator.username,
        remark=order.remark,
        created_at=order.created_at,
        items=item_outs,
    )


def list_outbounds(db: Session, query: OutboundQuery) -> tuple[list[OutboundOut], int]:
    orders, total = outbound_crud.list_orders(db, query)

    items: list[OutboundOut] = []
    for order in orders:
        first_item = order.items[0] if order.items else None
        product = first_item.product if first_item else None

        items.append(
            OutboundOut(
                id=order.id,
                order_no=order.order_no,
                product_id=product.id if product else None,
                product_name=product.name if product else None,
                barcode=product.barcode if product else None,
                unit=product.unit if product else None,
                outbound_type=order.outbound_type,
                total_qty=float(order.total_qty),
                total_amount=float(order.total_amount),
                reason=order.reason,
                operator_name=(
                    (order.operator.real_name or order.operator.username)
                    if order.operator
                    else None
                ),
                remark=order.remark,
                created_at=order.created_at,
                items=[_batch_item(item) for item in order.items],
            )
        )

    return items, total
