from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.models.inventory import Inventory, InventoryBatch


def add_stock(db: Session, product_id: int, quantity) -> None:
    """原子增加商品库存汇总，不存在则新建。"""
    stmt = mysql_insert(Inventory).values(product_id=product_id, total_qty=quantity)
    stmt = stmt.on_duplicate_key_update(
        total_qty=Inventory.total_qty + stmt.inserted.total_qty
    )
    db.execute(stmt)


def get_batch(db: Session, batch_id: int, for_update: bool = False) -> InventoryBatch | None:
    stmt = select(InventoryBatch).where(InventoryBatch.id == batch_id)
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def list_batches(db: Session, product_id: int, only_remaining: bool = True) -> list[InventoryBatch]:
    stmt = select(InventoryBatch).where(InventoryBatch.product_id == product_id)
    if only_remaining:
        stmt = stmt.where(InventoryBatch.qty_remaining > 0)
    stmt = stmt.order_by(InventoryBatch.expiry_date.asc(), InventoryBatch.id.asc())
    return list(db.scalars(stmt).all())


def create_batch(db: Session, **kwargs) -> InventoryBatch:
    batch = InventoryBatch(**kwargs)
    db.add(batch)
    db.flush()
    return batch
