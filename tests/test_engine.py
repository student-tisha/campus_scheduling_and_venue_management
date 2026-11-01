"""Run: python -m pytest tests -q   (needs exports/schedule.json from `engine.cli generate`)"""
import json, copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import validator
from engine import api
from engine.data import Ctx

D = json.load(open("data/cit_public.json"))
S = json.load(open("exports/schedule.json"))
T = api.from_schedule_json(S)


def test_validator_zero_hard():
    assert validator.run(D, S)["hard_violation_count"] == 0


def test_checker_agrees_with_validator_soft():
    assert api.check_timetable(D, T)["soft_total"] == validator.run(D, S)["soft_total"]
    assert api.check_timetable(D, T)["violations"] == []


def test_check_move_blocks_clash_and_wrong_room():
    sid = "MA101-AB-L1"
    other = next(k for k, v in T.items() if k != sid and v[2] != "OAT")
    r = api.check_move(D, T, sid, [T[other][0], T[other][1], T[other][2]])   # someone else's room+time
    assert not r["ok"] and r["violations"]
    r = api.check_move(D, T, sid, ["MON", 1, "OAT"])                         # open-air theatre: wrong type
    assert not r["ok"]


def test_check_move_accepts_noop():
    sid = "MA101-AB-L1"
    assert api.check_move(D, T, sid, T[sid])["ok"]


def test_no_legal_slot_explained():
    dis = {"changes": [{"type": "faculty_unavailable", "faculty_id": "F07", "days": D["calendar"]["days"],
                        "periods": list(range(1, 10)), "reason": "long leave"}]}
    r = api.propose_fix(D, T, dis)
    assert r["status"] == "infeasible"
    assert r["conflict"]["kind"] == "no_legal_slot" and "faculty" in r["conflict"]["message"]


def test_rule_conflict_explained():
    fx = lambda i, f: {"id": i, "course_id": "CS202", "kind": "lecture", "groups": ["CSE-2"], "faculty_id": f,
                       "size": 40, "duration": 1, "room_types": ["classroom"], "needs_accessible": False,
                       "basket_slot": None, "fixed_slot": {"day": "MON", "start_period": 3}}
    dis = {"changes": [{"type": "add_session", "session": fx("X1", "F06")}, {"type": "add_session", "session": fx("X2", "F06")}]}
    r = api.propose_fix(D, T, dis, time_limit=60)
    assert r["status"] == "infeasible"
    assert r["conflict"]["kind"] == "rule_conflict" and r["conflict"]["conflicting_rules"]
