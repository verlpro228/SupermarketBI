import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _token_for_role(role: str) -> str:
    """按角色直接签发 token：测试不依赖账号密码，也不会改动任何真实密码。"""
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.role == role, User.status == 1)
            .order_by(User.id.asc())
            .first()
        )
        if user is None:
            pytest.skip(f"数据库中没有角色为 {role} 的启用账号")
        return create_access_token(user.id, {"role": user.role})
    finally:
        db.close()


@pytest.fixture(scope="session")
def admin_token() -> str:
    return _token_for_role("admin")


@pytest.fixture(scope="session")
def keeper_token() -> str:
    return _token_for_role("keeper")


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def keeper_headers(keeper_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {keeper_token}"}
