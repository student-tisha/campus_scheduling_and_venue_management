"""Code-only validity checks. No LLM, no solver. Same rules as the official validator."""
from collections import defaultdict


def check_assignment(ctx, assign):
    """assign: sid -> (day,start,room). Returns list of {rule, sessions, detail}."""
    V = []
    def v(rule, sids, msg): V.append({"rule": rule, "sessions": list(sids), "detail": msg})
    room_occ, fac_occ, grp_occ = defaultdict(list), defaultdict(list), defaultdict(lambda: defaultdict(list))
    fac_day, basket_time = defaultdict(list), defaultdict(set)
    for sid in ctx.sessions:
        if sid not in assign: v("H1", [sid], f"{sid} is not scheduled")
    for sid, (day, start, rid) in assign.items():
        s = ctx.sessions.get(sid)
        if s is None: v("H1", [sid], f"unknown session {sid}"); continue
        if day not in ctx.days or rid not in ctx.rooms or not isinstance(start, int) \
                or start < 1 or start + s["duration"] - 1 > ctx.last:
            v("H1", [sid], f"{sid}: invalid day/period/room {day} P{start} {rid}"); continue
        for tag in ctx.blockers(s, day, start, rid):
            v(TAG_RULE[tag], [sid], f"{sid}: {TAG_TEXT[tag]} ({day} P{start}, {rid})")
        f = s["faculty_id"]
        for p in range(start, start + s["duration"]):
            room_occ[(rid, day, p)].append(sid)
            fac_occ[(f, day, p)].append(sid)
            for g in s["groups"]:
                grp_occ[(g, day, p)][s.get("basket_slot") or sid].append(sid)
        fac_day[(f, day)].append(sid)
        if s.get("basket_slot"): basket_time[s["basket_slot"]].add((day, start))
    for (rid, day, p), l in room_occ.items():
        if len(l) > 1: v("H4", l, f"room {rid} double-booked {day} P{p}: {', '.join(l)}")
    for (f, day, p), l in fac_occ.items():
        if len(l) > 1: v("H2", l, f"faculty {f} double-booked {day} P{p}: {', '.join(l)}")
    for (g, day, p), keys in grp_occ.items():
        if len(keys) > 1:
            v("H3", [x for k in keys.values() for x in k], f"group {g} double-booked {day} P{p}: {', '.join(sorted(keys))}")
    for b, times in basket_time.items():
        if len(times) > 1: v("H11", ctx.baskets[b], f"basket {b} sessions not at the same time: {sorted(times)}")
    for (f, day), sids in fac_day.items():
        h = sum(ctx.sessions[x]["duration"] for x in sids)
        mx = ctx.fac[f].get("max_hours_per_day", 4)
        if h > mx: v("H12", sids, f"faculty {f} teaches {h}h on {day} (max {mx})")
    return V


TAG_RULE = {"lunch": "H9", "lab_start": "H9", "fixed_slot": "H14", "room_type": "H6", "capacity": "H5",
            "accessible": "H10", "faculty_unavailable": "H7", "room_unavailable": "H8"}
TAG_TEXT = {"lunch": "runs across lunch", "lab_start": "labs may only start at P2 or P6",
            "fixed_slot": "session has a fixed slot", "room_type": "wrong room type",
            "capacity": "room too small", "accessible": "needs an accessible room",
            "faculty_unavailable": "faculty unavailable", "room_unavailable": "room unavailable (closed/maintenance)"}


def check_moves(ctx, assign, moves):
    """moves: {sid: (day,start,room)}. Returns (ok, NEW violations caused by the move)."""
    before = {(x["rule"], x["detail"]) for x in check_assignment(ctx, assign)}
    cand = dict(assign); cand.update({k: tuple(v) for k, v in moves.items()})
    new = [x for x in check_assignment(ctx, cand) if (x["rule"], x["detail"]) not in before]
    return (not new), new


def check_move(ctx, assign, sid, new_slot):
    """Is moving ONE session to new_slot=(day,start,room) valid? Elective-basket sessions must move together
    (use check_moves)."""
    return check_moves(ctx, assign, {sid: new_slot})


def soft_score(ctx, assign):
    """Same definition as validator S1-S6."""
    pen = defaultdict(int)
    grp_day, grp_hours, grp_course, bc, seen = defaultdict(set), defaultdict(int), defaultdict(int), defaultdict(int), set()
    for sid, (day, start, rid) in assign.items():
        s, r = ctx.sessions.get(sid), ctx.rooms.get(rid)
        if not s or not r: continue
        per = list(range(start, start + s["duration"]))
        for pf in ctx.fac.get(s["faculty_id"], {}).get("preferences", []):
            if pf.get("type") == "avoid" and day in pf.get("days", ctx.days):
                pen["S1"] += 2 * sum(1 for p in per if p in pf["periods"])
        if r["capacity"] and s["size"] / r["capacity"] < 0.4: pen["S5"] += 1
        if ctx.last in per: pen["S6"] += 1
        for g in s["groups"]:
            grp_day[(g, day)].update(per)
            if s.get("basket_slot"):
                if (g, s["basket_slot"]) in seen: continue
                seen.add((g, s["basket_slot"]))
            grp_hours[(g, day)] += s["duration"]
            if s["kind"] == "lecture" and not s.get("basket_slot"): grp_course[(g, day, s["course_id"])] += 1
        if s.get("basket_slot"): bc[(s["course_id"], day)] += 1
    for ps in grp_day.values(): pen["S2"] += sum(1 for p in range(min(ps), max(ps) + 1) if p not in ps)
    for h in grp_hours.values():
        if h > 6: pen["S3"] += 3 * (h - 6)
    for c in list(grp_course.values()) + list(bc.values()):
        if c > 1: pen["S4"] += 3 * (c - 1)
    for k in ("S1", "S2", "S3", "S4", "S5", "S6"): pen.setdefault(k, 0)
    return dict(sorted(pen.items())), sum(pen.values())
