"""Booking decision engine. Pure code: no LLM is ever used here."""
from collections import defaultdict
from datetime import datetime

DAYS = ["MON", "TUE", "WED", "THU", "FRI"]


def crosses_lunch(start: int, dur: int) -> bool:
    return start <= 5 and start + dur - 1 >= 6


def effective_category(order, caps, role, requested):
    cap = caps.get(role)
    if requested not in order:
        return cap or order[-1]
    if not cap or cap not in order:
        return requested
    return order[max(order.index(requested), order.index(cap))]


class State:
    def __init__(self, data, placed):
        self.rooms = {r["id"]: r for r in data["rooms"]}
        self.fac = {f["id"]: f for f in data["faculty"]}
        self.sess = {s["id"]: s for s in data["sessions"]}
        self.room_unavail = set()
        for u in data.get("room_unavailability", []):
            for p in u["periods"]:
                self.room_unavail.add((u["room_id"], u["day"], p))
        self.pos, self.room_occ, self.overrides = {}, {}, {}
        self.grp_occ = defaultdict(set)
        self.fac_occ = defaultdict(set)
        self.fac_hours = defaultdict(int)
        self.grp_book = defaultdict(set)
        self.titles, self.cats = {}, {}
        for a in placed:
            if a.get("session_id") in self.sess:
                self.add(a["session_id"], a["day"], a["start_period"], a["room_id"])

    def add(self, sid, day, start, room):
        self.pos[sid] = (day, start, room)
        s = self.sess[sid]
        for p in range(start, start + s["duration"]):
            self.room_occ[(room, day, p)] = ("session", sid)
            self.fac_occ[(s["faculty_id"], day, p)].add(sid)
            for g in s["groups"]:
                self.grp_occ[(g, day, p)].add(sid)
        self.fac_hours[(s["faculty_id"], day)] += s["duration"]

    def remove(self, sid):
        day, start, room = self.pos.pop(sid)
        s = self.sess[sid]
        for p in range(start, start + s["duration"]):
            if self.room_occ.get((room, day, p)) == ("session", sid):
                del self.room_occ[(room, day, p)]
            self.fac_occ[(s["faculty_id"], day, p)].discard(sid)
            for g in s["groups"]:
                self.grp_occ[(g, day, p)].discard(sid)
        self.fac_hours[(s["faculty_id"], day)] -= s["duration"]

    def add_booking(self, brid, day, periods, room, groups):
        for p in periods:
            self.room_occ[(room, day, p)] = ("booking", brid)
            for g in groups:
                self.grp_book[(g, day, p)].add(brid)

    def remove_booking(self, brid, day, periods, room, groups):
        for p in periods:
            if self.room_occ.get((room, day, p)) == ("booking", brid):
                del self.room_occ[(room, day, p)]
            for g in groups:
                self.grp_book[(g, day, p)].discard(brid)

    def static_reason(self, sid, day, start, room_id):
        s = self.sess[sid]
        dur = s["duration"]
        if start < 1 or start + dur - 1 > 9:
            return "time outside teaching periods"
        if crosses_lunch(start, dur):
            return "runs across lunch"
        if s["kind"] == "lab" and start not in (2, 6):
            return "lab start period"
        room = self.rooms[room_id]
        if room["type"] not in s["room_types"]:
            return "wrong room type"
        if room["capacity"] < s["size"]:
            return "room too small"
        if s.get("needs_accessible") and not room.get("accessible"):
            return "needs accessible room"
        allowed = room.get("allowed_uses")
        if allowed and s["kind"] not in allowed:
            return "room not allowed for this kind"
        periods = range(start, start + dur)
        for p in periods:
            if (room_id, day, p) in self.room_unavail:
                return "room under maintenance"
        fac = self.fac.get(s["faculty_id"], {})
        for u in fac.get("unavailable", []):
            if u["day"] == day and set(u["periods"]) & set(periods):
                return "faculty unavailable"
        return None

    def dynamic_blockers(self, sid, day, start, room_id):
        s = self.sess[sid]
        dur, fid = s["duration"], s["faculty_id"]
        basket = s.get("basket_slot")
        sids, booked = set(), False
        for p in range(start, start + dur):
            occ = self.room_occ.get((room_id, day, p))
            if occ:
                if occ[0] == "booking":
                    booked = True
                else:
                    sids.add(occ[1])
            sids |= set(self.fac_occ.get((fid, day, p), ()))
            for g in s["groups"]:
                for other in self.grp_occ.get((g, day, p), ()):
                    if basket and self.sess[other].get("basket_slot") == basket:
                        continue
                    sids.add(other)
                if self.grp_book.get((g, day, p)):
                    booked = True
        sids.discard(sid)
        fac = self.fac.get(fid, {})
        limit = self.fac_hours[(fid, day)] + dur > fac.get("max_hours_per_day", 4)
        return sids, booked, limit

    def session_reason(self, sid, day, start, room_id):
        r = self.static_reason(sid, day, start, room_id)
        if r:
            return r
        sids, booked, limit = self.dynamic_blockers(sid, day, start, room_id)
        if booked:
            return "booked for an event"
        if sids:
            return "clash with another session"
        if limit:
            return "faculty daily limit"
        return None

    def session_ok(self, sid, day, start, room_id):
        return self.session_reason(sid, day, start, room_id) is None

    def find_new_slot(self, sid, orig, only_slot=None):
        od, ostart, oroom = orig
        others = sorted((r for r in self.rooms.values() if r["id"] != oroom),
                        key=lambda r: r["capacity"])
        rooms = ([oroom] if oroom else []) + [r["id"] for r in others]
        for d in [od] + [x for x in DAYS if x != od]:
            for start in sorted(range(1, 10), key=lambda x: abs(x - ostart)):
                if only_slot and (d, start) != tuple(only_slot):
                    continue
                for rid in rooms:
                    if self.session_ok(sid, d, start, rid):
                        return (d, start, rid)
        return None


