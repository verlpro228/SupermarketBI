from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import success
from app.db.session import get_db

router = APIRouter()


@router.get("/health", summary="健康检查")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return success(
        {
            "status": "ok",
            "app": settings.APP_NAME,
            "database": settings.MYSQL_DB,
        }
    )
