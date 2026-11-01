"""solve_exams(data, timetable) -> [{"exam_id","day","session","rooms":[...]}, ...]
Exams are in a separate week, so the weekly timetable is not needed; the argument is kept for the interface."""
from .engine import api


def solve_exams(data, timetable=None):
    r = api.schedule_exams(data)
    if r["exams"] is None:
        raise RuntimeError(f"No valid exam schedule: {r['status']}")
    return r["exams"]
