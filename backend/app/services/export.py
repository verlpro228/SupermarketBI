from datetime import datetime
from io import BytesIO

from sqlalchemy.orm import Session

from app.schemas.expiry import ExpiryActionQuery, ExpiryQuery
from app.schemas.inbound import InboundQuery
from app.schemas.outbound import OutboundQuery
from app.schemas.stock import StockQuery
from app.services import expiry as expiry_service
from app.services import inbound as inbound_service
from app.services import outbound as outbound_service
from app.services import stock as stock_service
from app.utils.excel import build_workbook

MAX_EXPORT_ROWS = 50000

EXPIRY_LEVEL_TEXT = {
    "expired": "已过期",
    "urgent": "紧急",
    "warning": "预警",
    "normal": "正常",
}


def _filename(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"


def export_stock(db: Session, query: StockQuery, is_admin: bool) -> tuple[BytesIO, str]:
    query = query.model_copy(update={"page": 1, "page_size": MAX_EXPORT_ROWS})
    items, _ = stock_service.list_stock(db, query, is_admin)

    headers = ["商品名称", "条码", "分类", "单位", "当前库存", "安全库存", "最近到期日", "剩余天数", "状态"]
    if is_admin:
        headers.insert(6, "进价")
        headers.append("库存货值")

    rows = []
    for item in items:
        row = [
            item.name,
            item.barcode,
            item.category_name or "",
            item.unit or "",
            item.total_qty,
            item.safe_stock,
            item.nearest_expiry or "",
            item.days_left if item.days_left is not None else "",
            "正常" if item.product_status == 1 else "已停用",
        ]
        if is_admin:
            row.insert(6, getattr(item, "purchase_price", ""))
            row.append(getattr(item, "stock_value", ""))
        rows.append(row)

    return build_workbook("库存列表", headers, rows), _filename("库存列表")


def export_inbound(db: Session, query: InboundQuery) -> tuple[BytesIO, str]:
    query = query.model_copy(update={"page": 1, "page_size": MAX_EXPORT_ROWS})
    items, _ = inbound_service.list_inbounds(db, query)

    headers = [
        "入库单号",
        "商品名称",
        "条码",
        "批次号",
        "数量",
        "进价",
        "金额",
        "生产日期",
        "到期日",
        "供应商",
        "操作人",
        "备注",
        "入库时间",
    ]

    rows = [
        [
            item.order_no,
            item.product_name or "",
            item.barcode or "",
            item.batch_no or "",
            item.quantity,
            item.cost_price,
            item.amount,
            item.production_date,
            item.expiry_date,
            item.supplier or "",
            item.operator_name or "",
            item.remark or "",
            item.created_at or "",
        ]
        for item in items
    ]

    return build_workbook("入库记录", headers, rows), _filename("入库记录")


def export_outbound(db: Session, query: OutboundQuery) -> tuple[BytesIO, str]:
    query = query.model_copy(update={"page": 1, "page_size": MAX_EXPORT_ROWS})
    items, _ = outbound_service.list_outbounds(db, query)

    headers = [
        "出库单号",
        "商品名称",
        "条码",
        "出库类型",
        "数量",
        "成本金额",
        "报损原因",
        "操作人",
        "备注",
        "出库时间",
    ]

    rows = [
        [
            item.order_no,
            item.product_name or "",
            item.barcode or "",
            "销售出库" if item.outbound_type == "sale" else "报损出库",
            item.total_qty,
            item.total_amount,
            item.reason or "",
            item.operator_name or "",
            item.remark or "",
            item.created_at or "",
        ]
        for item in items
    ]

    return build_workbook("出库记录", headers, rows), _filename("出库记录")


def export_expiry(db: Session, query: ExpiryQuery, is_admin: bool) -> tuple[BytesIO, str]:
    query = query.model_copy(update={"page": 1, "page_size": MAX_EXPORT_ROWS})
    items, _, _ = expiry_service.list_expiry_batches(db, query, is_admin)

    headers = ["商品名称", "条码", "批次号", "生产日期", "到期日", "剩余天数", "数量", "分档"]
    if is_admin:
        headers.append("货值")

    rows = []
    for item in items:
        row = [
            item.product_name,
            item.barcode,
            item.batch_no,
            item.production_date,
            item.expiry_date,
            item.days_left,
            item.qty_remaining,
            EXPIRY_LEVEL_TEXT.get(item.level, item.level),
        ]
        if is_admin:
            row.append(getattr(item, "stock_value", ""))
        rows.append(row)

    return build_workbook("临期清单", headers, rows), _filename("临期清单")


def export_actions(db: Session, query: ExpiryActionQuery) -> tuple[BytesIO, str]:
    query = query.model_copy(update={"page": 1, "page_size": MAX_EXPORT_ROWS})
    items, _ = expiry_service.list_action_logs(db, query)

    headers = ["商品名称", "条码", "批次号", "处理方式", "处理数量", "关联出库单", "处理人", "处理时间"]
    rows = [
        [
            item.product_name or "",
            item.barcode or "",
            item.batch_no or "",
            "报损" if item.action == "loss" else "标记促销",
            item.quantity,
            item.order_no or "",
            item.operator_name or "",
            item.created_at or "",
        ]
        for item in items
    ]

    return build_workbook("临期处理记录", headers, rows), _filename("临期处理记录")
