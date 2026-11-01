"""python -m engine.cli generate --data data/cit_public.json --out exports/schedule.json
   python -m engine.cli disrupt  --data data/cit_public.json --schedule exports/schedule.json \
                                 --disruption data/sample_disruption.json --out exports/schedule_after.json"""
import argparse, json
from . import api


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate"); g.add_argument("--data", required=True); g.add_argument("--out", required=True)
    g.add_argument("--budget", type=int, default=150); g.add_argument("--team", default="TEAM"); g.add_argument("--fest")
    d = sub.add_parser("disrupt"); d.add_argument("--data", required=True); d.add_argument("--schedule", required=True)
    d.add_argument("--disruption", required=True); d.add_argument("--out", required=True)
    d.add_argument("--changes-out"); d.add_argument("--team", default="TEAM")
    a = ap.parse_args()
    data = json.load(open(a.data))
    if a.cmd == "generate":
        r = api.generate_timetable(data, time_budget=a.budget, log=print)
        if r["assign"] is None:
            raise SystemExit(f"No timetable: {r['status']} {r.get('empty')}")
        ex = api.schedule_exams(data)
        fest = json.load(open(a.fest)) if a.fest else None
        json.dump(api.to_schedule_json({k: list(v) for k, v in r["assign"].items()}, ex["exams"], fest, a.team, data["dataset_id"]),
                  open(a.out, "w"), indent=2)
        print("soft penalty", r["soft_total"], r["soft"])
    else:
        sched = json.load(open(a.schedule))
        r = api.propose_fix(data, api.from_schedule_json(sched), json.load(open(a.disruption)), log=print)
        if r["assign"] is None:
            raise SystemExit("No valid fix: " + r["conflict"]["message"])
        out = api.to_schedule_json({k: list(v) for k, v in r["assign"].items()}, sched.get("exams"), sched.get("fest_week"), a.team, data["dataset_id"])
        json.dump(out, open(a.out, "w"), indent=2)
        if a.changes_out: json.dump(r["changes"], open(a.changes_out, "w"), indent=2)
        print(f"moved {r['sessions_moved']} existing, added {r['sessions_added']}, hard violations {r['hard_violations_after']}")
        for c in r["changes"]: print(" ", c["type"], c["session_id"], c["old"], "->", c["new"], "|", c["reason"])


if __name__ == "__main__":
    main()
