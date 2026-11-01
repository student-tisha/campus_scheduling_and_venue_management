import copy
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import User
from app.services import booking_service
from app.services import dataset_loader as loader
from app.services import repair as greedy
from app.services import store
from app.services.validator import validate_timetable

try:  # Dipan's solver plugs in here if present
    from solver.repair import repair as solver_repair  # type: ignore
except Exception:  # noqa: BLE001
    solver_repair = None

SLOT = lambda a: (a.get("day"), a.get("start_period"), a.get("room_id"))  # noqa: E731


def apply_changes(data: dict, changes: list[dict]):
    data = copy.deepcopy(data)
    errors = []
    fac = {f["id"]: f for f in data["faculty"]}
    rooms = {r["id"] for r in data["rooms"]}
    for i, ch in enumerate(changes, 1):
        t = ch.get("type")
        tag = f"Change {i} ({t})"
        if t == "faculty_unavailable":
            f = fac.get(ch.get("faculty_id"))
            if not f:
                errors.append(f"{tag}: unknown faculty {ch.get('faculty_id')}")
                continue
            for d in ch.get("days", []):
                f.setdefault("unavailable", []).append(
                    {"day": d, "periods": ch.get("periods", list(range(1, 10))),
                     "reason": ch.get("reason", "")})
        elif t == "room_unavailable":
            if ch.get("room_id") not in rooms:
                errors.append(f"{tag}: unknown room {ch.get('room_id')}")
                continue
            for d in ch.get("days", []):
                data["room_unavailability"].append(
                    {"room_id": ch["room_id"], "day": d,
                     "periods": ch.get("periods", list(range(1, 10))),
                     "reason": ch.get("reason", "")})
        elif t == "add_faculty":
            if not ch.get("faculty") or ch["faculty"].get("id") in fac:
                errors.append(f"{tag}: missing or duplicate faculty")
                continue
            data["faculty"].append(ch["faculty"])
            fac[ch["faculty"]["id"]] = ch["faculty"]
        elif t == "add_session":
            s = ch.get("session")
            if not s or any(x["id"] == s.get("id") for x in data["sessions"]):
                errors.append(f"{tag}: missing or duplicate session")
                continue
            data["sessions"].append(s)
        elif t == "remove_session":
            before = len(data["sessions"])
            data["sessions"] = [s for s in data["sessions"] if s["id"] != ch.get("session_id")]
            if len(data["sessions"]) == before:
                errors.append(f"{tag}: unknown session {ch.get('session_id')}")
        else:
            errors.append(f"{tag}: unsupported change type")
    return data, errors


def build_diff(data, before, after):
    sess = {s["id"]: s for s in data["sessions"]}
    b = {a["session_id"]: a for a in before}
    a2 = {a["session_id"]: a for a in after}
    moved, added, removed = [], [], []
    for sid, new in a2.items():
        old = b.get(sid)
        item = {"session_id": sid, "course_id": sess.get(sid, {}).get("course_id"),
                "faculty_id": sess.get(sid, {}).get("faculty_id")}
        if old is None:
            added.append({**item, "to": SLOT(new)})
        elif SLOT(old) != SLOT(new):
            moved.append({**item, "from": SLOT(old), "to": SLOT(new)})
    for sid, old in b.items():
        if sid not in a2:
            removed.append({"session_id": sid, "from": SLOT(old)})
    return {"moved": moved, "added": added, "removed": removed,
            "moved_count": len(moved)}


def _candidates(new_data, current):
    runs = []
    if solver_repair:
        try:
            runs.append(("solver", solver_repair(new_data, current)))
        except Exception as e:  # noqa: BLE001
            runs.append(("solver", {"assignments": [], "infeasible": True,
                                    "conflicts": [f"solver error: {e}"]}))
    runs.append(("builtin", greedy.repair(new_data, current)))
    return runs


