from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def _cleanup_user(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def _create_temp_user(username: str, password: str, role: str = "keeper") -> None:
    _cleanup_user(username)
    db = SessionLocal()
    try:
        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                real_name="临时测试用户",
                role=role,
                status=1,
            )
        )
        db.commit()
    finally:
        db.close()


def test_login_success(client: TestClient):
    username = "t_login_ok"
    _create_temp_user(username, "Login@123")

    body = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "Login@123"}
    ).json()
    assert body["code"] == 0
    assert body["data"]["access_token"]
    assert body["data"]["user"]["role"] == "keeper"

    _cleanup_user(username)


def test_login_wrong_password(client: TestClient):
    username = "t_login_bad"
    _create_temp_user(username, "Right@123")

    body = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "wrong-password"}
    ).json()
    assert body["code"] != 0

    _cleanup_user(username)


def test_profile_requires_token(client: TestClient):
    response = client.get("/api/v1/auth/profile")
    assert response.status_code == 401


def test_profile_with_token(client: TestClient, admin_headers: dict[str, str]):
    body = client.get("/api/v1/auth/profile", headers=admin_headers).json()
    assert body["code"] == 0
    assert body["data"]["role"] == "admin"


def test_keeper_forbidden_user_management(
    client: TestClient, keeper_headers: dict[str, str]
):
    response = client.get("/api/v1/users", headers=keeper_headers)
    assert response.status_code == 403


def test_admin_can_list_users(client: TestClient, admin_headers: dict[str, str]):
    body = client.get("/api/v1/users", headers=admin_headers).json()
    assert body["code"] == 0
    assert body["data"]["total"] >= 2


def test_user_lifecycle(client: TestClient, admin_headers: dict[str, str]):
    username = "t_lifecycle"
    _cleanup_user(username)

    created = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": username,
            "password": "Init@123",
            "real_name": "测试账号",
            "role": "keeper",
        },
    ).json()
    assert created["code"] == 0, created
    user_id = created["data"]["id"]

    duplicated = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={"username": username, "password": "Init@123", "role": "keeper"},
    ).json()
    assert duplicated["code"] != 0

    updated = client.put(
        f"/api/v1/users/{user_id}",
        headers=admin_headers,
        json={"real_name": "改名后", "role": "keeper"},
    ).json()
    assert updated["code"] == 0
    assert updated["data"]["real_name"] == "改名后"

    disabled = client.put(
        f"/api/v1/users/{user_id}/status", headers=admin_headers, json={"status": 0}
    ).json()
    assert disabled["code"] == 0
    assert disabled["data"]["status"] == 0

    blocked_login = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "Init@123"}
    ).json()
    assert blocked_login["code"] != 0

    client.put(f"/api/v1/users/{user_id}/status", headers=admin_headers, json={"status": 1})

    reset = client.put(
        f"/api/v1/users/{user_id}/password",
        headers=admin_headers,
        json={"new_password": "New@123456"},
    ).json()
    assert reset["code"] == 0

    login_with_new = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "New@123456"}
    ).json()
    assert login_with_new["code"] == 0

    _cleanup_user(username)


def test_cannot_disable_self(client: TestClient, admin_headers: dict[str, str]):
    me = client.get("/api/v1/auth/profile", headers=admin_headers).json()["data"]
    body = client.put(
        f"/api/v1/users/{me['id']}/status", headers=admin_headers, json={"status": 0}
    ).json()
    assert body["code"] != 0


def test_change_own_password_persists(client: TestClient):
    """本人改密必须真实落库：旧密码失效、新密码生效。"""
    username = "t_change_pwd"
    _create_temp_user(username, "Origin@123")

    token = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "Origin@123"}
    ).json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    wrong_old = client.put(
        "/api/v1/auth/password",
        headers=headers,
        json={"old_password": "NotMyPwd@1", "new_password": "Changed@123"},
    ).json()
    assert wrong_old["code"] != 0

    changed = client.put(
        "/api/v1/auth/password",
        headers=headers,
        json={"old_password": "Origin@123", "new_password": "Changed@123"},
    ).json()
    assert changed["code"] == 0

    old_login = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "Origin@123"}
    ).json()
    assert old_login["code"] != 0

    new_login = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "Changed@123"}
    ).json()
    assert new_login["code"] == 0

    _cleanup_user(username)
