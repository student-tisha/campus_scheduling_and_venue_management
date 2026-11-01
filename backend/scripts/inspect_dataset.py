import json
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "data" / "cit_public.json"
data = json.loads(path.read_text(encoding="utf-8"))

print("TOP-LEVEL TYPE:", type(data).__name__)

if isinstance(data, dict):
    for key, value in data.items():
        if isinstance(value, list):
            print(f"\n[{key}] list with {len(value)} items")
            if value and isinstance(value[0], dict):
                print("  first item keys:", list(value[0].keys()))
                print("  first item:", json.dumps(value[0], ensure_ascii=False)[:400])
        elif isinstance(value, dict):
            print(f"\n[{key}] dict with keys: {list(value.keys())[:15]}")
        else:
            print(f"\n[{key}] = {value}")