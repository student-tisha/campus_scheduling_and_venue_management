import copy, json
from collections import defaultdict


def load_data(src):
    if isinstance(src, dict):
        return src
    with open(src, encoding="utf-8") as f:
        return json.load(f)


def apply_disruption(data, dis):
    """Returns a new dataset with the disruption applied (same semantics as the official validator)."""
    d = copy.deepcopy(data)
    fac = {f["id"]: f for f in d["faculty"]}
    for ch in dis.get("changes", []):
        t = ch["type"]
        if t == "faculty_unavailable":
            for day in ch["days"]:
                fac[ch["faculty_id"]].setdefault("unavailable", []).append(
                    {"day": day, "periods": ch["periods"], "reason": ch.get("reason", "")})
        elif t == "room_unavailable":
            for day in ch["days"]:
                d["room_unavailability"].append(
                    {"room_id": ch["room_id"], "day": day, "periods": ch["periods"], "reason": ch.get("reason", "")})
        elif t == "add_faculty":
            d["faculty"].append(ch["faculty"]); fac[ch["faculty"]["id"]] = ch["faculty"]
        elif t == "add_session":
            d["sessions"].append(ch["session"])
        elif t == "remove_session":
            d["sessions"] = [s for s in d["sessions"] if s["id"] != ch["session_id"]]
        else:
            raise ValueError(f"Unknown change type: {t}")
    return d


class Ctx:
    """Indexed, read-only view of a dataset."""

    def __init__(self, data):
        self.data = data
        cal = data["calendar"]
        self.days = cal["days"]
        self.lab_starts = set(cal["lab_start_periods"])
        self.lunch = cal["lunch"]["after_period"]
        self.last = max(p["id"] for p in cal["periods"] if p["teaching"])
        self.rooms = {r["id"]: r for r in data["rooms"]}
        self.fac = {f["id"]: f for f in data["faculty"]}
        self.groups = {g["id"]: g for g in data["student_groups"]}
        self.sessions = {s["id"]: s for s in data["sessions"]}
        self.baskets = defaultdict(list)
        for s in data["sessions"]:
            if s.get("basket_slot"):
                self.baskets[s["basket_slot"]].append(s["id"])
        self.fac_un = defaultdict(set)
        for f in data["faculty"]:
            for u in f.get("unavailable", []):
                for p in u["periods"]:
                    self.fac_un[f["id"]].add((u["day"], p))
        self.room_un = defaultdict(set)
        for u in data.get("room_unavailability", []):
            for p in u["periods"]:
                self.room_un[u["room_id"]].add((u["day"], p))
        self._blk = {}

    # ---- hard-constraint tags for a single (day, start, room) choice -------------
    def blockers(self, s, day, start, rid):
        """Set of per-session hard-constraint tags this placement breaks."""
        tags = set()
        r = self.rooms[rid]
        dur = s["duration"]
        per = range(start, start + dur)
        if per[0] <= self.lunch < per[-1]:
            tags.add("lunch")
        if s["kind"] == "lab" and start not in self.lab_starts:
            tags.add("lab_start")
        fx = s.get("fixed_slot")
        if fx and (fx["day"] != day or fx["start_period"] != start):
            tags.add("fixed_slot")
        if r["type"] not in s["room_types"]:
            tags.add("room_type")
        if r["capacity"] < s["size"]:
            tags.add("capacity")
        if s.get("needs_accessible") and not r["accessible"]:
            tags.add("accessible")
        if any((day, p) in self.fac_un[s["faculty_id"]] for p in per):
            tags.add("faculty_unavailable")
        if any((day, p) in self.room_un[rid] for p in per):
            tags.add("room_unavailable")
        return tags

    def all_blocked(self, sid):
        """List of ((day,start,room), tags) for every grid position of a session (cached)."""
        if sid not in self._blk:
            s = self.sessions[sid]
            out = []
            for d in self.days:
                for t in range(1, self.last - s["duration"] + 2):
                    for rid in self.rooms:
                        out.append(((d, t, rid), frozenset(self.blockers(s, d, t, rid))))
            self._blk[sid] = out
        return self._blk[sid]

    def options(self, sid, disabled=frozenset()):
        return [slot for slot, tags in self.all_blocked(sid) if not (tags - disabled)]
