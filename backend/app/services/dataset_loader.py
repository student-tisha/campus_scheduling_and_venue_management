import json

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DatasetItem, DatasetMeta

COLLECTIONS = [
    "rooms", "room_unavailability", "faculty", "student_groups", "courses",
    "sessions", "booking_requests", "cancellations", "exams",
]

META_KEYS = ["dataset_id", "institute", "calendar", "priority_order", "role_category_cap"]


def _item_id(item, index: int) -> str:
    if isinstance(item, dict):
        for key in ("id", "request_id"):
            if key in item:
                return str(item[key])
    return str(index)


def load_dataset(db: Session) -> dict:
    raw = json.loads(settings.dataset_path.read_text(encoding="utf-8"))
    db.execute(delete(DatasetItem))
    db.execute(delete(DatasetMeta))
    for key in META_KEYS:
        if key in raw:
            db.add(DatasetMeta(key=key, value={"value": raw[key]}))
    for kind in COLLECTIONS:
        for index, item in enumerate(raw.get(kind, [])):
            db.add(DatasetItem(kind=kind, item_id=_item_id(item, index),
                               position=index, data=item))
    db.commit()
    return get_summary(db)


def is_loaded(db: Session) -> bool:
    return db.scalar(select(func.count()).select_from(DatasetItem)) > 0


def get_items(db: Session, kind: str) -> list[dict]:
    rows = db.scalars(
        select(DatasetItem).where(DatasetItem.kind == kind).order_by(DatasetItem.position)
    ).all()
    return [row.data for row in rows]


def get_meta(db: Session, key: str):
    row = db.get(DatasetMeta, key)
    return row.value["value"] if row else None


def get_summary(db: Session) -> dict:
    return {kind: len(get_items(db, kind)) for kind in COLLECTIONS}


def get_data_dict(db: Session) -> dict:
    data = {kind: get_items(db, kind) for kind in COLLECTIONS}
    for key in ("calendar", "priority_order", "role_category_cap"):
        data[key] = get_meta(db, key)
    return data


def replace_items(db: Session, kind: str, items: list) -> None:
    db.execute(delete(DatasetItem).where(DatasetItem.kind == kind))
    for index, item in enumerate(items):
        db.add(DatasetItem(kind=kind, item_id=_item_id(item, index), position=index, data=item))
    db.commit()
