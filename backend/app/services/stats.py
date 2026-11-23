from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.crud import stats as stats_crud
from app.schemas.stats import (
    CategoryFlowItem,
    CategoryQuantityItem,
    CategoryValue,
    DashboardKpi,
    DashboardOut,
    ExpiryLevelCount,
    InboundAnalysisOut,
    IoTrendItem,
    LowStockItem,
    OutboundAnalysisOut,
    OutboundTypeItem,
    ProductQuantityItem,
    ProductValueItem,
    SupplierRankItem,
    TrendItem,
)
from app.utils.config import get_expiry_thresholds


def _label_series(start: date, end: date, granularity: str) -> list[str]:
    labels: list[str] = []

    if granularity == "month":
        cursor = date(start.year, start.month, 1)
        while cursor <= end:
            labels.append(cursor.strftime("%Y-%m"))
            cursor = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)
    else:
        cursor = start
        while cursor <= end:
            labels.append(cursor.strftime("%Y-%m-%d"))
            cursor += timedelta(days=1)

    return labels


def get_trend(db: Session, days: int, granularity: str) -> list[TrendItem]:
    end = date.today()
    start = end - timedelta(days=days - 1)
    fmt = "%Y-%m" if granularity == "month" else "%Y-%m-%d"

    inbound_map = stats_crud.inbound_trend(db, start, fmt)
    outbound_map = stats_crud.outbound_trend(db, start, fmt)

    return [
        TrendItem(
            label=label,
            inbound=float(inbound_map.get(label, 0)),
            outbound=float(outbound_map.get(label, 0)),
        )
        for label in _label_series(start, end, granularity)
    ]


def get_dashboard(db: Session, days: int, is_admin: bool) -> DashboardOut:
    urgent_days, warning_days = get_expiry_thresholds(db)
    start_date = date.today() - timedelta(days=days - 1)

    kpi = DashboardKpi(
        product_count=stats_crud.count_products(db),
        total_stock=float(stats_crud.sum_stock(db)),
        stock_value=float(stats_crud.sum_stock_value(db)) if is_admin else None,
        expiry_count=stats_crud.count_expiry_products(db, warning_days),
    )

    trend = get_trend(db, days, "day")

    category_value: list[CategoryValue] = []
    top_value_products: list[ProductValueItem] = []
    if is_admin:
        category_value = [
            CategoryValue(category=row["category"], value=round(float(row["value"]), 2))
            for row in stats_crud.category_stock_values(db)
        ]
        top_value_products = [
            ProductValueItem(name=row["name"], value=float(row["value"]))
            for row in stats_crud.top_value_products(db, 10)
        ]

    category_flow = [
        CategoryFlowItem(
            category=row["category"],
            inbound=float(row["inbound"]),
            outbound=float(row["outbound"]),
        )
        for row in stats_crud.category_flow(db, start_date)
    ]

    level_order = {"expired": 0, "urgent": 1, "warning": 2}
    raw_expiry = stats_crud.expiry_distribution(db, urgent_days, warning_days)
    raw_expiry.sort(key=lambda row: level_order.get(row["level"], 9))
    expiry_distribution = [
        ExpiryLevelCount(level=row["level"], count=int(row["count"]))
        for row in raw_expiry
    ]

    low_stock_products = [
        LowStockItem(name=row["name"], gap=float(row["gap"]))
        for row in stats_crud.low_stock_products(db, 10)
    ]

    return DashboardOut(
        kpi=kpi,
        trend=trend,
        category_value=category_value,
        category_flow=category_flow,
        expiry_distribution=expiry_distribution,
        top_value_products=top_value_products,
        low_stock_products=low_stock_products,
    )


def get_inbound_analysis(db: Session, days: int) -> InboundAnalysisOut:
    end = date.today()
    start = end - timedelta(days=days - 1)

    raw = {row["label"]: row for row in stats_crud.inbound_daily(db, start)}
    trend = [
        IoTrendItem(
            label=label,
            quantity=float(raw[label]["quantity"]) if label in raw else 0.0,
            orders=int(raw[label]["orders"]) if label in raw else 0,
        )
        for label in _label_series(start, end, "day")
    ]

    suppliers = [
        SupplierRankItem(
            supplier=row["supplier"],
            quantity=float(row["quantity"]),
            orders=int(row["orders"]),
        )
        for row in stats_crud.supplier_ranking(db, start)
    ]

    categories = [
        CategoryQuantityItem(
            category=row["category"], quantity=float(row["quantity"])
        )
        for row in stats_crud.category_inbound(db, start)
    ]

    return InboundAnalysisOut(
        days=days,
        trend=trend,
        supplier_ranking=suppliers,
        category_distribution=categories,
    )


def get_outbound_analysis(db: Session, days: int) -> OutboundAnalysisOut:
    end = date.today()
    start = end - timedelta(days=days - 1)

    raw = {row["label"]: row for row in stats_crud.outbound_daily(db, start)}
    trend = [
        IoTrendItem(
            label=label,
            quantity=float(raw[label]["quantity"]) if label in raw else 0.0,
            orders=int(raw[label]["orders"]) if label in raw else 0,
        )
        for label in _label_series(start, end, "day")
    ]

    type_distribution = [
        OutboundTypeItem(
            type=row["type"],
            quantity=float(row["quantity"]),
            orders=int(row["orders"]),
        )
        for row in stats_crud.outbound_type_distribution(db, start)
    ]

    products = [
        ProductQuantityItem(name=row["name"], quantity=float(row["quantity"]))
        for row in stats_crud.top_outbound_products(db, start)
    ]

    return OutboundAnalysisOut(
        days=days,
        trend=trend,
        type_distribution=type_distribution,
        top_products=products,
    )
