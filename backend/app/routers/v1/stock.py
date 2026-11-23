from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import AdminUser, CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.stock import StockAdjustPayload, StockQuery
from app.services import stock as stock_service

router = APIRouter()


@router.get("", summary="库存列表")
def list_stock(
    query: Annotated[StockQuery, Depends()],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    items, total = stock_service.list_stock(db, query, current_user.role == "admin")
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }
    )


@router.get("/{product_id}/records", summary="商品出入库流水")
def list_records(
    product_id: int,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    items, total = stock_service.list_records(db, product_id, page, page_size)
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/{product_id}/batches", summary="商品在库批次")
def list_batches(
    product_id: int,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    items = stock_service.list_batches(db, product_id)
    return success([item.model_dump() for item in items])


@router.post("/adjust", summary="调整库存")
def adjust_stock(
    payload: StockAdjustPayload,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    stock_service.adjust_stock(db, payload, current_user)
    return success(message="库存已调整")
