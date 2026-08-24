"""D10 질의 해석 조립 — **응답이 정본을 지키는가**.

⚠ **2026-08-25 판정 ㈎ 로 이 파일의 절반이 core-api 로 갔다.** 순위·근거 한 줄·관련도 막대에
관한 오라클은 `services/core-api/tests/test_search_assembly.py` 에, `tsvector` 실물 오라클은
`services/core-api/tests/test_search_execution.py` 에 있다. **여기 남은 것은 해석의 몫**이다.

  ① **뒤진 범위를 먼저 밝힌다** — 응답의 첫 열쇠가 `scope` 다.
  ② **결과를 만들지 않는다** — `results.items` 는 언제나 빈 배열이다. 찾는 것은 core-api 다.
  ③ **숫자·퍼센트·확신도 필드가 없다** (`CLAUDE.md §3 AI 응답 규격`).
  ④ **해석이 무너져도 검색어는 나온다** — 그것이 「AI 없이도 검색이 돈다」의 이쪽 절반이다.
"""
from __future__ import annotations

import json

from colab_ai.domains.d10_ai_services import SearchService
from colab_ai.domains.d9_ontology import Dictionaries, expand
from colab_ai.ports import Interpretation

DICTS = Dictionaries(method_terms=(), topic_synonyms=(("강우데이터", "강우·강수"),),
                     place_aliases=())


class FakeDictionaries:
    def expand(self, terms, query):
        return expand(terms, query=query, dictionaries=DICTS)


class BrokenDictionaries:
    def expand(self, terms, query):
        raise RuntimeError("사전 DB 가 없다")


def _service(interpretation=None, dictionaries=None):
    interpretation = interpretation or Interpretation(
        is_data_query=True, terms=("강우",), topic=None, source="llm",
        degraded=False, degraded_reason=None)

    class FixedInterpreter:
        def interpret(self, query):
            return interpretation

    return SearchService(interpreter=FixedInterpreter(),
                         dictionaries=dictionaries or FakeDictionaries())


def _search(service, query="강우 데이터", searched_count=3):
    return service.search(lab_id="0000000000000000000000000A", lab_name="A 연구실",
                          query=query, searched_count=searched_count)


def test_뒤진_범위가_먼저다() -> None:
    body = _search(_service())
    assert next(iter(body)) == "scope"
    assert body["scope"] == {"labId": "0000000000000000000000000A",
                             "labName": "A 연구실", "searchedCount": 3}


def test_뒤진_개수는_호출자가_센_값을_되비춘다() -> None:
    """**이 단위는 D3 를 못 읽는다** — 세는 것은 core-api 의 일이고 여기서 지어내지 않는다."""
    assert _search(_service(), searched_count=128)["scope"]["searchedCount"] == 128
    assert _search(_service(), searched_count=0)["scope"]["searchedCount"] == 0


def test_결과를_만들지_않는다() -> None:
    """`〈72〉-㉮` — 찾고 매기는 것은 `tsvector` 다. 이 단위에 후보가 생기면 그 선이 무너진다."""
    body = _search(_service())
    assert body["results"] == {"items": [], "totalCount": 0, "nextCursor": None}


def test_검색어와_주제를_돌려준다() -> None:
    body = _search(_service())
    assert body["interpretation"]["terms"] and body["interpretation"]["source"] == "llm"


def test_숫자_등급_확신도_필드가_없다() -> None:
    body = _search(_service())
    raw = json.dumps(body, ensure_ascii=False)
    assert "확신도" not in raw and "%" not in raw and "score" not in raw


def test_해석이_결정적이다() -> None:
    first, second = _search(_service()), _search(_service())
    assert first["interpretation"] == second["interpretation"]


def test_데이터_질문이_아니면_검색어가_비고_오류가_아니다() -> None:
    not_data = Interpretation(is_data_query=False, terms=(), topic=None, source="llm",
                              degraded=False, degraded_reason=None)
    body = _search(_service(interpretation=not_data))
    assert body["isDataQuery"] is False
    assert body["interpretation"]["terms"] == [] and body["degraded"] is False


def test_LLM_이_죽어도_질문의_낱말이_검색어로_나간다() -> None:
    """**「AI 없이도 v2 는 완결된 제품이다」의 이쪽 절반** — 해석만 무너지고 검색어는 산다.
    core-api 는 이 낱말로 실제 `tsvector` 검색을 돌린다."""
    literal = Interpretation(is_data_query=True, terms=("강우", "데이터"), topic=None,
                             source="literal", degraded=True,
                             degraded_reason="질의 해석 모델에 닿지 못했다 — 질문 그대로 찾았다.")
    body = _search(_service(interpretation=literal))
    assert body["degraded"] is True and body["degradedReason"]
    assert body["interpretation"]["terms"] == ["강우", "데이터"]
    assert body["interpretation"]["source"] == "literal"


def test_사전이_죽어도_검색어_원문이_나간다() -> None:
    body = _search(_service(dictionaries=BrokenDictionaries()))
    assert body["degraded"] is True and body["degradedReason"]
    assert body["interpretation"]["terms"] == ["강우"]


def test_사전이_주제를_정한다() -> None:
    interp = Interpretation(is_data_query=True, terms=("강우데이터",), topic=None,
                            source="llm", degraded=False, degraded_reason=None)
    body = _search(_service(interpretation=interp))
    assert body["interpretation"]["topic"] == "강우·강수"
    assert "강우·강수" in body["interpretation"]["terms"]


def test_검색어_수에_상한이_있다() -> None:
    """사전 확장이 질의를 통째로 넓혀 버리면 그 다음 `tsvector` 질의가 아무 말에나 맞는다."""
    many = Interpretation(is_data_query=True, terms=tuple(f"t{i}" for i in range(200)),
                          topic=None, source="llm", degraded=False, degraded_reason=None)
    body = _search(_service(interpretation=many))
    assert len(body["interpretation"]["terms"]) <= 24
