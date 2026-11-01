"""Weekly timetable model. One binary per (session, day, start, room) option."""
import time
from collections import defaultdict
from .mip import MIP

# soft weights: identical to the official validator
W_S1, W_S2, W_S3, W_S4, W_S5, W_S6 = 2, 1, 3, 3, 1, 1
HARD_TAGS = {"room_clash", "faculty_clash", "group_clash", "basket_same_time", "faculty_daily_limit"}


def solve_timetable(ctx, *, frozen=None, prev=None, move_weight=0, disabled=frozenset(),
                    time_limit=60, soft=True, rel_gap=0.0):
    """
    frozen : {sid: (day,start,room)} sessions that must stay exactly where they are
    prev   : {sid: slot} previous timetable; every session that leaves its slot costs `move_weight`
    disabled: hard-constraint tags to switch off (used only for conflict diagnosis)
    returns dict(status, assign, objective, seconds, empty=[sids with no option])
    """
    t0 = time.time()
    frozen, prev = frozen or {}, prev or {}
    sess = ctx.sessions
    opts = {}
    for sid in sess:
        opts[sid] = [frozen[sid]] if sid in frozen else ctx.options(sid, disabled)

    # basket sessions must share (day,start): keep only times every member can do
    basket_times = {}
    if "basket_same_time" not in disabled:
        for b, members in ctx.baskets.items():
            common = None
            for sid in members:
                ts = {(d, t) for d, t, r in opts[sid]}
                common = ts if common is None else common & ts
            basket_times[b] = common or set()
            for sid in members:
                opts[sid] = [o for o in opts[sid] if (o[0], o[1]) in basket_times[b]]
    empty = [sid for sid, o in opts.items() if not o]
    if empty:
        return {"status": "infeasible", "assign": None, "objective": None, "empty": empty,
                "seconds": time.time() - t0}

    m = MIP()
    X = {}
    room_cov, fac_cov, grp_cov = defaultdict(list), defaultdict(list), defaultdict(list)
    day_x = defaultdict(list)                 # (sid, day) -> vars
    fac_hours = defaultdict(list)             # (fac, day) -> (var, dur)
    in_basket = {sid: s.get("basket_slot") for sid, s in sess.items()}

    for sid, s in sess.items():
        dur, f = s["duration"], s["faculty_id"]
        pref = ctx.fac[f].get("preferences", [])
        for (d, t, r) in opts[sid]:
            per = range(t, t + dur)
            cost = 0.0
            if soft:
                for pf in pref:
                    if pf.get("type") == "avoid" and d in pf.get("days", ctx.days):
                        cost += W_S1 * sum(1 for p in per if p in pf["periods"])
                cap = ctx.rooms[r]["capacity"]
                if cap and s["size"] / cap < 0.4:
                    cost += W_S5
                if ctx.last in per:
                    cost += W_S6
            if sid in prev and move_weight:
                if tuple(prev[sid]) == (d, t, r):
                    cost -= move_weight
            v = m.var(obj=cost, integer=True)
            X[(sid, d, t, r)] = v
            day_x[(sid, d)].append(v)
            for p in per:
                room_cov[(r, d, p)].append(v)
                fac_cov[(f, d, p)].append(v)
                if not in_basket[sid]:
                    for g in s["groups"]:
                        grp_cov[(g, d, p)].append(v)
            fac_hours[(f, d)].append((v, dur))
        if sid in prev and move_weight:
            m.const += move_weight   # constant so objective counts moves

    # exactly once (non-basket) ------------------------------------------------
    for sid in sess:
        if not in_basket[sid]:
            m.add([(X[(sid, d, t, r)], 1) for (d, t, r) in opts[sid]], 1, 1)

    # baskets: y[b,d,t] = chosen time; each member takes exactly one room at that time
    Y = {}
    for b, members in ctx.baskets.items():
        durs = {sess[sid]["duration"] for sid in members}
        assert len(durs) == 1, f"basket {b} mixes durations"
        dur = durs.pop()
        groups = {g for sid in members for g in sess[sid]["groups"]}
        times = sorted(basket_times.get(b) or {(d, t) for d, t, r in opts[members[0]]})
        for (d, t) in times:
            y = m.var(integer=True)
            Y[(b, d, t)] = y
            for sid in members:
                m.add([(X[(sid, d, t, r)], 1) for (dd, tt, r) in opts[sid] if (dd, tt) == (d, t)] + [(y, -1)], 0, 0)
            for p in range(t, t + dur):
                for g in groups:
                    grp_cov[(g, d, p)].append(y)
        m.add([(Y[(b, d, t)], 1) for (d, t) in times], 1, 1)

    # hard clashes ----------------------------------------------------------------
    if "room_clash" not in disabled:
        for k, vs in room_cov.items():
            if len(vs) > 1: m.add([(v, 1) for v in vs], hi=1)
    if "faculty_clash" not in disabled:
        for k, vs in fac_cov.items():
            if len(vs) > 1: m.add([(v, 1) for v in vs], hi=1)
    if "group_clash" not in disabled:
        for k, vs in grp_cov.items():
            if len(vs) > 1: m.add([(v, 1) for v in vs], hi=1)
    if "faculty_daily_limit" not in disabled:
        for (f, d), items in fac_hours.items():
            mx = ctx.fac[f].get("max_hours_per_day", 4)
            if sum(dur for _, dur in items) > mx:
                m.add([(v, dur) for v, dur in items], hi=mx)

    # soft ------------------------------------------------------------------------
    if soft:
        _add_soft(ctx, m, X, Y, opts, day_x, grp_cov)

    status, x, obj = m.solve(time_limit, rel_gap)
    if x is None:
        return {"status": status, "assign": None, "objective": None, "empty": [],
                "seconds": time.time() - t0}
    assign = {}
    for (sid, d, t, r), v in X.items():
        if x[v] > 0.5:
            assign[sid] = (d, t, r)
    return {"status": status, "assign": assign, "objective": obj, "empty": [],
            "seconds": time.time() - t0}


