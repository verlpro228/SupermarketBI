from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product


def get_by_id(db: Session, category_id: int) -> Category | None:
    return db.get(Category, category_id)


def get_by_name(db: Session, name: str) -> Category | None:
    return db.scalar(select(Category).where(Category.name == name))


def list_all(db: Session, status: int | None = None) -> list[Category]:
    stmt = select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
    if status is not None:
        stmt = stmt.where(Category.status == status)
    return list(db.scalars(stmt).all())


def count_products(db: Session, category_id: int, only_active: bool = True) -> int:
    stmt = select(func.count(Product.id)).where(Product.category_id == category_id)
    if only_active:
        stmt = stmt.where(Product.status == 1)
    return db.scalar(stmt) or 0


def create(db: Session, name: str, sort_order: int) -> Category:
    category = Category(name=name, sort_order=sort_order, status=1)
    db.add(category)
    db.flush()
    return category
