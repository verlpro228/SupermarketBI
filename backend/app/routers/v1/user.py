from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import AdminUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.base import PageData
from app.schemas.user import (
    ResetPasswordPayload,
    UserCreate,
    UserOut,
    UserQuery,
    UserStatusPayload,
    UserUpdate,
)
from app.services import user as user_service

router = APIRouter()


@router.get("", summary="用户列表")
def list_users(
    query: Annotated[UserQuery, Depends()],
    _: AdminUser,
    db: Session = Depends(get_db),
):
    items, total = user_service.list_users(db, query)
    return success(
        PageData[UserOut](
            items=items, total=total, page=query.page, page_size=query.page_size
        ).model_dump()
    )


@router.post("", summary="新增用户")
def create_user(
    payload: UserCreate,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    return success(user_service.create_user(db, payload).model_dump(), "新增成功")


@router.put("/{user_id}", summary="编辑用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    result = user_service.update_user(db, user_id, payload, current_user)
    return success(result.model_dump(), "保存成功")


@router.put("/{user_id}/status", summary="启用或禁用用户")
def update_status(
    user_id: int,
    payload: UserStatusPayload,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    result = user_service.set_status(db, user_id, payload, current_user)
    return success(result.model_dump(), "状态已更新")


@router.put("/{user_id}/password", summary="重置用户密码")
def reset_password(
    user_id: int,
    payload: ResetPasswordPayload,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    user_service.reset_password(db, user_id, payload)
    return success(message="密码已重置")
