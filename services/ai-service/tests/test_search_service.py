"""D10 검색 조립 — **응답이 정본을 지키는가**.

`CLAUDE.md §3 AI 응답 규격` · `Policy_데이터_찾기 §1.3` 이 요구하는 것을 그대로 오라클로 옮겼다.
  ① **뒤진 범위를 먼저 밝힌다** — 응답의 첫 열쇠가 `scope` 다. 0건이어도 먼저다.
  ② **근거는 한 줄이고 필수다** — 줄바꿈이 없고 비어 있지 않다.
  ③ **숫자·퍼센트 필드를 화면 쪽에 만들지 않는다** — 확신도 필드도 점수 필드도 없다.
  ④ **0건은 정직한 빈 상태** — 억지 제안이 붙지 않는다.
  ⑤ **순위는 결정적이다** — 같은 입력이 같은 순서를 낸다 (`〈72〉-㉮`).
"""
from __future__ import annotations

import json

from colab_ai.domains.d10_ai_services import SearchService
from colab_ai.domains.d9_ontology import Dictionaries, expand
from colab_ai.ports import Interpretation, MatchRow

DICTS = Dictionaries(method_terms=(), topic_synonyms=(("강우데이터", "강우·강수"),),
                     place_aliases=())


class FakeDictionaries:
    def expand(self, terms, query):
        return expand(terms, query=query, dictionaries=DICTS)


class BrokenDictionaries:
    def expand(self, terms, query):
        raise RuntimeError("사전 DB 가 없다")


class FakeCatalog:
    def __init__(self, rows, count=3):
        self._rows, self._count = rows, count
        self.seen = []

    def count_datasets(self, *, lab_id, account_id):
        return self._count

    def match(self, *, lab_id, account_id, terms, topic, limit, offset):
        self.seen.append({"lab_id": lab_id, "terms": terms, "topic": topic})
        return list(self._rows)[offset:offset + limit], len(self._rows)


class BrokenCatalog:
    def count_datasets(self, *, lab_id, account_id):
        raise RuntimeError("카탈로그 DB 에 못 닿았다")

    def match(self, **_kw):
        raise RuntimeError("카탈로그 DB 에 못 닿았다")


DS1 = "0000000000000000000000DSA1"
DS2 = "0000000000000000000000DSA2"
ROWS = (
    MatchRow(dataset_id=DS2, rank=0.9, matched_terms=("강우",), where=("이름·주제·요약",)),
    MatchRow(dataset_id=DS1, rank=0.4, matched_terms=("강우",), where=("이름·주제·요약", "포맷·변수")),
)


def _service(rows=ROWS, count=3, interpretation=None, dictionaries=None, catalog=None):
    interpretation = interpretation or Interpretation(
        is_data_query=True, terms=("강우",), topic=None, source="llm",
        degraded=False, degraded_reason=None)

    class FixedInterpreter:
        def interpret(self, query):
            return interpretation

    return SearchService(interpreter=FixedInterpreter(),
                         dictionaries=dictionaries or FakeDictionaries(),
                         catalog=catalog or FakeCatalog(rows, count))


def _search(service, query="강우 데이터", limit=20):
    return service.search(lab_id="0000000000000000000000000A", lab_name="A 연구실",
                          account_id="000000000000000000000000A1", query=query, limit=limit,
                          cursor=None)


def test_뒤진_범위가_먼저다() -> None:
    body = _search(_service())
    assert next(iter(body)) == "scope"
    assert body["scope"] == {"labId": "0000000000000000000000000A",
                             "labName": "A 연구실", "searchedCount": 3}


def test_영건도_범위를_먼저_말한다() -> None:
    body = _search(_service(rows=()))
    assert next(iter(body)) == "scope"
    assert body["results"]["items"] == [] and body["results"]["totalCount"] == 0
    assert body["degraded"] is False          # 0건은 장애가 아니다
    assert body["isDataQuery"] is True


def test_근거는_필수이고_한_줄이다() -> None:
    body = _search(_service())
    for hit in body["results"]["items"]:
        assert isinstance(hit["rationale"], str) and hit["rationale"].strip()
        assert "\n" not in hit["rationale"] and "\r" not in hit["rationale"]


