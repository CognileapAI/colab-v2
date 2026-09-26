"""주기(산출 간격) 순서 — 「N 이하」 주기 상한 술어가 읽는 한 곳.

정본 = `contracts/search/semantics.json` `cadenceSeconds`(생성물 `search_semantics.SEMANTICS`).
intent `dev-package/intent/2026-09-26-cadence-range-predicate.md`:
  · 정의 — 「1시간 이하」 = 산출 간격(주기) ≤ 1시간
    (Ted 2026-09-26 원문 「측정 간격같은데 1시간이하는 산출간격(주기)」).
  · 주기는 정본(DATASETS.md) 선언값의 전재다. 파일 시간축 실측이 아니며 연속 관측을 보증하지 않는다.
  · 표에 없는 값·빈 값은 판정하지 않는다(None = unknown). unknown 은 supported 가 아니다.
  · 월·연의 초는 명목값(30일 · 365일)이라 순서 비교에만 쓴다.
경로 1(`client_search`·`d3_client_search`)과 경로 2(`search_evidence_conditions`)가 이 한 곳을 읽는다.
"""
from __future__ import annotations

import math
import re

from .search_semantics import SEMANTICS

#: 사람이 읽는 주기 이름 — 경로 2 판정 표시·카드 근거가 쓴다.
LABELS: dict[str, str] = dict([('5min', '5분'), ('10min', '10분'), ('15min', '15분'), ('hourly', '매시'),
                               ('daily', '일별'), ('weekly', '주간'), ('monthly', '월평균'),
                               ('yearly', '연 단위')])

#: 「N분/N시간 이하·이내」. 수는 아라비아 숫자 또는 「한·두·세」. 「이상·미만·초과」는 열지 않는다.
#: 한글 수사 앞에 한글이 붙으면(「대한 시간」) 수로 읽지 않는다 — 원문(압축 전)에 대고 쓴다.
_KOREAN = dict([('한', 1), ('두', 2), ('세', 3)])
RANGE = re.compile(r'(?:(?<![\d.])(\d+(?:\.\d+)?)|(?<![가-힣])(한|두|세))\s*(분|시간)\s*(?:이하|이내)')


def _limit(value) -> float:
    """상한(초)을 양의 유한 수로 못박는다. bool·문자열은 수가 아니다 — 호출자 검증을 믿지 않는다."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('maxCadenceSeconds must be a positive finite number of seconds')
    return float(value)


def cadence_seconds(value) -> int | None:
    """주기 값 → 명목 초. 표에 없거나 문자열이 아니면 None."""
    return SEMANTICS['cadenceSeconds'].get(value) if isinstance(value, str) else None


def cadence_within(value, max_seconds) -> bool | None:
    """사실 주기 `value` 가 상한 이하인가. 모르면(없음·표 밖) None — 맞았다고 하지 않는다."""
    limit = _limit(max_seconds)
    seconds = cadence_seconds(value)
    return None if seconds is None else seconds <= limit


def cadences_within(max_seconds) -> list[str]:
    """상한 이하의 주기 값 목록(짧은 순). SQL 후보가 이 목록 밖의 값을 부르지 않는다."""
    limit = _limit(max_seconds)
    table = SEMANTICS['cadenceSeconds']
    return [key for key in sorted(table, key=table.get) if table[key] <= limit]


def parse_max_cadence_seconds(text: str):
    """질의문의 첫 「N분/N시간 이하·이내」 → 초. 없거나 0 이하면 None."""
    found = RANGE.search(text or '')
    if not found:
        return None
    number = float(found[1]) if found[1] else float(_KOREAN[found[2]])
    seconds = number * (3600 if found[3] == '시간' else 60)
    if seconds <= 0:
        return None
    return int(seconds) if seconds.is_integer() else seconds


def strip_range(text: str) -> str:
    """범위 문구를 뗀 글 — 「10분 이내」의 「10분」이 등호 주기로 다시 읽히지 않게 한다."""
    return RANGE.sub(' ', text or '')


def limit_label(max_seconds) -> str:
    """상한의 사람 표기 — 3600 → 「1시간」, 1800 → 「30분」."""
    seconds = _limit(max_seconds)
    if seconds % 3600 == 0:
        return f'{seconds / 3600:g}시간'
    if seconds % 60 == 0:
        return f'{seconds / 60:g}분'
    return f'{seconds:g}초'
