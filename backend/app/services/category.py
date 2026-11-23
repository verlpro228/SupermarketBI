from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.crud import category as category_crud
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryOption, CategoryOut, CategoryUpdate


def list_categories(db: Session, status: int | None = None) -> list[CategoryOut]:
    return [CategoryOut.model_validate(item) for item in category_crud.list_all(db, status)]


def list_options(db: Session) -> list[CategoryOption]:
    return [CategoryOption.model_validate(item) for item in category_crud.list_all(db, status=1)]


def _get_or_raise(db: Session, category_id: int) -> Category:
    category = category_crud.get_by_id(db, category_id)
    if category is None:
        raise BusinessError("分类不存在")
    return category


def _ensure_name_available(db: Session, name: str, exclude_id: int | None = None) -> None:
    exists = category_crud.get_by_name(db, name)
    if exists and exists.id != exclude_id:
        raise BusinessError("分类名称已存在")


def create_category(db: Session, payload: CategoryCreate) -> CategoryOut:
    name = payload.name.strip()
    _ensure_name_available(db, name)

    try:
        category = category_crud.create(db, name, payload.sort_order)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(category)
    return CategoryOut.model_validate(category)


def update_category(db: Session, category_id: int, payload: CategoryUpdate) -> CategoryOut:
    category = _get_or_raise(db, category_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"] is not None:
        name = data["name"].strip()
        _ensure_name_available(db, name, exclude_id=category_id)
        category.name = name
    if "sort_order" in data and data["sort_order"] is not None:
        category.sort_order = data["sort_order"]

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(category)
    return CategoryOut.model_validate(category)


def set_status(db: Session, category_id: int, status: int) -> CategoryOut:
    category = _get_or_raise(db, category_id)

    if status == 0 and category_crud.count_products(db, category_id, only_active=True) > 0:
        raise BusinessError("该分类下仍有启用的商品，无法停用")

    category.status = status

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(category)
    return CategoryOut.model_validate(category)
