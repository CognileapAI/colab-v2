"""3회차(지역 포함 관계) — 「한반도」 region probe 5건을 **제품 코드 그대로** 두 경로에서 잰다.

2회차 `region_probe_states.py` 와 달리 **반사실 패치가 없다.** 경로 1 은 `d3_client_search.candidates`,
경로 2 는 `search_evidence_conditions`(파일 근거 후보) — 둘 다 이 브랜치의 `kernel/region_scope.py` 를
읽는다(intent `dev-package/intent/2026-09-26-region-containment-expansion.md` 완료 정의 ②④).

`measure_draft_contribution.py` 의 같은 평가기(`Evaluator`)를 불러, `--seed-dev-like` 로 시드된 일회용 DB
에서 상태 셋을 한 트랜잭션 안에 겹쳐 보고 rollback 한다. 새 판정 논리는 없다.

상태
  reviewed      초안 전부 뺌(= dev 에 이 payload 를 실었을 때 조건 검색이 보는 것)
  all_drafts    초안 전부 겹침(다음 승격 회차 뒤의 모양)
  region_drafts 지역 초안 규칙만 겹침

상향 누수 대조(안전 규칙 1) — 「남한」 조건이 한반도 자료를 부르는가. 셀 = 들어오면 안 되는 seq 가 들어온 수.
  경로 1 `{"region": "남한"}` forbid 한반도 사실 seq(6 · 초안 21~24) · 경로 2 `PB-LEAK-1`(남한 식생) forbid 6.

  services/core-api/.venv/bin/python <이 파일> <앱 롤 URL> --payload <payload> --output <json>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
REGION_RULES = ("region-from-lineage-parent", "region-from-lineage-sibling", "bbox-korea-peninsula",
                "region-from-registration-note")
LEAK_A = {"id": "LEAK-A-1", "name": "남한 조건 — 한반도 자료를 부르지 않는다",
          "conditions": {"region": "남한"}, "expectSeq": [1, 2, 19, 20], "forbidSeq": [6, 21, 22, 23, 24]}
LEAK_B = {"id": "LEAK-B-1", "name": "남한 식생 — 한반도 식생 자료(seq 6)를 파일 근거 후보로 올리지 않는다",
          "conditions": {"region": "남한"}, "expectSeq": [], "forbidSeq": [6],
          "pathB": {"id": "PB-LEAK-1", "query": "남한 식생 자료 찾아줘"}}


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "k4_measure_draft", REPO / "eval" / "k4-search" / "measure_draft_contribution.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("database_url")
    ap.add_argument("--payload", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    args = ap.parse_args()
    tool = load_tool()
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    facts = tool.draft_facts(payload)
    db = tool._db()
    _factory, session = tool._open(db, args.database_url)
    try:
        cases = tool.load_cases()
        ev = tool.Evaluator(db, session, payload, facts, cases)
        everything = frozenset(f["fact_id"] for f in facts)
        non_region = frozenset(f["fact_id"] for f in facts if f["rule"] not in REGION_RULES)
        states = {"reviewed": everything, "all_drafts": frozenset(), "region_drafts": non_region}
        region = [p for p in cases["probes"] if p["conditions"].get("region") == "korean_peninsula"]
        if len(region) != 5 or any("pathB" not in p for p in region):
            print(f"준비 실패: 「한반도」 region probe 5건(pathB 포함)이 아니다 — {[p['id'] for p in region]}",
                  file=sys.stderr)
            return 78
        rows = {p["id"]: {"id": p["id"], "name": p["name"], "mode": p.get("mode", "probe"),
                          "conditions": p["conditions"], "expectSeq": p["expectSeq"], "forbidSeq": p["forbidSeq"],
                          "pathB": p["pathB"]["query"]} for p in region}
        leaks, golden = {}, {}
        for name, removed in states.items():
            out = ev.evaluate(removed)  # 상태를 겹치고 경로 1 probe · 골든 두 경로를 잰다
            golden[name] = {g: sum(v["green"] for v in out[g].values()) for g in ("A", "B")}
            reviewed = db.d3_search_evidence.read_reviewed(session, include_source_text=False)
            cache: dict = {}
            for p in region:
                b = ev.path_b_probe(p, reviewed, cache)
                a_seqs = ev._seqs(db.d3_client_search.candidates(session, dict(p["conditions"]))[0])
                rows[p["id"]][name] = {"A": out["A"][p["id"]]["green"], "A_seqs": sorted(a_seqs),
                                       "B": b["green"], "B_evidenceSeqs": b["evidenceSeqs"],
                                       "B_search": b["greenSearch"], "B_criteria": b["criteria"]}
            a_leak = ev._seqs(db.d3_client_search.candidates(session, dict(LEAK_A["conditions"]))[0])
            b_leak = ev.path_b_probe(LEAK_B, reviewed, cache)
            leaks[name] = {
                "A": {"seqs": sorted(a_leak), "leaked": sorted(set(a_leak) & set(LEAK_A["forbidSeq"])),
                      "green": tool.probe_green(LEAK_A, a_leak)},
                "B": {"seqs": b_leak["evidenceSeqs"], "leaked": sorted(set(b_leak["evidenceSeqs"]) & {6}),
                      "green": b_leak["green"], "criteria": b_leak["criteria"]}}
        leak_total = sum(len(v[p]["leaked"]) for v in leaks.values() for p in ("A", "B"))
        counts = {name: {path: sum(r[name][path] for r in rows.values()) for path in ("A", "B")}
                  for name in states}
        result = {"schema": "colab-region-probe-states/2", "payload": str(args.payload),
                  "payloadSha256": tool.sha256_file(args.payload), "counterfactual": None,
                  "note": ("반사실 패치 없음 — 제품 코드(kernel/region_scope.py)로 잰다. 경로 2 green = 파일 근거 후보 "
                           "(search_evidence_conditions.candidates 포함 집합); B_search = 전체 검색 결과 기준 참고 열. "
                           "경로 2 해석 = interpret-fixture.json 규칙 기반 녹화(모델 호출 0 · 실모델 녹화 별도 승인 대기)."),
                  "regionProbes": list(rows.values()), "greenCounts": counts,
                  "upwardLeak": {"probes": [LEAK_A, LEAK_B], "states": leaks, "total": leak_total},
                  "goldenGreen": golden}
    finally:
        session.rollback()
        session.close()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"greenCounts": counts, "upwardLeakTotal": leak_total, "goldenGreen": golden},
                     ensure_ascii=False))
    for row in rows.values():
        print(row["id"], {s: (row[s]["A"], row[s]["B"]) for s in states})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
