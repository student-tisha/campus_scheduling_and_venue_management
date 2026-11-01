"""Midsem exam validation and a built-in fallback scheduler. Pure code."""
from collections import Counter, defaultdict


def exam_calendar(data):
    cal = (data.get("calendar") or {}).get("exam_week") or {}
    days = cal.get("days") or ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    sess = [s["id"] for s in cal.get("sessions", [])] or ["AM", "PM"]
    return days, sess


def eff_cap(room) -> int:
    return room["capacity"] // 2  # exam rule: effective capacity is halved


def validate_exams(data, exams):
    days, sess_ids = exam_calendar(data)
    rooms = {r["id"]: r for r in data["rooms"]}
    spec = {e["id"]: e for e in data["exams"]}
    errors, placed = [], {}
    for a in exams or []:
        eid = a.get("exam_id")
        if eid not in spec:
            errors.append(f"Unknown exam {eid}")
        elif eid in placed:
            errors.append(f"{eid} is scheduled more than once")
        else:
            placed[eid] = a
    for eid in spec:
        if eid not in placed:
            errors.append(f"{eid} is not scheduled")
    room_use, grp_use = defaultdict(list), defaultdict(list)
    for eid, a in placed.items():
        e = spec[eid]
        day, sess, rl = a.get("day"), a.get("session"), a.get("rooms") or []
        if day not in days or sess not in sess_ids:
            errors.append(f"{eid}: invalid day/session {day} {sess}")
            continue
        if e.get("duration_hours", 2) > 2:
            errors.append(f"{eid}: {e['duration_hours']}h is longer than one exam session")
        if not rl or len(set(rl)) != len(rl):
            errors.append(f"{eid}: needs one or more different rooms")
            continue
        total = 0
        for rid in rl:
            r = rooms.get(rid)
            if not r:
                errors.append(f"{eid}: unknown room {rid}")
                continue
            allowed = r.get("allowed_uses")
            if allowed and "exam" not in allowed:
                errors.append(f"{eid}: {rid} does not allow exams")
            total += eff_cap(r)
            room_use[(rid, day, sess)].append(eid)
        if total < e["size"]:
            errors.append(f"{eid}: rooms seat {total} (halved) for {e['size']} students")
        for g in e["groups"]:
            grp_use[(g, day, sess)].append(eid)
    for (rid, d, s), ids in room_use.items():
        if len(ids) > 1:
            errors.append(f"Room {rid} holds {len(ids)} exams on {d} {s}: {', '.join(ids)}")
    for (g, d, s), ids in grp_use.items():
        if len(ids) > 1:
            errors.append(f"Group {g} has {len(ids)} exams on {d} {s}: {', '.join(ids)}")
    return {"valid": not errors, "hard_count": len(errors), "violations": errors[:50]}


def schedule_exams(data):
    days, sess_ids = exam_calendar(data)
    rooms = [r for r in data["rooms"] if "exam" in (r.get("allowed_uses") or ["exam"])]
    unavailable_day = {(u["room_id"], u["day"]) for u in data.get("room_unavailability", [])}
    slots = [(d, s) for d in days for s in sess_ids]
    room_busy, grp_busy, grp_days = set(), set(), defaultdict(Counter)
    out, problems = [], []
    for e in sorted(data["exams"], key=lambda x: -x["size"]):
        best = None
        for idx, (d, s) in enumerate(slots):
            if any((g, d, s) in grp_busy for g in e["groups"]):
                continue
            avail = [r for r in rooms if (r["id"], d, s) not in room_busy
                     and (r["id"], d) not in unavailable_day]
            chosen, remaining = [], e["size"]
            while remaining > 0:
                cands = [r for r in avail if r not in chosen]
                if not cands:
                    break
                fit = [r for r in cands if eff_cap(r) >= remaining]
                pick = min(fit, key=eff_cap) if fit else max(cands, key=eff_cap)
                chosen.append(pick)
                remaining -= eff_cap(pick)
            if remaining > 0:
                continue
            key = (sum(grp_days[g][d] for g in e["groups"]), idx)
            if best is None or key < best[0]:
                best = (key, d, s, chosen)
        if best is None:
            problems.append(f"{e['id']}: no day/session has free rooms and free groups")
            continue
        _, d, s, chosen = best
        for r in chosen:
            room_busy.add((r["id"], d, s))
        for g in e["groups"]:
            grp_busy.add((g, d, s))
            grp_days[g][d] += 1
        out.append({"exam_id": e["id"], "day": d, "session": s, "rooms": [r["id"] for r in chosen]})
    order = {e["id"]: i for i, e in enumerate(data["exams"])}
    out.sort(key=lambda a: order[a["exam_id"]])
    return out, problems
