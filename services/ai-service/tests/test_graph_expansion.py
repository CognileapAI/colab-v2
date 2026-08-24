"""`K4-b` 그래프 증강의 **순수 규칙** — 확장 경계 넷이 코드에 있는가.

경계 넷의 출처 = `sessions/K1b-ONTOLOGY-CONTENT §D-6` · Ted `F-11` 승인 · `PLAN-SoT §9-〈90〉-㉰`.
  ① **하향 전용** — 질의어가 상위일 때만 하위로 편다. 하위를 물으면 형제가 따라오지 않는다
  ② **깊이 1** — 전이 폐포를 만들지 않는다
  ③ **팬아웃 상한 6** — 직계 하위가 여섯을 넘으면 그 질의어는 **확장하지 않는다**
  ④ **부모 금지 목록** — `expandable=false` 인 노드는 `~의 한 가지다` 의 도착이 될 수 없다

그리고 다섯째 — **넓힌 말마다 「어느 엣지가 일했는가」를 되돌려 준다.** 적을 수 없으면
확장하지 않는다는 §D-6 의 마지막 안전장치를 값으로 만든 것이고, 근거 한 줄의 재료다.

여기에 DB 가 없다. 시드 실물로 같은 규칙을 증명하는 것은 `test_concept_graph_db.py` 다.
"""
from __future__ import annotations

from colab_ai.domains.d9_ontology import (
    INSIDE,
    KIND_OF,
    MAX_FANOUT,
    SAME_AS,
    ConceptEdge,
    ConceptGraph,
    ConceptNode,
    expand_by_graph,
)


def _n(cid: str, label: str, expandable: bool = True) -> ConceptNode:
    return ConceptNode(concept_id=cid, label=label, expandable=expandable)


#: 시드의 축소판. 재격자화 아래 셋 + 영문 표기 둘 + 금지 목록 하나.
GRAPH = ConceptGraph(
    nodes=(
        _n("m-regrid", "재격자화"),
        _n("m-nearest", "최근린보간"),
        _n("m-nearest-en", "Nearest"),
        _n("m-bilinear", "이중선형보간"),
        _n("m-bilinear-en", "Bilinear"),
        _n("m-idw", "IDW"),
        _n("m-preproc", "전처리", expandable=False),
        _n("m-crop", "크롭"),
        _n("p-korea", "한반도"),
        _n("p-chung", "충청권"),
    ),
    edges=(
        ConceptEdge("m-nearest", KIND_OF, "m-regrid"),
        ConceptEdge("m-bilinear", KIND_OF, "m-regrid"),
        ConceptEdge("m-idw", KIND_OF, "m-regrid"),
        ConceptEdge("m-nearest", SAME_AS, "m-nearest-en"),
        ConceptEdge("m-bilinear", SAME_AS, "m-bilinear-en"),
        ConceptEdge("m-crop", KIND_OF, "m-preproc"),
        ConceptEdge("p-chung", INSIDE, "p-korea"),
    ),
)


def _terms(query: str, graph: ConceptGraph = GRAPH) -> tuple[str, ...]:
    return expand_by_graph((), query=query, graph=graph).terms


# ── ① 하향 전용 ──────────────────────────────────────────────────────────────

def test_상위를_물으면_하위가_펴진다() -> None:
    out = _terms("재격자화한 NDVI 자료")
    assert {"최근린보간", "이중선형보간", "IDW"} <= set(out)


def test_하위를_물으면_형제가_따라오지_않는다_상향_금지() -> None:
    """§D-6 두 번째 과확장 — `Bilinear` 하나를 물었는데 셋이 나오면 넷으로 쪼갠 이유가 무너진다."""
    out = _terms("Bilinear 로 만든 자료")
    assert "재격자화" not in out
    assert "최근린보간" not in out and "IDW" not in out


def test_안에_있다도_하향_전용이다() -> None:
    assert "충청권" in _terms("한반도 전체 식생 자료")
    assert "한반도" not in _terms("충청권 자료")


# ── ② 깊이 1 ────────────────────────────────────────────────────────────────

def test_전이_폐포를_만들지_않는다() -> None:
    """상위→하위 한 홉이면 끝이다. 손자를 부르지 않는다."""
    graph = ConceptGraph(
        nodes=(_n("a", "가"), _n("b", "나"), _n("c", "다")),
        edges=(ConceptEdge("b", KIND_OF, "a"), ConceptEdge("c", KIND_OF, "b")),
    )
    out = _terms("가 자료", graph)
    assert "나" in out and "다" not in out


