"""Midsem scheduler. Exam week MON-SAT x (AM, PM); rooms seat half capacity; an exam may use several rooms."""
from collections import defaultdict
from .mip import MIP


def schedule_exams(ctx, time_limit=60):
    data = ctx.data
    cal = data["calendar"]["exam_week"]
    slots = [(d, s["id"]) for d in cal["days"] for s in cal["sessions"]]
    rooms = [r for r in data["rooms"] if "exam" in r["allowed_uses"]]
    seats = {r["id"]: r["capacity"] // 2 for r in rooms}
    exams = data["exams"]
    m = MIP()
    X, N = {}, {}
    for e in exams:
        for sl in slots:
            X[(e["id"], sl)] = m.var(integer=True)
            for r in rooms:
                N[(e["id"], sl, r["id"])] = m.var(obj=0.01, integer=True)   # tiny cost: use few rooms
    for e in exams:
        eid = e["id"]
        m.add([(X[(eid, sl)], 1) for sl in slots], 1, 1)
        for sl in slots:
            for r in rooms:
                m.add([(N[(eid, sl, r["id"])], 1), (X[(eid, sl)], -1)], hi=0)
            m.add([(N[(eid, sl, r["id"])], seats[r["id"]]) for r in rooms] + [(X[(eid, sl)], -e["size"])], lo=0)
    for sl in slots:
        for r in rooms:
            m.add([(N[(e["id"], sl, r["id"])], 1) for e in exams], hi=1)
        for g in ctx.groups:
            terms = [(X[(e["id"], sl)], 1) for e in exams if g in e["groups"]]
            if len(terms) > 1: m.add(terms, hi=1)
    for g in ctx.groups:                           # soft: at most one exam per group per day
        for d in cal["days"]:
            terms = [(X[(e["id"], (d, s))], 1) for e in exams if g in e["groups"] for s in [x["id"] for x in cal["sessions"]]]
            if len(terms) > 1:
                w = m.var(ub=5, obj=5)
                m.add([(w, 1)] + [(v, -1) for v, _ in terms], lo=-1)
    status, x, obj = m.solve(time_limit, rel_gap=0.2)
    if x is None:
        return {"status": status, "exams": None}
    out = []
    for e in exams:
        for sl in slots:
            if x[X[(e["id"], sl)]] > 0.5:
                out.append({"exam_id": e["id"], "day": sl[0], "session": sl[1],
                            "rooms": [r["id"] for r in rooms if x[N[(e["id"], sl, r["id"])]] > 0.5]})
    return {"status": status, "exams": out}
