"""**적재된 그래프 실물**로 `K4-b` 를 증명한다 — 노드 55 · 엣지 21 (`PLAN-SoT §9-〈86〉`
+ Ted 판정 2026-09-18 결정 4·5, `0010_practitioner_concept`).

`test_graph_expansion.py` 는 규칙을 축소판 그래프로 증명한다. **여기서는 시드가 그 규칙을
실제로 먹이는가**를 본다. 둘이 갈리면 「규칙은 맞는데 시드가 그 규칙을 안 쓴다」가 조용히
성립하고, 그것이 §D-2 가 「그래프가 사는 자리」라고 부른 것이 죽는 방식이다.

DB 가 없으면 **skip 이 아니라 fail** 이다 (`conftest.py` 와 같은 규율).
"""
from __future__ import annotations

import pytest
from colab_ai.domains.d9_ontology import INSIDE, KIND_OF, SAME_AS

# 이 파일은 `dictionaries` 픽스처(= `COLAB_AI_TEST_DICT_DB_URL`)를 통째로 쓴다.
# 표식은 **빼기 위한 이름**이지 skip 의 근거가 아니다 — 고른 실행에서는 그대로 판정한다.
pytestmark = pytest.mark.dictdb


def _graphed(dictionaries, query: str):
    """**그래프가 붙인 말만** 돌려준다 — 사전이 붙인 말과 섞으면 무엇이 일했는지 못 센다."""
    out = dictionaries.expand((), query)
    assert set(h.term for h in out.graph_hops) <= set(out.terms)   # 홉은 실제로 나가는 말이다
    return (tuple(h.term for h in out.graph_hops),
            {h.term: (h.relation, h.parent) for h in out.graph_hops})


def test_시드가_노드_55_엣지_21_다(dictionaries) -> None:
    """`〈86〉` 의 확정값 + 2026-09-18 결정 4·5 + 2026-09-26 자료 지역 확정 1.

    49·19 → 54·20 은 원천표기 3(`s-era5`·`s-ecmwf`·`s-ecmwf-ko`) + 주제 2(`t-drought`·
    `t-fileformat`) + 엣지 `E1-12` 다. `~의 한 가지다` 7 은 **바뀌지 않는다** — 새 엣지는
    `같은 말이다` 하나뿐이고 `~이 제공한다` 는 결정 8 이 닫아 두었다.
    54·20 → 55·21 은 지명 `p-south-korea`(남한) + 엣지 「남한 안에 있다 한반도」다(2026-09-26).
    """
    graph = dictionaries.load_graph()
    assert len(graph.nodes) == 55
    assert len(graph.edges) == 21
    assert sum(1 for e in graph.edges if e.relation == SAME_AS) == 12
    assert sum(1 for e in graph.edges if e.relation == KIND_OF) == 7


def test_금지_목록_셋이_실물로_있다(dictionaries) -> None:
    """경계 ④ 는 코드의 다짐이 아니라 **시드의 열 값**이다."""
    blocked = {n.label for n in dictionaries.load_graph().nodes if not n.expandable}
    assert blocked == {"전처리", "품질검사", "유역 집계"}


def test_재격자화가_하위_셋과_그_영문_표기를_데려온다(dictionaries) -> None:
    """§D-2 — 그래프가 사는 가장 큰 자리. `Nearest`·`Bilinear` 가 데이터셋 이름의 말이다."""
    terms, hops = _graphed(dictionaries, "재격자화한 NDVI 자료")
    assert {"최근린보간", "이중선형보간", "IDW", "Nearest", "Bilinear"} <= set(terms)
    assert hops["Nearest"] == (KIND_OF, "재격자화")
    assert hops["IDW"] == (KIND_OF, "재격자화")


def test_Co_Kriging_은_따라오지_않는다_F_4d_기각(dictionaries) -> None:
    """`F-4d` 를 Ted 가 기각했다 (`〈86〉`). **그래서 3건이지 4건이 아니다.**

    시드에 그 엣지를 되살리면 여기가 red 를 낸다 — 판정이 코드가 아니라 오라클로 남는다.
    """
    terms, _ = _graphed(dictionaries, "재격자화한 NDVI 자료")
    assert "Co-Kriging" not in terms and "Regression Kriging" not in terms


def test_전처리는_확장을_시작하지_않는다(dictionaries) -> None:
    """§D-6 첫 번째 과확장. **금지 목록이라 도착이 될 수 없다.**"""
    terms, _ = _graphed(dictionaries, "전처리한 강우 자료")
    assert terms == ()


def test_Bilinear_을_물으면_형제가_따라오지_않는다(dictionaries) -> None:
    """§D-6 두 번째 과확장 — 상향 확장이면 `D-03`·`D-05` 가 오답으로 딸려 온다."""
    terms, _ = _graphed(dictionaries, "Bilinear 로 만든 자료")
    assert "재격자화" not in terms
    assert "최근린보간" not in terms and "IDW" not in terms


def test_다운스케일과_한국수자원학회가_함께_펴진다(dictionaries) -> None:
    """§D-4 — `E5-8` + `E1-11`. 사전만으로는 0건이던 질의다."""
    terms, hops = _graphed(dictionaries, "한국수자원학회 학회 발표에 쓴 다운스케일 자료")
    assert "KWRA" in terms and hops["KWRA"] == (SAME_AS, "한국수자원학회")


def test_한반도가_충청권을_데려온다_안에_있다(dictionaries) -> None:
    """§D-5 — `E2-1`. 결과 **집합**이 아니라 **순위**가 바뀌는 자리다."""
    terms, hops = _graphed(dictionaries, "한반도 전체 식생 자료")
    assert "충청권" in terms and hops["충청권"][1] == "한반도"


def test_한반도가_남한을_데려온다_안에_있다(dictionaries) -> None:
    """2026-09-26 Ted 판정 「자료 지역 확정」 1 — 「남한⊂한반도 관계로 연결」. 정본 남한 자료
    (기상청 관측망 seq 1·2·19·20)에 「한반도」 질의가 닿는 한 홉이다."""
    terms, hops = _graphed(dictionaries, "한반도 강수 자료")
    assert "남한" in terms and hops["남한"] == (INSIDE, "한반도")


def test_남한을_물으면_한반도로_올라가지_않는다(dictionaries) -> None:
    terms, _ = _graphed(dictionaries, "남한 강수 자료")
    assert "한반도" not in terms


def test_충청권을_물으면_한반도로_올라가지_않는다(dictionaries) -> None:
    terms, _ = _graphed(dictionaries, "충청권 식생 자료")
    assert "한반도" not in terms


def test_같은_질의가_같은_검색어를_낸다(dictionaries) -> None:
    """`〈72〉-㉮` 의 재현성이 **DB 를 지나서도** 성립하는가."""
    first = _graphed(dictionaries, "재격자화한 한반도 NDVI 자료")
    for _ in range(3):
        assert _graphed(dictionaries, "재격자화한 한반도 NDVI 자료") == first


def test_그래프가_한_일이_없으면_빈_손이다(dictionaries) -> None:
    _, hops = _graphed(dictionaries, "금강 염분 자료")
    assert hops == {}
