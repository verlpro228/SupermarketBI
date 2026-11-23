from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.inspection import InspectionItemStatusPayload, InspectionQuery
from app.services import inspection as inspection_service

router = APIRouter()


@router.post("/run", summary="开始巡检")
def run(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    result = inspection_service.run_inspection(db, current_user)
    return success(result.model_dump(), f"巡检完成，命中 {result.hit_count} 条")


@router.put("/items/status", summary="标记巡检明细状态")
def update_item_status(
    payload: InspectionItemStatusPayload,
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    count = inspection_service.update_item_status(db, payload)
    return success({"count": count}, "状态已更新")


@router.get("", summary="巡检记录列表")
def list_records(
    query: Annotated[InspectionQuery, Depends()],
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    items, total = inspection_service.list_records(db, query)
    return success(
        {
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        }
    )


@router.get("/{record_id}", summary="巡检记录详情")
def get_detail(
    record_id: int,
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    return success(inspection_service.get_detail(db, record_id).model_dump())
