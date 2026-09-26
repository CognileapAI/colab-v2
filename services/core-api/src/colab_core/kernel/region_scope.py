"""지역 조건의 표기 집합 — 의미 식별자와 그 **직계 하위** 한 단계(`regionWithin`).

정본 = `contracts/search/semantics.json` `regionWithin`(생성물 `search_semantics.SEMANTICS`).
표의 원본은 D9 그래프의 `안에 있다` 엣지이고, 둘의 일치는 게이트 `region-within-drift` 가 본다.
intent `dev-package/intent/2026-09-26-region-containment-expansion.md` 안전 규칙:
  · 하향 전용 — 표는 부모 → 하위 방향만 갖는다. 하위 표기로 부모를 부르는 길은 없다.
  · 깊이 1 — 하위의 하위를 따라가지 않는다(전이 폐포를 만들지 않는다).
  · 압축 후 정확 일치 — 부분 문자열로 넓히지 않는다.
경로 1(`client_search`·`d3_client_search`)과 경로 2(`search_evidence_conditions`)가 이 한 곳을 읽는다.
"""
from __future__ import annotations

import re

from .search_semantics import SEMANTICS


def compact(value) -> str:
    """경로 1 의 비교 형태 — 공백·`_`·`-` 제거 후 casefold(`d3_client_search` SQL 과 같은 규칙)."""
    return re.sub(r'[\s_\-]+', '', str(value)).casefold()


def region_scope(wanted: str, *, expand: bool = True) -> dict[str, str | None]:
    """`{압축 표기: 경유 하위 라벨 | None}` — None 은 질의 지역 자신(과 그 별칭)이다.

    `wanted` 가 의미 식별자가 아니면(기준 파일 지역처럼 원문에서 온 값) 자기 자신만 맞춘다.
    `expand=False` 는 종전 어휘(식별자 + `regions` 별칭)다 — reference_match 가 쓴다.
    """
    scope: dict[str, str | None] = {compact(wanted): None}
    for alias in SEMANTICS['regions'].get(wanted, ()):
        scope[compact(alias)] = None
    entry = SEMANTICS.get('regionWithin', {}).get(wanted) if expand else None
    if entry:
        for alias in (entry['place'], *entry.get('placeAliases', ())):
            scope.setdefault(compact(alias), None)
        for child, aliases in entry['within'].items():
            for label in (child, *aliases):
                scope.setdefault(compact(label), child)
    return scope


def region_match(wanted: str, actual, *, expand: bool = True) -> tuple[bool, str | None]:
    """사실 지역 `actual` 이 조건 `wanted` 를 맞추는가 · 맞았다면 경유한 하위 라벨(없으면 None)."""
    if actual is None or actual == '':
        return False, None
    scope = region_scope(wanted, expand=expand)
    key = compact(actual)
    if key not in scope:
        return False, None
    return True, scope[key]


def place_label(wanted: str) -> str | None:
    """표에 실린 의미 식별자의 지명 라벨(「한반도」). 표에 없으면 None."""
    entry = SEMANTICS.get('regionWithin', {}).get(wanted)
    return entry['place'] if entry else None
