"""Deterministic explanations. No LLM: every sentence is built from solver / checker facts."""
from collections import Counter
from .checker import check_move, check_moves, soft_score, TAG_TEXT
from .model import solve_timetable, HARD_TAGS

RULE_TEXT = dict(TAG_TEXT)
RULE_TEXT.update({"room_clash": "a room cannot hold two sessions at once",
                  "faculty_clash": "a faculty member cannot be in two places at once",
                  "group_clash": "a student group cannot be in two places at once",
                  "basket_same_time": "elective-basket sessions must share one day and period",
                  "faculty_daily_limit": "faculty daily teaching-hour limit"})
OPTION_TAGS = set(TAG_TEXT)


def explain_infeasible(ctx, time_limit=25, deep=True):
    """Which rules are in conflict? Step 1: sessions with no legal slot. Step 2: deletion filter over rule groups."""
    empty = []
    for sid in ctx.sessions:
        if not ctx.options(sid):
            blk = ctx.all_blocked(sid)
            solo = Counter(next(iter(t)) for _, t in blk if len(t) == 1)
            allt = Counter(x for _, t in blk for x in t)
            empty.append({"session_id": sid,
                          "relaxing_would_open": {RULE_TEXT[k]: n for k, n in solo.most_common()},
                          "blocked_by": [RULE_TEXT[k] for k, _ in allt.most_common()]})
    if empty:
        e = empty[0]
        msg = (f"{len(empty)} session(s) have no legal day/period/room at all, e.g. {e['session_id']}: "
               f"every position is ruled out by: {'; '.join(e['blocked_by'])}.")
        return {"feasible": False, "kind": "no_legal_slot", "sessions": empty, "conflicting_rules": [],
                "message": msg}
    if not deep:
        return {"feasible": None, "message": "not checked"}
    tags = sorted(HARD_TAGS | OPTION_TAGS)
    keep = list(tags)
    first = solve_timetable(ctx, soft=False, time_limit=time_limit)
    if first["assign"] is not None:
        return {"feasible": True, "message": "A valid timetable exists.", "conflicting_rules": []}
    if first["status"] != "infeasible":
        return {"feasible": None, "kind": "timeout", "conflicting_rules": [],
                "message": "Solver ran out of time before proving a conflict."}
    for tag in list(keep):                      # deletion filter: drop every rule not needed for the conflict
        trial = [k for k in keep if k != tag]
        dis = frozenset(set(tags) - set(trial))
        r = solve_timetable(ctx, soft=False, time_limit=time_limit, disabled=dis)
        if r["status"] == "infeasible":
            keep = trial
    rules = [RULE_TEXT[k] for k in keep]
    return {"feasible": False, "kind": "rule_conflict", "sessions": [], "conflicting_rules": rules,
            "message": "No valid timetable exists. These rules cannot all hold together (a minimal conflicting set): " + "; ".join(rules) + "."}


def explain_placement(ctx, assign, sid, max_alts=400):
    """Why is `sid` where it is? Facts: what blocks the alternatives, and the soft cost of this choice."""
    s, cur = ctx.sessions[sid], tuple(assign[sid])
    members = ctx.baskets.get(s.get("basket_slot")) if s.get("basket_slot") else None
    base_soft, base_total = soft_score(ctx, assign)
    legal = [o for o in ctx.options(sid) if o != cur]
    blockers, free = Counter(), []
    if members and len(members) > 1:
        text_basket = (f"{sid} is in elective basket {s['basket_slot']}: all {len(members)} parallel electives must share "
                       f"one day and period, so it moves only together with them.")
    else:
        text_basket = ""
        for o in legal[:max_alts]:
            ok, new = check_move(ctx, assign, sid, o)
            if ok:
                cand = dict(assign); cand[sid] = o
                free.append((soft_score(ctx, cand)[1] - base_total, o))
            else:
                for rule in {x["rule"] for x in new}:
                    blockers[rule] += 1
    free.sort()
    d, t, r = cur
    own = []
    room = ctx.rooms[r]
    for pf in ctx.fac[s["faculty_id"]].get("preferences", []):
        if pf.get("type") == "avoid" and d in pf.get("days", ctx.days) and any(p in pf["periods"] for p in range(t, t + s["duration"])):
            own.append("it falls in a time the faculty asked to avoid")
    if room["capacity"] and s["size"] / room["capacity"] < 0.4: own.append("the room is under 40% full")
    if ctx.last in range(t, t + s["duration"]): own.append("it uses the last period (P9)")
    names = {"H2": "faculty busy", "H3": "student group busy", "H4": "room taken", "H12": "faculty daily limit",
             "H7": "faculty unavailable", "H8": "room closed", "H11": "basket break"}
    parts = [f"{sid} is on {d} P{t}" + (f"-P{t+s['duration']-1}" if s['duration'] > 1 else "") + f" in {r}."]
    parts.append(f"Its own rules (room type, capacity, availability, lunch/lab-start) leave {len(ctx.options(sid))} possible positions.")
    if text_basket:
        parts.append(text_basket)
    else:
        parts.append(f"Of the other {len(legal)}, {len(free)} would not create a clash"
                     + (f"; the rest are blocked by: {', '.join(f'{names.get(k, k)} ({n})' for k, n in blockers.most_common(4))}." if blockers else "."))
        if free:
            best = free[0]
            if best[0] >= 0:
                parts.append(f"None of the clash-free alternatives scores better on soft rules (best change: {best[0]:+d} penalty points), so this one was kept.")
            else:
                parts.append(f"A slightly better slot exists ({best[1]}, {best[0]:+d} points) but was not found within the time budget.")
        else:
            parts.append("No other clash-free position exists, so this placement is forced.")
    if t == 1: parts.append("8 AM carries no penalty of its own, so it is used whenever it fits without a clash.")
    if own: parts.append("Soft cost of this slot: " + "; ".join(own) + ".")
    return {"session_id": sid, "slot": {"day": d, "start_period": t, "room_id": r},
            "legal_positions": len(ctx.options(sid)), "clash_free_alternatives": len(free),
            "blocked_by": dict(blockers), "soft_cost_reasons": own, "text": " ".join(parts)}
