from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.core.security import hash_password
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import (
    ResetPasswordPayload,
    UserCreate,
    UserOut,
    UserQuery,
    UserStatusPayload,
    UserUpdate,
)


def list_users(db: Session, query: UserQuery) -> tuple[list[UserOut], int]:
    users, total = user_crud.list_users(db, query)
    return [UserOut.model_validate(item) for item in users], total


def _get_or_raise(db: Session, user_id: int) -> User:
    user = user_crud.get_by_id(db, user_id)
    if user is None:
        raise BusinessError("用户不存在")
    return user


def create_user(db: Session, payload: UserCreate) -> UserOut:
    if user_crud.username_exists(db, payload.username):
        raise BusinessError("账号已存在")

    try:
        user = user_crud.create(db, payload, hash_password(payload.password))
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return UserOut.model_validate(user)


def update_user(db: Session, user_id: int, payload: UserUpdate, operator: User) -> UserOut:
    user = _get_or_raise(db, user_id)

    if payload.role is not None and payload.role != user.role:
        if user.id == operator.id:
            raise BusinessError("不能修改自己的角色")
        if (
            user.role == "admin"
            and user.status == 1
            and user_crud.count_active_admins(db, exclude_id=user.id) == 0
        ):
            raise BusinessError("系统至少需要保留一个启用状态的管理员")
        user.role = payload.role

    if payload.real_name is not None:
        user.real_name = payload.real_name

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return UserOut.model_validate(user)


def set_status(
    db: Session, user_id: int, payload: UserStatusPayload, operator: User
) -> UserOut:
    if user_id == operator.id and payload.status == 0:
        raise BusinessError("不能禁用当前登录的账号")

    user = _get_or_raise(db, user_id)

    if (
        payload.status == 0
        and user.role == "admin"
        and user.status == 1
        and user_crud.count_active_admins(db, exclude_id=user.id) == 0
    ):
        raise BusinessError("系统至少需要保留一个启用状态的管理员")

    user.status = payload.status

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return UserOut.model_validate(user)


def reset_password(db: Session, user_id: int, payload: ResetPasswordPayload) -> None:
    user = _get_or_raise(db, user_id)
    user.password_hash = hash_password(payload.new_password)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
