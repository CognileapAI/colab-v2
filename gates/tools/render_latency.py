#!/usr/bin/env python3
"""미리보기 렌더 성능 합격선 — **판정부**.

`PLAN-SoT §9 〈233〉`(정본 `Policy_데이터셋_상세` v2.6 `§8` 조건 ⑺)이 못 박은 두 눈금을
기계가 읽는 자리로 옮긴 것이다.
  · **p95 ≤ 합격선** — 표본의 95 백분위가 눈금 안이다
  · **모든 표본 ≤ 상한** — 하나라도 넘으면 그 건은 실패다

⚠ **이 판정부는 「몇 초가 걸렸다」를 스스로 재지 않는다.** 재는 것은 시험 쪽이고
(`services/viz-render/tests/test_perf_render_latency.py`), 여기는 그 초를 눈금과 대는 일만 한다.
양쪽에서 재면 기준이 두 곳으로 갈린다.

세는 단위 = **`렌더초` 속성이 붙은 시험 케이스 1건.**

세 상태 (`CLAUDE.md §4`)
  · 표본이 있으면 → 판정한다
  · **표본 0건 → red.** 이 자리의 자연스러운 대상 수는 원천이 안 붙은 환경에서 0 이다
  · 선언(눈금)이 없으면 → red. 「선언이 없다」와 「0 초다」는 다르다

⚠ **실패·건너뛴 케이스도 red 다** — 그리지 못한 것은 시간이 짧다. 빠르다고 세지 않는다.
"""
from __future__ import annotations

import argparse
import math
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

SEC = "렌더초"
FMT = "렌더포맷"
BYTES = "렌더바이트"


def _die(msg: str) -> None:
    print(f"::error::render-latency red — {msg}")
    sys.exit(1)


def _load(path: Path) -> dict:
    if not path.is_file():
        _die(f"선언 파일이 없다: {path}. 「선언이 없다」와 「0 초다」는 다르다.")
    try:
        doc = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        _die(f"선언 파일을 읽지 못했다: {exc}")
    bar = doc.get("합격선")
    if not isinstance(bar, dict):
        _die("선언 파일에 `[합격선]` 절이 없다. 없는 것을 통과로 세지 않는다.")
    need = ("미리보기_p95_초", "미리보기_상한_초", "최소_표본", "최소_포맷")
    for k in need:
        if k not in bar:
            _die(f"`[합격선]` 에 `{k}` 가 없다. 눈금이 빠진 채로 통과를 찍지 않는다.")
        if not isinstance(bar[k], (int, float)) or bar[k] <= 0:
            _die(f"`[합격선] {k}` 는 0 보다 큰 수여야 한다 — 지금 값: {bar[k]!r}")
    if bar["미리보기_p95_초"] > bar["미리보기_상한_초"]:
        _die("`미리보기_p95_초` 가 `미리보기_상한_초` 보다 크다 — 눈금이 뒤집혔다.")
    return bar


def _cases(xml: Path) -> list[tuple[str, str, float | None, int | None, str]]:
    """(포맷, 케이스 이름, 초, 바이트, 결과)"""
    if not xml.is_file():
        _die(f"시험 리포트가 없다: {xml}. 못 돈 것을 통과로 세지 않는다.")
    try:
        root = ET.parse(xml).getroot()
    except Exception as exc:  # noqa: BLE001
        _die(f"시험 리포트를 읽지 못했다: {exc}")
    out = []
    for tc in root.iter("testcase"):
        props = {p.get("name"): p.get("value") for p in tc.iter("property")}
        if SEC not in props and FMT not in props:
            continue
        name = f"{tc.get('classname', '')}::{tc.get('name', '')}".lstrip(":")
        if tc.find("skipped") is not None:
            res = "건너뜀"
        elif tc.find("failure") is not None or tc.find("error") is not None:
            res = "실패"
        else:
            res = "통과"
        sec: float | None
        try:
            sec = float(props[SEC]) if props.get(SEC) is not None else None
        except ValueError:
            sec = None
        try:
            by = int(props[BYTES]) if props.get(BYTES) is not None else None
        except ValueError:
            by = None
        out.append((props.get(FMT) or "[포맷 미표기]", name, sec, by, res))
    return out


