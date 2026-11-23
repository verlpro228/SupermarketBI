from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.inbound import InboundOrder
from app.models.inventory import InventoryBatch
from app.models.product import Product
from app.models.user import User
from app.schemas.inbound import InboundQuery


def _build_filters(query: InboundQuery) -> list:
    conditions = []
    if query.keyword:
        like = f"%{query.keyword.strip()}%"
        conditions.append(or_(Product.name.like(like), Product.barcode.like(like)))
    if query.product_id:
        conditions.append(InboundOrder.product_id == query.product_id)
    if query.start_date:
        conditions.append(func.date(InboundOrder.created_at) >= query.start_date)
    if query.end_date:
        conditions.append(func.date(InboundOrder.created_at) <= query.end_date)
    return conditions


def list_inbounds(db: Session, query: InboundQuery):
    stmt = (
        select(InboundOrder, Product, InventoryBatch, User)
        .join(Product, Product.id == InboundOrder.product_id)
        .outerjoin(InventoryBatch, InventoryBatch.inbound_id == InboundOrder.id)
        .join(User, User.id == InboundOrder.operator_id)
    )

    conditions = _build_filters(query)
    if conditions:
        stmt = stmt.where(*conditions)

    count_stmt = (
        select(func.count(InboundOrder.id))
        .select_from(InboundOrder)
        .join(Product, Product.id == InboundOrder.product_id)
    )
    if conditions:
        count_stmt = count_stmt.where(*conditions)

    total = db.scalar(count_stmt) or 0

    rows = db.execute(
        stmt.order_by(InboundOrder.created_at.desc(), InboundOrder.id.desc())
        .offset((query.page - 1) * query.page_size)
        .limit(query.page_size)
    ).all()

    return rows, total


def create_order(db: Session, **kwargs) -> InboundOrder:
    order = InboundOrder(**kwargs)
    db.add(order)
    db.flush()
    return order
