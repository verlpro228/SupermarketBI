from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.core.security import create_access_token, hash_password, verify_password
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import ChangePasswordPayload, LoginOut, LoginPayload, UserOut


def login(db: Session, payload: LoginPayload) -> LoginOut:
    user = user_crud.get_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise BusinessError("账号或密码错误")
    if user.status != 1:
        raise BusinessError("账号已被禁用，请联系管理员")

    user.last_login_at = datetime.now()
    db.commit()

    token = create_access_token(user.id, {"role": user.role})
    return LoginOut(access_token=token, user=UserOut.model_validate(user))


def change_own_password(db: Session, user: User, payload: ChangePasswordPayload) -> None:
    if not verify_password(payload.old_password, user.password_hash):
        raise BusinessError("原密码不正确")
    if payload.old_password == payload.new_password:
        raise BusinessError("新密码不能与原密码相同")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
