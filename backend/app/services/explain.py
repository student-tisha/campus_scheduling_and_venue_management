"""Explanations. Facts come from code; the LLM may only reword them."""
import re
from collections import Counter

from sqlalchemy.orm import Session

from app.services import dataset_loader as loader
from app.services import store
from app.services.assistant import PERIOD_HOUR, slot_text
from app.services.booking_engine import DAYS, State
from app.services.llm import call_llm
from app.services.validator import validate_timetable

REWORD = """Rewrite these facts as 2 to 4 short, plain sentences for a college staff member.
Use ONLY the facts given. Do not add numbers, reasons, names or advice that are not in the facts.
Facts:
"""


def friendly(facts: list[str]) -> tuple[str, str]:
    plain = " ".join(facts)
    out = call_llm("You reword facts. You never add information.", REWORD + "\n".join(facts))
    if not out:
        return plain, "rules"
    nums = set(re.findall(r"\d+", plain))
    if set(re.findall(r"\d+", out)) - nums:
        return plain, "rules"
    return out.strip(), "llm"


def explain_session(db: Session, sid: str) -> dict | None:
    data = loader.get_data_dict(db)
    tt = store.get_doc(db, "timetable", {"sessions": []})["sessions"]
    sess = {s["id"]: s for s in data["sessions"]}
    s = sess.get(sid)
    if not s:
        return None
    title = next((c["title"] for c in data["courses"] if c["id"] == s["course_id"]), s["course_id"])
    cur = next((a for a in tt if a["session_id"] == sid), None)
    if not cur:
        return {"target": sid, "facts": [f"{sid} is not scheduled in the current timetable."]}
    end = cur["start_period"] + s["duration"] - 1
    room = next((r for r in data["rooms"] if r["id"] == cur["room_id"]), {})
    facts = [f"{sid} ({title}, {s['kind']}, {s['duration']}h) runs at "
             f"{slot_text(cur['day'], cur['start_period'], end)} in "
             f"{room.get('name', cur['room_id'])}."]
    if s.get("fixed_slot"):
        facts.append("This session has a fixed slot, so it cannot be moved.")
    if s.get("basket_slot"):
        n = sum(1 for x in data["sessions"] if x.get("basket_slot") == s["basket_slot"])
        facts.append(f"It belongs to elective basket {s['basket_slot']}: all {n} sessions in the "
                     f"basket must share the same day and period.")
    if s["kind"] == "lab":
        facts.append("Three-hour labs can only start at P2 or P6.")
    st = State(data, [a for a in tt if a["session_id"] != sid])
    counts, feasible = Counter(), []
    for d in DAYS:
        for start in range(1, 10):
            for rid in st.rooms:
                r = st.session_reason(sid, d, start, rid)
                if r:
                    counts[r] += 1
                else:
                    feasible.append((d, start, rid))
    total = len(DAYS) * 9 * len(st.rooms)
    top = ", ".join(f"{n} by {r}" for r, n in counts.most_common(3))
    facts.append(f"Hard rules leave {len(feasible)} valid (day, period, room) options out of "
                 f"{total}. The rest are blocked mainly: {top}.")
    base = validate_timetable(data, tt)["soft_penalty"]
    here = (cur["day"], cur["start_period"], cur["room_id"])
    rest = [a for a in tt if a["session_id"] != sid]
    best = None
    for d, start, rid in sorted(feasible, key=lambda x: (x[0] != cur["day"],
                                abs(x[1] - cur["start_period"])))[:25]:
        if (d, start, rid) == here:
            continue
        pen = validate_timetable(data, rest + [{"session_id": sid, "day": d, "start_period": start,
                                                "room_id": rid}])["soft_penalty"]
        if best is None or pen < best[0]:
            best = (pen, d, start, rid)
    if best is None:
        facts.append("There is no other valid option for this session, so this placement is forced.")
    elif best[0] >= base:
        facts.append(f"Among {min(25, len(feasible))} nearby valid alternatives, none lowers the soft "
                     f"penalty (now {base}, best alternative {best[0]}), so this slot is as good as "
                     f"any checked.")
    else:
        facts.append(f"A slightly better option may exist: {slot_text(best[1], best[2])} in "
                     f"{best[3]} would lower the soft penalty from {base} to {best[0]}.")
    if end == 9:
        facts.append("It ends in P9 (17:00), which carries a small soft penalty.")
    return {"target": sid, "facts": facts}


