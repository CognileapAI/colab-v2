"""2회차 지역 — probe 별 green 상태표(사례 점수판의 재료)와 「한반도⊃남한」 반사실 대조.

`measure_draft_contribution.py` 의 **같은 평가기**(`Evaluator`)를 그대로 불러, 이미 `--seed-dev-like` 로
시드된 일회용 DB 에서 상태 몇 개를 한 트랜잭션 안에 겹쳐 보고 rollback 한다. 새 판정 논리는 없다.

상태
  reviewed      초안 전부 뺌(= dev 에 이 payload 를 실었을 때 조건 검색이 보는 것)
  all_drafts    초안 전부 겹침
  region_drafts 지역 초안 규칙만 겹침(region-from-lineage-parent · region-from-lineage-sibling ·
                bbox-korea-peninsula · region-from-registration-note)
  cf_*          **반사실** — 경로 1 region 술어의 표기 사전(`SEMANTICS['regions']['korean_peninsula']`)에
                개념 그래프 한 홉(한반도 → 남한 · 충청권 · Korea)을 **이 프로세스 안에서만** 더했을 때.
                제품 코드·계약은 고치지 않는다. 판정 근거가 아니라 「그래프가 조건 검색에 닿으면」의 크기다.

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
#: 개념 그래프 한 홉 — `db/ai/seed/*.sql` 의 「한반도」 하위(`안에 있다`)와 같은 말(`같은 말이다`).
GRAPH_ONE_HOP = ["남한", "충청권", "Korea"]


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
    factory, session = tool._open(db, args.database_url)
    try:
        cases = tool.load_cases()
        ev = tool.Evaluator(db, session, payload, facts, cases)
        everything = frozenset(f["fact_id"] for f in facts)
        non_region = frozenset(f["fact_id"] for f in facts if f["rule"] not in REGION_RULES)
        states = {"reviewed": everything, "all_drafts": frozenset(), "region_drafts": non_region}
        out = {}
        for name, removed in states.items():
            out[name] = ev.evaluate(removed)
        from colab_core.kernel.search_semantics import SEMANTICS  # noqa: PLC0415 — 같은 dict 객체
        original = list(SEMANTICS["regions"]["korean_peninsula"])
        try:
            SEMANTICS["regions"]["korean_peninsula"] = original + GRAPH_ONE_HOP
            for name, removed in states.items():
                out["cf_" + name] = ev.evaluate(removed)
            # 반사실 규칙표 — 지역 초안만 대상으로 같은 `measure()`(규칙 단위·사실 단위 빼기)를 돈다.
            region_facts = [f for f in facts if f["rule"] in REGION_RULES]
            cf_table = tool.measure(ev.evaluate, region_facts, list(REGION_RULES), ev.case_reads)
        finally:
            SEMANTICS["regions"]["korean_peninsula"] = original
        probes = {p["id"]: p for p in cases["probes"]}
        table = []
        for pid, probe in probes.items():
            row = {"id": pid, "name": probe["name"], "mode": probe.get("mode", "probe"),
                   "region": "region" in probe["conditions"], "conditions": probe["conditions"]}
            for name in out:
                row[name] = out[name]["A"][pid]["green"]
            table.append(row)
        golden = []
        for cid in sorted(out["reviewed"]["B"]):
            golden.append({"id": cid, **{name: out[name]["B"][cid]["green"] for name in out}})
        result = {"schema": "colab-region-probe-states/1", "payload": str(args.payload),
                  "payloadSha256": tool.sha256_file(args.payload), "graphOneHop": GRAPH_ONE_HOP,
                  "regionRules": REGION_RULES, "probesA": table, "goldenB": golden,
                  "counterfactualRules": [
                      {k: r[k] for k in ("rule", "facts", "contribution_A", "reversal_A", "flipped_case_ids_A",
                                         "contribution_B", "reversal_B", "measured_A", "measured_B")}
                      for r in cf_table["rules"]],
                  "counterfactualNote": ("반사실 — 판정 근거가 아니다(결정 5 는 제품 경로의 기여만 센다). 경로 1 region "
                                         "표기 사전에 그래프 한 홉을 더했을 때 지역 초안 규칙이 낼 기여의 크기다."),
                  "greenCounts": {name: {g: sum(v["green"] for v in out[name][g].values())
                                         for g in ("A", "B")} for name in out}}
    finally:
        session.rollback()
        session.close()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result["greenCounts"], ensure_ascii=False))
    for row in table:
        if row["region"]:
            print(row["id"], {k: row[k] for k in out})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
