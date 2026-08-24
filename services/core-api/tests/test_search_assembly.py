"""검색 결과 조립 — **응답이 정본을 지키는가.**

`K4-a` 가 `services/ai-service/tests/test_search_service.py` 에 세운 오라클 중
**조립에 관한 것**을 옮겼다. 조립이 D10 에서 core-api 로 왔기 때문이다
(Ted 판정 2026-08-25 ㈎). 해석기·사전에 관한 오라클은 ai-service 에 그대로 남아 있다.

  ① **근거는 한 줄이고 필수다** — 줄바꿈이 없고 비어 있지 않다.
  ② **한계를 같은 줄에서 밝힌다** — 좋은 점만 적는 줄을 만들지 않는다.
  ③ **숫자·퍼센트·확신도 필드가 없다** (`CLAUDE.md §3 AI 응답 규격`).
  ④ **순위는 결정적이다** — `ts_rank_cd` 내림차순, 동점은 식별자 오름차순 (`〈72〉-㉮`).
  ⑤ **0건은 정직한 빈 상태**다.
"""
from __future__ import annotations

import json

from colab_core.app import dataset_search
from colab_core.domains.d3_catalog import SearchMatch

DS1 = "0000000000000000000000DSA1"
DS2 = "0000000000000000000000DSA2"
MATCHES = (
    SearchMatch(dataset_id=DS2, rank=0.9, matched_terms=("강우",), where=("이름·주제·요약",)),
    SearchMatch(dataset_id=DS1, rank=0.4, matched_terms=("강우",),
                where=("이름·주제·요약", "포맷·변수")),
)


def _compose(matches=MATCHES, *, total=None, offset=0, topic=None, degraded=False,
             expansions=None):
    return dataset_search.compose(
        matches, lab_name="A 연구실", searched=3, topic=topic,
        interpretation_degraded=degraded, expansions=expansions,
        total=len(matches) if total is None else total, offset=offset)


def test_근거는_필수이고_한_줄이다() -> None:
    items, _ = _compose()
    assert items
    for hit in items:
        assert isinstance(hit["rationale"], str) and hit["rationale"].strip()
        assert "\n" not in hit["rationale"] and "\r" not in hit["rationale"]


def test_한계를_같은_줄에서_밝힌다() -> None:
    items, _ = _compose()
    assert all("못" in h["rationale"] or "않" in h["rationale"] for h in items)


def test_뒤진_범위를_근거_한_줄이_먼저_말한다() -> None:
    """`Policy_데이터_찾기 §3.3` — 「우리 연구실 데이터 N개를 뒤졌지만…」."""
    items, _ = _compose()
    assert all(h["rationale"].startswith("A 연구실 안 3건에서") for h in items)


def test_결과에_숫자_등급_확신도_필드가_없다() -> None:
    items, _ = _compose()
    for hit in items:
        assert set(hit) == {"datasetId", "relevanceBar", "rationale"}
        assert "%" not in hit["rationale"]
    assert "확신도" not in json.dumps(items, ensure_ascii=False)


def test_순위가_결정적이다() -> None:
    first, _ = _compose()
    second, _ = _compose()
    assert [h["datasetId"] for h in first] == [h["datasetId"] for h in second] == [DS2, DS1]


def test_같은_점수면_식별자_오름차순으로_고정된다() -> None:
    tied = (SearchMatch(dataset_id=DS2, rank=0.5, matched_terms=("강우",), where=("이름·주제·요약",)),
            SearchMatch(dataset_id=DS1, rank=0.5, matched_terms=("강우",), where=("이름·주제·요약",)))
    items, _ = _compose(tied)
    assert [h["datasetId"] for h in items] == [DS1, DS2]


def test_막대는_0과_1_사이다() -> None:
    items, _ = _compose()
    bars = [h["relevanceBar"] for h in items]
    assert all(0.0 <= b <= 1.0 for b in bars) and bars == sorted(bars, reverse=True)


def test_영건은_정직한_빈_상태다() -> None:
    items, next_cursor = _compose(())
    assert items == [] and next_cursor is None


def test_이어보기_토큰은_더_없을_때_null_이다() -> None:
    _, next_cursor = _compose()
    assert next_cursor is None


