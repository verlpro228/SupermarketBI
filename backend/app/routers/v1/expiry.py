from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.expiry import (
    ExpiryActionQuery,
    ExpiryLossPayload,
    ExpiryPromoPayload,
    ExpiryQuery,
)
from app.services import expiry as expiry_service

router = APIRouter()


@router.get("", summary="临期清单")
def list_expiry(
    query: Annotated[ExpiryQuery, Depends()],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    items, total, thresholds = expiry_service.list_expiry_batches(
        db, query, current_user.role == "admin"
    )
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "thresholds": thresholds.model_dump(),
        }
    )


@router.post("/loss", summary="临期报损（支持批量）")
def loss(
    payload: ExpiryLossPayload,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    count = expiry_service.batch_loss(db, payload, current_user)
    return success({"count": count}, f"已完成 {count} 个批次报损")


@router.post("/promo", summary="标记促销")
def promo(
    payload: ExpiryPromoPayload,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    expiry_service.mark_promo(db, payload, current_user)
    return success(message="已标记为促销")


@router.get("/actions", summary="临期处理记录")
def list_actions(
    query: Annotated[ExpiryActionQuery, Depends()],
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    items, total = expiry_service.list_action_logs(db, query)
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }
    )
