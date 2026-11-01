"""Minimal-move rescheduler. Nothing is applied here: it returns a proposal for an Admin to approve."""
import time
from .data import Ctx, load_data, apply_disruption
from .checker import check_assignment, soft_score
from .model import solve_timetable
from .explain import explain_infeasible

MOVE_WEIGHT = 1000


def _with_baskets(ctx, free):
    for b, members in ctx.baskets.items():
        if any(m in free for m in members): free |= set(members)
    return free


def propose_fix(data, assign, disruption, time_limit=90, log=print):
    """data: original dataset; assign: current timetable {sid: (day,start,room)}; disruption: change file dict."""
    t0 = time.time()
    new_data = apply_disruption(load_data(data), disruption)
    ctx = Ctx(new_data)
    old = {k: tuple(v) for k, v in assign.items() if k in ctx.sessions}
    removed = sorted(k for k in assign if k not in ctx.sessions)
    viol = check_assignment(ctx, old)
    affected = {sid for v in viol for sid in v["sessions"] if sid in ctx.sessions}
    affected |= {sid for sid in ctx.sessions if sid not in old}
    log(f"{len(affected)} session(s) directly affected: {sorted(affected)}")
    if not affected:
        return _result("no_change", ctx, old, old, removed, viol, t0, new_data)
    affected = _with_baskets(ctx, set(affected))
    facs = {ctx.sessions[s]["faculty_id"] for s in affected}
    grps = {g for s in affected for g in ctx.sessions[s]["groups"]}
    near = {s for s, x in ctx.sessions.items() if x["faculty_id"] in facs or set(x["groups"]) & grps}
    stages = [("directly affected sessions", affected),
              ("+ sessions sharing faculty or student groups", _with_baskets(ctx, affected | near)),
              ("all sessions", set(ctx.sessions))]
    best, best_moves, last_status = None, None, None
    for name, free in stages:
        left = time_limit - (time.time() - t0)
        if left < 5 and best: break
        frozen = {k: v for k, v in old.items() if k not in free}
        r = solve_timetable(ctx, frozen=frozen, prev=old, move_weight=MOVE_WEIGHT, time_limit=max(10, left))
        last_status = r["status"]
        if r["assign"] is None:
            log(f"  stage '{name}': {r['status']}"); continue
        moves = sum(1 for k, v in r["assign"].items() if k in old and old[k] != v)
        log(f"  stage '{name}': {moves} existing session(s) moved ({r['seconds']:.0f}s)")
        if best is None or moves < best_moves:
            best, best_moves = r["assign"], moves
        if best_moves <= len(affected & set(old)):   # cannot beat "only the broken ones moved"
            break
    if best is None:
        why = explain_infeasible(ctx, time_limit=20) if last_status == "infeasible" else \
            {"message": "Solver found no valid fix within the time limit.", "conflicting_rules": []}
        return {"status": "infeasible" if last_status == "infeasible" else "unknown", "conflict": why,
                "changes": [], "assign": None, "seconds": time.time() - t0, "new_data": new_data}
    return _result("ok", ctx, old, best, removed, viol, t0, new_data)


def _result(status, ctx, old, new, removed, viol, t0, new_data):
    bad = {}
    for v in viol:
        for sid in v["sessions"]: bad.setdefault(sid, []).append(v["detail"].split(": ", 1)[-1])
    changes = []
    moved_ids = [k for k in new if k in old and old[k] != new[k]]
    for sid in sorted(new):
        n = new[sid]
        if sid not in old:
            changes.append({"session_id": sid, "type": "added", "old": None, "new": list(n),
                            "reason": "New session placed."})
        elif old[sid] != n:
            if sid in bad:
                why = "Old slot no longer valid: " + "; ".join(sorted(set(bad[sid]))[:3])
            else:
                why = _displaced_by(ctx, sid, old[sid], new, moved_ids)
            changes.append({"session_id": sid, "type": "moved", "old": list(old[sid]), "new": list(n), "reason": why})
    for sid in removed:
        changes.append({"session_id": sid, "type": "removed", "old": None, "new": None, "reason": "Session removed."})
    soft = soft_score(ctx, new)
    return {"status": status, "assign": new, "changes": changes,
            "sessions_moved": len(moved_ids), "sessions_added": sum(1 for c in changes if c["type"] == "added"),
            "hard_violations_after": len(check_assignment(ctx, new)), "soft_total": soft[1], "soft": soft[0],
            "seconds": time.time() - t0, "new_data": new_data}


def _displaced_by(ctx, sid, o, new, moved_ids):
    d, t, r = o
    s = ctx.sessions[sid]
    for other in new:
        if other == sid: continue
        od, ot, orr = new[other]
        x = ctx.sessions[other]
        if od != d or not (ot < t + s["duration"] and t < ot + x["duration"]): continue
        if orr == r: return f"Its old room {r} is now needed by {other}."
        if x["faculty_id"] == s["faculty_id"]: return f"Faculty {x['faculty_id']} is now teaching {other} at that time."
        if set(x["groups"]) & set(s["groups"]): return f"Its student group now has {other} at that time."
    return "Moved to make space for the fix."
