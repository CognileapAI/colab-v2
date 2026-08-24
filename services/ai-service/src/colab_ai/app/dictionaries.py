"""D9 사전 3종 + **개념 그래프 두 표** 조회 — `ports.DictionaryPort` 의 구현.

**넓히는 규칙은 여기 없다.** 규칙은 `domains/d9_ontology.py` 의 순수 함수이고 이 파일은
그 함수에 먹일 행을 AI 체인에서 읽어 올 뿐이다. 두 곳에 규칙을 적으면 갈라진다.

다섯 표 어디에도 `lab_id` 가 없다 — **연구실 공통 지식**이기 때문이다(`db/ai/schema.sql`).
그래서 여기엔 경계 주입이 없고, 대신 **읽기만** 한다.

⚠ **이 커넥션은 이 배포 단위만 갖는다** (`PLAN-SoT §9-〈90〉-㉮`). 그래프는 D9 의 자기
테이블이고, core-api 가 같은 표에 직접 붙으면 2026-08-25 판정 ㈎ 로 고친 위반의 거울상이
된다 — 그때 넘은 것도 `import` 가 아니라 **DB 커넥션**이었다. core-api 로는 **말만** 간다.
"""
from __future__ import annotations

from dataclasses import replace

from sqlalchemy import text
from sqlalchemy.engine import Engine

from colab_ai.domains.d9_ontology import (
    ConceptEdge,
    ConceptGraph,
    ConceptNode,
    Dictionaries,
    Expansion,
    expand,
    expand_by_graph,
)
from colab_ai.kernel.db import make_session_factory

METHODS_SQL = text("SELECT term FROM d9_method_term ORDER BY term")
TOPICS_SQL = text("SELECT synonym, topic FROM d9_topic_synonym ORDER BY synonym")
PLACES_SQL = text("SELECT alias, place_name FROM d9_place_alias ORDER BY alias")
#: **정렬해서 읽는다.** 확장 규칙이 스스로 다시 정렬하지만, 읽는 쪽도 순서를 고정해
#: 두어야 「DB 의 물리적 행 순서」가 어떤 경로로도 답에 스미지 않는다 (`〈72〉-㉮` 재현성).
CONCEPTS_SQL = text("SELECT concept_id, label, expandable FROM d9_concept ORDER BY concept_id")
EDGES_SQL = text("SELECT src, relation, dst FROM d9_concept_edge ORDER BY src, relation, dst")


class SqlDictionaries:
    """사전 3종 + 그래프를 읽어 넓힌다. **캐시하지 않는다** — 시드가 바뀌면 다음 질의부터다."""

    def __init__(self, engine: Engine) -> None:
        self._factory = make_session_factory(engine)

    def _read(self) -> tuple[Dictionaries, ConceptGraph]:
        """**한 트랜잭션에서 다섯 표를 함께 읽는다.** 사전과 그래프를 따로 읽으면 시드가
        바뀌는 순간에 반쪽씩 다른 세대를 보고 넓힐 수 있다 — 그러면 같은 질의가 같은
        검색어를 낸다는 성질이 그 한 번에 깨진다.
        """
        session = self._factory()
        try:
            session.begin()
            session.execute(text("SET TRANSACTION READ ONLY"))
            methods = tuple(r[0] for r in session.execute(METHODS_SQL))
            topics = tuple((r[0], r[1]) for r in session.execute(TOPICS_SQL))
            places = tuple((r[0], r[1]) for r in session.execute(PLACES_SQL))
            nodes = tuple(ConceptNode(concept_id=r[0], label=r[1], expandable=bool(r[2]))
                          for r in session.execute(CONCEPTS_SQL))
            edges = tuple(ConceptEdge(src=r[0], relation=r[1], dst=r[2])
                          for r in session.execute(EDGES_SQL))
        finally:
            session.rollback()
            session.close()
        return (Dictionaries(method_terms=methods, topic_synonyms=topics, place_aliases=places),
                ConceptGraph(nodes=nodes, edges=edges))

    def load(self) -> Dictionaries:
        return self._read()[0]

    def load_graph(self) -> ConceptGraph:
        return self._read()[1]

    def expand(self, terms: tuple[str, ...], query: str) -> Expansion:
        """**사전이 먼저, 그래프가 나중이다.**

        순서에 이유가 있다 — 사전은 「같은 뜻의 다른 표기」를 붙이고 그래프는 「상위어의
        하위들」을 붙인다. 사전이 먼저 돌면 그래프가 볼 수 있는 표제어가 늘고, 반대 순서로
        하면 사전이 그래프가 데려온 말을 다시 넓혀 **깊이 1 이 조용히 2 가 된다.**
        """
        dictionaries, graph = self._read()
        base = expand(terms, query=query, dictionaries=dictionaries)
        graphed = expand_by_graph(base.terms, query=query, graph=graph)
        return replace(base, terms=base.terms + graphed.terms, graph_hops=graphed.hops)
