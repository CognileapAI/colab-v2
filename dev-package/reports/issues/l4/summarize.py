import json, pathlib, sys
here = pathlib.Path(__file__).parent
for name in sys.argv[1:]:
    d = json.load(open(here / f"run-{name}.json", encoding="utf-8"))
    a = dict(d.get("analysis") or {})
    a.pop("log", None)
    r = dict(d.get("render") or {})
    r.pop("resultKeys", None)
    print("==", name, "pieces", d.get("pieceCount"), "bytes", d.get("byteSum"))
    print("  intake ", json.dumps(d.get("intake"), ensure_ascii=False))
    print("  analysis", json.dumps(a, ensure_ascii=False))
    print("  render ", json.dumps(r, ensure_ascii=False))
