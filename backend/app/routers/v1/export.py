from io import BytesIO
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.schemas.expiry import ExpiryActionQuery, ExpiryQuery
from app.schemas.inbound import InboundQuery
from app.schemas.outbound import OutboundQuery
from app.schemas.stock import StockQuery
from app.services import export as export_service

router = APIRouter()

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _file_response(buffer: BytesIO, filename: str) -> StreamingResponse:
    return StreamingResponse(
        buffer,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
        },
    )


@router.get("/stock", summary="导出库存列表")
def export_stock(
    query: Annotated[StockQuery, Depends()],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    buffer, filename = export_service.export_stock(
        db, query, current_user.role == "admin"
    )
    return _file_response(buffer, filename)


@router.get("/inbound", summary="导出入库记录")
def export_inbound(
    query: Annotated[InboundQuery, Depends()],
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    buffer, filename = export_service.export_inbound(db, query)
    return _file_response(buffer, filename)


@router.get("/outbound", summary="导出出库记录")
def export_outbound(
    query: Annotated[OutboundQuery, Depends()],
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    buffer, filename = export_service.export_outbound(db, query)
    return _file_response(buffer, filename)


@router.get("/expiry", summary="导出临期清单")
def export_expiry(
    query: Annotated[ExpiryQuery, Depends()],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    buffer, filename = export_service.export_expiry(
        db, query, current_user.role == "admin"
    )
    return _file_response(buffer, filename)


@router.get("/expiry-actions", summary="导出临期处理记录")
def export_expiry_actions(
    query: Annotated[ExpiryActionQuery, Depends()],
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    buffer, filename = export_service.export_actions(db, query)
    return _file_response(buffer, filename)
