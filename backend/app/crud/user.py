from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserQuery


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def username_exists(db: Session, username: str, exclude_id: int | None = None) -> bool:
    stmt = select(User.id).where(User.username == username)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalar(stmt) is not None


def list_users(db: Session, query: UserQuery) -> tuple[list[User], int]:
    stmt = select(User)

    if query.keyword:
        like = f"%{query.keyword.strip()}%"
        stmt = stmt.where(or_(User.username.like(like), User.real_name.like(like)))
    if query.role:
        stmt = stmt.where(User.role == query.role)
    if query.status is not None:
        stmt = stmt.where(User.status == query.status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    items = list(
        db.scalars(
            stmt.order_by(User.id.asc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).all()
    )
    return items, total


def create(db: Session, payload: UserCreate, password_hash: str) -> User:
    user = User(
        username=payload.username,
        password_hash=password_hash,
        real_name=payload.real_name,
        role=payload.role,
        status=1,
    )
    db.add(user)
    db.flush()
    return user


def count_active_admins(db: Session, exclude_id: int | None = None) -> int:
    stmt = select(func.count(User.id)).where(User.role == "admin", User.status == 1)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalar(stmt) or 0
