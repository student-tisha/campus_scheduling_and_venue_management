"""generate_timetable: fast feasible solve, then large-neighbourhood search on the soft penalty."""
import random, time
from .data import Ctx, load_data
from .model import solve_timetable
from .checker import check_assignment, soft_score


def _neighbourhood(ctx, assign, rng, size):
    sids = list(assign)
    kind = rng.choice(["groups", "day", "faculty", "random"])
    free = set()
    if kind == "groups":
        gs = list(ctx.groups); rng.shuffle(gs)
        for g in gs:
            free |= {s for s in sids if g in ctx.sessions[s]["groups"]}
            if len(free) >= size: break
    elif kind == "day":
        day = rng.choice(ctx.days)
        free = {s for s in sids if assign[s][0] == day}
    elif kind == "faculty":
        fs = list({ctx.sessions[s]["faculty_id"] for s in sids}); rng.shuffle(fs)
        for f in fs:
            free |= {s for s in sids if ctx.sessions[s]["faculty_id"] == f}
            if len(free) >= size: break
    else:
        free = set(rng.sample(sids, min(size, len(sids))))
    for b, members in ctx.baskets.items():          # baskets move as a unit
        if any(m in free for m in members): free |= set(members)
    return free


def generate_timetable(data, time_budget=120, seed=0, log=print, neighbourhood=45):
    """Returns {assign, soft_total, soft, status, seconds}. assign: sid -> (day, start, room)."""
    t0 = time.time()
    ctx = Ctx(load_data(data))
    r = solve_timetable(ctx, soft=False, time_limit=90)
    if r["assign"] is None:
        return {"assign": None, "status": r["status"], "empty": r["empty"], "seconds": time.time() - t0}
    cur = r["assign"]
    best = soft_score(ctx, cur)[1]
    log(f"feasible timetable in {time.time()-t0:.0f}s, soft penalty {best}")
    rng, it = random.Random(seed), 0
    while time.time() - t0 < time_budget:
        it += 1
        free = _neighbourhood(ctx, cur, rng, neighbourhood)
        frozen = {k: v for k, v in cur.items() if k not in free}
        lim = max(5, min(25, time_budget - (time.time() - t0)))
        r = solve_timetable(ctx, frozen=frozen, time_limit=lim)
        if r["assign"] is None: continue
        s = soft_score(ctx, r["assign"])[1]
        if s < best and not check_assignment(ctx, r["assign"]):
            cur, best = r["assign"], s
            log(f"  LNS {it}: soft penalty {best}  ({time.time()-t0:.0f}s)")
    soft, tot = soft_score(ctx, cur)
    return {"assign": cur, "soft": soft, "soft_total": tot, "status": "ok", "seconds": time.time() - t0}
