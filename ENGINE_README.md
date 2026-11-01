# CIT scheduling engine (Dipan's part)

Pure Python. No web framework, no LLM. Tisha's FastAPI imports **only** `engine/api.py`.

## Run
    pip install -r requirements.txt
    python -m engine.cli generate --data data/cit_public.json --out exports/schedule.json --budget 150 --team "<team>"
    python -m engine.cli disrupt  --data data/cit_public.json --schedule exports/schedule.json \
        --disruption data/sample_disruption.json --out exports/schedule_after.json --changes-out exports/changes_after.json
    python validator.py --data data/cit_public.json --schedule exports/schedule.json

Pass `--fest fest.json` to `generate` to embed Tisha's `fest_week` block (bookings + session_overrides).

## Functions (engine/api.py)  - timetable = {session_id: [day, start_period, room_id]}
| function | returns |
|---|---|
| generate_timetable(data, time_budget) | assign, soft_total, soft |
| schedule_exams(data) | exams list in schedule.json format |
| propose_fix(data, timetable, disruption) | status ok / infeasible / unknown, assign, changes[], sessions_moved, conflict |
| explain_infeasible(data) | which rules conflict, in plain language |
| explain_placement(data, timetable, sid) | why a session is where it is (text + facts) |
| check_move(data, timetable, sid, [day,p,room]) | {ok, violations[]}  - use for manual scheduling and AI proposals |
| check_timetable(data, timetable) | all hard violations + soft score |

`propose_fix` applies nothing. On Admin approval, store `result["new_data"]` (dataset with the disruption) and `result["assign"]`.
Each entry of `changes`: `{session_id, type: moved|added|removed, old, new, reason}`.

## How it works
- engine/data.py: indexes the dataset; every session's legal (day, start, room) positions are computed from room type, capacity, accessibility, lunch, lab starts, fixed slots, faculty and room unavailability.
- engine/model.py: MILP with one binary per option; room / faculty / group no-overlap, elective baskets, daily limit; soft penalties S1-S6 use the validator's own weights.
- engine/solve.py: quick feasible solve, then large-neighbourhood search (re-optimise ~45 sessions at a time) within a time budget.
- engine/reschedule.py: previous slot is rewarded 1000 points, so the fewest sessions move; widens the set of free sessions only if needed.
- engine/explain.py: deterministic explanations; infeasible cases use a deletion filter to find a minimal set of conflicting rules.
- engine/checker.py: independent rule checker (no solver, no LLM).

## Results on cit_public.json
- schedule.json: 0 hard violations, soft penalty 7, exam soft penalty 0 (official validator).
- schedule_after.json (sample disruption): 0 hard violations, 11 sessions moved (the minimum: 11 were broken).

## THIRD_PARTY.md entries
- SciPy (BSD-3) - `scipy.optimize.milp`, which wraps the HiGHS solver (MIT)
- NumPy (BSD-3)
