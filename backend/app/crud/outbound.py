from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.outbound import OutboundItem, OutboundOrder
from app.models.product import Product
from app.schemas.outbound import OutboundQuery


def create_order(db: Session, **kwargs) -> OutboundOrder:
    order = OutboundOrder(**kwargs)
    db.add(order)
    db.flush()
    return order


def create_item(db: Session, **kwargs) -> OutboundItem:
    item = OutboundItem(**kwargs)
    db.add(item)
    db.flush()
    return item


def list_orders(db: Session, query: OutboundQuery):
    stmt = select(OutboundOrder).options(
        selectinload(OutboundOrder.items).selectinload(OutboundItem.product)
    )

    conditions = []
    if query.outbound_type:
        conditions.append(OutboundOrder.outbound_type == query.outbound_type)
    if query.start_date:
        conditions.append(func.date(OutboundOrder.created_at) >= query.start_date)
    if query.end_date:
        conditions.append(func.date(OutboundOrder.created_at) <= query.end_date)
    if query.keyword:
        like = f"%{query.keyword.strip()}%"
        subquery = (
            select(OutboundItem.outbound_id)
            .join(Product, Product.id == OutboundItem.product_id)
            .where(or_(Product.name.like(like), Product.barcode.like(like)))
        )
        conditions.append(OutboundOrder.id.in_(subquery))

    if conditions:
        stmt = stmt.where(*conditions)

    count_stmt = select(func.count(OutboundOrder.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total = db.scalar(count_stmt) or 0

    orders = list(
        db.scalars(
            stmt.order_by(OutboundOrder.created_at.desc(), OutboundOrder.id.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).all()
    )
    return orders, total
