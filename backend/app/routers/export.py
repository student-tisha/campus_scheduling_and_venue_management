import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import BACKEND_DIR
from app.core.deps import require_roles
from app.database import get_db
from app.models import User
from app.services import dataset_loader as loader
from app.services import store

router = APIRouter(prefix="/api/export", tags=["export"])

EXPORT_DIR = BACKEND_DIR.parent / "exports"


def build_schedule_json(db: Session) -> dict:
    tt = store.get_doc(db, "timetable", {"sessions": []})
    fest = store.get_doc(db, "fest_week", {"bookings": [], "session_overrides": []})
    exams = store.get_doc(db, "exams", [])
    return {
        "team": "CIT Scheduler",
        "dataset_id": loader.get_meta(db, "dataset_id"),
        "sessions": tt["sessions"],
        "fest_week": fest,
        "exams": exams,
    }


@router.get("/schedule")
def export_schedule(
    db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))
):
    return build_schedule_json(db)


@router.post("/save")
def save_export(
    name: str = Query("schedule.json"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    if name not in ("schedule.json", "schedule_after.json"):
        raise HTTPException(status_code=400, detail="Invalid file name")
    EXPORT_DIR.mkdir(exist_ok=True)
    path = EXPORT_DIR / name
    path.write_text(json.dumps(build_schedule_json(db), indent=2), encoding="utf-8")
    return {"saved": str(path)}
