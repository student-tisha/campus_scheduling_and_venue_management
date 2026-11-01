from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.services import dataset_loader as loader
from app.services import store
from app.services.booking_engine import DAYS, clean_for_export, decide_all


def all_requests(db: Session, data: dict, extras: list) -> list:
    return list(data["booking_requests"]) + list(extras)


def compute(db: Session, extras: list, extra_cancels: list) -> dict:
    data = loader.get_data_dict(db)
    placed = store.get_doc(db, "timetable", {"sessions": []})["sessions"]
    reqs = all_requests(db, data, extras)
    cancels = list(data["cancellations"]) + list(extra_cancels)
    result = decide_all(data, placed, reqs, cancels)
    result["requests"] = reqs
    return result


def current_extras(db):
    return store.get_doc(db, "extra_requests", []), store.get_doc(db, "extra_cancellations", [])


def run_and_store(db: Session) -> dict:
    extras, cancels = current_extras(db)
    result = compute(db, extras, cancels)
    store.set_doc(db, "booking_decisions", result["decisions"])
    store.set_doc(db, "fest_week", clean_for_export(result["decisions"], result["overrides"]))
    return result


def validate_input(data: dict, body: dict) -> list[str]:
    errors = []
    order = data["priority_order"]
    if body["requested_category"] not in order:
        errors.append(f"Category must be one of {order}")
    if body["attendance"] < 1:
        errors.append("Attendance must be at least 1")
    if body["duration_periods"] < 1:
        errors.append("Duration must be at least 1 period")
    if not body["windows"]:
        errors.append("At least one time window is required")
    for w in body["windows"]:
        if w["day"] not in DAYS:
            errors.append(f"Day must be one of {DAYS}")
        elif not (1 <= w["from_period"] <= w["to_period"] <= 13):
            errors.append("Periods must be between 1 and 13, and 'from' must not be after 'to'")
        elif w["to_period"] - w["from_period"] + 1 < body["duration_periods"]:
            errors.append(f"Window {w['day']} P{w['from_period']}-P{w['to_period']} is shorter "
                          f"than the duration")
    groups = {g["id"] for g in data["student_groups"]}
    for g in body.get("mandatory_for_groups") or []:
        if g not in groups:
            errors.append(f"Unknown student group '{g}'")
    return errors


def build_request(user, body: dict, existing: list, data: dict) -> dict:
    all_ids = [r["id"] for r in data["booking_requests"]] + [r["id"] for r in existing]
    latest = max(datetime.fromisoformat(r["submitted_at"]) for r in data["booking_requests"]) \
        if data["booking_requests"] else datetime.now().astimezone()
    n = len(existing) + 1
    return {
        "id": f"BR-U{n:02d}" if f"BR-U{n:02d}" not in all_ids else f"BR-U{n:02d}x",
        "submitted_at": (latest + timedelta(minutes=n)).isoformat(),
        "requester": user.club_name or user.name,
        "role": user.role,
        "department": user.department,
        "requested_category": body["requested_category"],
        "title": body["title"],
        "attendance": body["attendance"],
        "duration_periods": body["duration_periods"],
        "windows": body["windows"],
        "room_types": body.get("room_types") or [],
        "needs": body.get("needs") or [],
        "requested_room": body.get("requested_room"),
        "mandatory_for_groups": body.get("mandatory_for_groups") or [],
        "series_id": None,
        "raw_text": body.get("raw_text"),
        "submitted_by_user": user.id,
    }


def diff_decisions(before: list, after: list, skip_id: str | None = None) -> list:
    b = {d["request_id"]: d for d in before}
    changed = []
    for d in after:
        old = b.get(d["request_id"])
        if d["request_id"] == skip_id or old is None:
            continue
        keys = ("status", "day", "start_period", "room_id")
        if any(old.get(k) != d.get(k) for k in keys):
            changed.append({"request_id": d["request_id"], "was": old["status"],
                            "now": d["status"], "reason": d["reason"]})
    return changed
