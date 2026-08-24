"""ai-service 의 **경계 표면**. 값 객체와 Protocol 만 있고 구현은 없다.

왜 값 객체가 여기 사는가
  `import-boundary` 계약 5·7 이 `app > d10 > ports > d9` 를 강제하고 **D10 은 D9 를 직접
  import 하지 못한다.** 그래서 두 층이 함께 쓰는 모양(해석 결과·매칭 행)은 **아래층인
  여기**에 산다. 조립은 `app/` 이 한다.

이 파일에 **없는 것**
  · **카탈로그 조회 표면이 없다.** `K4-a` 의 `CatalogSearchPort`·`MatchRow` 는 2026-08-25
    판정 ㈎ 로 core-api(`domains/d3_catalog.SearchMatch`)로 갔다 — D3 는 저쪽 도메인이고,
    이 단위가 그 표면을 갖고 있는 한 D10 이 D3 에 붙을 자리가 남는다 (`CLAUDE.md §3-1`).
  · 순위 규칙이 없다 — 순위는 core-api 의 `tsvector` 가 낸다 (`PLAN-SoT §9-〈72〉-㉮`).
  · 결과 본문 생성이 없다 — 이름·요약·잠김은 core-api 가 D3·D2 에서 붙인다.
  · 점수·퍼센트 필드가 없다 (`CLAUDE.md §3 AI 응답 규격`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

#: 주제 고정 4값. **여기서 새로 정하는 것이 아니라** 두 정본(`db/ai/schema.sql`
#: `d9_topic_synonym.topic` CHECK · `db/platform/schema.sql` `d3_dataset_description`
#: CHECK)이 같은 값을 각각 적어 둔 것을 코드 쪽에 한 번 더 옮긴 것이다 (`㊸-④-2`).
TOPICS = ("강우·강수", "식생·NDVI", "지형·DEM", "토지피복·LULC")


@dataclass(frozen=True)
class Interpretation:
    """자연어 질의 → **검색어·필터**. LLM 의 일은 여기까지다 (`〈72〉-㉮`).

    `source` 가 `"literal"` 이면 모델이 아니라 문자열 분해가 만든 것이다 —
    **그래도 검색은 돈다.** 그 사실을 `degraded` 로 정직하게 말한다.
    """
    is_data_query: bool
    terms: tuple[str, ...]
    topic: str | None
    source: str                      # "llm" | "literal"
    degraded: bool
    degraded_reason: str | None


class QueryInterpreterPort(Protocol):
    """질의 해석기. **실패해도 예외를 던지지 않는다** — 문자열 해석으로 떨어진다."""

    def interpret(self, query: str) -> Interpretation:
        ...


class DictionaryPort(Protocol):
    """D9 사전 3종 조회. D10 은 이 표면으로만 지식을 읽는다 (`DOMAINS §2`)."""

    def expand(self, terms: tuple[str, ...], query: str):
        ...