def static_candidates(st, req):
    out = []
    for r in st.rooms.values():
        types = req.get("room_types") or []
        if types and r["type"] not in types:
            continue
        if r["capacity"] < req["attendance"]:
            continue
        ok = True
        for n in req.get("needs") or []:
            if n == "accessible":
                ok = ok and bool(r.get("accessible"))
            else:
                ok = ok and n in (r.get("features") or [])
        if not ok:
            continue
        allowed = r.get("allowed_uses")
        if allowed and "event" not in allowed:
            continue
        out.append(r)
    wish = req.get("requested_room")
    out.sort(key=lambda r: (r["id"] != wish, r["capacity"]))
    return out


def check_slot(st, req, day, periods, room_id, allow_displace):
    blockers, disp = [], set()
    groups = req.get("mandatory_for_groups") or []

    def handle_session(sid, where):
        s = st.sess[sid]
        if allow_displace and not s.get("fixed_slot") and not s.get("basket_slot"):
            disp.add(sid)
        else:
            blockers.append(f"{where} has class {sid} on {day} P{periods[0]}-P{periods[-1]}")

    for p in periods:
        if (room_id, day, p) in st.room_unavail:
            blockers.append(f"{room_id} is under maintenance on {day}")
        occ = st.room_occ.get((room_id, day, p))
        if occ:
            if occ[0] == "booking":
                b = occ[1]
                blockers.append(
                    f"{room_id} is booked for '{st.titles.get(b, b)}' ({b}, {st.cats.get(b, '')}) "
                    f"which has equal or higher priority"
                )
            else:
                handle_session(occ[1], room_id)
        for g in groups:
            for sid in list(st.grp_occ.get((g, day, p), [])):
                handle_session(sid, f"group {g}")
            for b in st.grp_book.get((g, day, p), []):
                blockers.append(f"group {g} is already committed to {b}")
    return (not blockers), disp, sorted(set(blockers))


def try_displace(st, req, day, periods, room_id, sids):
    groups = req.get("mandatory_for_groups") or []
    original = {sid: st.pos[sid] for sid in sids}
    for sid in sids:
        st.remove(sid)
    st.add_booking(req["id"], day, periods, room_id, groups)
    moves = {}
    for sid in sids:
        new = st.find_new_slot(sid, original[sid])
        if not new:
            for m in moves:
                st.remove(m)
            st.remove_booking(req["id"], day, periods, room_id, groups)
            for sid2, o in original.items():
                st.add(sid2, *o)
            return None
        st.add(sid, *new)
        moves[sid] = new
    return moves


