"""#30㈎ 부모 찾기 0행 재현 — 조사 스크립트(읽기 전용)."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from l4api import call

st, out, url = call("GET", "/datasets", {"limit": 100})
items = out["items"] if isinstance(out, dict) else []
print("== /datasets ==")
print("status", st, "rows", len(items), "keys", list(out.keys()) if isinstance(out, dict) else out)
print("nextCursor", out.get("nextCursor") if isinstance(out, dict) else None)
labs = {}
for it in items:
    labs.setdefault(it["uploader"]["accountId"], 0)
    labs[it["uploader"]["accountId"]] += 1
print("uploaders", labs)
print("levels", sorted({it.get("processingLevel") for it in items}))

cases = [
    ("필터 없음", {"limit": 25}),
    ("필터 없음 ＋ 자기 제외(가상 id)", {"limit": 25, "excludeDatasetId": "01M0Y1WK2YCZNQHME5JBKV5JMQ"}),
    ("분류 1값", {"limit": 25, "category": "위성"}),
    ("주제 1값", {"limit": 25, "topic": "식생·NDVI"}),
    ("가공 단계 필터 0", {"limit": 25, "processingLevel": 0}),
    ("가공 단계 필터 1", {"limit": 25, "processingLevel": 1}),
]
print()
print("== /lineage-candidates ==")
for name, q in cases:
    st, out, url = call("GET", "/lineage-candidates", q)
    rows = None
    cur = None
    if isinstance(out, dict):
        rows = len(out.get("items") or [])
        cur = out.get("nextCursor")
    print(f"[{name}] status={st} rows={rows} nextCursor={cur}")
    print("   URL", url)
    if isinstance(out, str):
        print("   body", out[:300])
    elif rows:
        r = out["items"][0]
        print("   first", {k: r.get(k) for k in ("datasetId", "name", "processingLevel", "topic", "category")})
