from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.services import dataset_loader as loader
from app.services import store
from app.services.exams import validate_exams
from app.services.validator import validate_timetable

DAYS = ["MON", "TUE", "WED", "THU", "FRI"]


def build(db: Session, user) -> dict:
    data = loader.get_data_dict(db)
    tt = store.get_doc(db, "timetable", {"sessions": []})["sessions"]
    exams = store.get_doc(db, "exams", [])
    decisions = store.get_doc(db, "booking_decisions", [])
    props = store.get_doc(db, "change_proposals", [])
    approvals = set(store.get_doc(db, "booking_admin_approvals", []))
    sess = {s["id"]: s for s in data["sessions"]}
    rep = validate_timetable(data, tt) if tt else None
    by_rule = Counter(v["rule"] for v in rep["hard_violations"]) if rep else {}

    maint = defaultdict(int)
    for u in data["room_unavailability"]:
        maint[u["room_id"]] += len(u["periods"])
    used = defaultdict(int)
    for a in tt:
        s = sess.get(a["session_id"])
        if s:
            used[a["room_id"]] += s["duration"]
    rooms = []
    for r in data["rooms"]:
        avail = max(45 - maint[r["id"]], 1)
        rooms.append({"room_id": r["id"], "name": r["name"], "type": r["type"],
                      "hours_used": used[r["id"]], "hours_available": avail,
                      "utilisation_pct": round(100 * used[r["id"]] / avail, 1)})
    rooms.sort(key=lambda x: -x["utilisation_pct"])
    teaching = [r for r in rooms if r["type"] not in ("outdoor", "seminar_hall")]
    overall = round(sum(r["utilisation_pct"] for r in teaching) / len(teaching), 1) if teaching else 0

    load = defaultdict(lambda: {"hours": 0, "days": Counter()})
    for a in tt:
        s = sess.get(a["session_id"])
        if s:
            load[s["faculty_id"]]["hours"] += s["duration"]
            load[s["faculty_id"]]["days"][a["day"]] += s["duration"]
    names = {f["id"]: f["name"] for f in data["faculty"]}
    faculty = sorted(({"faculty_id": f, "name": names.get(f, f), "weekly_hours": v["hours"],
                       "busiest_day_hours": max(v["days"].values())} for f, v in load.items()),
                     key=lambda x: -x["weekly_hours"])[:10]

    pending = [{"id": p["id"], "type": "change", "by": p["created_by"]["name"],
                "note": p.get("note"), "moves": p.get("diff", {}).get("moved_count")}
               for p in props if p["status"] == "pending"
               and (user.role == "admin" or p["created_by"]["id"] == user.id)]
    if user.role == "admin":
        pending += [{"id": d["request_id"], "type": "booking_moves_class",
                     "displaced": d["displaced"]} for d in decisions
                    if d.get("needs_admin_approval") and d["request_id"] not in approvals]
    fest = Counter(d["status"] for d in decisions)
    exam_rep = validate_exams(data, exams) if exams else None
    return {
        "role": user.role,
        "summary": {"sessions_total": len(sess), "sessions_scheduled": len(tt),
                    "hard_violations": rep["hard_count"] if rep else None,
                    "soft_penalty": rep["soft_penalty"] if rep else None,
                    "exams_total": len(data["exams"]), "exams_scheduled": len(exams),
                    "exam_violations": exam_rep["hard_count"] if exam_rep else None,
                    "pending_approvals": len(pending),
                    "avg_room_utilisation_pct": overall},
        "conflicts": {"by_rule": dict(by_rule),
                      "items": rep["hard_violations"][:30] if rep else []},
        "soft_penalty_breakdown": rep["soft"] if rep else {},
        "room_utilisation": rooms,
        "busiest_faculty": faculty,
        "pending_approvals": pending,
        "fest_week": {"decisions": dict(fest), "total": len(decisions)},
    }