def decide_one(st, req, eff, order, caps):
    rid = req["id"]
    d = req["duration_periods"]
    groups = req.get("mandatory_for_groups") or []
    note = ""
    if eff != req.get("requested_category"):
        note = f" Category capped to '{eff}' for role '{req['role']}'."

    base = {"request_id": rid, "effective_category": eff, "needs_admin_approval": False,
            "displaced": []}

    def reject(reason):
        return {**base, "status": "rejected", "reason": reason + note}

    cands = static_candidates(st, req)
    if not cands:
        biggest = max(
            (r["capacity"] for r in st.rooms.values()
             if not req.get("room_types") or r["type"] in req["room_types"]),
            default=0,
        )
        if req["attendance"] > biggest:
            return reject(f"No venue of the requested type seats {req['attendance']} "
                          f"(largest seats {biggest})")
        return reject(f"No venue matches the requested type, features {req.get('needs')} "
                      f"and capacity {req['attendance']}")

    slots = []
    for w in req.get("windows") or []:
        for start in range(w["from_period"], w["to_period"] - d + 2):
            if not crosses_lunch(start, d) and start + d - 1 <= 13:
                slots.append((w["day"], start))
    if not slots:
        return reject("The requested window is too short for the duration or crosses lunch")

    def approve(room, day, start, extra=""):
        end = start + d - 1
        wish = req.get("requested_room")
        wish_note = ""
        if wish and wish != room["id"]:
            wish_note = f" Requested room {wish} was not available or not suitable."
        st.titles[rid], st.cats[rid] = req["title"], eff
        return {**base, "status": "approved", "day": day, "start_period": start,
                "end_period": end, "room_id": room["id"],
                "reason": f"Approved as {eff.replace('_', ' ')}: {room['name']} on {day} "
                          f"P{start}-P{end}.{wish_note}{extra}{note}"}

    blockers = []
    for room in cands:
        for day, start in slots:
            periods = list(range(start, start + d))
            ok, _, bl = check_slot(st, req, day, periods, room["id"], False)
            if ok:
                st.add_booking(rid, day, periods, room["id"], groups)
                return approve(room, day, start)
            blockers.extend(bl)

    if eff == "institute_event":
        for room in cands:
            for day, start in slots:
                periods = list(range(start, start + d))
                ok, disp, bl = check_slot(st, req, day, periods, room["id"], True)
                if not ok or not disp:
                    continue
                moves = try_displace(st, req, day, periods, room["id"], sorted(disp))
                if moves:
                    for sid, (nd, ns, nr) in moves.items():
                        st.overrides[sid] = {"session_id": sid, "day": nd,
                                             "start_period": ns, "room_id": nr,
                                             "displaced_by": rid}
                    res = approve(room, day, start,
                                  f" Moved class(es) {', '.join(moves)} for this week only.")
                    res["needs_admin_approval"] = True
                    res["displaced"] = sorted(moves)
                    return res

    w0 = req["windows"][0] if req.get("windows") else {"day": "MON", "from_period": 1}
    best = None
    for day in DAYS:
        for start in range(1, 14 - d + 1):
            if crosses_lunch(start, d):
                continue
            dist = abs(DAYS.index(day) - DAYS.index(w0["day"])) * 20 + abs(start - w0["from_period"])
            for rank, room in enumerate(cands):
                periods = list(range(start, start + d))
                ok, _, _ = check_slot(st, req, day, periods, room["id"], False)
                if ok:
                    key = (dist, rank)
                    if best is None or key < best[0]:
                        best = (key, day, start, room)
                    break
    why = "; ".join(sorted(set(blockers))[:3]) or "no free slot in the requested window"
    if best:
        _, day, start, room = best
        st.titles[rid], st.cats[rid] = req["title"], eff
        st.add_booking(rid, day, list(range(start, start + d)), room["id"], groups)
        return {**base, "status": "alternative_offered", "day": day, "start_period": start,
                "end_period": start + d - 1, "room_id": room["id"],
                "reason": f"Requested slot not possible ({why}). Offered {room['name']} on "
                          f"{day} P{start}-P{start + d - 1} instead.{note}"}
    return reject(f"No suitable venue free in the requested window ({why}) and no alternative "
                  f"slot found this week")


def decide_all(data, placed, requests, cancellations):
    order = data["priority_order"]
    caps = data["role_category_cap"]
    st = State(data, placed)
    cancelled = {c["request_id"]: c for c in cancellations}

    def sub(r):
        try:
            return datetime.fromisoformat(r["submitted_at"])
        except Exception:
            return datetime.max.replace(tzinfo=None)

    items = []
    for r in requests:
        eff = effective_category(order, caps, r["role"], r["requested_category"])
        items.append((order.index(eff) if eff in order else len(order), sub(r), r["id"], r, eff))
    items.sort(key=lambda x: (x[0], x[1].replace(tzinfo=None), x[2]))

    decisions = {}
    for _, _, rid, r, eff in items:
        if rid in cancelled:
            c = cancelled[rid]
            decisions[rid] = {"request_id": rid, "status": "rejected",
                              "effective_category": eff, "needs_admin_approval": False,
                              "displaced": [],
                              "reason": f"Cancelled by {c.get('by', 'requester')}: {c.get('note', '')}".strip()}
        else:
            decisions[rid] = decide_one(st, r, eff, order, caps)
    ordered = [decisions[r["id"]] for r in requests]
    return {"decisions": ordered, "overrides": list(st.overrides.values())}


def clean_for_export(decisions, overrides):
    out = []
    for d in decisions:
        if d["status"] == "rejected":
            out.append({"request_id": d["request_id"], "status": "rejected", "reason": d["reason"]})
        else:
            out.append({k: d[k] for k in ("request_id", "status", "day", "start_period",
                                          "end_period", "room_id", "reason")})
    return {"bookings": out, "session_overrides": overrides}
