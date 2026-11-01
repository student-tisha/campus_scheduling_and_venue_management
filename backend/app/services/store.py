from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import StoredDoc


def get_doc(db: Session, key: str, default=None):
    row = db.get(StoredDoc, key)
    return row.data["value"] if row else default


def set_doc(db: Session, key: str, value) -> None:
    row = db.get(StoredDoc, key)
    if row:
        row.data = {"value": value}
    else:
        db.add(StoredDoc(key=key, data={"value": value}))
    db.commit()


def clear_all(db: Session) -> None:
    db.execute(delete(StoredDoc))
    db.commit()
