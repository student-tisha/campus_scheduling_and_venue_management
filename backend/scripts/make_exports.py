"""Produces exports/schedule.json and exports/schedule_after.json using the app itself.

Run from the backend folder:   python scripts/make_exports.py
Needs data/cit_public.json and the sample disruption file (data/sample_disruption.json).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

BACKEND = Path(__file__).resolve().parent.parent
disruption = next((p for p in (BACKEND / "data" / "sample_disruption.json",
                               BACKEND / "data" / "examples" / "sample_disruption.json")
                   if p.exists()), None)
if disruption is None:
    sys.exit("Put sample_disruption.json in backend/data/ first.")

with TestClient(app) as c:
    tok = c.post("/api/auth/login", json={"email": "admin@cit.edu",
                                          "password": "Admin@123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    print("1. reset demo data:", c.post("/api/admin/reset", headers=h).status_code)
    gen = c.post("/api/admin/generate", headers=h).json()
    t, e = gen["timetable"], gen["exams"]
    print(f"2. timetable by '{t['engine']}': valid={t['valid']} hard={t['hard_count']} "
          f"soft={t['soft_penalty']}")
    print(f"   exams by '{e['engine']}': valid={e['valid']} scheduled={e['scheduled']}/{e['total']}")
    print("   bookings:", gen["bookings"]["counts"])
    print("3. saved:", c.post("/api/export/save?name=schedule.json", headers=h).json())
    changes = json.loads(disruption.read_text(encoding="utf-8"))
    p = c.post("/api/changes/propose", headers=h, json={"changes": changes["changes"],
                                                         "note": "sample disruption"})
    prop = p.json()
    if p.status_code != 200 or prop.get("infeasible"):
        sys.exit(f"No valid fix: {prop}")
    print(f"4. proposal {prop['id']}: moves {prop['diff']['moved_count']} sessions "
          f"(engine {prop['engine']})")
    print("5. approve:", c.post(f"/api/changes/{prop['id']}/approve", headers=h).json())
    print("6. saved:", c.post("/api/export/save?name=schedule_after.json", headers=h).json())

print("\nNow run the official checker from the repo root:")
print("  python backend/data/validator.py --data backend/data/cit_public.json "
      "--schedule exports/schedule.json")
print("  python backend/data/validator.py --data backend/data/cit_public.json "
      "--schedule exports/schedule_after.json --disruption backend/data/sample_disruption.json "
      "--baseline exports/schedule.json")
