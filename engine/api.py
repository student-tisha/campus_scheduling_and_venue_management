"""The ONLY module the FastAPI backend needs to import. All functions take/return plain dicts.

Timetable format everywhere:  {session_id: [day, start_period, room_id]}
"""
from .data import Ctx, load_data, apply_disruption
from . import solve as _solve, exams as _exams, reschedule as _resched, explain as _explain, checker as _checker


def generate_timetable(data, time_budget=120, seed=0, log=lambda *_: None):
    """-> {assign, soft_total, soft, status, seconds}"""
    return _solve.generate_timetable(data, time_budget=time_budget, seed=seed, log=log)


def schedule_exams(data):
    """-> {status, exams:[{exam_id, day, session, rooms}]}"""
    return _exams.schedule_exams(Ctx(load_data(data)))


def propose_fix(data, timetable, disruption, time_limit=90, log=lambda *_: None):
    """Proposal only; nothing is applied. -> {status: ok|infeasible|unknown|no_change, assign, changes:[...],
    sessions_moved, hard_violations_after, conflict (if infeasible), new_data}. Admin approval is the caller's job:
    on approve, store result['new_data'] as the dataset and result['assign'] as the timetable."""
    return _resched.propose_fix(data, timetable, disruption, time_limit=time_limit, log=log)


def explain_infeasible(data, time_limit=25):
    return _explain.explain_infeasible(Ctx(load_data(data)), time_limit=time_limit)


def explain_placement(data, timetable, session_id):
    return _explain.explain_placement(Ctx(load_data(data)), {k: tuple(v) for k, v in timetable.items()}, session_id)


def check_move(data, timetable, session_id, new_slot):
    """Code-only validity check for manual scheduling and AI-assistant proposals.
    new_slot = [day, start_period, room_id]. -> {ok: bool, violations: [{rule, detail, sessions}]}"""
    ok, v = _checker.check_move(Ctx(load_data(data)), {k: tuple(x) for k, x in timetable.items()}, session_id, tuple(new_slot))
    return {"ok": ok, "violations": v}


def check_timetable(data, timetable):
    ctx = Ctx(load_data(data))
    a = {k: tuple(v) for k, v in timetable.items()}
    soft, tot = _checker.soft_score(ctx, a)
    return {"violations": _checker.check_assignment(ctx, a), "soft": soft, "soft_total": tot}


def to_schedule_json(timetable, exams=None, fest_week=None, team="TEAM", dataset_id="cit-public-v1"):
    out = {"team": team, "dataset_id": dataset_id,
           "sessions": [{"session_id": k, "day": v[0], "start_period": v[1], "room_id": v[2]} for k, v in sorted(timetable.items())]}
    if fest_week is not None: out["fest_week"] = fest_week
    if exams is not None: out["exams"] = exams
    return out


def from_schedule_json(sched):
    return {e["session_id"]: [e["day"], e["start_period"], e["room_id"]] for e in sched["sessions"]}
