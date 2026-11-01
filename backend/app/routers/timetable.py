from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models import User
from app.services import dataset_loader as loader
from app.services import store
from app.services.validator import validate_timetable

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


class TimetableIn(BaseModel):
    sessions: list[dict]
    fest_week: dict | None = None
    exams: list[dict] | None = None


def enrich(data: dict, assignments: list[dict]) -> list[dict]:
    sessions = {s["id"]: s for s in data["sessions"]}
    rooms = {r["id"]: r for r in data["rooms"]}
    faculty = {f["id"]: f for f in data["faculty"]}
    courses = {c["id"]: c for c in data["courses"]}
    out = []
    for a in assignments:
        s = sessions.get(a.get("session_id"))
        if not s:
            continue
        out.append({
            "session_id": s["id"],
            "course_id": s["course_id"],
            "course_title": courses.get(s["course_id"], {}).get("title", ""),
            "kind": s["kind"],
            "groups": s["groups"],
            "faculty_id": s["faculty_id"],
            "faculty_name": faculty.get(s["faculty_id"], {}).get("name", ""),
            "room_id": a.get("room_id"),
            "room_name": rooms.get(a.get("room_id"), {}).get("name", ""),
            "day": a.get("day"),
            "start_period": a.get("start_period"),
            "end_period": (a.get("start_period") or 0) + s["duration"] - 1,
            "duration": s["duration"],
            "basket_slot": s.get("basket_slot"),
        })
    return out


@router.get("/options")
def options(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = loader.get_data_dict(db)
    return {
        "groups": [{"id": g["id"], "name": g["name"]} for g in data["student_groups"]],
        "faculty": [{"id": f["id"], "name": f["name"]} for f in data["faculty"]],
        "rooms": [{"id": r["id"], "name": r["name"], "type": r["type"]} for r in data["rooms"]],
    }


@router.get("")
def get_timetable(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return store.get_doc(db, "timetable", {"sessions": []})


@router.put("")
def put_timetable(
    body: TimetableIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    store.set_doc(db, "timetable", {"sessions": body.sessions})
    if body.fest_week is not None:
        store.set_doc(db, "fest_week", body.fest_week)
    if body.exams is not None:
        store.set_doc(db, "exams", body.exams)
    report = validate_timetable(loader.get_data_dict(db), body.sessions)
    return {
        "stored": True,
        "valid": report["valid"],
        "hard_count": report["hard_count"],
        "soft_penalty": report["soft_penalty"],
        "first_violations": report["hard_violations"][:30],
    }


@router.get("/validate")
def validate(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tt = store.get_doc(db, "timetable", {"sessions": []})
    return validate_timetable(loader.get_data_dict(db), tt["sessions"])


@router.get("/view")
def view(
    by: str = Query(..., pattern="^(group|faculty|room)$"),
    id: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = loader.get_data_dict(db)
    tt = store.get_doc(db, "timetable", {"sessions": []})
    entries = enrich(data, tt["sessions"])
    if by == "group":
        entries = [e for e in entries if id in e["groups"]]
    elif by == "faculty":
        entries = [e for e in entries if e["faculty_id"] == id]
    else:
        entries = [e for e in entries if e["room_id"] == id]
    return {"by": by, "id": id, "entries": entries}
