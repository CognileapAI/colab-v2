"""4회차 — 「1시간 이하」 주기 범위 probe 를 **제품 코드 그대로** 두 경로에서 잰다(반사실 패치 없음).

intent `dev-package/intent/2026-09-26-cadence-range-predicate.md`. 경로 1 = `d3_client_search.candidates`,
경로 2 = `search_evidence_conditions`(파일 근거 후보). 둘 다 `kernel/cadence_scope.py` 를 읽는다.
`measure_draft_contribution.py` 의 평가기(`Evaluator`)를 불러 `--seed-dev-like` 로 시드된 일회용 DB 에서
상태 둘을 한 트랜잭션 안에 겹쳐 보고 rollback 한다. 새 판정 논리는 없다. 모델 호출 0.

상태
  reviewed    초안 전부 뺌(= dev 에 이 payload 를 실었을 때 조건 검색이 보는 것)
  all_drafts  초안 전부 겹침

녹화만 한 대조 질의(probe 아님)의 경로 2 해석 조건도 적는다 — 「30분 이내」(PB-CADENCE-3) ·
「한반도 15분 주기」(PB-REGION-4, 경로 2 가 「15분」을 주기로 읽는지).

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
CONTROL_QUERIES = ("PB-CADENCE-3", "PB-REGION-4")


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
    names = {row["seq"]: row["name"] for row in payload["datasets"]}
    facts = tool.draft_facts(payload)
    db = tool._db()
    _factory, session = tool._open(db, args.database_url)
    try:
        cases = tool.load_cases()
        ev = tool.Evaluator(db, session, payload, facts, cases)
        states = {"reviewed": frozenset(f["fact_id"] for f in facts), "all_drafts": frozenset()}
        probes = [p for p in cases["probes"] if "maxCadenceSeconds" in p["conditions"]]
        if len(probes) != 5:
            print(f"준비 실패: 「1시간 이하」 probe 5건이 아니다 — {[p['id'] for p in probes]}", file=sys.stderr)
            return 78
        rows = {p["id"]: {"id": p["id"], "name": p["name"], "conditions": p["conditions"],
                          "expectSeq": p["expectSeq"], "forbidSeq": p["forbidSeq"],
                          "pathB": p.get("pathB", {}).get("query")} for p in probes}
        golden = {}
        region4: dict = dict()
        for name, removed in states.items():
            out = ev.evaluate(removed)
            golden[name] = {g: sum(v["green"] for v in out[g].values()) for g in ("A", "B")}
            reviewed = db.d3_search_evidence.read_reviewed(session, include_source_text=False)
            cache: dict = {}
            for p in probes:
                a_seqs = sorted(ev._seqs(db.d3_client_search.candidates(session, dict(p["conditions"]))[0]))
                cell = {"A": out["A"][p["id"]]["green"], "A_seqs": a_seqs,
                        "A_datasets": [f"{s} {names.get(s)}" for s in a_seqs]}
                if "pathB" in p:
                    b = ev.path_b_probe(p, reviewed, cache)
                    cell.update(B=b["green"], B_evidenceSeqs=b["evidenceSeqs"], B_search=b["greenSearch"],
                                B_criteria=b["criteria"])
                rows[p["id"]][name] = cell
            # 「15분」을 경로 2 가 주기로 읽게 된 뒤의 PC-2-4 「한반도 15분 주기」(PB-REGION-4) — 3회차 red 의 원인이었다.
            for p in [q for q in cases["probes"] if q.get("pathB", dict()).get("id") == "PB-REGION-4"]:
                b = ev.path_b_probe(p, reviewed, cache)
                region4.setdefault(p["id"], dict(name=p["name"], expectSeq=p["expectSeq"], forbidSeq=p["forbidSeq"]))[name] = dict(
                    B=b["green"], B_evidenceSeqs=b["evidenceSeqs"], B_search=b["greenSearch"], B_criteria=b["criteria"])
        controls = {pid: {"query": cases["interpret"][pid]["query"],
                         "criteria": {k: v for k, v in ev.sec.parse(cases["interpret"][pid]["query"]).items()
                                      if v is not False}} for pid in CONTROL_QUERIES}
        counts = {name: {"A": sum(r[name]["A"] for r in rows.values()),
                         "B": sum(r[name].get("B", False) for r in rows.values()),
                         "B_total": sum("B" in r[name] for r in rows.values())} for name in states}
        result = {"schema": "colab-cadence-probe-states/1", "payload": str(args.payload),
                  "payloadSha256": tool.sha256_file(args.payload), "counterfactual": None,
                  "note": ("반사실 패치 없음 — 제품 코드(kernel/cadence_scope.py)로 잰다. 경로 2 green = 파일 근거 후보 "
                           "(search_evidence_conditions.candidates 포함 집합); B_search = 전체 검색 결과 기준 참고 열. "
                           "경로 2 해석 = interpret-fixture.json 규칙 기반 녹화(모델 호출 0)."),
                  "cadenceProbes": list(rows.values()), "greenCounts": counts, "controls": controls,
                  "fifteenMinutePathB": region4,
                  "goldenGreen": golden}
    finally:
        session.rollback()
        session.close()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"greenCounts": counts, "goldenGreen": golden}, ensure_ascii=False))
    for row in rows.values():
        print(row["id"], row["reviewed"]["A_seqs"], row["reviewed"].get("B_evidenceSeqs"),
              {s: (row[s]["A"], row[s].get("B")) for s in states})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
