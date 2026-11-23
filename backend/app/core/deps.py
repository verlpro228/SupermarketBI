from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, PermissionError_
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("未登录或登录已失效")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise AuthError("账号不存在或已被删除")
    if user.status != 1:
        raise AuthError("账号已被禁用，请联系管理员")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise PermissionError_("仅管理员可执行该操作")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
