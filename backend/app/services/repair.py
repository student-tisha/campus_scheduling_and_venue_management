"""Minimal-move timetable repair (built-in fallback). Pure code, no LLM.

Dipan's solver can plug in by creating backend/solver/repair.py with:
    def repair(data: dict, current: list[dict]) -> dict
returning {"assignments": [...], "infeasible": bool, "conflicts": [str]}.
"""
from collections import Counter

from app.services.booking_engine import DAYS, State
from app.services.validator import validate_timetable

MULTI = {"faculty_clash", "room_clash", "group_clash", "faculty_daily_limit", "basket_slot"}


def _valid_assignment(a):
    return isinstance(a.get("start_period"), int) and a.get("day") in DAYS and a.get("room_id")


def _to_move(data, sessions, cur, report):
    move = set()
    for v in report["hard_violations"]:
        ids = [x for x in v["sessions"] if x in sessions]
        if not ids:
            continue
        if v["rule"] == "basket_slot":
            move.update(ids)
        elif v["rule"] in MULTI:
            cand = [x for x in ids if not sessions[x].get("fixed_slot")] or ids
            if not any(x in move for x in cand):
                move.add(sorted(cand)[-1])
        else:
            move.update(ids)
    for sid in sessions:
        if sid not in cur:
            move.add(sid)
    for sid in list(move):
        slot = sessions[sid].get("basket_slot")
        if slot:
            move.update(x for x, s in sessions.items() if s.get("basket_slot") == slot)
    return move


def _diagnose(st, sid, only=None):
    counts = Counter()
    for d in DAYS:
        for start in range(1, 10):
            if only and (d, start) != tuple(only):
                continue
            for rid in st.rooms:
                counts[st.session_reason(sid, d, start, rid) or "free"] += 1
    total = sum(counts.values())
    top = ", ".join(f"{n} blocked by {r}" for r, n in counts.most_common(4) if r != "free")
    return f"{sid}: none of {total} (day, period, room) options works: {top}"


def _chain(st, sid, only):
    s = st.sess[sid]
    cands = []
    for d in DAYS:
        for start in range(1, 10):
            if only and (d, start) != tuple(only):
                continue
            for rid in st.rooms:
                if st.static_reason(sid, d, start, rid) is None:
                    cands.append((d, start, rid))
    for d, start, rid in cands:
        blockers, booked, limit = st.dynamic_blockers(sid, d, start, rid)
        if booked or limit or len(blockers) != 1:
            continue
        y = next(iter(blockers))
        sy = st.sess[y]
        if sy.get("fixed_slot") or sy.get("basket_slot") or y not in st.pos:
            continue
        yorig = st.pos[y]
        st.remove(y)
        st.add(sid, d, start, rid)
        new = st.find_new_slot(y, yorig)
        if new:
            st.add(y, *new)
            return True
        st.remove(sid)
        st.add(y, *yorig)
    return False


def _place_basket(st, members, origs):
    first = origs.get(members[0], ("MON", 1, None))
    for d in [first[0]] + [x for x in DAYS if x != first[0]]:
        for start in sorted(range(1, 10), key=lambda x: abs(x - first[1])):
            placed = []
            ok = True
            for m in members:
                room = None
                for rid in st.rooms:
                    if st.session_ok(m, d, start, rid):
                        room = rid
                        break
                if room is None:
                    ok = False
                    break
                st.add(m, d, start, room)
                placed.append(m)
            if ok:
                return True
            for m in placed:
                st.remove(m)
    return False


def repair(data: dict, current: list[dict]) -> dict:
    sessions = {s["id"]: s for s in data["sessions"]}
    cur = {a["session_id"]: dict(a) for a in current if a.get("session_id") in sessions}
    conflicts: list[str] = []
    for _ in range(4):
        report = validate_timetable(data, list(cur.values()))
        move = _to_move(data, sessions, cur, report)
        if not move:
            break
        origs = {sid: (cur[sid]["day"], cur[sid]["start_period"], cur[sid]["room_id"])
                 for sid in move if sid in cur and _valid_assignment(cur[sid])}
        keep = [a for sid, a in cur.items() if sid not in move and _valid_assignment(a)]
        st = State(data, keep)

        def difficulty(sid):
            s = sessions[sid]
            fits = sum(1 for r in st.rooms.values()
                       if r["type"] in s["room_types"] and r["capacity"] >= s["size"])
            return (0 if s.get("fixed_slot") else 1, fits)

        done_baskets = set()
        conflicts = []
        for sid in sorted(move, key=difficulty):
            if sid in st.pos:
                continue
            s = sessions[sid]
            slot = s.get("basket_slot")
            if slot:
                if slot in done_baskets:
                    continue
                members = sorted(x for x, t in sessions.items() if t.get("basket_slot") == slot)
                if _place_basket(st, members, origs):
                    done_baskets.add(slot)
                else:
                    conflicts.append(f"Elective basket {slot}: no common day and period works "
                                     f"for all its sessions")
                continue
            fixed = s.get("fixed_slot")
            only = (fixed["day"], fixed["start_period"]) if fixed else None
            new = st.find_new_slot(sid, origs.get(sid, ("MON", 1, None)), only)
            if new:
                st.add(sid, *new)
            elif not _chain(st, sid, only):
                conflicts.append(_diagnose(st, sid, only))
        cur = {sid: {"session_id": sid, "day": d, "start_period": p, "room_id": r}
               for sid, (d, p, r) in st.pos.items()}
        if conflicts:
            break
    final = validate_timetable(data, list(cur.values()))
    ok = final["valid"] and not conflicts
    return {"assignments": list(cur.values()), "infeasible": not ok,
            "conflicts": conflicts or ([] if ok else
                                       [v["message"] for v in final["hard_violations"][:5]])}
