from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models import User
from app.services import booking_service as svc
from app.services import dataset_loader as loader
from app.services import store

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


class Window(BaseModel):
    day: str
    from_period: int
    to_period: int


class BookingIn(BaseModel):
    title: str
    requested_category: str
    attendance: int
    duration_periods: int
    windows: list[Window]
    room_types: list[str] = []
    needs: list[str] = []
    requested_room: str | None = None
    mandatory_for_groups: list[str] = []
    raw_text: str | None = None


def body_dict(body: BookingIn) -> dict:
    d = body.model_dump()
    return d


def visible(user: User, req: dict) -> bool:
    if user.role == "admin":
        return True
    if user.role == "department_coordinator":
        return req.get("department") == user.department or req.get("requester") == user.name
    return req.get("requester") in (user.name, user.club_name)


def stored_decisions(db: Session) -> dict:
    return {d["request_id"]: d for d in store.get_doc(db, "booking_decisions", [])}


@router.get("")
def list_bookings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = loader.get_data_dict(db)
    extras, _ = svc.current_extras(db)
    decisions = stored_decisions(db)
    approvals = set(store.get_doc(db, "booking_admin_approvals", []))
    out = []
    for r in svc.all_requests(db, data, extras):
        if visible(user, r):
            d = decisions.get(r["id"])
            if d:
                d = {**d, "admin_approved": r["id"] in approvals}
            out.append({"request": r, "decision": d})
    return {"count": len(out), "bookings": out, "decided": bool(decisions)}


@router.post("/decide")
def decide(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    result = svc.run_and_store(db)
    counts = {}
    for d in result["decisions"]:
        counts[d["status"]] = counts.get(d["status"], 0) + 1
    return {"counts": counts, "session_overrides": len(result["overrides"]),
            "needs_admin_approval": [d["request_id"] for d in result["decisions"]
                                     if d["needs_admin_approval"]]}


@router.post("/preview")
def preview(body: BookingIn, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    data = loader.get_data_dict(db)
    b = body_dict(body)
    errors = svc.validate_input(data, b)
    if errors:
        return {"valid_input": False, "errors": errors}
    extras, cancels = svc.current_extras(db)
    before = svc.compute(db, extras, cancels)["decisions"]
    req = svc.build_request(user, b, extras, data)
    after = svc.compute(db, extras + [req], cancels)["decisions"]
    mine = next(d for d in after if d["request_id"] == req["id"])
    return {"valid_input": True, "decision": mine,
            "changes_to_others": svc.diff_decisions(before, after, req["id"])}


@router.post("/request")
def submit(body: BookingIn, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    data = loader.get_data_dict(db)
    b = body_dict(body)
    errors = svc.validate_input(data, b)
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    extras, cancels = svc.current_extras(db)
    before = svc.compute(db, extras, cancels)["decisions"]
    req = svc.build_request(user, b, extras, data)
    store.set_doc(db, "extra_requests", extras + [req])
    result = svc.run_and_store(db)
    mine = next(d for d in result["decisions"] if d["request_id"] == req["id"])
    return {"request_id": req["id"], "decision": mine,
            "changes_to_others": svc.diff_decisions(before, result["decisions"], req["id"])}


@router.post("/{request_id}/cancel")
def cancel(request_id: str, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    data = loader.get_data_dict(db)
    extras, cancels = svc.current_extras(db)
    req = next((r for r in svc.all_requests(db, data, extras) if r["id"] == request_id), None)
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if not visible(user, req):
        raise HTTPException(status_code=403, detail="You can only cancel your own requests")
    already = {c["request_id"] for c in data["cancellations"]} | {c["request_id"] for c in cancels}
    if request_id in already:
        raise HTTPException(status_code=400, detail="Request is already cancelled")
    before = svc.compute(db, extras, cancels)["decisions"]
    cancels = cancels + [{"request_id": request_id, "by": user.name, "note": "Cancelled by user"}]
    store.set_doc(db, "extra_cancellations", cancels)
    result = svc.run_and_store(db)
    return {"cancelled": request_id,
            "changes_to_others": svc.diff_decisions(before, result["decisions"], request_id)}


@router.post("/{request_id}/admin-approve")
def admin_approve(request_id: str, db: Session = Depends(get_db),
                  user: User = Depends(require_roles("admin"))):
    data = loader.get_data_dict(db)
    extras, _ = svc.current_extras(db)
    req = next((r for r in svc.all_requests(db, data, extras) if r["id"] == request_id), None)
    dec = stored_decisions(db).get(request_id)
    if req is None or dec is None:
        raise HTTPException(status_code=404, detail="Decided booking not found")
    if not dec.get("needs_admin_approval"):
        raise HTTPException(status_code=400, detail="This booking does not move any class")
    if req.get("submitted_by_user") == user.id:
        raise HTTPException(status_code=403, detail="Nobody can approve their own request")
    approvals = store.get_doc(db, "booking_admin_approvals", [])
    if request_id not in approvals:
        store.set_doc(db, "booking_admin_approvals", approvals + [request_id])
    return {"approved": request_id, "moved_classes": dec["displaced"]}
