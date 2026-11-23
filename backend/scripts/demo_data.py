"""演示业务数据：入库批次、销售出库、报损、临期处理、库存调整、巡检。

数据设计目标：
1. 近 30 天都有出入库发生，看板与趋势图不为空；
2. 覆盖临期三档（已过期 / 紧急 / 预警）；
3. 覆盖低库存场景，巡检能命中问题；
4. 覆盖促销标记、报损、盘点调整等处理记录。

所有数据通过 service 层写入，与手工操作走同一套业务规则。
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.inbound import InboundOrder
from app.models.inventory import InventoryBatch
from app.models.product import Product
from app.models.user import User
from app.schemas.expiry import ExpiryLossItem, ExpiryLossPayload, ExpiryPromoPayload
from app.schemas.inbound import InboundCreate
from app.schemas.outbound import OutboundCreate
from app.schemas.stock import StockAdjustPayload
from app.services import expiry as expiry_service
from app.services import inbound as inbound_service
from app.services import inspection as inspection_service
from app.services import outbound as outbound_service
from app.services import stock as stock_service

DEMO_REMARK = "演示数据"

SUPPLIERS = [
    "华润万家配送中心",
    "本地生鲜合作社",
    "康师傅区域代理商",
    "光明乳业经销商",
    "宝洁日化批发部",
]

# (条码, 生产日期相对今天的天数, 数量, 进价)
INBOUND_PLAN: list[tuple[str, int, float, float]] = [
    # 伊利纯牛奶：正常批次 + 紧急临期批次（到期 +4 天）
    ("6901234567890", -35, 30, 45.00),
    ("6901234567890", -176, 12, 45.00),
    # 蒙牛酸奶：已过期批次（到期 -7 天）+ 预警批次（到期 +16 天）
    ("6901234567891", -28, 40, 12.50),
    ("6901234567891", -5, 25, 12.50),
    ("6902345678901", -20, 20, 42.00),  # 可口可乐
    ("6902345678902", -30, 35, 24.00),  # 农夫山泉
    # 乐事薯片：正常批次 + 预警批次（到期 +15 天）
    ("6903456789012", -40, 60, 4.20),
    ("6903456789012", -165, 25, 4.20),
    ("6903456789013", -30, 45, 5.80),  # 奥利奥
    ("6904567890123", -3, 8, 3.60),  # 有机生菜，紧急（到期 +2 天）
    ("6904567890124", -8, 6, 22.00),  # 精瘦肉，已过期（到期 -5 天）
    ("6905678901234", -50, 15, 58.00),  # 金龙鱼调和油
    ("6905678901235", -60, 30, 6.80),  # 海天生抽
    ("6906789012345", -45, 25, 18.00),  # 洁柔抽纸
]

# (条码, 数量, 出库日相对今天的天数)
SALE_PLAN: list[tuple[str, float, int]] = [
    ("6901234567890", 5, -20),
    ("6902345678901", 8, -18),
    ("6902345678902", 12, -15),
    ("6903456789012", 18, -12),
    ("6903456789013", 12, -9),
    ("6905678901234", 5, -6),
    ("6906789012345", 6, -3),
]


def _set_created_at(
    db: Session, table: str, row_id: int, day: date, hour: int = 10, minute: int = 0
) -> None:
    db.execute(
        text(f"UPDATE {table} SET created_at = :ts WHERE id = :row_id"),
        {"ts": datetime.combine(day, time(hour, minute)), "row_id": row_id},
    )
    db.commit()


def _entry_date(production_date: date, today: date) -> date:
    """入库日：生产后 2 天补货，但不早于近 28 天，也不晚于今天。"""
    entry = max(production_date + timedelta(days=2), today - timedelta(days=28))
    return min(entry, today)


def _fill_new_product_stock(db: Session, admin: User, today: date) -> None:
    """给扩充商品补一批初始库存，避免库存页出现大量零库存告警。"""
    rows = db.execute(
        text(
            """
            SELECT p.id, p.barcode, p.purchase_price, p.safe_stock, p.shelf_life_days
            FROM product p
            LEFT JOIN inventory i ON i.product_id = p.id
            WHERE p.barcode LIKE '691%' AND i.product_id IS NULL
            ORDER BY p.id
            """
        )
    ).mappings().all()

    if not rows:
        print("新增商品均已有库存，无需补充")
        return

    for index, row in enumerate(rows):
        shelf_life = int(row["shelf_life_days"]) or 30
        safe_stock = float(row["safe_stock"]) or 10
        quantity = max(10.0, round(safe_stock * 1.6, 0))

        # 生产日期尽量贴近近期，短保生鲜落在紧急档，长保商品保持正常
        production_offset = min(25, max(0, shelf_life // 4))
        production_date = today - timedelta(days=production_offset)
        # 入库时间分散到近 28 天，避免同一天集中入库造成趋势图尖峰；且不早于生产日期
        entry_offset = min((index * 5) % 28, production_offset)
        entry_day = today - timedelta(days=entry_offset)

        result = inbound_service.create_inbound(
            db,
            InboundCreate(
                product_id=row["id"],
                quantity=quantity,
                cost_price=float(row["purchase_price"]),
                production_date=production_date,
                supplier=SUPPLIERS[index % len(SUPPLIERS)],
                remark=DEMO_REMARK,
            ),
            admin,
        )
        _set_created_at(db, "inbound_order", result.id, entry_day, 9, 30)

    print(f"已为 {len(rows)} 个新增商品补充初始库存")


def generate_demo_data(db: Session) -> None:
    admin = db.scalar(select(User).where(User.username == "admin"))
    if admin is None:
        print("未找到 admin 账号，跳过演示数据")
        return

    today = date.today()

    exists = db.scalar(
        select(func.count(InboundOrder.id)).where(InboundOrder.remark == DEMO_REMARK)
    )
    if exists:
        print("演示数据已存在，仅补充新增商品的初始库存")
        _fill_new_product_stock(db, admin, today)
        return

    products = {item.barcode: item for item in db.scalars(select(Product)).all()}

    # ---------- 1. 入库：按生产日期建批次 ----------
    entry_dates: dict[str, date] = {}
    batch_map: dict[tuple[str, int], int] = {}
    supplier_index = 0

    for barcode, offset, quantity, cost_price in INBOUND_PLAN:
        product = products.get(barcode)
        if product is None:
            continue

        production_date = today + timedelta(days=offset)
        result = inbound_service.create_inbound(
            db,
            InboundCreate(
                product_id=product.id,
                quantity=quantity,
                cost_price=cost_price,
                production_date=production_date,
                supplier=SUPPLIERS[supplier_index % len(SUPPLIERS)],
                remark=DEMO_REMARK,
            ),
            admin,
        )
        supplier_index += 1

        entry_day = _entry_date(production_date, today)
        _set_created_at(db, "inbound_order", result.id, entry_day, 9, 30)
        entry_dates.setdefault(barcode, entry_day)

        batch = db.scalar(
            select(InventoryBatch).where(InventoryBatch.batch_no == result.batch_no)
        )
        if batch is not None:
            batch_map[(barcode, offset)] = batch.id

    print(f"演示入库完成：{len(batch_map)} 个批次")

    # ---------- 2. 销售出库 ----------
    for barcode, quantity, offset in SALE_PLAN:
        product = products.get(barcode)
        if product is None:
            continue

        result = outbound_service.create_outbound(
            db,
            OutboundCreate(
                product_id=product.id,
                outbound_type="sale",
                quantity=quantity,
                remark=DEMO_REMARK,
            ),
            admin,
        )

        earliest_entry = entry_dates.get(barcode, today - timedelta(days=20))
        sale_day = max(earliest_entry + timedelta(days=1), today + timedelta(days=offset))
        _set_created_at(db, "outbound_order", result.id, sale_day, 15, 20)

    print(f"演示销售出库完成：{len(SALE_PLAN)} 笔")

    # ---------- 3. 报损出库（非临期，破损核销） ----------
    soy = products.get("6905678901235")
    if soy is not None:
        result = outbound_service.create_outbound(
            db,
            OutboundCreate(
                product_id=soy.id,
                outbound_type="loss",
                quantity=3,
                reason="运输破损",
                remark=DEMO_REMARK,
            ),
            admin,
        )
        _set_created_at(
            db, "outbound_order", result.id, today - timedelta(days=10), 11, 0
        )
        print("演示报损出库完成：1 笔")

    # ---------- 4. 临期处理：报损已过期批次 ----------
    # 精瘦肉（已过期）刻意保留在待处理清单中，用于展示"已过期"分档
    loss_items: list[ExpiryLossItem] = []
    for key in [("6901234567891", -28)]:
        batch_id = batch_map.get(key)
        if batch_id is None:
            continue
        batch = db.scalar(
            select(InventoryBatch).where(InventoryBatch.id == batch_id)
        )
        if batch is None or batch.qty_remaining <= 0:
            continue
        loss_items.append(
            ExpiryLossItem(batch_id=batch_id, quantity=float(batch.qty_remaining))
        )

    if loss_items:
        expiry_service.batch_loss(
            db,
            ExpiryLossPayload(items=loss_items, reason="超过保质期下架"),
            admin,
        )
        print(f"演示临期报损完成：{len(loss_items)} 个批次")

    # ---------- 5. 临期处理：标记促销 ----------
    # 只促销生菜一个批次，其余临期批次保留在待处理清单中
    promo_keys = [("6904567890123", -3)]
    promo_count = 0
    for key in promo_keys:
        batch_id = batch_map.get(key)
        if batch_id is None:
            continue
        try:
            expiry_service.mark_promo(db, ExpiryPromoPayload(batch_id=batch_id), admin)
            promo_count += 1
        except Exception:
            db.rollback()
    print(f"演示标记促销完成：{promo_count} 个批次")

    # ---------- 6. 库存调整：盘点差异 ----------
    tissue_key = ("6906789012345", -45)
    tissue_batch_id = batch_map.get(tissue_key)
    tissue = products.get("6906789012345")
    if tissue_batch_id and tissue:
        batch = db.scalar(
            select(InventoryBatch).where(InventoryBatch.id == tissue_batch_id)
        )
        if batch is not None and batch.qty_remaining > 2:
            stock_service.adjust_stock(
                db,
                StockAdjustPayload(
                    product_id=tissue.id,
                    batch_id=tissue_batch_id,
                    new_qty=float(batch.qty_remaining) - 2,
                    reason="月度盘点差异",
                ),
                admin,
            )
            print("演示库存调整完成：1 笔")

    # ---------- 7. 扩充商品的初始库存 ----------
    # 必须在巡检之前完成，否则扩充商品会被全部判定为低库存
    _fill_new_product_stock(db, admin, today)

    # ---------- 8. 巡检快照 ----------
    record = inspection_service.run_inspection(db, admin)
    _set_created_at(
        db, "inspection_record", record.id, today - timedelta(days=1), 16, 0
    )
    print(f"演示巡检完成：命中 {record.hit_count} 条问题")
