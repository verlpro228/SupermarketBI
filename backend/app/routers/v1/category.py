from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import AdminUser, CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services import category as category_service

router = APIRouter()


@router.get("", summary="分类列表")
def list_categories(
    _: CurrentUser,
    status: int | None = None,
    db: Session = Depends(get_db),
):
    items = category_service.list_categories(db, status)
    return success([item.model_dump() for item in items])


@router.get("/options", summary="启用分类下拉选项")
def list_options(_: CurrentUser, db: Session = Depends(get_db)):
    items = category_service.list_options(db)
    return success([item.model_dump() for item in items])


@router.post("", summary="新增分类")
def create_category(
    payload: CategoryCreate,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    return success(category_service.create_category(db, payload).model_dump(), "新增成功")


@router.put("/{category_id}", summary="编辑分类")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    result = category_service.update_category(db, category_id, payload)
    return success(result.model_dump(), "保存成功")


@router.put("/{category_id}/status", summary="启用或停用分类")
def update_status(
    category_id: int,
    status: int,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    result = category_service.set_status(db, category_id, status)
    return success(result.model_dump(), "状态已更新")


@router.delete("/{category_id}", summary="删除分类（逻辑停用）")
def delete_category(
    category_id: int,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    category_service.set_status(db, category_id, 0)
    return success(message="已停用")
