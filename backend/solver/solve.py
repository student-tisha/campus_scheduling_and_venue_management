from collections import defaultdict
from ortools.sat.python import cp_model

TIME_LIMIT = 90


def solve(data):
    days = data["calendar"]["days"]
    rooms = {r["id"]: r for r in data["rooms"]}
    fac = {f["id"]: f for f in data["faculty"]}
    sessions = data["sessions"]
    sess = {s["id"]: s for s in sessions}
    gids = [g["id"] for g in data["student_groups"]]

    room_off = set()
    for u in data.get("room_unavailability", []):
        for p in u["periods"]:
            room_off.add((u["room_id"], u["day"], p))
    fac_off = set()
    for f in data["faculty"]:
        for u in f.get("unavailable", []):
            for p in u["periods"]:
                fac_off.add((f["id"], u["day"], p))

    def starts(s):
        out = []
        for p in range(1, 10):
            per = list(range(p, p + s["duration"]))
            if per[-1] > 9:
                continue
            if per[0] <= 5 and per[-1] >= 6:
                continue
            if s["kind"] == "lab" and p not in (2, 6):
                continue
            out.append(p)
        return out

    m = cp_model.CpModel()
    x = {}
    tx = defaultdict(list)
    cover_room = defaultdict(list)
    cost = []

    for s in sessions:
        sid = s["id"]
        cand = [r for r in rooms.values()
                if r["type"] in s["room_types"]
                and r["capacity"] >= s["size"]
                and (r.get("accessible") or not s["needs_accessible"])]
        fx = s.get("fixed_slot")
        opts = []
        for d in days:
            if fx and fx["day"] != d:
                continue
            for p in starts(s):
                if fx and fx["start_period"] != p:
                    continue
                per = list(range(p, p + s["duration"]))
                if any((s["faculty_id"], d, q) in fac_off for q in per):
                    continue
                s1 = 0
                for pref in fac[s["faculty_id"]].get("preferences", []):
                    if pref.get("type") == "avoid" and d in pref.get("days", days):
                        s1 += 2 * sum(1 for q in per if q in pref["periods"])
                for r in cand:
                    if any((r["id"], d, q) in room_off for q in per):
                        continue
                    v = m.NewBoolVar("x")
                    x[(sid, d, p, r["id"])] = v
                    opts.append(v)
                    tx[(sid, d, p)].append(v)
                    for q in per:
                        cover_room[(r["id"], d, q)].append(v)
                    c = s1
                    if r["capacity"] and s["size"] / r["capacity"] < 0.4:
                        c += 1
                    if 9 in per:
                        c += 1
                    if c:
                        cost.append(c * v)
        if not opts:
            raise RuntimeError("No options for session " + sid)
        m.AddExactlyOne(opts)

    tv = {}
    for k, lst in tx.items():
        b = m.NewBoolVar("t")
        m.Add(sum(lst) == b)
        tv[k] = b

    for lst in cover_room.values():
        if len(lst) > 1:
            m.AddAtMostOne(lst)

    day_terms = defaultdict(list)
    cover_fac = defaultdict(list)
    hours_fac = defaultdict(list)
    for (sid, d, p), b in tv.items():
        s = sess[sid]
        day_terms[(sid, d)].append(b)
        for q in range(p, p + s["duration"]):
            cover_fac[(s["faculty_id"], d, q)].append(b)
        hours_fac[(s["faculty_id"], d)].append(s["duration"] * b)
    for lst in cover_fac.values():
        if len(lst) > 1:
            m.AddAtMostOne(lst)
    for (f, d), lst in hours_fac.items():
        m.Add(sum(lst) <= fac[f]["max_hours_per_day"])

    baskets = defaultdict(list)
    for s in sessions:
        if s.get("basket_slot"):
            baskets[s["basket_slot"]].append(s)

    cover_grp = defaultdict(list)
    for bslot, lst in baskets.items():
        dur = lst[0]["duration"]
        grps = set()
        for s in lst:
            grps.update(s["groups"])
        for d in days:
            for p in range(1, 10):
                bt = m.NewBoolVar("bt")
                for s in lst:
                    k = (s["id"], d, p)
                    if k in tv:
                        m.Add(tv[k] == bt)
                    else:
                        m.Add(bt == 0)
                for g in grps:
                    for q in range(p, p + dur):
                        if q <= 9:
                            cover_grp[(g, d, q)].append(bt)

    for (sid, d, p), b in tv.items():
        s = sess[sid]
        if s.get("basket_slot"):
            continue
        for g in s["groups"]:
            for q in range(p, p + s["duration"]):
                cover_grp[(g, d, q)].append(b)

    occ = {}
    for g in gids:
        for d in days:
            for q in range(1, 10):
                o = m.NewBoolVar("o")
                lst = cover_grp.get((g, d, q), [])
                if lst:
                    m.Add(sum(lst) == o)
                else:
                    m.Add(o == 0)
                occ[(g, d, q)] = o

    for g in gids:
        for d in days:
            ex = m.NewIntVar(0, 9, "ex")
            m.Add(ex >= sum(occ[(g, d, q)] for q in range(1, 10)) - 6)
            cost.append(3 * ex)
            bef, aft = {}, {}
            for q in range(2, 9):
                bef[q] = m.NewBoolVar("bf")
                aft[q] = m.NewBoolVar("af")
            for q in range(2, 9):
                m.Add(bef[q] >= occ[(g, d, q - 1)])
                if q > 2:
                    m.Add(bef[q] >= bef[q - 1])
                m.Add(aft[q] >= occ[(g, d, q + 1)])
                if q < 8:
                    m.Add(aft[q] >= aft[q + 1])
                gp = m.NewBoolVar("gp")
                m.Add(gp >= bef[q] + aft[q] - occ[(g, d, q)] - 1)
                cost.append(gp)

    gc = defaultdict(list)
    for s in sessions:
        if s["kind"] == "lecture" and not s.get("basket_slot"):
            for g in s["groups"]:
                gc[(g, s["course_id"])].append(s["id"])
    for (g, c), sids in gc.items():
        for d in days:
            terms = []
            for sid in sids:
                terms += day_terms.get((sid, d), [])
            if len(terms) > 1:
                ex = m.NewIntVar(0, len(sids), "e4")
                m.Add(ex >= sum(terms) - 1)
                cost.append(3 * ex)

    bc = defaultdict(list)
    for s in sessions:
        if s.get("basket_slot"):
            bc[s["course_id"]].append(s["id"])
    for c, sids in bc.items():
        for d in days:
            terms = []
            for sid in sids:
                terms += day_terms.get((sid, d), [])
            if len(terms) > 1:
                ex = m.NewIntVar(0, len(sids), "e4b")
                m.Add(ex >= sum(terms) - 1)
                cost.append(3 * ex)

    try:
        from app.services.repair import repair
        base = repair(data, [])["assignments"]
        keys = {(a["session_id"], a["day"], a["start_period"], a["room_id"]) for a in base}
        for k, v in x.items():
            m.AddHint(v, 1 if k in keys else 0)
    except Exception:
        pass

    m.Minimize(sum(cost))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIME_LIMIT
    solver.parameters.num_workers = 8
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("Solver found no timetable")

    out = []
    for (sid, d, p, r), v in x.items():
        if solver.Value(v):
            out.append({"session_id": sid, "day": d, "start_period": p, "room_id": r})
    return out
