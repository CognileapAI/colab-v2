#!/usr/bin/env python3
"""러너 진행 관찰기 — `state.json` 과 `fail/` 을 20초마다 다시 읽어 새 줄만 출력한다.

- 자리 = `--work-dir`(기본 = 이 폴더의 `.work/`) · 환경변수 `COLAB_SEED_WORK_DIR`.
- 러너를 건드리지 않는다. 읽기만 하고 `report` 단계가 `done` 이면 `ALL-DONE` 을 찍고 끝난다.
- ⛔ 절대경로를 코드에 적지 않는다 — 자리는 인자·환경변수로만 받는다.
"""

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_WORK_DIR = TOOL_DIR / ".work"


def snapshot(base):
    try:
        st = json.load(open(os.path.join(base, "state.json"), encoding="utf-8"))
    except Exception:
        return [], None
    out = []
    ds = st.get("datasets") or (st.get("steps") or {}).get("datasets") or {}
    items = ds.items() if isinstance(ds, dict) else enumerate(ds)
    for k, v in items:
        if not isinstance(v, dict):
            continue
        state = v.get("status")
        if state in ("done", "failed", "error", "blocked"):
            out.append("seq %s %s %s id=%s bytes=%s elapsed=%s" % (
                k, v.get("name", ""), state, v.get("dataset_id", ""),
                v.get("bytes", ""), v.get("elapsed_s", "")))
    term = None
    for k in ("verify", "report"):
        v = st.get(k) or (st.get("steps") or {}).get(k)
        if isinstance(v, dict) and v.get("status"):
            out.append("phase %s %s" % (k, v.get("status")))
            if k == "report" and v.get("status") == "done":
                term = "ALL-DONE"
    return out, term


def main():
    ap = argparse.ArgumentParser(description="러너 진행 관찰기")
    ap.add_argument("--work-dir", default=os.environ.get("COLAB_SEED_WORK_DIR"),
                    help="러너의 작업 자리. 기본값 = 이 폴더의 .work/")
    ap.add_argument("--interval", type=float, default=20.0, help="다시 읽는 간격(초)")
    args = ap.parse_args()
    base = str(Path(args.work_dir).expanduser() if args.work_dir else DEFAULT_WORK_DIR)

    seen = set()
    seen_fail = set()
    while True:
        lines, term = snapshot(base)
        for ln in lines:
            if ln not in seen:
                seen.add(ln)
                print(ln, flush=True)
        for f in sorted(glob.glob(os.path.join(base, "fail", "*.txt"))):
            if f not in seen_fail:
                seen_fail.add(f)
                print("FAIL " + os.path.basename(f), flush=True)
        if term:
            print(term, flush=True)
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
