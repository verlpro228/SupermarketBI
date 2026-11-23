from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.inbound import InboundCreate, InboundQuery
from app.services import inbound as inbound_service

router = APIRouter()


@router.post("", summary="入库登记")
def create_inbound(
    payload: InboundCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    result = inbound_service.create_inbound(db, payload, current_user)
    return success(result.model_dump(), "入库成功")


@router.get("", summary="入库记录")
def list_inbounds(
    query: Annotated[InboundQuery, Depends()],
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    items, total = inbound_service.list_inbounds(db, query)
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }
    )
