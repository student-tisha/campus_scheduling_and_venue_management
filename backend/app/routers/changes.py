from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models import User
from app.services import changes as svc
from app.services import dataset_loader as loader
from app.services import store

router = APIRouter(prefix="/api/changes", tags=["changes"])


class ProposeIn(BaseModel):
    changes: list[dict]
    note: str | None = None


class RejectIn(BaseModel):
    reason: str | None = None


def check_permission(db: Session, user: User, changes: list[dict]):
    if user.role == "admin":
        return
    fac = {f["id"]: f for f in loader.get_items(db, "faculty")}
    for ch in changes:
        t = ch.get("type")
        if user.role == "faculty":
            own_unavail = t == "faculty_unavailable" and ch.get("faculty_id") == user.faculty_id
            own_extra = t == "add_session" and \
                (ch.get("session") or {}).get("faculty_id") == user.faculty_id
            if not (own_unavail or own_extra):
                raise HTTPException(403, "Faculty can only change their own sessions")
        elif user.role == "department_coordinator":
            ok = t == "faculty_unavailable" and \
                fac.get(ch.get("faculty_id"), {}).get("department") == user.department
            ok = ok or (t == "add_session")
            if not ok:
                raise HTTPException(403, "Coordinators can only change their department's sessions")
        else:
            raise HTTPException(403, "Your role cannot request schedule changes")


@router.post("/propose")
def propose(body: ProposeIn, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    check_permission(db, user, body.changes)
    result = svc.create_proposal(db, user, body.changes, body.note)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return svc.public(result, full=True)


@router.get("")
def list_changes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    props = store.get_doc(db, "change_proposals", [])
    if user.role != "admin":
        props = [p for p in props if p["created_by"]["id"] == user.id]
    return {"count": len(props), "proposals": [svc.public(p) for p in props],
            "pending": sum(1 for p in props if p["status"] == "pending")}


@router.get("/{pid}")
def get_change(pid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    props = store.get_doc(db, "change_proposals", [])
    prop = next((p for p in props if p["id"] == pid), None)
    if prop is None or (user.role != "admin" and prop["created_by"]["id"] != user.id):
        raise HTTPException(404, "Proposal not found")
    return svc.public(prop, full=True)


@router.post("/{pid}/approve")
def approve(pid: str, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    res = svc.approve(db, user, pid)
    if "error" in res:
        raise HTTPException(res["code"], res if "details" in res else res["error"])
    return res


@router.post("/{pid}/reject")
def reject(pid: str, body: RejectIn, db: Session = Depends(get_db),
           user: User = Depends(require_roles("admin"))):
    res = svc.reject(db, user, pid, body.reason)
    if "error" in res:
        raise HTTPException(404, res["error"])
    return res
