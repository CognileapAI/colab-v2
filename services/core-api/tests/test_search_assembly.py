"""검색 결과 조립 — **응답이 정본을 지키는가.**

`K4-a` 가 `services/ai-service/tests/test_search_service.py` 에 세운 오라클 중
**조립에 관한 것**을 옮겼다. 조립이 D10 에서 core-api 로 왔기 때문이다
(Ted 판정 2026-08-25 ㈎). 해석기·사전에 관한 오라클은 ai-service 에 그대로 남아 있다.

  ① **근거는 한 줄이고 필수다** — 줄바꿈이 없고 비어 있지 않다.
  ② **근거는 검색된 이유만 싣는다** — 한계·부정 문장과 질의 공통부(범위·주제·해석 여부)는
     카드 근거에 없다. 같은 사실의 구조형이 `rationaleFacts` 다 (intent
     `2026-09-25-search-rationale-separation.md` Q6·Q7·Q8 · Ted 2026-09-26 승인).
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


#: 카드 근거에 나오면 안 되는 한계·부정 문구 (intent 검증 절 축자 + 종전 공통부).
NEGATIVE = ("확인하지 못", "미확인", "불일치", "보장하지 않", "아니에요", "없었어요", "못했어요")
COMMON = ("A 연구실", "안 3건에서", "좁혀 뒤졌어요", "질의 해석 없이")


def _compose(matches=MATCHES, *, total=None, offset=0, expansions=None):
    return dataset_search.compose(
        matches, expansions=expansions,
        total=len(matches) if total is None else total, offset=offset)


def _texts(hit) -> list[str]:
    return [hit["rationale"], *(i for f in hit["rationaleFacts"] for i in f["items"])]


def test_근거는_필수이고_한_줄이다() -> None:
    items, _ = _compose()
    assert items
    for hit in items:
        assert isinstance(hit["rationale"], str) and hit["rationale"].strip()
        assert "\n" not in hit["rationale"] and "\r" not in hit["rationale"]


def test_근거에_한계_부정_문구가_없다() -> None:
    """Ted 2026-09-26 「뭐뭐는 아니에요 없었어요 같은 표현은 다 빼버리고 검색된 이유만」."""
    items, _ = _compose()
    assert items
    for hit in items:
        for text in _texts(hit):
            assert not [w for w in NEGATIVE if w in text], text


def test_질의_공통부는_카드_근거에_없다() -> None:
    """뒤진 범위·주제·해석 여부는 응답 머리가 한 번 말한다 (`scope`·`topic`·`degraded` · Q8)."""
    items, _ = _compose()
    for hit in items:
        for text in _texts(hit):
            assert not [w for w in COMMON if w in text], text


def test_낱말로_맞으면_낱말_일치_항목이_선다() -> None:
    items, _ = _compose()
    assert items[0]["rationaleFacts"] == [
        {"kind": "term", "items": ["‘강우’가 이름·주제·요약에 맞았어요"]}]


def _term_item(*terms: str) -> str:
    match = SearchMatch(dataset_id=DS1, rank=0.9, matched_terms=terms, where=("이름",))
    return dataset_search.rationale_facts(match)[0]["items"][0]


def test_낱말_일치_조사는_끝_글자_받침을_본다() -> None:
    """받침이 있으면 「이」, 없으면 「가」 — 닫는 따옴표 앞 마지막 한글 음절을 본다."""
    assert _term_item("강우량") == "‘강우량’이 이름에 맞았어요"
    assert _term_item("강수") == "‘강수’가 이름에 맞았어요"
    # 여러 낱말이면 마지막 낱말에 붙는다.
    assert _term_item("강수", "강우량") == "‘강수’, ‘강우량’이 이름에 맞았어요"
    # 한글로 끝나지 않는 낱말은 종전 모양 그대로다.
    assert _term_item("NDVI") == "‘NDVI’가 이름에 맞았어요"


TOPIC = "강우·강수"
DEV_QUERY = "강우 예측 pred_sample.npy 파일의 바로 앞 입력 데이터셋"


def _topic_item(terms, *, query=DEV_QUERY, where=("이름·주제·요약",)) -> str:
    match = SearchMatch(dataset_id=DS1, rank=0.9, matched_terms=tuple(terms), where=where)
    facts = dataset_search.rationale_facts(match, topic=TOPIC, query=query)
    assert [f["kind"] for f in facts] == ["term"]
    return facts[0]["items"][0]


def test_사용자가_치지_않은_주제_라벨은_맞은_낱말에서_빠진다() -> None:
    """헤더가 이미 주제를 말한다 — 확장으로만 들어온 라벨은 낱말 목록에 없다
    (intent `2026-09-26-rationale-facts-wording.md` ② ⑴)."""
    assert _topic_item(["강우", TOPIC]) == "‘강우’가 이름·주제·요약에 맞았어요"


def test_질의에_친_주제_라벨은_남는다() -> None:
    """② ⑵ — 사용자가 친 말이면 맞은 낱말이다. 공백·대소문자는 접어 대조한다."""
    assert _topic_item(["강우", TOPIC], query="강우·강수  자료") == \
        "‘강우’, ‘강우·강수’가 이름·주제·요약에 맞았어요"


def test_주제_라벨만_맞았으면_라벨을_남긴다() -> None:
    """② ⑶ — 근거 필수(`product.md` §3). 문형은 현행 낱말 일치 그대로다(해소 ⒜)."""
    assert _topic_item([TOPIC]) == "‘강우·강수’가 이름·주제·요약에 맞았어요"


def test_라벨을_빼면_다음_실제_낱말이_상한_안에_든다() -> None:
    """② ⑷ — 빼기는 3개 상한 적용 **전**이다."""
    assert _topic_item([TOPIC, "강우", "예측", "pred_sample.npy"]) == \
        "‘강우’, ‘예측’, ‘pred_sample.npy’가 이름·주제·요약에 맞았어요"


def test_낱말_일치_자리_목록에_확인한_파일_근거가_없다() -> None:
    """③ — 파일 근거는 「파일 근거」·「연결된 자료」 종류가 말한다."""
    assert _topic_item(["강우", TOPIC], where=("이름·주제·요약", "확인한 파일 근거")) == \
        "‘강우’가 이름·주제·요약에 맞았어요"


def test_주제_라벨_분리는_한_줄에도_같이_적용된다() -> None:
    """`rationale` 한 줄은 같은 사실에서 다시 만든다 — 패널과 갈라지지 않는다."""
    match = SearchMatch(dataset_id=DS1, rank=0.9, matched_terms=("강우", TOPIC),
                        where=("이름·주제·요약", "확인한 파일 근거"))
    items, _ = dataset_search.compose((match,), total=1, offset=0, topic=TOPIC, query=DEV_QUERY)
    assert items[0]["rationale"] == "‘강우’가 이름·주제·요약에 맞았어요."


def test_관련_개념으로만_맞아도_이유가_하나_이상_있다() -> None:
    """`where == ("온톨로지 연결 근거",)` 만으로 맞은 결과 — 이 항목이 없으면 이유가 0개다
    (근거 필수 · `product.md` §3). 내부 기법 이름(온톨로지)은 화면 문구에 쓰지 않는다."""
    concept = (SearchMatch(dataset_id=DS1, rank=0.3, matched_terms=(),
                           where=("온톨로지 연결 근거",)),)
    items, _ = _compose(concept)
    facts = items[0]["rationaleFacts"]
    assert [f["kind"] for f in facts] == ["concept"] and facts[0]["items"]
    assert all("온톨로지" not in t and "계보" not in t for t in _texts(items[0]))


def test_파일_근거로_맞으면_파일_근거_항목이_선다() -> None:
    evidence = (SearchMatch(dataset_id=DS1, rank=0.3, matched_terms=(),
                            where=("확인한 파일 근거",)),)
    items, _ = _compose(evidence)
    assert [f["kind"] for f in items[0]["rationaleFacts"]] == ["evidence"]
    # 파일 근거로만 맞은 결과는 낱말 일치 항목을 내지 않는다(③ · 해소 ⒝).
    facts = dataset_search.rationale_facts(evidence[0], topic="강우·강수", query="강우")
    assert [f["kind"] for f in facts] == ["evidence"]


def test_한_줄은_사실을_순서대로_이은_것이다() -> None:
    """구 화면(`rationale` 만 읽는 화면)과 새 패널이 같은 사실을 말한다 (미해결 질문 ⒝)."""
    facts = [{"kind": "evidence", "items": ["파일 근거가 맞았어요"]},
             {"kind": "term", "items": ["‘강우’가 이름에 맞았어요"]},
             {"kind": "linked", "items": []}]
    ordered = dataset_search.ordered_facts(facts)
    assert [f["kind"] for f in ordered] == ["term", "evidence"]
    assert dataset_search.rationale_line(ordered) == "‘강우’가 이름에 맞았어요. 파일 근거가 맞았어요."


def test_결과에_숫자_등급_확신도_필드가_없다() -> None:
    items, _ = _compose()
    for hit in items:
        assert set(hit) == {"datasetId", "relevanceBar", "rationale", "rationaleFacts"}
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


def test_근거_한_줄은_해요체다() -> None:
    """화면 검수 2026-09-03 #12 — 제품 문체는 해요체인데 이 줄만 해라체였다.

    근거 문장은 **서버가 만들어 화면이 그대로 싣는다.** 화면만 고쳐서는 닫히지 않는 자리라
    오라클도 여기 산다. 정본 = `Policy_데이터_찾기 §120행`(AI 근거 블록) · 제품 문체 = 해요체.
    """
    items, _ = _compose()
    assert items, "근거를 한 건도 못 만들었다 — 이 시험이 아무것도 안 세고 있다."
    for h in items:
        r = h["rationale"]
        assert r.endswith("요."), f"해요체 종결이 아니다: {r}"
        for 해라체 in ("맞았다", "뒤졌다", "직접 보라"):
            assert 해라체 not in r, f"해라체 «{해라체}» 가 남아 있다: {r}"


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
    # 확장어는 「낱말 일치」 아래다 — 「관련 개념」은 개념 주석 일치에만 쓴다 (미해결 질문 ⒜).
    assert [f["kind"] for f in items[0]["rationaleFacts"]] == ["term"]


def test_같은_말_엣지도_읽어_준다() -> None:
    items, _ = _compose(GRAPHED, expansions={"Nearest": ("같은 말이다", "최근린보간")})
    assert "‘최근린보간’과 같은 말인 ‘Nearest’" in items[0]["rationale"]
    items, _ = _compose(GRAPHED, expansions={"Nearest": ("같은 말이다", "강수")})
    assert "‘강수’와 같은 말인 ‘Nearest’" in items[0]["rationale"]


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
    assert set(json.loads(json.dumps(items[0]))) == {"datasetId", "relevanceBar", "rationale",
                                                     "rationaleFacts"}


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
