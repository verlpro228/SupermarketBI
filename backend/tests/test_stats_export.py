from datetime import date

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.adjust import StockAdjustLog
from app.models.category import Category
from app.models.expiry import ExpiryActionLog
from app.models.inbound import InboundOrder
from app.models.inspection import InspectionItem
from app.models.inventory import Inventory, InventoryBatch
from app.models.outbound import OutboundItem, OutboundOrder
from app.models.product import Product

TEST_BARCODE = "TEST-STATS-001"
TEST_CATEGORY = "统计测试分类"


def _cleanup() -> None:
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.barcode == TEST_BARCODE).first()
        if product:
            batch_ids = [
                row[0]
                for row in db.query(InventoryBatch.id)
                .filter(InventoryBatch.product_id == product.id)
                .all()
            ]
            if batch_ids:
                db.query(InspectionItem).filter(
                    InspectionItem.batch_id.in_(batch_ids)
                ).delete(synchronize_session=False)
            db.query(InspectionItem).filter(
                InspectionItem.product_id == product.id
            ).delete(synchronize_session=False)
            db.query(ExpiryActionLog).filter(
                ExpiryActionLog.product_id == product.id
            ).delete()

            order_ids = [
                row[0]
                for row in db.query(OutboundItem.outbound_id)
                .filter(OutboundItem.product_id == product.id)
                .distinct()
                .all()
            ]
            db.query(OutboundItem).filter(OutboundItem.product_id == product.id).delete()
            if order_ids:
                db.query(OutboundOrder).filter(
                    OutboundOrder.id.in_(order_ids)
                ).delete(synchronize_session=False)

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


def _prepare_data(client: TestClient, admin_headers: dict[str, str]) -> int:
    _cleanup()

    category_id = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 96},
    ).json()["data"]["id"]

    product_id = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "统计测试商品",
            "category_id": category_id,
            "unit": "件",
            "purchase_price": 20,
            "sale_price": 30,
            "safe_stock": 2,
            "shelf_life_days": 30,
        },
    ).json()["data"]["id"]

    client.post(
        "/api/v1/inbound",
        headers=admin_headers,
        json={
            "product_id": product_id,
            "quantity": 10,
            "cost_price": 20,
            "production_date": date.today().isoformat(),
        },
    )

    client.post(
        "/api/v1/outbound",
        headers=admin_headers,
        json={"product_id": product_id, "outbound_type": "sale", "quantity": 3},
    )

    return product_id


def test_dashboard_and_trend(
    client: TestClient, admin_headers: dict[str, str], keeper_headers: dict[str, str]
):
    _prepare_data(client, admin_headers)

    dashboard = client.get("/api/v1/stats/dashboard", headers=admin_headers).json()["data"]
    kpi = dashboard["kpi"]
    assert kpi["product_count"] >= 1
    assert kpi["total_stock"] >= 7
    assert kpi["stock_value"] is not None
    assert kpi["expiry_count"] >= 0
    assert len(dashboard["trend"]) == 30
    assert dashboard["trend"][-1]["inbound"] >= 10
    assert dashboard["trend"][-1]["outbound"] >= 3
    assert len(dashboard["category_value"]) >= 1

    keeper_dashboard = client.get(
        "/api/v1/stats/dashboard", headers=keeper_headers
    ).json()["data"]
    assert keeper_dashboard["kpi"]["stock_value"] is None
    assert keeper_dashboard["category_value"] == []

    trend = client.get(
        "/api/v1/stats/trend",
        headers=admin_headers,
        params={"days": 90, "granularity": "month"},
    ).json()["data"]
    assert trend["granularity"] == "month"
    assert 1 <= len(trend["items"]) <= 5
    assert trend["items"][-1]["inbound"] >= 10

    _cleanup()


def test_export_files(
    client: TestClient, admin_headers: dict[str, str], keeper_headers: dict[str, str]
):
    _prepare_data(client, admin_headers)

    cases = [
        ("/api/v1/export/stock", admin_headers),
        ("/api/v1/export/inbound", keeper_headers),
        ("/api/v1/export/outbound", keeper_headers),
        ("/api/v1/export/expiry", admin_headers),
    ]

    for url, headers in cases:
        response = client.get(url, headers=headers)
        assert response.status_code == 200, url
        assert response.content[:2] == b"PK"
        assert "spreadsheetml" in response.headers["content-type"]
        assert "filename*=UTF-8''" in response.headers["content-disposition"]

    _cleanup()
