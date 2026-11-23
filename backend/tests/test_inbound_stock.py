from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.adjust import StockAdjustLog
from app.models.category import Category
from app.models.inbound import InboundOrder
from app.models.inventory import Inventory, InventoryBatch
from app.models.product import Product

TEST_BARCODE = "TEST-STOCK-001"
TEST_CATEGORY = "库存测试分类"


def _cleanup() -> None:
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.barcode == TEST_BARCODE).first()
        if product:
            db.query(StockAdjustLog).filter(
                StockAdjustLog.product_id == product.id
            ).delete()
            db.query(InventoryBatch).filter(
                InventoryBatch.product_id == product.id
            ).delete()
            db.query(InboundOrder).filter(
                InboundOrder.product_id == product.id
            ).delete()
            db.query(Inventory).filter(Inventory.product_id == product.id).delete()
            db.delete(product)
            db.commit()

        category = db.query(Category).filter(Category.name == TEST_CATEGORY).first()
        if category:
            db.delete(category)
            db.commit()
    finally:
        db.close()


def test_inbound_and_stock_flow(
    client: TestClient, admin_headers: dict[str, str], keeper_headers: dict[str, str]
):
    _cleanup()

    category_id = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 90},
    ).json()["data"]["id"]

    product_id = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "库存测试商品",
            "category_id": category_id,
            "unit": "箱",
            "purchase_price": 10,
            "sale_price": 15,
            "safe_stock": 20,
            "shelf_life_days": 30,
        },
    ).json()["data"]["id"]

    production_date = date.today().isoformat()

    # 库管员可执行入库
    inbound = client.post(
        "/api/v1/inbound",
        headers=keeper_headers,
        json={
            "product_id": product_id,
            "quantity": 10,
            "cost_price": 12.5,
            "production_date": production_date,
            "supplier": "测试供应商",
            "remark": "首次入库",
        },
    ).json()
    assert inbound["code"] == 0, inbound
    data = inbound["data"]
    assert data["order_no"].startswith("RK")
    assert data["amount"] == 125.0
    expected_expiry = date.today() + timedelta(days=30)
    assert data["expiry_date"] == expected_expiry.isoformat()

    # 库存汇总已同步
    stock = client.get(
        "/api/v1/stock",
        headers=admin_headers,
        params={"keyword": TEST_BARCODE},
    ).json()["data"]["items"][0]
    # 库存货值口径：当前库存 × 商品当前进价（非批次进价）
    assert stock["total_qty"] == 10
    assert stock["stock_value"] == 100.0
    assert stock["is_low_stock"] is True
    assert stock["nearest_expiry"] == expected_expiry.isoformat()

    # 库管员视角无金额字段
    keeper_stock = client.get(
        "/api/v1/stock", headers=keeper_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]["items"][0]
    assert "stock_value" not in keeper_stock
    assert "purchase_price" not in keeper_stock

    # 流水记录
    records = client.get(
        f"/api/v1/stock/{product_id}/records", headers=admin_headers
    ).json()["data"]
    assert records["total"] == 1
    assert records["items"][0]["record_type"] == "inbound"
    assert records["items"][0]["quantity"] == 10

    # 批次与调整
    batches = client.get(
        f"/api/v1/stock/{product_id}/batches", headers=admin_headers
    ).json()["data"]
    assert len(batches) == 1
    batch_id = batches[0]["batch_id"]

    forbidden_adjust = client.post(
        "/api/v1/stock/adjust",
        headers=keeper_headers,
        json={"product_id": product_id, "batch_id": batch_id, "new_qty": 1, "reason": "越权"},
    )
    assert forbidden_adjust.status_code == 403

    adjusted = client.post(
        "/api/v1/stock/adjust",
        headers=admin_headers,
        json={
            "product_id": product_id,
            "batch_id": batch_id,
            "new_qty": 8,
            "reason": "盘点差异",
        },
    ).json()
    assert adjusted["code"] == 0, adjusted

    stock_after = client.get(
        "/api/v1/stock", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]["items"][0]
    assert stock_after["total_qty"] == 8

    # 入库金额由后端计算，前端传值无效
    assert data["amount"] == round(data["quantity"] * data["cost_price"], 2)

    _cleanup()


def test_inbound_rejects_disabled_product(
    client: TestClient, admin_headers: dict[str, str]
):
    _cleanup()

    category_id = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 91},
    ).json()["data"]["id"]

    product_id = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "库存测试商品",
            "category_id": category_id,
            "shelf_life_days": 30,
        },
    ).json()["data"]["id"]

    client.put(
        f"/api/v1/products/{product_id}/status",
        headers=admin_headers,
        params={"status": 0},
    )

    result = client.post(
        "/api/v1/inbound",
        headers=admin_headers,
        json={
            "product_id": product_id,
            "quantity": 1,
            "cost_price": 1,
            "production_date": date.today().isoformat(),
        },
    ).json()
    assert result["code"] != 0

    _cleanup()
