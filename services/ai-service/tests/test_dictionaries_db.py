"""D9 사전 3종을 **실물 체인에서** 읽는다 (`db/ai`).

K2 시드가 적재한 수를 여기서 고정한다 — 13 · 5 · 4 = 22 (실측, `db/ai/seed/k2_ontology_seed.sql`).
수가 바뀌면 이 시험이 red 를 내고, 그때 사람이 「시드가 늘었다」와 「사전이 지워졌다」를 가른다.
"""
from __future__ import annotations

from colab_ai.domains.d9_ontology import expand


def test_시드_22행이_그대로_읽힌다(dictionaries) -> None:
    loaded = dictionaries.load()
    assert len(loaded.method_terms) == 13
    assert len(loaded.topic_synonyms) == 5
    assert len(loaded.place_aliases) == 4


def test_강우데이터가_주제로_간다(dictionaries) -> None:
    out = dictionaries.expand(("강우데이터",), "강우데이터")
    assert out.topic == "강우·강수"


def test_낙동강_유역이_별칭으로_잡힌다(dictionaries) -> None:
    out = dictionaries.expand(("낙동강", "유역"), "낙동강 유역 강우")
    assert "낙동강 유역" in out.places


def test_적재된_사전으로_넓힌_결과가_순수함수와_같다(dictionaries) -> None:
    loaded = dictionaries.load()
    assert dictionaries.expand(("강우데이터",), "강우데이터") == \
        expand(("강우데이터",), query="강우데이터", dictionaries=loaded)
