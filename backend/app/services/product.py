from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.crud import category as category_crud
from app.crud import product as product_crud
from app.models.product import Product
from app.schemas.product import (
    ProductAdminOut,
    ProductCreate,
    ProductOption,
    ProductOut,
    ProductQuery,
    ProductUpdate,
)


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _qty(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def to_out(product: Product, include_purchase_price: bool) -> ProductOut:
    payload = {
        "id": product.id,
        "barcode": product.barcode,
        "name": product.name,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else None,
        "spec": product.spec,
        "unit": product.unit,
        "sale_price": float(product.sale_price),
        "safe_stock": float(product.safe_stock),
        "shelf_life_days": product.shelf_life_days,
        "status": product.status,
        "created_at": product.created_at,
    }
    if include_purchase_price:
        return ProductAdminOut(purchase_price=float(product.purchase_price), **payload)
    return ProductOut(**payload)


def list_products(
    db: Session, query: ProductQuery, is_admin: bool
) -> tuple[list[ProductOut], int]:
    products, total = product_crud.list_products(db, query)
    return [to_out(item, is_admin) for item in products], total


def create_product(db: Session, payload: ProductCreate) -> ProductOut:
    category = category_crud.get_by_id(db, payload.category_id)
    if category is None:
        raise BusinessError("所选分类不存在")
    if category.status != 1:
        raise BusinessError("所选分类已停用")

    if product_crud.barcode_exists(db, payload.barcode.strip()):
        raise BusinessError("条码已存在")

    values = {
        "purchase_price": _money(payload.purchase_price),
        "sale_price": _money(payload.sale_price),
        "safe_stock": _qty(payload.safe_stock),
        "shelf_life_days": payload.shelf_life_days,
        "status": 1,
    }

    try:
        product = product_crud.create(db, payload, values)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(product)
    return to_out(product, include_purchase_price=True)


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> ProductOut:
    product = product_crud.get_by_id(db, product_id)
    if product is None:
        raise BusinessError("商品不存在")

    data = payload.model_dump(exclude_unset=True)

    if "barcode" in data and data["barcode"] is not None:
        barcode = data["barcode"].strip()
        if product_crud.barcode_exists(db, barcode, exclude_id=product_id):
            raise BusinessError("条码已存在")
        product.barcode = barcode

    if "name" in data and data["name"] is not None:
        product.name = data["name"].strip()

    if "category_id" in data and data["category_id"] is not None:
        category = category_crud.get_by_id(db, data["category_id"])
        if category is None:
            raise BusinessError("所选分类不存在")
        if category.status != 1:
            raise BusinessError("所选分类已停用")
        product.category_id = data["category_id"]

    if "spec" in data:
        product.spec = data["spec"]
    if "unit" in data:
        product.unit = data["unit"]
    if "shelf_life_days" in data and data["shelf_life_days"] is not None:
        product.shelf_life_days = data["shelf_life_days"]
    if "purchase_price" in data and data["purchase_price"] is not None:
        product.purchase_price = _money(data["purchase_price"])
    if "sale_price" in data and data["sale_price"] is not None:
        product.sale_price = _money(data["sale_price"])
    if "safe_stock" in data and data["safe_stock"] is not None:
        product.safe_stock = _qty(data["safe_stock"])

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(product)
    return to_out(product, include_purchase_price=True)


def set_status(db: Session, product_id: int, status: int) -> ProductOut:
    product = product_crud.get_by_id(db, product_id)
    if product is None:
        raise BusinessError("商品不存在")

    product.status = status

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(product)
    return to_out(product, include_purchase_price=True)


def list_options(
    db: Session, keyword: str | None, is_admin: bool
) -> list[ProductOption]:
    rows = product_crud.list_options(db, keyword)
    result: list[ProductOption] = []
    for product, stock_qty in rows:
        result.append(
            ProductOption(
                id=product.id,
                barcode=product.barcode,
                name=product.name,
                spec=product.spec,
                unit=product.unit,
                shelf_life_days=product.shelf_life_days,
                stock_qty=float(stock_qty),
                purchase_price=float(product.purchase_price) if is_admin else None,
            )
        )
    return result