def _add_soft(ctx, m, X, Y, opts, day_x, grp_cov):
    sess = ctx.sessions
    last = ctx.last
    # S2 gaps: gap[g,d,p] >= before + after - occupied - 1 (free period between two classes)
    for g in ctx.groups:
        for d in ctx.days:
            occ = {p: grp_cov.get((g, d, p), []) for p in range(1, last + 1)}
            if not any(occ.values()):
                continue
            a = {p: m.var() for p in occ}
            b = {p: m.var() for p in occ}
            for p in occ:
                m.add([(a[p], 1)] + [(v, -1) for v in occ[p]], lo=0)
                m.add([(b[p], 1)] + [(v, -1) for v in occ[p]], lo=0)
                if p > 1: m.add([(a[p], 1), (a[p - 1], -1)], lo=0)
                if p < last: m.add([(b[p], 1), (b[p + 1], -1)], lo=0)
                if 1 < p < last:
                    gp = m.var(ub=1, obj=W_S2)
                    m.add([(gp, 1), (a[p], -1), (b[p], -1)] + [(v, 1) for v in occ[p]], lo=-1)
    # S3 more than 6 hours a day (basket counted once per slot) and S4 same course twice a day
    for g, grp in ctx.groups.items():
        for d in ctx.days:
            terms = []
            for sid, s in sess.items():
                if g in s["groups"] and not s.get("basket_slot"):
                    terms += [(v, s["duration"]) for v in day_x[(sid, d)]]
            for b, members in ctx.baskets.items():
                if any(g in sess[sid]["groups"] for sid in members):
                    dur = sess[members[0]]["duration"]
                    terms += [(y, dur) for (bb, dd, t), y in Y.items() if bb == b and dd == d]
            if terms and sum(c for _, c in terms) > 6:
                e = m.var(ub=20, obj=W_S3)
                m.add([(e, 1)] + [(v, -c) for v, c in terms], lo=-6)
    by_gc = defaultdict(list)
    for sid, s in sess.items():
        if s["kind"] == "lecture" and not s.get("basket_slot"):
            for g in s["groups"]:
                by_gc[(g, s["course_id"])].append(sid)
    for (g, c), sids in by_gc.items():
        if len(sids) < 2: continue
        for d in ctx.days:
            z = m.var(ub=len(sids), obj=W_S4)
            m.add([(z, 1)] + [(v, -1) for sid in sids for v in day_x[(sid, d)]], lo=-1)
    bc = defaultdict(list)
    for b, members in ctx.baskets.items():
        for sid in members:
            bc[sess[sid]["course_id"]].append(b)
    for c, bl in bc.items():
        if len(bl) < 2: continue
        for d in ctx.days:
            z = m.var(ub=len(bl), obj=W_S4)
            m.add([(z, 1)] + [(y, -1) for (b, dd, t), y in Y.items() if dd == d and b in bl], lo=-1)
