from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.adjust import StockAdjustLog
from app.models.category import Category
from app.models.inbound import InboundOrder
from app.models.inventory import Inventory, InventoryBatch
from app.models.outbound import OutboundItem, OutboundOrder
from app.models.product import Product

TEST_BARCODE = "TEST-OUTBOUND-001"
TEST_CATEGORY = "出库测试分类"


def _cleanup() -> None:
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.barcode == TEST_BARCODE).first()
        if product:
            order_ids = [
                row[0]
                for row in db.query(OutboundItem.outbound_id)
                .filter(OutboundItem.product_id == product.id)
                .distinct()
                .all()
            ]
            db.query(OutboundItem).filter(OutboundItem.product_id == product.id).delete()
            if order_ids:
                db.query(OutboundOrder).filter(OutboundOrder.id.in_(order_ids)).delete(
                    synchronize_session=False
                )
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


def test_fifo_outbound_flow(
    client: TestClient, admin_headers: dict[str, str], keeper_headers: dict[str, str]
):
    _cleanup()

    category_id = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 92},
    ).json()["data"]["id"]

    product_id = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "出库测试商品",
            "category_id": category_id,
            "unit": "箱",
            "purchase_price": 10,
            "sale_price": 15,
            "safe_stock": 5,
            "shelf_life_days": 30,
        },
    ).json()["data"]["id"]

    today = date.today()
    # 三个批次：到期日 T+5 / T+10 / T+20，进价 10 / 11 / 12，各 5 件
    batch_plan = [
        (today - timedelta(days=25), 10),
        (today - timedelta(days=20), 11),
        (today - timedelta(days=10), 12),
    ]
    batch_nos: list[str] = []
    for production, cost in batch_plan:
        result = client.post(
            "/api/v1/inbound",
            headers=keeper_headers,
            json={
                "product_id": product_id,
                "quantity": 5,
                "cost_price": cost,
                "production_date": production.isoformat(),
            },
        ).json()
        assert result["code"] == 0, result
        batch_nos.append(result["data"]["batch_no"])

    # 销售出库 8 件，应跨两个批次：先扣到期最早的 5 件，再扣下一批 3 件
    outbound = client.post(
        "/api/v1/outbound",
        headers=keeper_headers,
        json={
            "product_id": product_id,
            "outbound_type": "sale",
            "quantity": 8,
        },
    ).json()
    assert outbound["code"] == 0, outbound
    data = outbound["data"]
    assert data["order_no"].startswith("CK")
    assert data["total_qty"] == 8
    assert len(data["items"]) == 2
    assert data["items"][0]["batch_no"] == batch_nos[0]
    assert data["items"][0]["quantity"] == 5
    assert data["items"][1]["batch_no"] == batch_nos[1]
    assert data["items"][1]["quantity"] == 3

    # 汇总库存已扣减
    stock = client.get(
        "/api/v1/stock", headers=admin_headers, params={"keyword": TEST_BARCODE}
    ).json()["data"]["items"][0]
    assert stock["total_qty"] == 7

    # 剩余批次：批次二剩 2，批次三剩 5
    batches = client.get(
        f"/api/v1/stock/{product_id}/batches", headers=admin_headers
    ).json()["data"]
    remaining = {item["batch_no"]: item["qty_remaining"] for item in batches}
    assert remaining[batch_nos[1]] == 2
    assert remaining[batch_nos[2]] == 5
    assert batch_nos[0] not in remaining

    # 库存不足拦截
    insufficient = client.post(
        "/api/v1/outbound",
        headers=keeper_headers,
        json={
            "product_id": product_id,
            "outbound_type": "sale",
            "quantity": 100,
        },
    ).json()
    assert insufficient["code"] != 0
    assert "库存不足" in insufficient["message"]

    # 报损必须填写原因
    missing_reason = client.post(
        "/api/v1/outbound",
        headers=keeper_headers,
        json={
            "product_id": product_id,
            "outbound_type": "loss",
            "quantity": 2,
        },
    )
    assert missing_reason.status_code == 422

    loss = client.post(
        "/api/v1/outbound",
        headers=keeper_headers,
        json={
            "product_id": product_id,
            "outbound_type": "loss",
            "quantity": 2,
            "reason": "包装破损",
        },
    ).json()
    assert loss["code"] == 0
    assert loss["data"]["items"][0]["batch_no"] == batch_nos[1]
    assert loss["data"]["items"][0]["quantity"] == 2

    # 流水按批次明细展开：3 条入库 + 3 条出库（销售 2 批次 + 报损 1 批次）
    records = client.get(
        f"/api/v1/stock/{product_id}/records", headers=admin_headers
    ).json()["data"]
    assert records["total"] == 6
    outbound_records = [r for r in records["items"] if r["record_type"] == "outbound"]
    assert len(outbound_records) == 3
    assert all(r["days_left"] is not None for r in outbound_records)

    # 出库记录查询
    outbound_list = client.get(
        "/api/v1/outbound",
        headers=keeper_headers,
        params={"keyword": TEST_BARCODE},
    ).json()["data"]
    assert outbound_list["total"] == 2
    assert outbound_list["items"][0]["items"]

    _cleanup()


def test_outbound_rejects_disabled_product(
    client: TestClient, admin_headers: dict[str, str]
):
    _cleanup()

    category_id = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": TEST_CATEGORY, "sort_order": 93},
    ).json()["data"]["id"]

    product_id = client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={
            "barcode": TEST_BARCODE,
            "name": "出库测试商品",
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
        "/api/v1/outbound",
        headers=admin_headers,
        json={
            "product_id": product_id,
            "outbound_type": "sale",
            "quantity": 1,
        },
    ).json()
    assert result["code"] != 0

    _cleanup()
