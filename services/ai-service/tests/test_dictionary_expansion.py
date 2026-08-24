"""사전 3종으로 검색어를 넓히는 규칙 — **D9 가 아는 전부**다 (`db/ai/schema.sql`).

`〈72〉-㉮` 가 매칭·순위를 tsvector + 사전 3종에 맡겼으므로, **넓히는 규칙이 결정적이어야
한다.** 같은 질의가 같은 검색어 집합을 낸다 — 그래야 평가셋이 회귀를 잡는다.
"""
from __future__ import annotations

from colab_ai.domains.d9_ontology import Dictionaries, expand

DICTS = Dictionaries(
    method_terms=("격자화", "재격자화"),
    topic_synonyms=(("강우데이터", "강우·강수"), ("강우·강수", "강우·강수")),
    place_aliases=(("낙동강 유역", "낙동강 유역"), ("한강 상류", "한강 상류")),
)


def test_동의어가_주제로_간다() -> None:
    out = expand(("강우데이터",), query="강우데이터", dictionaries=DICTS)
    assert out.topic == "강우·강수"
    assert "강우데이터" in out.terms and "강우·강수" in out.terms


def test_지명_별칭은_통째로_붙는다_토큰이_갈라져도() -> None:
    """「낙동강 유역」은 두 토큰이라 낱말 단위로는 못 만난다 — 질의 원문을 함께 훑는다."""
    out = expand(("낙동강", "유역", "강우"), query="낙동강 유역 강우", dictionaries=DICTS)
    assert "낙동강 유역" in out.places
    assert "낙동강 유역" in out.terms


def test_같은_질의는_같은_검색어_집합을_낸다() -> None:
    a = expand(("강우데이터", "낙동강", "유역"), query="강우데이터 낙동강 유역", dictionaries=DICTS)
    b = expand(("강우데이터", "낙동강", "유역"), query="강우데이터 낙동강 유역", dictionaries=DICTS)
    assert a.terms == b.terms and a.topic == b.topic


def test_사전에_없으면_아무것도_지어내지_않는다() -> None:
    out = expand(("염분",), query="금강 염분", dictionaries=DICTS)
    assert out.terms == ("염분",)
    assert out.topic is None and out.places == () and out.methods == ()


def test_중복은_한_번만_남고_순서는_질의_순서다() -> None:
    out = expand(("강우데이터", "강우·강수"), query="강우데이터 강우·강수", dictionaries=DICTS)
    assert out.terms == ("강우데이터", "강우·강수")


def test_주제는_첫_일치가_이긴다() -> None:
    dicts = Dictionaries(method_terms=(),
                         topic_synonyms=(("지형", "지형·DEM"), ("강우데이터", "강우·강수")),
                         place_aliases=())
    out = expand(("강우데이터", "지형"), query="강우데이터 지형", dictionaries=dicts)
    assert out.topic == "강우·강수"
