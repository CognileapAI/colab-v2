"""4회차 Ted 판정(2026-09-26 「전부 권고대로」) 을 오라클 probe 기대에 옮긴다 — 질문 2 · 4.

  · 질문 2 — rn15_sample(seq 4) 의 reviewed cadence 15min 을 거두고 계보 초안으로 내렸다. reviewed 만 읽는
    조건 검색에서 seq 4 는 주기를 모른다(unknown) → 15분 등호·「1시간 이하」 probe 의 기대에서 4 를 뺀다.
  · 질문 4 — hsr_sample(seq 3) 에 계보 초안 5min 을 실었다. 초안 포함 측정에서 seq 3 이 주기 조건에 들어오므로
    「1시간 이하」 probe 의 forbidSeq 에서 3 을 뺀다(초안이 맞게 부르는 것을 금지로 세지 않는다).
  measure_only probe(초안 포함 측정 전용)는 기대를 바꾸지 않는다.

  python3 dev-package/reports/evidence-promotion/round-4-2026-09-26/apply_cadence_decisions.py   # 멱등
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
ORACLE = REPO / "eval" / "k4-search" / "practitioner-conditions.json"
sys.path.insert(0, str(HERE))
import oracle_format  # noqa: E402

NOTE_4 = ("2026-09-26 Ted 「전부 권고대로」 질문 2 — seq 4(rn15_sample) 주기는 계보 초안이라 reviewed 만으로는 "
          "unknown 이다 → 기대에서 뺐다")
NOTE_3 = ("2026-09-26 Ted 「전부 권고대로」 질문 4 — seq 3(hsr_sample) 에 계보 초안 5min 이 있어 초안 포함 측정에서 "
          "맞는다 → forbidSeq 에서 뺐다")
#: (사례, probe 이름) → (expectSeq 에서 뺄 seq, forbidSeq 에서 뺄 seq)
EDITS = dict([
    (("PC-1-4", "15분 주기"), ([4], [])),
    (("PC-2-4", "강수 변수 + 15분 주기"), ([4], [])),
    (("PC-1-4", "1시간 이하 주기 — 범위 술어(전 자료)"), ([4], [3])),
    (("PC-1-4", "강수 변수 + 1시간 이하"), ([4], [])),
    (("PC-1-4", "1시간 이하 + 5 km 이하"), ([], [3])),
])


def main() -> int:
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    done = []
    for case in oracle["cases"]:
        for probe in case.get("probes") or []:
            edit = EDITS.get((case["id"], probe["name"]))
            if not edit:
                continue
            drop_expect, drop_forbid = edit
            notes = []
            if set(drop_expect) & set(probe["expectSeq"]):
                probe["expectSeq"] = [s for s in probe["expectSeq"] if s not in drop_expect]
                notes.append(NOTE_4)
            if set(drop_forbid) & set(probe["forbidSeq"]):
                probe["forbidSeq"] = [s for s in probe["forbidSeq"] if s not in drop_forbid]
                notes.append(NOTE_3)
            if notes:
                probe["decisionNote"] = " · ".join(notes)
            done.append(f"{case['id']} · {probe['name']}")
    if len(done) != len(EDITS):
        raise SystemExit(f"찾은 probe {len(done)} / 기대 {len(EDITS)} — {done}")
    ORACLE.write_text(oracle_format.dumps(oracle), encoding="utf-8")
    print(json.dumps(done, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
