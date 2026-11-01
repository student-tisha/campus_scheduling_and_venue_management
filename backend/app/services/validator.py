from collections import defaultdict

DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
MAX_PERIOD = 9


def validate_timetable(data: dict, assignments: list[dict]) -> dict:
    """Check a list of {session_id, day, start_period, room_id} against all rules."""
    sessions = {s["id"]: s for s in data["sessions"]}
    rooms = {r["id"]: r for r in data["rooms"]}
    faculty = {f["id"]: f for f in data["faculty"]}
    lab_starts = (data.get("calendar") or {}).get("lab_start_periods", [2, 6])
    hard: list[dict] = []

    def v(rule, message, involved=None):
        hard.append({"rule": rule, "message": message, "sessions": involved or []})

    placed: dict[str, dict] = {}
    for a in assignments:
        sid = a.get("session_id")
        if sid not in sessions:
            v("unknown_session", f"Unknown session {sid}", [sid])
        elif sid in placed:
            v("scheduled_once", f"{sid} is scheduled more than once", [sid])
        else:
            placed[sid] = a
    for sid in sessions:
        if sid not in placed:
            v("scheduled_once", f"{sid} is not scheduled", [sid])

    fac_cells = defaultdict(list)
    room_cells = defaultdict(list)
    grp_cells = defaultdict(list)
    fac_hours = defaultdict(int)
    baskets = defaultdict(set)
    basket_sids = defaultdict(list)
    fac_day_sids = defaultdict(list)
    placed_ok = {}

    for sid, a in placed.items():
        s = sessions[sid]
        day, start, room_id = a.get("day"), a.get("start_period"), a.get("room_id")
        dur = s["duration"]

        if day not in DAYS or not isinstance(start, int) or start < 1 or start + dur - 1 > MAX_PERIOD:
            v("time_slot", f"{sid}: invalid slot {day} P{start}", [sid])
            continue
        periods = list(range(start, start + dur))
        placed_ok[sid] = (day, periods)

        if start <= 5 and start + dur - 1 >= 6:
            v("lunch", f"{sid} runs across lunch ({day} P{start}-P{start + dur - 1})", [sid])
        if s["kind"] == "lab" and start not in lab_starts:
            v("lab_start", f"{sid}: lab must start at P{lab_starts}, not P{start}", [sid])

        fixed = s.get("fixed_slot")
        if fixed and (fixed.get("day") != day or fixed.get("start_period") != start):
            v("fixed_slot", f"{sid} must stay at {fixed['day']} P{fixed['start_period']}", [sid])

        room = rooms.get(room_id)
        if room is None:
            v("room_missing", f"{sid}: room '{room_id}' does not exist", [sid])
        else:
            if room["type"] not in s["room_types"]:
                v("room_type", f"{sid} needs {s['room_types']}, {room_id} is {room['type']}", [sid])
            if room["capacity"] < s["size"]:
                v("capacity", f"{sid} has {s['size']} students, {room_id} seats {room['capacity']}", [sid])
            if s.get("needs_accessible") and not room.get("accessible"):
                v("accessible", f"{sid} needs an accessible room, {room_id} is not", [sid])
            allowed = room.get("allowed_uses")
            if allowed and s["kind"] not in allowed:
                v("room_use", f"{room_id} does not allow '{s['kind']}' sessions", [sid])
            for u in data.get("room_unavailability", []):
                if u["room_id"] == room_id and u["day"] == day and set(u["periods"]) & set(periods):
                    v("room_unavailable", f"{room_id} unavailable on {day}: {u.get('reason', '')}", [sid])
            for p in periods:
                room_cells[(room_id, day, p)].append(sid)

        fac = faculty.get(s["faculty_id"])
        if fac:
            for u in fac.get("unavailable", []):
                if u["day"] == day and set(u["periods"]) & set(periods):
                    v("faculty_unavailable", f"{fac['name']} unavailable {day}: {u.get('reason', '')}", [sid])
        for p in periods:
            fac_cells[(s["faculty_id"], day, p)].append(sid)
            for g in s["groups"]:
                grp_cells[(g, day, p)].append(sid)
        fac_hours[(s["faculty_id"], day)] += dur
        fac_day_sids[(s["faculty_id"], day)].append(sid)

        if s.get("basket_slot"):
            baskets[s["basket_slot"]].add((day, start))
            basket_sids[s["basket_slot"]].append(sid)

    for (fid, day, p), sids in fac_cells.items():
        if len(set(sids)) > 1:
            v("faculty_clash", f"{fid} is in {len(set(sids))} places on {day} P{p}", sorted(set(sids)))
    for (rid, day, p), sids in room_cells.items():
        if len(set(sids)) > 1:
            v("room_clash", f"Room {rid} double-booked on {day} P{p}", sorted(set(sids)))
    for (g, day, p), sids in grp_cells.items():
        uniq = set(sids)
        if len(uniq) > 1:
            slots = {sessions[x].get("basket_slot") for x in uniq}
            if len(slots) == 1 and None not in slots:
                continue
            v("group_clash", f"Group {g} has {len(uniq)} sessions on {day} P{p}", sorted(uniq))
    for (fid, day), hours in fac_hours.items():
        limit = faculty[fid]["max_hours_per_day"] if fid in faculty else 4
        if hours > limit:
            v("faculty_daily_limit", f"{fid} teaches {hours}h on {day} (limit {limit})",
              sorted(fac_day_sids[(fid, day)]))
    for slot, times in baskets.items():
        if len(times) > 1:
            v("basket_slot", f"Basket {slot} sessions are not all at the same day and period",
              sorted(basket_sids[slot]))

    soft = _soft(sessions, faculty, rooms, placed_ok, placed, grp_cells)
    return {
        "valid": len(hard) == 0,
        "hard_count": len(hard),
        "hard_violations": hard,
        "soft": soft,
        "soft_penalty": soft["total"],
    }


def _soft(sessions, faculty, rooms, placed_ok, placed, grp_cells):
    s1 = 0
    for sid, (day, periods) in placed_ok.items():
        fac = faculty.get(sessions[sid]["faculty_id"])
        for pref in (fac or {}).get("preferences", []):
            if pref.get("type") != "avoid":
                continue
            days, pers = pref.get("days") or [], pref.get("periods") or []
            for p in periods:
                if (not days or day in days) and (not pers or p in pers):
                    s1 += 2

    by_group_day = defaultdict(set)
    for (g, day, p) in grp_cells:
        by_group_day[(g, day)].add(p)
    s2 = sum((max(ps) - min(ps) + 1) - len(ps) for ps in by_group_day.values())
    s3 = sum(1 for ps in by_group_day.values() if len(ps) > 6)

    lectures = defaultdict(int)
    for sid, (day, _) in placed_ok.items():
        s = sessions[sid]
        if s["kind"] == "lecture":
            for g in s["groups"]:
                lectures[(g, day, s["course_id"])] += 1
    s4 = sum(1 for n in lectures.values() if n > 1)

    s5 = 0
    for sid, a in placed.items():
        room = rooms.get(a.get("room_id"))
        if room and sessions[sid]["size"] < 0.4 * room["capacity"]:
            s5 += 1
    s6 = sum(1 for _, (_, periods) in placed_ok.items() if 9 in periods)

    return {
        "S1_faculty_avoid": s1,
        "S2_group_gaps": s2,
        "S3_over_6_hours": s3,
        "S4_same_course_same_day": s4,
        "S5_low_room_use": s5,
        "S6_period_9": s6,
        "total": s1 + s2 + s3 + s4 + s5 + s6,
    }
