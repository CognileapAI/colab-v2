"""온톨로지 회차 2단계 — 자료별 빈칸·후보·미등록 낱말 분석(오프라인).

입력: collect.py 가 만든 datasets.json. DB·모델·네트워크를 부르지 않는다.
출력: analysis.json — 자료마다
  · gaps       : 검색 근거 카드에 없는 핵심 칸(region·cadence·nativeResolutionM·platform·period)
  · candidates : 칸별 후보 값과 출처(등록 칸 선언 / 설명 문장 파서). 전부 **초안 후보**다 — 값 확정은 Ted 판정.
  · unknownTerms : 이름·설명에 나오지만 D9 사전·개념 어디에도 없는 낱말(에이전트가 동의어·관계 후보를 판단할 재료)

제품 코드를 재사용한다 — 설명 문장 파서는 core-api `search_evidence_conditions.parse`,
사전·개념은 `db/ai/seed/*.sql` 적재물(ai-service 어휘 오라클과 같은 로더). 같은 규칙으로 읽어야
회차 후보가 실제 검색과 어긋나지 않는다.

  services/core-api/.venv/bin/python analyze.py <datasets.json> --out <analysis.json>
종료코드: 0 · 1(입력 형식 불일치) · 78(실행 환경 부재).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services/core-api/src"))
sys.path.insert(0, str(ROOT / "services/ai-service/src"))

CORE_AXES = ("region", "cadence", "nativeResolutionM", "platform", "period")
# 등록 칸 → 근거 카드 값. 등록자가 올릴 때 선언한 값이라 「등록 선언」 출처로 적는다.
INTERVAL = {("분", 5): "5min", ("분", 10): "10min", ("분", 15): "15min", ("분", 60): "hourly",
            ("시", 1): "hourly", ("일", 1): "daily", ("일", 7): "weekly", ("월", 1): "monthly", ("년", 1): "yearly"}
PLATFORM = {"지상관측자료": "ground", "위성자료": "satellite", "재분석자료": "model", "수치모형자료": "model"}
STOP = set("자료 데이터 원자료 결과 변환 파일 제공 기준 단위 이상 이하 대한 관련 포함 경우 위한 통해 사용 연구 분석 "
           "the and of for from with data file files raw sample".split())


def _load_seed_helpers():
    """ai-service 어휘 오라클과 같은 적재물 로더를 쓴다(손으로 사전을 적지 않는다)."""
    p = ROOT / "services/ai-service/tests/test_practitioner_lexical.py"
    spec = importlib.util.spec_from_file_location("_lexical_oracle", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.SEED


def known_surfaces(seed) -> set[str]:
    out = set()
    for r in seed.get("d9_method_term", ()): out.add(r["term"])
    for r in seed.get("d9_topic_synonym", ()): out.update((r["synonym"], r["topic"]))
    for r in seed.get("d9_place_alias", ()): out.update((r["alias"], r["place_name"]))
    for r in seed.get("d9_concept", ()): out.add(r["label"])
    return {s.lower() for s in out if s}


# 한국어 낱말 끝의 조사·어미를 떼고 센다(형태소 분석기 없이 — 후보는 에이전트가 다시 본다).
JOSA = re.compile(r"(에서|으로|에게|까지|부터|이다|한다|하는|하고|했다|된|한|을|를|은|는|이|가|의|에|로|와|과|이며)$")
FUNCTION = set("에서 따른 대한 위한 통한 같은 있는 없는 되는 이런 그런 각각 모두 전부 해당 기존 이후 이전".split())


def tokens(text: str) -> list[str]:
    out = []
    for t in re.findall(r"[A-Za-z][A-Za-z0-9\-]{1,}|[가-힣]{2,}", text or ""):
        if re.match(r"[가-힣]", t):
            t = JOSA.sub("", t) if len(t) > 2 else t
            if len(t) < 2 or t in FUNCTION:
                continue
        out.append(t)
    return out


def interval_candidate(iv):
    if not iv:
        return None
    key = (iv.get("unit"), int(iv.get("value") or 0))
    return INTERVAL.get(key, f"unmapped:{iv.get('value')}{iv.get('unit')}")


def analyse(ds: dict, parse, known: set[str]) -> dict:
    ev = ds.get("evidence") or {}
    keys = set(ev.get("keys") or [])
    text = " ".join(x for x in (ds.get("name"), ds.get("summary"), ds.get("gridDescription")) if x)
    cands: dict[str, list[dict]] = {}

    def add(axis, value, source):
        if value is not None and value != "":
            cands.setdefault(axis, []).append({"value": value, "source": source})

    add("cadence", interval_candidate(ds.get("observationInterval")), "등록 칸 observation_interval(등록자 선언)")
    add("platform", PLATFORM.get(ds.get("dataType") or ""), f"등록 칸 data_type={ds.get('dataType')}")
    add("topic", ds.get("topic"), "등록 칸 topic")
    add("provider", ds.get("sourceLabel"), "등록 칸 source_label")
    parsed = parse(text) if text else {}
    for axis in ("region", "cadence", "period", "topic", "variable"):
        if parsed.get(axis):
            add(axis, parsed[axis], "설명 문장 파서(search_evidence_conditions.parse)")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(km|m)\b", text, re.I)
    if m:
        add("nativeResolutionM", float(m[1]) * (1000 if m[2].lower() == "km" else 1), "설명 문장 해상도 표기")
    unknown = sorted({t for t in tokens(text) if t.lower() not in known and t.lower() not in STOP})
    status = "no-evidence" if not ev.get("rows") else ("partial" if set(CORE_AXES) - keys else "covered")
    return {"id": ds["id"], "name": ds.get("name"), "uploadedAt": ds.get("uploadedAt"),
            "evidenceStatus": status, "evidenceRows": ev.get("rows", 0), "reviewedRows": ev.get("reviewed", 0),
            "gaps": [a for a in CORE_AXES if a not in keys],
            "candidates": cands, "unknownTerms": unknown,
            "fileExtensions": ds.get("fileExtensions") or {}}


def summary_md(out: dict) -> str:
    s = out["summary"]
    lines = [f"# 온톨로지 회차 요약 — 수집 {out.get('collectedAt')}", "",
             f"- 대상 자료 {s['datasets']}건 (지난 회차 이후: {out.get('since') or '전체'})",
             f"- 근거 카드 없음 {s['noEvidence']} · 일부 {s['partial']} · 핵심 칸 모두 있음 {s['covered']}", "",
             "## 자료별 빈칸과 후보 (후보는 전부 초안 — 값 확정은 Ted 판정)", "",
             "| 자료 | 상태 | 빈 칸 | 후보 |", "|---|---|---|---|"]
    for r in out["datasets"]:
        c = "; ".join(f"{k}={'/'.join(str(v['value']) for v in vs)}" for k, vs in r["candidates"].items())
        lines.append(f"| {r['name']} | {r['evidenceStatus']} | {', '.join(r['gaps']) or '─'} | {c or '─'} |")
    lines += ["", "## 사전에 없는 낱말 (빈도순 · 에이전트가 동의어·지명·관계 후보를 판단한다)", "",
              ", ".join(f"{t}({n})" for t, n in s["unknownTerms"]), ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("datasets", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--md", type=pathlib.Path, help="사람이 읽는 요약(summary.md)도 쓴다")
    a = ap.parse_args(argv)
    try:
        from colab_core.app.search_evidence_conditions import parse
    except Exception as e:  # noqa: BLE001
        print(f"준비 실패: core-api 모듈을 못 불렀다 ({e}) — services/core-api/.venv/bin/python 으로 실행한다",
              file=sys.stderr)
        return 78
    data = json.loads(a.datasets.read_text(encoding="utf-8"))
    if data.get("schema") != "colab-ontology-round-collect/1":
        print("판정 실패: collect.py 산출물이 아니다", file=sys.stderr)
        return 1
    known = known_surfaces(_load_seed_helpers())
    rows = [analyse(d, parse, known) for d in data["datasets"]]
    term_count: dict[str, int] = {}
    for r in rows:
        for t in r["unknownTerms"]:
            term_count[t] = term_count.get(t, 0) + 1
    out = {"schema": "colab-ontology-round-analysis/1", "input": str(a.datasets),
           "collectedAt": data.get("collectedAt"), "since": data.get("since"),
           "summary": {"datasets": len(rows),
                       "noEvidence": sum(r["evidenceStatus"] == "no-evidence" for r in rows),
                       "partial": sum(r["evidenceStatus"] == "partial" for r in rows),
                       "covered": sum(r["evidenceStatus"] == "covered" for r in rows),
                       "unknownTerms": sorted(term_count.items(), key=lambda x: (-x[1], x[0]))[:60]},
           "datasets": rows}
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if a.md:
        a.md.write_text(summary_md(out), encoding="utf-8")
    print(json.dumps(out["summary"] | {"unknownTerms": len(term_count)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