def create_proposal(db: Session, user: User, changes: list[dict], note: str | None):
    data = loader.get_data_dict(db)
    current = store.get_doc(db, "timetable", {"sessions": []})["sessions"]
    if not current:
        return {"error": "No timetable is stored yet. Generate or load the timetable first."}
    new_data, errors = apply_changes(data, changes)
    if errors:
        return {"error": errors}
    best = None
    conflicts = []
    for name, res in _candidates(new_data, current):
        if res["infeasible"]:
            conflicts += res["conflicts"]
            continue
        rep = validate_timetable(new_data, res["assignments"])
        if not rep["valid"]:
            conflicts += [v["message"] for v in rep["hard_violations"][:3]]
            continue
        moved = build_diff(new_data, current, res["assignments"])["moved_count"]
        if best is None or moved < best[0]:
            best = (moved, name, res["assignments"], rep)
    props = store.get_doc(db, "change_proposals", [])
    pid = f"CH-{len(props) + 1:03d}"
    base = {"id": pid, "status": "pending", "created_by": {"id": user.id, "name": user.name,
            "role": user.role}, "created_at": datetime.now().astimezone().isoformat(),
            "note": note, "changes": changes}
    if best is None:
        prop = {**base, "status": "no_valid_fix", "infeasible": True,
                "conflicts": sorted(set(conflicts)),
                "message": "No valid fix exists. These constraints are in conflict."}
    else:
        moved, name, assignments, rep = best
        before_rep = validate_timetable(data, current)
        prop = {**base, "infeasible": False, "engine": name, "conflicts": [],
                "diff": build_diff(new_data, current, assignments),
                "soft_before": before_rep["soft_penalty"], "soft_after": rep["soft_penalty"],
                "hard_after": rep["hard_count"], "new_assignments": assignments,
                "baseline_size": len(current)}
    store.set_doc(db, "change_proposals", props + [prop])
    return prop


def public(prop: dict, full: bool = False) -> dict:
    out = {k: v for k, v in prop.items() if k != "new_assignments"}
    if not full and "diff" in out:
        d = out["diff"]
        out["diff"] = {"moved_count": d["moved_count"], "added": len(d["added"]),
                       "removed": len(d["removed"])}
    return out


def approve(db: Session, user: User, pid: str):
    props = store.get_doc(db, "change_proposals", [])
    prop = next((p for p in props if p["id"] == pid), None)
    if prop is None:
        return {"error": "Proposal not found", "code": 404}
    if prop["status"] != "pending":
        return {"error": f"Proposal is already {prop['status']}", "code": 400}
    if prop["created_by"]["id"] == user.id and user.role != "admin":
        return {"error": "Nobody can approve their own request", "code": 403}
    data = loader.get_data_dict(db)
    current = store.get_doc(db, "timetable", {"sessions": []})["sessions"]
    if len(current) != prop["baseline_size"]:
        return {"error": "Timetable changed since this proposal. Please propose again.", "code": 409}
    new_data, errors = apply_changes(data, prop["changes"])
    rep = validate_timetable(new_data, prop["new_assignments"])
    if errors or not rep["valid"]:
        return {"error": "Proposal failed final validation, not applied",
                "details": errors or rep["hard_violations"][:5], "code": 409}
    loader.replace_items(db, "faculty", new_data["faculty"])
    loader.replace_items(db, "room_unavailability", new_data["room_unavailability"])
    loader.replace_items(db, "sessions", new_data["sessions"])
    store.set_doc(db, "timetable", {"sessions": prop["new_assignments"]})
    prop["status"] = "approved"
    prop["approved_by"] = user.name
    prop["approved_at"] = datetime.now().astimezone().isoformat()
    store.set_doc(db, "change_proposals", props)
    if store.get_doc(db, "booking_decisions", []):
        booking_service.run_and_store(db)
    return {"approved": pid, "moved_count": prop["diff"]["moved_count"]}


def reject(db: Session, user: User, pid: str, reason: str | None):
    props = store.get_doc(db, "change_proposals", [])
    prop = next((p for p in props if p["id"] == pid), None)
    if prop is None or prop["status"] != "pending":
        return {"error": "Pending proposal not found", "code": 404}
    prop["status"] = "rejected"
    prop["rejected_by"] = user.name
    prop["reject_reason"] = reason
    store.set_doc(db, "change_proposals", props)
    return {"rejected": pid}
