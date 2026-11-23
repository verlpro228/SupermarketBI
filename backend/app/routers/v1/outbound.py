from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.outbound import OutboundCreate, OutboundQuery
from app.services import outbound as outbound_service

router = APIRouter()


@router.post("", summary="出库登记")
def create_outbound(
    payload: OutboundCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    result = outbound_service.create_outbound(db, payload, current_user)
    return success(result.model_dump(), "出库成功")


@router.get("", summary="出库记录")
def list_outbounds(
    query: Annotated[OutboundQuery, Depends()],
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    items, total = outbound_service.list_outbounds(db, query)
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }
    )
