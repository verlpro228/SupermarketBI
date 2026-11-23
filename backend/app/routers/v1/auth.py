from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.response import success
from app.db.session import get_db
from app.schemas.user import ChangePasswordPayload, LoginPayload, UserOut
from app.services import auth as auth_service

router = APIRouter()


@router.post("/login", summary="登录")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    result = auth_service.login(db, payload)
    return success(result.model_dump())


@router.get("/profile", summary="获取当前登录用户信息")
def profile(current_user: CurrentUser):
    return success(UserOut.model_validate(current_user).model_dump())


@router.put("/password", summary="修改本人密码")
def change_password(
    payload: ChangePasswordPayload,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    auth_service.change_own_password(db, current_user, payload)
    return success(message="密码修改成功")
