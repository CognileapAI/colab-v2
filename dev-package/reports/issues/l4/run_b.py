"""측정 실행기 — `measure_b.run` 을 팔레트 1값으로 부른다."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from l4api import call
import measure_b

st, pal, _ = call("GET", "/preview-palettes")
palette = pal["items"][0]["palette"]
label = sys.argv[1]
count = int(sys.argv[2])
here = pathlib.Path(__file__).parent
rec = measure_b.run(label, count, palette, here / f"run-{label}.json")
print(json.dumps(rec, ensure_ascii=False, indent=2)[:2500])