def _p95(sorted_secs: list[float]) -> float:
    """최근접 순위법 — 표본이 적을 때 보간은 없는 정밀도를 지어낸다."""
    k = max(1, math.ceil(0.95 * len(sorted_secs)))
    return sorted_secs[k - 1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    args = ap.parse_args()

    bar = _load(args.config)
    cases = _cases(args.junit)
    p95_bar = float(bar["미리보기_p95_초"])
    cap = float(bar["미리보기_상한_초"])
    min_n = int(bar["최소_표본"])
    min_f = int(bar["최소_포맷"])

    print(f"미리보기 렌더 성능 — 눈금 p95 {p95_bar:g}초 · 상한 {cap:g}초 "
          f"· 최소 표본 {min_n} · 최소 포맷 {min_f}")

    bad = False

    broken = [(n, r) for _, n, _, _, r in cases if r != "통과"]
    for n, r in broken:
        print(f"::error::render-latency red — 케이스 {r}: {n}. "
              "그리지 못한 것은 시간이 짧다 — 빠르다고 세지 않는다.")
        bad = True

    good = [(f, n, s, b) for f, n, s, b, r in cases if r == "통과"]
    missing = [n for f, n, s, b in good if s is None]
    for n in missing:
        print(f"::error::render-latency red — `{SEC}` 속성이 없는 통과 케이스: {n}. "
              "재지 않은 것을 통과로 세지 않는다.")
        bad = True

    timed = [(f, n, s, b) for f, n, s, b in good if s is not None]
    n_total = len(timed)
    formats = sorted({f for f, _, _, _ in timed})

    # ⚠ 표본 0건 — 이 게이트의 존재 이유다.
    if n_total == 0:
        print(f"::error::render-latency red — `{SEC}` 가 붙은 통과 케이스 0건. "
              "원천이 안 붙었거나 표식이 지워졌다. 대상 0건은 통과가 아니다.")
        sys.exit(1)

    if n_total < min_n:
        print(f"::error::render-latency red — 표본 {n_total}건 < 최소 {min_n}건. "
              "p95 라는 말이 성립하지 않는 표본으로 통과를 찍지 않는다.")
        bad = True
    if len(formats) < min_f:
        print(f"::error::render-latency red — 포맷 {len(formats)}종 < 최소 {min_f}종 "
              f"(관측: {', '.join(formats)}). 한 포맷만 빨라도 통과가 되는 것을 막는다.")
        bad = True

    secs = sorted(s for _, _, s, _ in timed)
    p95 = _p95(secs)
    print(f"  · 표본 {n_total}건 · 포맷 {len(formats)}종({', '.join(formats)}) "
          f"· 최소 {secs[0]:.3f}초 · 중앙값 {secs[len(secs) // 2]:.3f}초 "
          f"· p95 {p95:.3f}초 · 최대 {secs[-1]:.3f}초")
    for f in formats:
        s = sorted(x for ff, _, x, _ in timed if ff == f)
        b = next((bb for ff, _, _, bb in timed if ff == f), None)
        size = f" · 본체 {b / 1e6:.1f} MB" if b else ""
        print(f"    · {f} — {len(s)}건 · 중앙값 {s[len(s) // 2]:.3f}초 "
              f"· 최대 {s[-1]:.3f}초{size}")

    over = [(n, s) for _, n, s, _ in timed if s > cap]
    for n, s in over:
        print(f"::error::render-latency red — 상한 초과 {s:.3f}초 > {cap:g}초: {n}")
        bad = True

    if p95 > p95_bar:
        print(f"::error::render-latency red — p95 {p95:.3f}초 > 합격선 {p95_bar:g}초.")
        bad = True

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
