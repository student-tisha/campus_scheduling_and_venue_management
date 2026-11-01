"""repair(data, current) -> list of {"session_id","day","start_period","room_id"}

Keeps every session where it is unless the change forces a move (fewest moves wins).
Method: sessions untouched by the change are frozen in their current slot; only the affected ones are re-solved
(then neighbours, then everything, only if needed). Uses SciPy/HiGHS, not OR-Tools.

The returned object is a normal list, and ALSO answers result["infeasible"], result["conflicts"],
result["assignments"], so both calling styles work.
`data` = dataset that already contains the change; `current` = previous timetable list.
"""
from .engine import api


class RepairResult(list):
    infeasible = False
    conflicts = ()

    @property
    def assignments(self):
        return list(self)

    def __getitem__(self, key):
        if isinstance(key, str):
            return {"infeasible": self.infeasible, "conflicts": list(self.conflicts),
                    "assignments": list(self)}[key]
        return super().__getitem__(key)


def _rows(assign):
    return [{"session_id": k, "day": v[0], "start_period": v[1], "room_id": v[2]}
            for k, v in sorted(assign.items())]


def repair(data, current, time_limit=90):
    old = {e["session_id"]: [e["day"], e["start_period"], e["room_id"]] for e in current}
    r = api.propose_fix(data, old, {"changes": []}, time_limit=time_limit)
    if r["assign"] is None:
        c = r.get("conflict", {})
        msgs = [c.get("message", "No valid fix found within the time limit.")]
        msgs += [f"Rule in conflict: {x}" for x in c.get("conflicting_rules", [])]
        for s in c.get("sessions", [])[:5]:
            msgs.append(f"{s['session_id']} has no legal slot (blocked by: {'; '.join(s['blocked_by'])})")
        out = RepairResult()
        out.infeasible, out.conflicts = True, msgs
        return out
    return RepairResult(_rows(r["assign"]))