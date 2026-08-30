#!/usr/bin/env python3
"""실데이터 포맷 완주 커버리지 — **판정부**.

`S3`(실데이터 E2E) 완료 정의 축자 두 줄을 기계가 읽는 자리로 옮긴 것이다.
  · 「**4종 각각 최소 1건**이 **시각화 화면에 그려지고**」  → 포맷별 통과 케이스 ≥ 1
  · 「실패 파일은 목록으로 남긴다(**조용히 건너뛰지 않는다**)」 → 실패·건너뜀을 이름으로 찍는다

⚠ **이 판정부는 「그려졌다」를 스스로 정의하지 않는다.** 그 정의는 시험 쪽에 있다
(`services/viz-render/tests/test_e2e_real.py::_assert_drawn` — 경계·범례·타일의
**불투명 픽셀**까지 본다). 여기서 다시 정의하면 기준이 두 곳으로 갈린다.

세는 단위 = **포맷 표식이 붙은 시험 케이스 1건.** 파일 수로 세지 않는다 —
한 케이스가 원천 파일 여럿을 읽는 자리가 있어 파일 수와 케이스 수는 애초에 같지 않다.

세 상태 (`CLAUDE.md §4`)
  · 필수 포맷에 케이스가 있으면 → 검사한다(하나라도 실패·건너뜀이면 red)
  · 필수 포맷이 `[면제]` 에 이름으로 적혀 있으면 → **건수를 드러낸 채** 통과
  · 아무 말도 없으면 → red. **총 케이스 0건도 red 다**

⚠ **총 0건이 red 인 이유** — 이 자리의 자연스러운 대상 수는 원천이 안 붙은 환경에서
**0** 이다. 0 을 통과로 세면 게이트가 아무것도 안 보면서 green 을 찍는다.
"""
from __future__ import annotations

import argparse
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

PROP = "실데이터포맷"


def _die(msg: str) -> None:
    print(f"::error::e2e-format-coverage red — {msg}")
    sys.exit(1)


def _load_config(path: Path) -> tuple[list[str], list[str], str]:
    if not path.is_file():
        _die(f"선언 파일이 없다: {path}. 「선언이 없다」와 「필수가 0건이다」는 다르다.")
    try:
        doc = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _die(f"선언 파일을 읽지 못했다: {exc}")
    req = doc.get("required")
    if not isinstance(req, dict) or "formats" not in req:
        _die("선언 파일에 `[required] formats` 항목이 없다. 없는 것을 0건으로 세지 않는다.")
    formats = req["formats"]
    if not isinstance(formats, list) or not all(isinstance(x, str) for x in formats):
        _die("`[required] formats` 는 포맷 이름의 목록이어야 한다.")
    if not formats:
        _die("`[required] formats` 가 비어 있다 — 필수 0건은 검사가 아니다.")
    ex = doc.get("면제")
    if not isinstance(ex, dict) or "formats" not in ex:
        _die("선언 파일에 `[면제] formats` 항목이 없다. 「없는 것」을 「0건」으로 세지 않는다.")
    exempt = ex["formats"]
    if not isinstance(exempt, list) or not all(isinstance(x, str) for x in exempt):
        _die("`[면제] formats` 는 포맷 이름의 목록이어야 한다.")
    return list(formats), list(exempt), str(ex.get("reason", ""))


def _cases(xml: Path) -> list[tuple[str, str, str]]:
    """(포맷, 케이스 이름, 결과) — 결과는 `통과`·`실패`·`건너뜀`."""
    if not xml.is_file():
        _die(f"시험 리포트가 없다: {xml}. 못 돈 것을 통과로 세지 않는다.")
    try:
        root = ET.parse(xml).getroot()
    except Exception as exc:
        _die(f"시험 리포트를 읽지 못했다: {exc}")
    out: list[tuple[str, str, str]] = []
    for tc in root.iter("testcase"):
        fmt = None
        for prop in tc.iter("property"):
            if prop.get("name") == PROP:
                fmt = prop.get("value")
        if fmt is None:
            continue
        name = f"{tc.get('classname', '')}::{tc.get('name', '')}".lstrip(":")
        if tc.find("skipped") is not None:
            res = "건너뜀"
        elif tc.find("failure") is not None or tc.find("error") is not None:
            res = "실패"
        else:
            res = "통과"
        out.append((fmt, name, res))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    args = ap.parse_args()

    required, exempt, reason = _load_config(args.config)
    cases = _cases(args.junit)

    total = len(cases)
    print(f"실데이터 포맷 완주 — 필수 {len(required)}종 · 표식 붙은 케이스 {total}건 "
          f"· 면제 {len(exempt)}종")

    bad = False

    # ⚠ 총 0건 — 이 게이트의 존재 이유다. 0 을 통과로 세면 아무것도 안 본다.
    if total == 0:
        print("::error::e2e-format-coverage red — 포맷 표식이 붙은 케이스 0건. "
              "원천이 안 붙었거나 표식이 지워졌다. 대상 0건은 통과가 아니다.")
        bad = True

    unknown = sorted({f for f, _, _ in cases} - set(required))
    if unknown:
        print(f"::error::e2e-format-coverage red — 선언에 없는 포맷 표식: {', '.join(unknown)}. "
              "목록이 실물보다 낡았다 — 정본 목록을 먼저 고친다.")
        bad = True

    for fmt in required:
        mine = [(n, r) for f, n, r in cases if f == fmt]
        passed = [n for n, r in mine if r == "통과"]
        broken = [(n, r) for n, r in mine if r != "통과"]
        if fmt in exempt:
            # 면제는 검사 면제가 아니라 **선언**이다 — 건수를 드러낸 채 넘어간다.
            print(f"  · {fmt} — 면제 선언(사유: {reason}) · 관측 케이스 {len(mine)}건")
            continue
        if broken:
            for n, r in broken:
                print(f"::error::e2e-format-coverage red — {fmt} 케이스 {r}: {n}")
            bad = True
        if not passed:
            print(f"::error::e2e-format-coverage red — {fmt} 의 통과 케이스 0건. "
                  "「최소 1건이 그려진다」가 충족되지 않았다.")
            bad = True
        else:
            print(f"  · {fmt} — 통과 {len(passed)} / 관측 {len(mine)}")

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