def test_남은_것이_있으면_이어보기_토큰이_선다() -> None:
    items, next_cursor = _compose(total=10)
    assert next_cursor and dataset_search.decode_cursor(next_cursor) == len(items)


def test_주제로_좁혔으면_근거가_그렇게_말한다() -> None:
    items, _ = _compose(topic="강우·강수")
    assert all("주제 강우·강수" in h["rationale"] for h in items)


def test_해석_없이_찾았으면_근거가_그_사실을_밝힌다() -> None:
    """**「AI 없이도 검색이 돈다」를 근거 한 줄이 숨기지 않는다.**"""
    items, _ = _compose(degraded=True)
    assert all("질의 해석 없이" in h["rationale"] for h in items)


def test_망가진_커서는_처음부터다() -> None:
    assert dataset_search.decode_cursor("!!!") == 0
    assert dataset_search.decode_cursor(None) == 0


# ─────────────────────────────────────────────────────────────────────────────
# K4-b — **근거 한 줄이 그래프가 한 일을 이름으로 말한다** (`PLAN-SoT §9-〈90〉-㉱`)
#
# 「확장으로 걸린 결과는 근거 한 줄에 그 엣지를 이름으로 적을 수 있어야 한다. 적을 수
# 없으면 확장하지 않는다」 — `sessions/K1b-ONTOLOGY-CONTENT §D-6` 의 다섯째 안전장치다.
# 그 문장을 만드는 것은 core-api 이므로 오라클도 여기 산다.
# ─────────────────────────────────────────────────────────────────────────────

GRAPHED = (SearchMatch(dataset_id=DS1, rank=0.9, matched_terms=("Nearest",),
                       where=("이름·주제·요약",)),)


def test_그래프가_데려온_말이면_엣지를_이름으로_적는다() -> None:
    items, _ = _compose(GRAPHED, expansions={"Nearest": ("~의 한 가지다", "재격자화")})
    assert "‘재격자화’의 한 가지인 ‘Nearest’" in items[0]["rationale"]


def test_같은_말_엣지도_읽어_준다() -> None:
    items, _ = _compose(GRAPHED, expansions={"Nearest": ("같은 말이다", "최근린보간")})
    assert "‘최근린보간’와 같은 말인 ‘Nearest’" in items[0]["rationale"]


def test_안에_있다_엣지도_읽어_준다() -> None:
    items, _ = _compose(GRAPHED, expansions={"Nearest": ("안에 있다", "한반도")})
    assert "‘한반도’ 안에 있는 ‘Nearest’" in items[0]["rationale"]


def test_그래프가_안_데려온_말은_예전_문장_그대로다() -> None:
    items, _ = _compose(expansions={"Nearest": ("~의 한 가지다", "재격자화")})
    assert "‘강우’가" in items[0]["rationale"] and "한 가지" not in items[0]["rationale"]


def test_그래프_근거를_붙여도_여전히_한_줄이고_숫자가_없다() -> None:
    items, _ = _compose(GRAPHED, expansions={"Nearest": ("~의 한 가지다", "재격자화")})
    line = items[0]["rationale"]
    assert "\n" not in line
    assert "%" not in line
    assert set(json.loads(json.dumps(items[0]))) == {"datasetId", "relevanceBar", "rationale"}


def test_모르는_관계는_지어내지_않고_예전_문장으로_떨어진다() -> None:
    """저쪽이 계약 밖 관계를 보내와도 **근거가 그것을 사용자에게 옮기지 않는다.**"""
    items, _ = _compose(GRAPHED, expansions={"Nearest": ("비슷하다", "재격자화")})
    assert "‘Nearest’가" in items[0]["rationale"] and "비슷하다" not in items[0]["rationale"]


def test_그래프_확장이_순위를_바꾸지_않는다() -> None:
    """**그래프는 검색어만 넓힌다** (`〈72〉-㉮`). 같은 후보면 같은 순서·같은 막대다."""
    plain, _ = _compose()
    graphed, _ = _compose(expansions={"강우": ("~의 한 가지다", "강수")})
    assert [h["datasetId"] for h in plain] == [h["datasetId"] for h in graphed]
    assert [h["relevanceBar"] for h in plain] == [h["relevanceBar"] for h in graphed]
