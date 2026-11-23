from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.category import Category
from app.models.product import Product

TEST_BARCODE = "TEST-BARCODE-001"
TEST_CATEGORY = "测试分类"


def _cleanup() -> None:
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.barcode == TEST_BARCODE).first()
        if product:
            db.delete(product)
        category = db.query(Category).filter(Category.name == TEST_CATEGORY).first()
        if category:
            db.delete(category)
        db.commit()
    finally:
        db.close()


def test_category_and_product_flow(
    client: TestClient, admin_headers: dict[str, str], keeper_headers: dict[str, str]
):
    _cleanup()

    created_category = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 99},
    ).json()
    assert created_category["code"] == 0, created_category
    category_id = created_category["data"]["id"]

    duplicated = client.post(
        "/api/v1/categories", headers=admin_headers, json={"name": TEST_CATEGORY}
    ).json()
    assert duplicated["code"] != 0

    forbidden = client.post(
        "/api/v1/categories", headers=keeper_headers, json={"name": "越权分类"}
    )
    assert forbidden.status_code == 403

    created_product = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "测试商品",
            "category_id": category_id,
            "spec": "1*1",
            "unit": "件",
            "purchase_price": 10.5,
            "sale_price": 15.9,
            "safe_stock": 5,
            "shelf_life_days": 30,
        },
    ).json()
    assert created_product["code"] == 0, created_product
    product_id = created_product["data"]["id"]
    assert created_product["data"]["purchase_price"] == 10.5

    duplicate_barcode = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "测试商品2",
            "category_id": category_id,
        },
    ).json()
    assert duplicate_barcode["code"] != 0

    admin_list = client.get(
        "/api/v1/products", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()
    assert "purchase_price" in admin_list["data"]["items"][0]

    keeper_list = client.get(
        "/api/v1/products", headers=keeper_headers, params={"keyword": TEST_BARCODE}
    ).json()
    assert "purchase_price" not in keeper_list["data"]["items"][0]

    blocked_category = client.put(
        f"/api/v1/categories/{category_id}/status",
        headers=admin_headers,
        params={"status": 0},
    ).json()
    assert blocked_category["code"] != 0

    updated = client.put(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
        json={"sale_price": 18.8, "safe_stock": 8},
    ).json()
    assert updated["code"] == 0
    assert updated["data"]["sale_price"] == 18.8

    keeper_write = client.put(
        f"/api/v1/products/{product_id}", headers=keeper_headers, json={"sale_price": 1}
    )
    assert keeper_write.status_code == 403

    disabled = client.put(
        f"/api/v1/products/{product_id}/status",
        headers=admin_headers,
        params={"status": 0},
    ).json()
    assert disabled["code"] == 0

    options = client.get(
        "/api/v1/products/options", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()
    assert options["data"] == []

    _cleanup()
