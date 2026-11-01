from sqlalchemy.orm import Session

from app.services import booking_service
from app.services import dataset_loader as loader
from app.services import repair as greedy
from app.services import store
from app.services.exams import schedule_exams, validate_exams
from app.services.validator import validate_timetable

try:  # Dipan's solver plugs in here: solve(data) -> list of assignments
    from solver.solve import solve as solver_solve  # type: ignore
except Exception:  # noqa: BLE001
    solver_solve = None
try:  # optional: solve_exams(data, timetable) -> list of exam assignments
    from solver.exams import solve_exams as solver_exams  # type: ignore
except Exception:  # noqa: BLE001
    solver_exams = None


def _assignments(res):
    return res.get("assignments", []) if isinstance(res, dict) else res


def generate_timetable(db: Session) -> dict:
    data = loader.get_data_dict(db)
    runs = []
    if solver_solve:
        try:
            runs.append(("solver", _assignments(solver_solve(data))))
        except Exception as e:  # noqa: BLE001
            runs.append(("solver_error", []))
            print("solver failed:", e)
    runs.append(("builtin", greedy.repair(data, [])["assignments"]))
    best = None
    for name, assigns in runs:
        if not assigns:
            continue
        rep = validate_timetable(data, assigns)
        key = (rep["hard_count"], rep["soft_penalty"])
        if best is None or key < best[0]:
            best = (key, name, assigns, rep)
    key, name, assigns, rep = best
    store.set_doc(db, "timetable", {"sessions": assigns})
    return {"engine": name, "valid": rep["valid"], "hard_count": rep["hard_count"],
            "soft_penalty": rep["soft_penalty"], "soft": rep["soft"],
            "sessions": len(assigns), "first_violations": rep["hard_violations"][:10]}


def generate_exams(db: Session) -> dict:
    data = loader.get_data_dict(db)
    tt = store.get_doc(db, "timetable", {"sessions": []})["sessions"]
    cands = []
    if solver_exams:
        try:
            cands.append(("solver", solver_exams(data, tt)))
        except Exception as e:  # noqa: BLE001
            print("exam solver failed:", e)
    out, problems = schedule_exams(data)
    cands.append(("builtin", out))
    best = None
    for name, exams in cands:
        rep = validate_exams(data, exams)
        if best is None or rep["hard_count"] < best[0]:
            best = (rep["hard_count"], name, exams, rep)
    _, name, exams, rep = best
    store.set_doc(db, "exams", exams)
    return {"engine": name, "valid": rep["valid"], "hard_count": rep["hard_count"],
            "scheduled": len(exams), "total": len(data["exams"]),
            "violations": rep["violations"][:10], "problems": problems}


def generate_all(db: Session) -> dict:
    tt = generate_timetable(db)
    ex = generate_exams(db)
    res = booking_service.run_and_store(db)
    counts = {}
    for d in res["decisions"]:
        counts[d["status"]] = counts.get(d["status"], 0) + 1
    return {"timetable": tt, "exams": ex,
            "bookings": {"counts": counts, "session_overrides": len(res["overrides"]),
                         "needs_admin_approval": [d["request_id"] for d in res["decisions"]
                                                  if d["needs_admin_approval"]]}}
