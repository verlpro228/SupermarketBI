from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.crud import inbound as inbound_crud
from app.crud import inventory as inventory_crud
from app.crud import product as product_crud
from app.models.user import User
from app.schemas.inbound import InboundCreate, InboundOut, InboundQuery
from app.utils.order_no import generate_batch_no, generate_order_no


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _qty(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def create_inbound(db: Session, payload: InboundCreate, operator: User) -> InboundOut:
    from app.models.inbound import InboundOrder

    product = product_crud.get_by_id(db, payload.product_id)
    if product is None:
        raise BusinessError("商品不存在")
    if product.status != 1:
        raise BusinessError("商品已停用，无法入库")
    if product.shelf_life_days <= 0:
        raise BusinessError("该商品未维护保质期天数，请先在商品管理中补充")

    quantity = _qty(payload.quantity)
    cost_price = _money(Decimal(str(payload.cost_price)))
    amount = _money(quantity * cost_price)
    expiry_date = payload.production_date + timedelta(days=product.shelf_life_days)

    order_no = generate_order_no(db, "RK", InboundOrder)
    batch_no = generate_batch_no()

    try:
        order = inbound_crud.create_order(
            db,
            order_no=order_no,
            product_id=product.id,
            quantity=quantity,
            cost_price=cost_price,
            amount=amount,
            production_date=payload.production_date,
            expiry_date=expiry_date,
            supplier=payload.supplier,
            operator_id=operator.id,
            remark=payload.remark,
        )

        inventory_crud.create_batch(
            db,
            product_id=product.id,
            batch_no=batch_no,
            inbound_id=order.id,
            production_date=payload.production_date,
            expiry_date=expiry_date,
            qty_initial=quantity,
            qty_remaining=quantity,
            cost_price=cost_price,
            is_promo=0,
        )

        inventory_crud.add_stock(db, product.id, quantity)

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(order)

    return InboundOut(
        id=order.id,
        order_no=order.order_no,
        product_id=product.id,
        product_name=product.name,
        barcode=product.barcode,
        unit=product.unit,
        batch_no=batch_no,
        quantity=float(order.quantity),
        cost_price=float(order.cost_price),
        amount=float(order.amount),
        production_date=order.production_date,
        expiry_date=order.expiry_date,
        supplier=order.supplier,
        operator_name=operator.real_name or operator.username,
        remark=order.remark,
        created_at=order.created_at,
    )


def list_inbounds(db: Session, query: InboundQuery) -> tuple[list[InboundOut], int]:
    rows, total = inbound_crud.list_inbounds(db, query)

    items: list[InboundOut] = []
    for order, product, batch, user in rows:
        items.append(
            InboundOut(
                id=order.id,
                order_no=order.order_no,
                product_id=product.id,
                product_name=product.name,
                barcode=product.barcode,
                unit=product.unit,
                batch_no=batch.batch_no if batch else None,
                quantity=float(order.quantity),
                cost_price=float(order.cost_price),
                amount=float(order.amount),
                production_date=order.production_date,
                expiry_date=order.expiry_date,
                supplier=order.supplier,
                operator_name=user.real_name or user.username,
                remark=order.remark,
                created_at=order.created_at,
            )
        )

    return items, total
