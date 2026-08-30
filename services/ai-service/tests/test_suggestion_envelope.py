"""제안 응답의 조립 — **0건을 사유 없이 내지 못한다.**

이 레포의 대표 실패형은 「검사 대상이 0건인데 통과」다. 제안 기능은 재료가 없으면
무엇이든 0건이라 그 실패형이 **기본 동작**으로 나온다. 그래서 조립기를 세 상태로 만든다.

  ⓐ 제안이 **있다**        → 전건을 타입으로 검증한다. 하나라도 규격 밖이면 만들지 않는다
  ⓑ **0건을 명시 선언**한다 → 통과하되 **건수와 사유를 응답에 드러낸다**
  ⓒ **아무 선언도 없다**   → **실패한다.** 「말하지 않은 0건」을 통과로 세지 않는다
"""
from __future__ import annotations

import json

import pytest

from colab_ai.domains.d10_suggestion import (KIND_PARENT, Suggestion,
                                             SuggestionEnvelope)

LAB = "0000000000000000000000000A"
OK_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"


def _one():
    return Suggestion(suggestion_id=OK_ID, kind=KIND_PARENT, confidence="애매",
                      rationale="이름과 기간이 겹친다",
                      parent_dataset_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
                      parent_dataset_name="강우 원자료")


def _env(**over):
    kw = dict(lab_id=LAB, lab_name="A 연구실", searched_count=12,
              raw_data_likely=False)
    kw.update(over)
    return SuggestionEnvelope(**kw)


# ── ⓐ 대상이 있으면 검사한다 ────────────────────────────────────────────────
def test_제안이_있으면_전건을_타입으로_검증한다() -> None:
    body = _env().build(suggestions=[_one()])
    assert len(body["suggestions"]) == 1
    assert body["suggestions"][0]["confidence"] == "애매"


def test_타입을_지나지_않은_제안은_실릴_수_없다() -> None:
    """dict 를 그대로 실으면 확신도·근거 검사가 통째로 건너뛰어진다."""
    with pytest.raises(TypeError):
        _env().build(suggestions=[{"kind": KIND_PARENT, "confidence": "확실"}])


# ── ⓑ 0건을 선언하면 건수를 드러낸 채 통과한다 ──────────────────────────────
def test_선언된_0건은_건수와_사유를_응답에_드러낸다() -> None:
    body = _env().build(suggestions=[], empty_declaration="후보를 실을 자리가 요청에 없다")
    assert body["suggestions"] == []
    assert body["degraded"] is True, "재료가 없어 못 만든 것은 「찾았는데 없다」가 아니다"
    reason = body["degradedReason"]
    assert "0건" in reason, "몇 건인지 응답이 스스로 말해야 한다"
    assert "12" in reason, "뒤진 범위의 개수를 사유가 되짚어야 한다"
    assert "후보를 실을 자리가 요청에 없다" in reason


# ── ⓒ 아무 선언도 없으면 실패한다 ───────────────────────────────────────────
def test_선언_없는_0건은_통과하지_못한다() -> None:
    with pytest.raises(ValueError):
        _env().build(suggestions=[])


def test_목록_자체가_없으면_통과하지_못한다() -> None:
    """`None` 은 「0건」이 아니라 「말하지 않았다」다 — 둘을 같은 값으로 접지 않는다."""
    with pytest.raises(ValueError):
        _env().build(suggestions=None)


# ── 범위를 먼저 밝힌다 ──────────────────────────────────────────────────────
def test_뒤진_범위가_직렬화된_바이트에서도_제안보다_앞이다() -> None:
    raw = json.dumps(_env().build(suggestions=[_one()]), ensure_ascii=False)
    assert raw.index('"scope"') < raw.index('"suggestions"')


def test_범위가_요청의_연구실을_그대로_되비춘다() -> None:
    scope = _env().build(suggestions=[_one()])["scope"]
    assert scope == {"labId": LAB, "labName": "A 연구실", "searchedCount": 12}


def test_뒤진_대상이_0건인_것과_찾고_못_찾은_것이_갈린다() -> None:
    """음성 판정이 공짜가 되는 자리 — `searchedCount` 가 그 둘을 가른다."""
    none_to_search = _env(searched_count=0).build(
        suggestions=[], empty_declaration="연구실에 뒤질 데이터가 없다")
    assert none_to_search["scope"]["searchedCount"] == 0
    assert _env().build(suggestions=[_one()])["scope"]["searchedCount"] == 12


def test_원자료_판정을_지어내지_않는다() -> None:
    """`가공 흔적이 없어 원자료로 판정되면` 의 **판정 방법을 정본이 적지 않았다**.

    그래서 이 서비스는 원자료라고 **주장하지 않는다** — 주장하면 화면이
    `원천 표기만 남기면 된다` 를 근거 없이 띄운다.
    """
    body = _env().build(suggestions=[], empty_declaration="재료 없음")
    assert body["rawDataLikely"] is False
