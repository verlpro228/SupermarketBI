from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.adjust import StockAdjustLog
from app.models.category import Category
from app.models.expiry import ExpiryActionLog
from app.models.inbound import InboundOrder
from app.models.inspection import InspectionItem, InspectionRecord
from app.models.inventory import Inventory, InventoryBatch
from app.models.outbound import OutboundItem, OutboundOrder
from app.models.product import Product

TEST_BARCODE = "TEST-EXPIRY-001"
TEST_CATEGORY = "临期测试分类"


def _cleanup(record_ids: list[int] | None = None) -> None:
    db = SessionLocal()
    try:
        # 巡检明细通过外键引用批次，必须最先清理
        if record_ids:
            db.query(InspectionItem).filter(
                InspectionItem.record_id.in_(record_ids)
            ).delete(synchronize_session=False)

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

            # 低库存类明细没有批次，需按商品再清一次
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

        if record_ids:
            db.query(InspectionRecord).filter(
                InspectionRecord.id.in_(record_ids)
            ).delete(synchronize_session=False)
            db.commit()

        category = db.query(Category).filter(Category.name == TEST_CATEGORY).first()
        if category:
            db.delete(category)
            db.commit()
    finally:
        db.close()


def test_expiry_and_inspection_flow(
    client: TestClient, admin_headers: dict[str, str], keeper_headers: dict[str, str]
):
    _cleanup()

    category_id = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 94},
    ).json()["data"]["id"]

    product_id = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "临期测试商品",
            "category_id": category_id,
            "unit": "瓶",
            "purchase_price": 10,
            "sale_price": 15,
            "safe_stock": 50,
            "shelf_life_days": 30,
        },
    ).json()["data"]["id"]

    today = date.today()
    # 到期日：T-5（已过期）/ T+2（紧急）/ T+10（预警）/ T+25（预警）
    plan = [
        (today - timedelta(days=35), 3),
        (today - timedelta(days=28), 4),
        (today - timedelta(days=20), 5),
        (today - timedelta(days=5), 6),
    ]
    batch_nos: list[str] = []
    for production, qty in plan:
        result = client.post(
            "/api/v1/inbound",
            headers=keeper_headers,
            json={
                "product_id": product_id,
                "quantity": qty,
                "cost_price": 10,
                "production_date": production.isoformat(),
            },
        ).json()
        assert result["code"] == 0, result
        batch_nos.append(result["data"]["batch_no"])

    # 临期清单：4 条，按剩余天数升序
    expiry = client.get(
        "/api/v1/expiry", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]
    assert expiry["total"] == 4
    days = [item["days_left"] for item in expiry["items"]]
    assert days == [-5, 2, 10, 25]
    assert [item["level"] for item in expiry["items"]] == [
        "expired",
        "urgent",
        "warning",
        "warning",
    ]
    assert expiry["thresholds"] == {"urgent_days": 7, "warning_days": 30}
    assert expiry["items"][0]["stock_value"] == 30.0

    # 库管员视图无金额
    keeper_expiry = client.get(
        "/api/v1/expiry", headers=keeper_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]
    assert "stock_value" not in keeper_expiry["items"][0]

    # 分档筛选
    expired = client.get(
        "/api/v1/expiry",
        headers=admin_headers,
        params={"keyword": TEST_BARCODE, "level": "expired"},
    ).json()["data"]
    assert expired["total"] == 1

    warning = client.get(
        "/api/v1/expiry",
        headers=admin_headers,
        params={"keyword": TEST_BARCODE, "level": "warning"},
    ).json()["data"]
    assert warning["total"] == 2

    batch_map = {item["batch_no"]: item["batch_id"] for item in expiry["items"]}

    # 标记促销：该批次从待处理清单移除
    promo = client.post(
        "/api/v1/expiry/promo",
        headers=keeper_headers,
        json={"batch_id": batch_map[batch_nos[1]]},
    ).json()
    assert promo["code"] == 0

    after_promo = client.get(
        "/api/v1/expiry", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]
    assert after_promo["total"] == 3

    # 报损已过期批次全部 3 件
    loss = client.post(
        "/api/v1/expiry/loss",
        headers=keeper_headers,
        json={
            "items": [{"batch_id": batch_map[batch_nos[0]], "quantity": 3}],
            "reason": "已过期下架",
        },
    ).json()
    assert loss["code"] == 0, loss

    after_loss = client.get(
        "/api/v1/expiry", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]
    assert after_loss["total"] == 2

    # 库存同步扣减 18 - 3 = 15
    stock = client.get(
        "/api/v1/stock", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]["items"][0]
    assert stock["total_qty"] == 15

    # 报损数量超过批次剩余时拦截
    over_loss = client.post(
        "/api/v1/expiry/loss",
        headers=keeper_headers,
        json={
            "items": [{"batch_id": batch_map[batch_nos[1]], "quantity": 999}],
            "reason": "超量报损",
        },
    ).json()
    assert over_loss["code"] != 0

    # 处理记录：促销 1 条 + 报损 1 条
    actions = client.get(
        "/api/v1/expiry/actions",
        headers=admin_headers,
        params={"keyword": TEST_BARCODE},
    ).json()["data"]
    assert actions["total"] == 2

    # 执行巡检：低库存 1 条（15 < 50）+ 临期 3 条（剩余批次均 <= 30 天）
    run = client.post("/api/v1/inspections/run", headers=keeper_headers).json()
    assert run["code"] == 0, run
    record = run["data"]
    record_id = record["id"]
    assert record["hit_count"] >= 4
    assert record["low_stock_count"] >= 1
    assert record["near_expiry_count"] >= 3

    detail = client.get(f"/api/v1/inspections/{record_id}", headers=admin_headers).json()[
        "data"
    ]
    test_items = [
        item
        for item in detail["items"]
        if item["barcode"] == TEST_BARCODE
    ]
    low_items = [item for item in test_items if item["problem_type"] == "low_stock"]
    expiry_items = [item for item in test_items if item["problem_type"] == "near_expiry"]
    assert len(low_items) == 1
    assert low_items[0]["gap_qty"] == 35.0
    assert len(expiry_items) == 3

    # 标记已处理
    updated = client.put(
        "/api/v1/inspections/items/status",
        headers=keeper_headers,
        json={"ids": [low_items[0]["id"]], "status": "handled"},
    ).json()
    assert updated["code"] == 0

    detail_after = client.get(
        f"/api/v1/inspections/{record_id}", headers=admin_headers
    ).json()["data"]
    handled = [i for i in detail_after["items"] if i["id"] == low_items[0]["id"]][0]
    assert handled["status"] == "handled"
    assert handled["handled_at"]

    # 记录列表
    records = client.get("/api/v1/inspections", headers=admin_headers).json()["data"]
    assert records["total"] >= 1

    _cleanup([record_id])


def test_expiry_promo_twice_rejected(
    client: TestClient, admin_headers: dict[str, str]
):
    _cleanup()

    category_id = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 95},
    ).json()["data"]["id"]

    product_id = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "临期测试商品",
            "category_id": category_id,
            "shelf_life_days": 30,
        },
    ).json()["data"]["id"]

    inbound = client.post(
        "/api/v1/inbound",
        headers=admin_headers,
        json={
            "product_id": product_id,
            "quantity": 5,
            "cost_price": 10,
            "production_date": (date.today() - timedelta(days=25)).isoformat(),
        },
    ).json()

    batch_id = client.get(
        "/api/v1/expiry", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]["items"][0]["batch_id"]

    first = client.post(
        "/api/v1/expiry/promo", headers=admin_headers, json={"batch_id": batch_id}
    ).json()
    assert first["code"] == 0

    second = client.post(
        "/api/v1/expiry/promo", headers=admin_headers, json={"batch_id": batch_id}
    ).json()
    assert second["code"] != 0

    assert inbound["code"] == 0
    _cleanup()
