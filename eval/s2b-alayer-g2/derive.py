#!/usr/bin/env python3
"""2세대 검색 평가셋의 **기대값을 데이터에서 다시 만든다.**

    python3 eval/s2b-alayer-g2/derive.py            # 도출 결과를 보여 준다(파일 안 고침)
    python3 eval/s2b-alayer-g2/derive.py --write    # evalset-g2.json 을 다시 쓴다
    python3 eval/s2b-alayer-g2/derive.py --check    # 커밋된 파일이 지금 실물과 같은지만 본다

`--check` 가 어긋나면 **적재분이나 사전이 움직였다는 뜻**이다. 그때 할 일은 기대를 손으로
맞추는 것이 아니라 `--write` 로 다시 뽑고 무엇이 달라졌는지 회차 문서에 적는 것이다.

종료 코드는 판정이 아니라 「잴 수 있었는가」다 — `0` 도출 성공 · `2` 못 쟀다 · `3` 커밋된 기대와 실물이 다름.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import common as C


def main() -> int:
    ap = argparse.ArgumentParser(description="적재된 데이터에서 검색 평가셋 기대값을 도출한다")
    ap.add_argument("--pg", default=C.DEFAULT_PG)
    ap.add_argument("--ai", default=C.DEFAULT_AI)
    ap.add_argument("--db", default=C.DEFAULT_DB)
    ap.add_argument("--role", default=C.DEFAULT_ROLE)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    cfg = ap.parse_args()

    try:
        cases_doc = json.loads(C.CASES.read_text(encoding="utf-8"))
        data, _ = C.measure_ground_truth(cfg.pg, cfg.db, cfg.role)
        expansions = C.measure_expansion(cfg.ai, cases_doc["cases"])
        built = C.build_evalset(cases_doc, data, expansions)
    except C.Unmeasurable as e:
        print(f"⛔ 못 쟀다 — {e}", file=sys.stderr)
        return 2

    gt = built["ground_truth"]
    print("═══ 실물 측정(기대값의 출처) ═══")
    print(f"시점 = {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}")
    print(f"대상 데이터셋 = {gt['대상_데이터셋']}건 · 설명 본문 빈 것 0건")
    print(f"최신 설명 갱신 시각 = {gt['최신_설명_갱신시각']}")
    print(f"출처 = {gt['출처']}")
    print()
    print(f"{'#':<6}{'갈래':<20}기대")
    print("─" * 110)
    for it in built["items"]:
        print(f"{it['id']:<6}{it['kind']:<20}{json.dumps(it['expected'], ensure_ascii=False)}")
    print("─" * 110)
    kinds: dict[str, int] = {}
    for it in built["items"]:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    print("갈래별 " + " · ".join(f"{k} {v}건" for k, v in sorted(kinds.items())))

    if cfg.check:
        if not C.EVALSET.is_file():
            print("⛔ 커밋된 기대 파일이 없다", file=sys.stderr)
            return 3
        old = json.loads(C.EVALSET.read_text(encoding="utf-8"))
        if json.dumps(old["items"], ensure_ascii=False, sort_keys=True) != \
           json.dumps(built["items"], ensure_ascii=False, sort_keys=True):
            print("⛔ 커밋된 기대와 지금 실물에서 뽑은 기대가 다르다 — 적재분·사전이 움직였다. "
                  "`--write` 로 다시 뽑고 회차 문서에 무엇이 달라졌는지 적는다", file=sys.stderr)
            return 3
        print("✓ 커밋된 기대 = 지금 실물에서 뽑은 기대")

    if cfg.write:
        built["도출_시점"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        C.EVALSET.write_text(json.dumps(built, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n기대값 → {C.EVALSET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