def test_한계를_같은_줄에서_밝힌다() -> None:
    body = _search(_service())
    assert all("못" in h["rationale"] or "않" in h["rationale"]
               for h in body["results"]["items"])


def test_결과에_숫자_등급_확신도_필드가_없다() -> None:
    body = _search(_service())
    for hit in body["results"]["items"]:
        assert set(hit) == {"datasetId", "relevanceBar", "rationale"}
        assert "%" not in hit["rationale"]
        assert "확신도" not in json.dumps(body, ensure_ascii=False)


def test_순위가_결정적이다() -> None:
    first = _search(_service())["results"]["items"]
    second = _search(_service())["results"]["items"]
    assert [h["datasetId"] for h in first] == [h["datasetId"] for h in second] == [DS2, DS1]


def test_같은_점수면_식별자_오름차순으로_고정된다() -> None:
    tied = (MatchRow(dataset_id=DS2, rank=0.5, matched_terms=("강우",), where=("이름·주제·요약",)),
            MatchRow(dataset_id=DS1, rank=0.5, matched_terms=("강우",), where=("이름·주제·요약",)))
    body = _search(_service(rows=tied))
    assert [h["datasetId"] for h in body["results"]["items"]] == [DS1, DS2]


def test_막대는_0과_1_사이다() -> None:
    body = _search(_service())
    bars = [h["relevanceBar"] for h in body["results"]["items"]]
    assert all(0.0 <= b <= 1.0 for b in bars) and bars == sorted(bars, reverse=True)


def test_데이터_질문이_아니면_결과가_비고_오류가_아니다() -> None:
    not_data = Interpretation(is_data_query=False, terms=(), topic=None, source="llm",
                              degraded=False, degraded_reason=None)
    body = _search(_service(interpretation=not_data))
    assert body["isDataQuery"] is False
    assert body["results"]["items"] == [] and body["degraded"] is False


def test_LLM_이_죽어도_문자열_해석으로_검색이_돈다() -> None:
    """**「AI 없이도 v2 는 완결된 제품이다」의 2층** — 해석만 무너지고 검색은 산다."""
    literal = Interpretation(is_data_query=True, terms=("강우", "데이터"), topic=None,
                             source="literal", degraded=True,
                             degraded_reason="질의 해석 모델에 닿지 못했다 — 질문 그대로 찾았다.")
    body = _search(_service(interpretation=literal))
    assert body["degraded"] is True and body["degradedReason"]
    assert len(body["results"]["items"]) == 2       # **결과는 그대로 나온다**


def test_카탈로그가_죽으면_정직한_빈_상태다() -> None:
    body = _search(_service(catalog=BrokenCatalog()))
    assert body["degraded"] is True and body["results"]["items"] == []
    assert body["scope"]["searchedCount"] == 0
    assert body["isDataQuery"] is True             # 하지 않은 판정을 말하지 않는다


def test_사전이_죽어도_검색어_원문으로_찾는다() -> None:
    body = _search(_service(dictionaries=BrokenDictionaries()))
    assert body["degraded"] is True
    assert len(body["results"]["items"]) == 2


def test_주제_필터가_실행기에_그대로_내려간다() -> None:
    catalog = FakeCatalog(ROWS)
    interp = Interpretation(is_data_query=True, terms=("강우데이터",), topic=None,
                            source="llm", degraded=False, degraded_reason=None)
    _search(_service(interpretation=interp, catalog=catalog))
    assert catalog.seen[-1]["topic"] == "강우·강수"      # 사전이 정한다
    assert "강우·강수" in catalog.seen[-1]["terms"]


def test_경계는_요청_scope_그대로_실행기에_간다() -> None:
    catalog = FakeCatalog(ROWS)
    _search(_service(catalog=catalog))
    assert catalog.seen[-1]["lab_id"] == "0000000000000000000000000A"


def test_이어보기_토큰은_더_없을_때_null_이다() -> None:
    body = _search(_service())
    assert body["results"]["nextCursor"] is None
