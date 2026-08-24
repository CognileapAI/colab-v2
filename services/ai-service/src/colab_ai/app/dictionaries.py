"""D9 사전 3종 조회 — `ports.DictionaryPort` 의 구현.

**넓히는 규칙은 여기 없다.** 규칙은 `domains/d9_ontology.py` 의 순수 함수이고 이 파일은
그 함수에 먹일 행을 `db/ai` 체인에서 읽어 올 뿐이다. 두 곳에 규칙을 적으면 갈라진다.

`db/ai` 세 표에는 `lab_id` 가 없다 — **연구실 공통 지식**이기 때문이다(`db/ai/schema.sql`).
그래서 여기엔 경계 주입이 없고, 대신 **읽기만** 한다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from colab_ai.domains.d9_ontology import Dictionaries, Expansion, expand
from colab_ai.kernel.db import make_session_factory

METHODS_SQL = text("SELECT term FROM d9_method_term ORDER BY term")
TOPICS_SQL = text("SELECT synonym, topic FROM d9_topic_synonym ORDER BY synonym")
PLACES_SQL = text("SELECT alias, place_name FROM d9_place_alias ORDER BY alias")


class SqlDictionaries:
    """사전 3종을 읽어 넓힌다. **캐시하지 않는다** — 시드가 바뀌면 다음 질의부터 반영된다."""

    def __init__(self, engine: Engine) -> None:
        self._factory = make_session_factory(engine)

    def load(self) -> Dictionaries:
        session = self._factory()
        try:
            session.begin()
            session.execute(text("SET TRANSACTION READ ONLY"))
            methods = tuple(r[0] for r in session.execute(METHODS_SQL))
            topics = tuple((r[0], r[1]) for r in session.execute(TOPICS_SQL))
            places = tuple((r[0], r[1]) for r in session.execute(PLACES_SQL))
        finally:
            session.rollback()
            session.close()
        return Dictionaries(method_terms=methods, topic_synonyms=topics, place_aliases=places)

    def expand(self, terms: tuple[str, ...], query: str) -> Expansion:
        return expand(terms, query=query, dictionaries=self.load())
