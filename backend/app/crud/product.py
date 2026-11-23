from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductQuery


def get_by_id(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def barcode_exists(db: Session, barcode: str, exclude_id: int | None = None) -> bool:
    stmt = select(Product.id).where(Product.barcode == barcode)
    if exclude_id is not None:
        stmt = stmt.where(Product.id != exclude_id)
    return db.scalar(stmt) is not None


def list_products(db: Session, query: ProductQuery) -> tuple[list[Product], int]:
    stmt = select(Product)

    if query.keyword:
        like = f"%{query.keyword.strip()}%"
        stmt = stmt.where(or_(Product.name.like(like), Product.barcode.like(like)))
    if query.category_id:
        stmt = stmt.where(Product.category_id == query.category_id)
    if query.status is not None:
        stmt = stmt.where(Product.status == query.status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    items = list(
        db.scalars(
            stmt.order_by(Product.id.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).all()
    )
    return items, total


def list_options(db: Session, keyword: str | None = None) -> list[tuple[Product, Decimal]]:
    stmt = (
        select(Product, func.coalesce(Inventory.total_qty, 0))
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .where(Product.status == 1)
    )
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Product.name.like(like), Product.barcode.like(like)))
    stmt = stmt.order_by(Product.name.asc()).limit(50)
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def create(db: Session, payload: ProductCreate, values: dict) -> Product:
    product = Product(
        barcode=payload.barcode.strip(),
        name=payload.name.strip(),
        category_id=payload.category_id,
        spec=payload.spec,
        unit=payload.unit,
        **values,
    )
    db.add(product)
    db.flush()
    return product