def explain_booking(db: Session, rid: str, user) -> dict | None:
    from app.routers.bookings import visible  # local import avoids a cycle
    data = loader.get_data_dict(db)
    extras = store.get_doc(db, "extra_requests", [])
    req = next((r for r in list(data["booking_requests"]) + list(extras) if r["id"] == rid), None)
    if req is None:
        return None
    if not visible(user, req):
        return {"target": rid, "facts": ["You can only ask about your own booking requests."]}
    dec = next((d for d in store.get_doc(db, "booking_decisions", []) if d["request_id"] == rid), None)
    order = data["priority_order"]
    if not dec:
        return {"target": rid, "facts": [f"{rid} has not been decided yet. An Admin runs the "
                                         f"decision step first."]}
    facts = [f"{rid} ('{req['title']}') from {req['requester']} asked for "
             f"{req['requested_category'].replace('_', ' ')} for {req['attendance']} people."]
    if dec["effective_category"] != req["requested_category"]:
        facts.append(f"The {req['role']} role can claim at most "
                     f"{data['role_category_cap'].get(req['role'], '?').replace('_', ' ')}, so it "
                     f"was treated as {dec['effective_category'].replace('_', ' ')}.")
    facts.append("Priority order is: " + ", then ".join(o.replace("_", " ") for o in order) +
                 ". Equal priority goes to the earlier submission.")
    facts.append(f"Decision: {dec['status'].replace('_', ' ')}. {dec['reason']}")
    if dec.get("displaced"):
        facts.append("Classes moved for this week only: " + ", ".join(dec["displaced"]) +
                     ". An Admin must approve this.")
    if dec["status"] in ("rejected", "alternative_offered"):
        facts.append("You can submit a new request with another time window, another room type, "
                     "fewer requirements, or a smaller attendance.")
    return {"target": rid, "facts": facts}


def explain_change(db: Session, pid: str, user) -> dict | None:
    prop = next((p for p in store.get_doc(db, "change_proposals", []) if p["id"] == pid), None)
    if prop is None or (user.role != "admin" and prop["created_by"]["id"] != user.id):
        return None
    facts = [f"Change request {pid} by {prop['created_by']['name']} is {prop['status'].replace('_', ' ')}."]
    if prop.get("infeasible"):
        facts.append("No valid timetable exists for this change. Conflicts: " +
                     "; ".join(prop.get("conflicts", [])[:5]))
    else:
        facts.append(f"The fix moves {prop['diff']['moved_count']} session(s) and adds "
                     f"{len(prop['diff']['added'])}. Hard violations after the change: "
                     f"{prop['hard_after']}. Soft penalty {prop['soft_before']} -> "
                     f"{prop['soft_after']}.")
    return {"target": pid, "facts": facts}


def ask(db: Session, user, question: str) -> dict:
    q = question.strip()
    data = loader.get_data_dict(db)
    sids = [s["id"] for s in data["sessions"] if re.search(rf"\b{re.escape(s['id'])}\b", q, re.I)]
    if not sids:
        cs = [c["id"] for c in data["courses"] if re.search(rf"\b{re.escape(c['id'])}\b", q, re.I)]
        sids = [s["id"] for s in data["sessions"] if s["course_id"] in cs][:3]
    br = re.findall(r"\bBR-[A-Za-z0-9]+\b", q, re.I)
    ch = re.findall(r"\bCH-\d+\b", q, re.I)
    res = None
    if br:
        res = explain_booking(db, br[0].upper() if br[0][3:].isdigit() else br[0], user)
    elif ch:
        res = explain_change(db, ch[0].upper(), user)
    elif sids:
        parts = [explain_session(db, x) for x in sids[:3]]
        parts = [p for p in parts if p]
        if parts:
            res = {"target": ", ".join(p["target"] for p in parts),
                   "facts": [f for p in parts for f in p["facts"]]}
    if not res:
        return {"found": False, "explanation": "Tell me which session, booking or change you mean, "
                "for example: \"Why is MA101-AB-L1 at 8 AM?\" or \"Why was BR-07 rejected?\"",
                "facts": [], "source": "rules"}
    text, source = friendly(res["facts"])
    return {"found": True, "target": res["target"], "facts": res["facts"],
            "explanation": text, "source": source}
