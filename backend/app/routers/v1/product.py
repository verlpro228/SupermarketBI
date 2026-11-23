from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import AdminUser, CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductQuery, ProductUpdate
from app.services import product as product_service

router = APIRouter()


@router.get("", summary="商品列表")
def list_products(
    query: Annotated[ProductQuery, Depends()],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    is_admin = current_user.role == "admin"
    items, total = product_service.list_products(db, query, is_admin)
    # 直接序列化实例，避免 PageData[ProductOut] 二次校验丢弃管理员专属字段
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }
    )


@router.get("/options", summary="启用商品下拉选项")
def list_options(
    current_user: CurrentUser,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    items = product_service.list_options(db, keyword, current_user.role == "admin")
    return success([item.model_dump() for item in items])


@router.post("", summary="新增商品")
def create_product(
    payload: ProductCreate,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    return success(product_service.create_product(db, payload).model_dump(), "新增成功")


@router.put("/{product_id}", summary="编辑商品")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    return success(
        product_service.update_product(db, product_id, payload).model_dump(), "保存成功"
    )


@router.put("/{product_id}/status", summary="启用或停用商品")
def update_status(
    product_id: int,
    status: int,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    return success(
        product_service.set_status(db, product_id, status).model_dump(), "状态已更新"
    )
