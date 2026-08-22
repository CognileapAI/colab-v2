#!/usr/bin/env python3
"""K2 커버리지 판정기 — 기준(TSV)과 적재된 행(사실 TSV)을 대조한다.

이것이 WU-K2 의 **완료 오라클**이다 (WORK-UNITS §8 「시드 커버리지 체크 (핵심 어휘 미커버 0)」).

  기준 = db/ai/seed/k2-coverage-standard.tsv  (03-HANDOFF §1 K2 행을 옮긴 것)
  사실 = DB 에서 뽑은 `kind<TAB>value` 줄들 (stdin)

미커버가 한 건이라도 있으면 **red(exit 1)** 다. 0 건이어야 green.
「대상이 없어서 통과」를 만들지 않는다 — 기준이 비었거나 사실이 비면 그 자체가 red 다
(CLAUDE.md §4: 검사를 못 한 것은 통과가 아니다).

표준 라이브러리만 쓴다. DB 접속은 이 파일이 하지 않는다 — 껍데기(k2-coverage-check.sh)의 일이다.
"""
from __future__ import annotations

import sys
from pathlib import Path

KINDS = ("method", "topic", "place")
KIND_LABEL = {"method": "가공 방식 어휘", "topic": "주제", "place": "지명"}
EXPECTED = {"method": 13, "topic": 4, "place": 4}


def red(msg: str) -> None:
    print(f"::error::k2-coverage red — {msg}")
    raise SystemExit(1)


def load_standard(path: Path) -> list[tuple[str, str, str]]:
    if not path.is_file():
        red(f"커버리지 기준 정본이 없다: {path.name}")
    rows: list[tuple[str, str, str]] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
            red(f"기준 {n}행이 'kind<TAB>value<TAB>citation' 3열이 아니다 (인용 없는 기준 항목은 기준이 아니다)")
        kind, value, cite = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if kind not in KINDS:
            red(f"기준 {n}행의 kind 가 알 수 없는 값이다: {kind}")
        rows.append((kind, value, cite))
    if not rows:
        red("커버리지 기준이 비었다. 기준 0건을 green 으로 세지 않는다.")
    return rows


def main() -> int:
    std_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "seed" / "k2-coverage-standard.tsv"
    )
    standard = load_standard(std_path)

    # 기준 자체의 무결성 — 03-HANDOFF 가 못 박은 13/4/4 와 다르면 기준이 조용히 줄어든 것이다.
    for kind in KINDS:
        got = sum(1 for k, _, _ in standard if k == kind)
        if got != EXPECTED[kind]:
            red(f"기준 항목 수가 03-HANDOFF §1 K2 행과 다르다 — {KIND_LABEL[kind]} {got}건 (있어야 할 값 {EXPECTED[kind]}건). "
                "검사 대상을 줄여 green 을 만들지 않는다 (CLAUDE.md §4).")

    loaded: dict[str, set[str]] = {k: set() for k in KINDS}
    seen = 0
    for line in sys.stdin.read().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            red(f"사실 줄이 'kind<TAB>value' 가 아니다: {line!r}")
        kind, value = parts[0].strip(), parts[1].strip()
        if kind not in KINDS:
            red(f"사실 줄의 kind 가 알 수 없는 값이다: {kind}")
        loaded[kind].add(value)
        seen += 1
    if seen == 0:
        red("적재된 행이 0건이다. 빈 DB 를 '미커버 없음'으로 세지 않는다.")

    uncovered = [(k, v, c) for k, v, c in standard if v not in loaded[k]]

    print("k2-coverage — 기준 대비 적재 커버리지")
    for kind in KINDS:
        need = [v for k, v, _ in standard if k == kind]
        miss = [v for k, v, _ in uncovered if k == kind]
        mark = "OK" if not miss else f"미커버 {len(miss)}"
        print(f"  {KIND_LABEL[kind]:<12} 기준 {len(need)}건 · 적재 {len(need) - len(miss)}건  [{mark}]")
    print(f"  (DB 에서 읽은 값 {seen}건 — 기준 밖 값은 미커버 판정에 쓰이지 않는다)")

    if uncovered:
        print("::error::k2-coverage red — 핵심 어휘 미커버 "
              f"{len(uncovered)}건. 완료 정의는 '미커버 0' 이다 (WORK-UNITS §8 K2).")
        for k, v, c in uncovered:
            print(f"   - [{KIND_LABEL[k]}] {v}\n       정본 인용: {c}")
        return 1

    print("k2-coverage green — 핵심 어휘 미커버 0건 (기준 21건 전부 적재됨).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