def test_같은_말은_한_홉이다() -> None:
    graph = ConceptGraph(
        nodes=(_n("x", "엑스"), _n("y", "와이"), _n("z", "제트")),
        edges=(ConceptEdge("x", SAME_AS, "y"), ConceptEdge("y", SAME_AS, "z")),
    )
    out = _terms("엑스 자료", graph)
    assert "와이" in out and "제트" not in out


# ── ③ 팬아웃 상한 ────────────────────────────────────────────────────────────

def test_직계_하위가_상한을_넘으면_그_질의어는_확장하지_않는다() -> None:
    kids = tuple(_n(f"k{i}", f"자식{i}") for i in range(MAX_FANOUT + 1))
    graph = ConceptGraph(
        nodes=(_n("p", "넓은말"), *kids),
        edges=tuple(ConceptEdge(f"k{i}", KIND_OF, "p") for i in range(MAX_FANOUT + 1)),
    )
    assert _terms("넓은말 자료", graph) == ()


def test_상한_안이면_전부_펴진다() -> None:
    kids = tuple(_n(f"k{i}", f"자식{i}") for i in range(MAX_FANOUT))
    graph = ConceptGraph(
        nodes=(_n("p", "넓은말"), *kids),
        edges=tuple(ConceptEdge(f"k{i}", KIND_OF, "p") for i in range(MAX_FANOUT)),
    )
    assert len(_terms("넓은말 자료", graph)) == MAX_FANOUT


# ── ④ 부모 금지 목록 ─────────────────────────────────────────────────────────

def test_금지_목록은_도착이_될_수_없다() -> None:
    """「전처리한 강우 자료」가 부풀지 않는 이유 — 확장이 **시작되지 않는다**."""
    assert _terms("전처리한 강우 자료") == ()


def test_금지_목록이어도_같은_말은_막지_않는다() -> None:
    """금지된 것은 `~의 한 가지다` 의 도착이지 표기 변형이 아니다 (§D-6 경계 4 의 글자 그대로)."""
    graph = ConceptGraph(
        nodes=(_n("m-qc", "품질검사", expandable=False), _n("m-dqf", "DQF 마스킹")),
        edges=(ConceptEdge("m-dqf", SAME_AS, "m-qc"),),
    )
    assert "DQF 마스킹" in _terms("품질검사한 자료", graph)


# ── ⑤ 근거에 이름을 적을 수 있다 ─────────────────────────────────────────────

def test_넓힌_말마다_일한_엣지를_되돌려_준다() -> None:
    out = expand_by_graph((), query="재격자화한 NDVI 자료", graph=GRAPH)
    hop = {h.term: h for h in out.hops}
    assert hop["최근린보간"].relation == KIND_OF and hop["최근린보간"].parent == "재격자화"
    # 자식의 표기 변형은 **자식의 근거를 그대로 물려받는다** — §D-6 의 예문이 그 모양이다
    assert hop["Nearest"].relation == KIND_OF and hop["Nearest"].parent == "재격자화"
    assert set(hop) == set(out.terms)


def test_모든_넓힌_말에_근거가_있다_없으면_확장하지_않는다() -> None:
    out = expand_by_graph((), query="한반도 재격자화 자료", graph=GRAPH)
    assert len(out.hops) == len(out.terms)


# ── 결정성 ──────────────────────────────────────────────────────────────────

def test_같은_질의는_같은_순서의_같은_집합을_낸다() -> None:
    a = expand_by_graph((), query="재격자화한 한반도 NDVI", graph=GRAPH)
    for _ in range(5):
        b = expand_by_graph((), query="재격자화한 한반도 NDVI", graph=GRAPH)
        assert b.terms == a.terms and b.hops == a.hops


def test_엣지_순서가_바뀌어도_결과가_같다() -> None:
    """시드 파일의 줄 순서 같은 우연이 검색어 순서를 정하지 않는다."""
    shuffled = ConceptGraph(nodes=tuple(reversed(GRAPH.nodes)),
                            edges=tuple(reversed(GRAPH.edges)))
    assert _terms("재격자화한 NDVI 자료", shuffled) == _terms("재격자화한 NDVI 자료")


def test_이미_있는_말은_다시_붙이지_않는다() -> None:
    out = expand_by_graph(("최근린보간",), query="재격자화한 자료", graph=GRAPH)
    assert "최근린보간" not in out.terms


def test_그래프에_없으면_아무것도_지어내지_않는다() -> None:
    assert _terms("금강 염분 자료") == ()
