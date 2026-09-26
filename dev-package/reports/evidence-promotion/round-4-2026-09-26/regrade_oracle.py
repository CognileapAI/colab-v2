"""4회차 — 1회차 승격(dev 반영 완료) 뒤의 실상태로 오라클을 다시 매기고, 「1시간 이하」 deferred 를 닫는다.

오라클 자신의 규칙(`modes`)만 쓴다. `full` = 정본이 고정한 사실만으로 조건 충족 판정이 선다.
  · 1회차 승격 3규칙(platform-from-instrument · direct-observation-from-level · native-resolution-carried)은
    dev 에 reviewed 로 실렸다(`dev-package/intent/2026-09-21-evidence-promotion.md` 「dev 반영 완료
    2026-09-25T23:52Z」). 그 규칙에 기대던 measure_only probe 는 이제 초안 값이 아니다 — 판정 probe 로 옮긴다.
  · 아직 초안(지역 규칙 `region-from-lineage-parent` 등)에 기대는 probe 는 measure_only 에 남긴다.
  · 판정 probe 가 없던 blocked_draft 3사례(PC-1-2 · 1-6 · 2-2)는 옮긴 probe 로 판정이 서므로 full 이다.
  · PC-1-3 · PC-2-3 은 2회차가 platform 초안 **때문에** partial 로 내린 사례다(deferred 축자). 그 사유가 풀려
    1회차 등급(full)으로 되돌린다. 지역 probe 는 초안 대기로 measure_only 에 남는다.
  · PC-1-4 「5 km 이하」는 seq 3 해상도(native-resolution-carried)가 승격돼 1회차 기대(supersedes)가 판정 기대다.
옮기기 전 확인 — 4회차 측정(`measurement-code/draft-contribution.json`)에서 옮길 probe 가 **초안 제외(reviewed
만)로 green** 이어야 한다. 아니면 옮기지 않고 멈춘다.

  python3 dev-package/reports/evidence-promotion/round-4-2026-09-26/regrade_oracle.py <측정 json>
멱등하다 — 이미 옮긴 뒤에 다시 돌리면 바꿀 것이 없다.
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

PROMOTED = ("platform-from-instrument", "direct-observation-from-level", "native-resolution-carried")
#: 옮길 measure_only probe — 사례별 이름. 승격 3규칙(platform · directObservation · seq 3 해상도)에만 기댄다.
MOVE = {
    "PC-1-2": ["지상(레이더·지상격자·관측소)", "위성", "모형·재분석"],
    "PC-1-3": ["레이더 기간 전체를 덮는 지상 자료", "식생 예측 기간을 덮는 모형 자료"],
    "PC-1-4": ["5 km 이하 원 관측 해상도 — 1회차 기대(seq 3 포함)"],
    "PC-1-6": ["직접 관측", "직접 관측이 아닌 것(예측·재분석·지수)"],
    "PC-2-2": ["위성 + 2 km 이하", "지상 + 1 km 이하"],
    "PC-2-3": ["2022년을 덮는 모형 자료"],
}
TO_FULL = ("PC-1-2", "PC-1-6", "PC-2-2")
#: 2회차(d533d374)가 platform 초안 때문에 full → partial 로 내린 두 사례. 그 사례 deferred 가 사유를 축자로 적었다 —
#: 「platform 으로 지상·모형을 가르던 축 — … 기간 축만 남겨 partial 로 내렸다」(PC-1-3) ·
#: 「platform 은 규칙 추론값이라 … 연도 축만 남겨 partial 로 내렸다」(PC-2-3). 1회차 등급은 같은 probe 로 full 이었다
#: (`git show d533d374^:eval/k4-search/practitioner-conditions.json`). 사유가 풀렸으므로 1회차 등급으로 되돌린다.
#: 남은 deferred(지역 초안 · NWP 원천 0건 · 기간 교집합)는 1회차 full 때도 있던 것이다.
BACK_TO_FULL = ("PC-1-3", "PC-2-3")
BACK_NOTE = ("2026-09-26 4회차 재채점 — 2회차가 platform 초안 때문에 partial 로 내렸던 사례다(그 deferred 축자 「… partial 로 내렸다」). platform 이 1회차에 승격돼 1회차 probe 가 reviewed 만으로 green 이라 1회차 등급(full)으로 되돌린다. 지역 probe 는 초안 승격 대기로 measure_only 에 남는다(PC-2-4 · 2-7 과 같은 모양)")
MOVED_NOTE = ("2026-09-26 4회차 재채점 — 1회차 승격(platform-from-instrument · direct-observation-from-level · "
              "native-resolution-carried, dev 반영 2026-09-25T23:52Z) 뒤 reviewed 만으로 green 이라 measure_only 에서 "
              "판정 probe 로 옮겼다(intent 2026-09-26-cadence-range-predicate)")
REGRADE_NOTE = ("2026-09-26 4회차 재채점 — blocked_draft 사유였던 규칙 추론값이 1회차에 승격돼 dev 에 reviewed 로 실렸다. "
                "되살린 1회차 probe 가 reviewed 만으로 green 이라 full 이다(오라클 modes.full)")
#: 닫는 deferred — 문장에 이 표지가 있으면 뺀다.
CLOSE_DEFERRED = {
    "PC-1-2": ["platform 승격"],
    "PC-1-3": ["platform 으로 지상·모형을 가르던 축"],
    "PC-1-4": ["「1시간 이하」 범위 술어", "hsr_sample(seq 3)의 공간해상도"],
    "PC-1-6": ["directObservation 승격"],
    "PC-2-2": ["platform 승격"],
    "PC-2-3": ["platform 은 규칙 추론값이라"],
    "PC-2-4": ["「1시간 이하」 범위 술어"],
}


def _as_probe(probe: dict) -> dict:
    moved = dict((k, v) for k, v in probe.items() if k not in ("mode", "reason", "supersedes", "supersedeReason"))
    moved["regradeNote"] = MOVED_NOTE
    return moved


def main() -> int:
    measured = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    reviewed_green = set(measured["greenWithoutAnyDraft"]["A"])
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    changed = []
    for case in oracle["cases"]:
        cid = case["id"]
        restored = case.get("measureOnlyProbes") or []
        wanted = MOVE.get(cid, [])
        keep, move = [], []
        for index, probe in enumerate(restored, 1):
            if probe["name"] in wanted:
                if f"{cid}#m{index}" not in reviewed_green:
                    raise SystemExit(f"{cid}#m{index} {probe['name']} 는 reviewed 만으로 green 이 아니다 — 옮기지 않는다")
                move.append(probe)
            else:
                keep.append(probe)
        for probe in move:
            superseded = probe.get("supersedes")
            converted = _as_probe(probe)
            if superseded:
                slot = next(i for i, p in enumerate(case["probes"]) if p["name"] == superseded)
                converted["name"] = superseded
                converted["regradeNote"] = MOVED_NOTE + " · 1회차 기대(seq 3 포함)가 이 probe 의 기대를 대신한다"
                case["probes"][slot] = converted
            else:
                case["probes"].append(converted)
            changed.append(f"{cid}: {probe['name']}")
        if move:
            if keep:
                case["measureOnlyProbes"] = keep
            else:
                case.pop("measureOnlyProbes")
        if cid in TO_FULL and case["mode"] == "blocked_draft":
            case["mode"] = "full"
            case.pop("reason", None)
            case["regradeNote"] = REGRADE_NOTE
            changed.append(f"{cid}: blocked_draft → full")
        if cid in BACK_TO_FULL and case["mode"] == "partial":
            case["mode"] = "full"
            case["regradeNote"] = BACK_NOTE
            changed.append(f"{cid}: partial → full")
        marks = CLOSE_DEFERRED.get(cid, [])
        if marks and "deferred" in case:
            before = len(case["deferred"])
            case["deferred"] = [d for d in case["deferred"] if not any(m in d for m in marks)]
            if len(case["deferred"]) != before:
                changed.append(f"{cid}: deferred {before - len(case['deferred'])} 닫음")
    missing = [(cid, n) for cid, names in MOVE.items() for n in names
               if not any(p.get("name") == n or p.get("regradeNote", "").startswith("2026-09-26 4회차")
                          for c in oracle["cases"] if c["id"] == cid for p in c["probes"])]
    if missing:
        raise SystemExit(f"옮길 probe 를 찾지 못했다: {missing}")
    oracle["regradeNote"] = ("2026-09-26 4회차 재채점(intent 2026-09-26-cadence-range-predicate) — 1회차 승격 3규칙이 dev 에 "
                             "reviewed 로 실린 실상태로 다시 매겼다. 조건 검색 pytest 의 일회용 DB 도 같은 승격을 겹쳐 싣는다"
                             "(services/core-api/tests/test_practitioner_conditions.py DEV_PROMOTED_RULES).")
    ORACLE.write_text(oracle_format.dumps(oracle), encoding="utf-8")
    modes = [c["mode"] for c in oracle["cases"]]
    print(json.dumps({"changed": changed, "modes": {m: modes.count(m) for m in dict.fromkeys(modes)},
                      "measureOnly": sum(len(c.get("measureOnlyProbes") or []) for c in oracle["cases"])},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
