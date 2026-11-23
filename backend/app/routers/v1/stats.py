from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.services import stats as stats_service

router = APIRouter()


@router.get("/dashboard", summary="数据看板")
def dashboard(
    current_user: CurrentUser,
    days: int = Query(30, ge=1, le=365, description="趋势统计天数"),
    db: Session = Depends(get_db),
):
    result = stats_service.get_dashboard(db, days, current_user.role == "admin")
    return success(result.model_dump())


@router.get("/trend", summary="出入库趋势")
def trend(
    _: CurrentUser,
    days: int = Query(30, ge=1, le=365),
    granularity: Annotated[str, Query(pattern="^(day|month)$")] = "day",
    db: Session = Depends(get_db),
):
    items = stats_service.get_trend(db, days, granularity)
    return success(
        {
            "granularity": granularity,
            "days": days,
            "items": [item.model_dump() for item in items],
        }
    )


@router.get("/inbound-analysis", summary="入库分析")
def inbound_analysis(
    _: CurrentUser,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return success(stats_service.get_inbound_analysis(db, days).model_dump())


@router.get("/outbound-analysis", summary="出库分析")
def outbound_analysis(
    _: CurrentUser,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return success(stats_service.get_outbound_analysis(db, days).model_dump())
