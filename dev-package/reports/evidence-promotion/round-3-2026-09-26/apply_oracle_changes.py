"""3회차 측정 결과를 오라클(`eval/k4-search/practitioner-conditions.json`)에 옮긴다 — 줄 단위(서식 보존).

규칙(오케스트레이터 지시 · intent `2026-09-26-region-containment-expansion.md` 완료 정의 ⑤):
  「한반도」 measure_only probe 는 **경로 1 · reviewed 만으로 green 인 것만** `probes` 로 옮긴다.
  3회차 측정(`region-probe-states.json` · 반사실 패치 없음)에서 그것은 PC-1-4#m2(seq 1) 하나다.
  나머지 4건(PC-1-3#m3 · PC-2-3#m2 · PC-2-4#m1 · PC-2-7#m1)은 seq 3·4·5 남한이 초안
  (`region-from-lineage-parent`)이라 measure_only 로 남는다.
  남는 probe 의 regionNote 와 사례 deferred 의 region 문장은 「표기 일치라 펴지 않는다」에서
  「포함 관계는 열렸고 남은 간극은 초안 승격」으로 바꾼다.

  python3 dev-package/reports/evidence-promotion/round-3-2026-09-26/apply_oracle_changes.py
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
ORACLE = REPO / "eval" / "k4-search" / "practitioner-conditions.json"
STATES = HERE / "region-probe-states.json"

MOVE = {"PC-1-4": "한반도 + 5분 주기"}
REGION_NOTE = ("2026-09-26 Ted 판정 「자료 지역 확정」 — 1 「남한⊂한반도 관계로 연결」. 조건 검색은 이제 한반도 → 남한·충청권 "
               "한 단계를 편다(intent 2026-09-26-region-containment-expansion · contracts/search/semantics.json regionWithin). "
               "남은 간극은 seq 3·4·5 의 「남한」이 초안(region-from-lineage-parent)이라 reviewed 만 읽는 조건 검색에 서지 않는 것 — "
               "승격 뒤 green 을 기대한다")
MOVED_NOTE = ("2026-09-26 3회차 — 지역 포함 관계(intent 2026-09-26-region-containment-expansion)로 reviewed seq 1(남한)이 "
              "한반도 조건에 맞아 measure_only 에서 판정 probe 로 옮겼다(3회차 측정 경로 1 reviewed green)")
DEFERRED_OLD_MARK = "조건 검색 region 은 표기 일치라"
DEFERRED = {
    "PC-1-3": ("region 술어 — 2026-09-26 정본이 seq 1·2·19·20=남한 · 6=한반도로 고정했고(Ted 판정 「자료 지역 확정」) 조건 검색이 "
               "한반도 → 남한 한 단계를 편다(3회차). 남은 간극은 seq 3·4·5 남한이 초안이라는 것 — measureOnlyProbes 로 잰다"),
    "PC-2-4": ("region 한반도 — 조건 검색이 한반도 → 남한 한 단계를 편다(3회차 · intent 2026-09-26-region-containment-expansion). "
               "seq 4 남한이 초안이라 이 probe 는 승격 뒤 green 이다 — measureOnlyProbes 로 잰다"),
}


def main() -> int:
    states = json.loads(STATES.read_text(encoding="utf-8"))
    reviewed_green = {r["name"] for r in states["regionProbes"] if r["reviewed"]["A"]}
    for case_id, name in MOVE.items():
        if name not in reviewed_green:
            raise SystemExit(f"{case_id} {name!r} 는 3회차 경로 1 reviewed 에서 green 이 아니다 — 옮기지 않는다")
    lines = ORACLE.read_text(encoding="utf-8").split("\n")
    out, case_id, moved_line, probes_end = [], None, {}, {}
    for line in lines:
        stripped = line.strip()
        indent = line[:len(line) - len(line.lstrip())]
        if stripped.startswith('"id": "PC-'):
            case_id = stripped.split('"')[3]
        if stripped.startswith("{") and '"korean_peninsula"' in stripped:
            comma = stripped.endswith(",")
            probe = json.loads(stripped.rstrip(","))
            if MOVE.get(case_id) == probe["name"] and probe.get("mode") == "measure_only":
                moved = {k: v for k, v in probe.items() if k not in ("mode", "reason", "regionNote")}
                moved["regionNote"] = MOVED_NOTE
                moved_line[case_id] = json.dumps(moved, ensure_ascii=False)
                # 앞 줄의 쉼표를 정리한다(이 줄이 목록의 마지막이었다면).
                if not comma and out and out[-1].rstrip().endswith(","):
                    out[-1] = out[-1].rstrip()[:-1]
                continue
            probe["regionNote"] = REGION_NOTE
            line = indent + json.dumps(probe, ensure_ascii=False) + ("," if comma else "")
        if stripped.startswith('"deferred":') and case_id in DEFERRED:
            body = json.loads("{" + stripped.rstrip(",") + "}")
            items = [DEFERRED[case_id] if DEFERRED_OLD_MARK in d else d for d in body["deferred"]]
            line = indent + '"deferred": ' + json.dumps(items, ensure_ascii=False) + ("," if stripped.endswith(",") else "")
        out.append(line)
    # 옮긴 probe 를 그 사례 probes 목록 끝에 붙인다.
    final, case_id, in_probes = [], None, False
    for line in out:
        stripped = line.strip()
        if stripped.startswith('"id": "PC-'):
            case_id = stripped.split('"')[3]
        if stripped.startswith('"probes": ['):
            in_probes = True
        if in_probes and stripped.startswith("]") and case_id in moved_line:
            if final and not final[-1].rstrip().endswith(","):
                final[-1] = final[-1] + ","
            indent = final[-1][:len(final[-1]) - len(final[-1].lstrip())]
            final.append(indent + moved_line.pop(case_id))
            in_probes = False
        elif in_probes and stripped.startswith("]"):
            in_probes = False
        final.append(line)
    if moved_line:
        raise SystemExit(f"옮길 자리를 찾지 못했다: {list(moved_line)}")
    ORACLE.write_text("\n".join(final), encoding="utf-8")
    json.loads(ORACLE.read_text(encoding="utf-8"))
    print("moved", list(MOVE), "· regionNote 갱신 · deferred 갱신", list(DEFERRED))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
