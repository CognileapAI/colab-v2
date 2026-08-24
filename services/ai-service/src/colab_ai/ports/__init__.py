"""ai-service 의 **경계 표면**. 값 객체와 Protocol 만 있고 구현은 없다.

왜 값 객체가 여기 사는가
  `import-boundary` 계약 5·7 이 `app > d10 > ports > d9` 를 강제하고 **D10 은 D9 를 직접
  import 하지 못한다.** 그래서 두 층이 함께 쓰는 모양(해석 결과·매칭 행)은 **아래층인
  여기**에 산다. 조립은 `app/` 이 한다.

이 파일에 **없는 것**
  · 순위 규칙이 없다 — 순위는 `tsvector` 가 낸다 (`PLAN-SoT §9-〈72〉-㉮`).
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


@dataclass(frozen=True)
class MatchRow:
    """실행기가 낸 후보 한 건. **관련도는 DB 가 계산한 값 그대로**다.

    `where` 는 어느 색인에서 맞았는가(이름·주제·요약 / 포맷·변수 / 원천 표기)이고
    근거 한 줄의 재료다. `matched_terms` 는 **실제로 맞은 검색어**다 —
    안 맞은 말을 근거에 적지 않으려고 행마다 따로 받는다.
    """
    dataset_id: str
    rank: float
    matched_terms: tuple[str, ...]
    where: tuple[str, ...]


class QueryInterpreterPort(Protocol):
    """질의 해석기. **실패해도 예외를 던지지 않는다** — 문자열 해석으로 떨어진다."""

    def interpret(self, query: str) -> Interpretation:
        ...


class DictionaryPort(Protocol):
    """D9 사전 3종 조회. D10 은 이 표면으로만 지식을 읽는다 (`DOMAINS §2`)."""

    def expand(self, terms: tuple[str, ...], query: str):
        ...


class CatalogSearchPort(Protocol):
    """`tsvector` 질의 실행기.

    **연구실 경계는 이 아래 Postgres 층에 남는다** — 구현이 세션에 경계를 심고 RLS 가
    행을 지운다. D10 코드에는 경계 판단이 한 줄도 없다 (`CLAUDE.md §3-5`).
    **읽기 전용이다** — 이 표면에 쓰기 메서드가 존재하지 않는다.
    """

    def count_datasets(self, *, lab_id: str, account_id: str) -> int:
        ...

    def match(self, *, lab_id: str, account_id: str, terms: tuple[str, ...],
              topic: str | None, limit: int, offset: int) -> tuple[list[MatchRow], int]:
        ...
