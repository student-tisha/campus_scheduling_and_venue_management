from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models import User
from app.services import dataset_loader as loader
from app.services import store

router = APIRouter(prefix="/api/dataset", tags=["dataset"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return loader.get_summary(db)


@router.get("/meta")
def meta(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {key: loader.get_meta(db, key) for key in loader.META_KEYS}


@router.post("/reload")
def reload_dataset(
    db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))
):
    counts = loader.load_dataset(db)
    store.clear_all(db)
    return {"reloaded": True, "counts": counts}
