"""계보 제안 **한 장**의 타입 — 확신도 enum 과 근거 필수를 **값이 아니라 타입이 지킨다**.

정본이 못 박은 것 넷을 여기서 강제한다 (`CLAUDE.md §3 AI 응답 규격` ·
`Policy_업로드와_계보_확정 §1.3-6`·`§4 용어(확신도)` · `PRD §5.2 Out-of-scope`).

  ① 확신도는 `확실 | 애매 | 모름` **enum** — 숫자·퍼센트가 들어올 자리가 없다
  ② 근거는 **필수**이고 nullable 이 아니다 (`common.json#AiRationale` minLength 1)
  ③ 근거는 **한 줄** — 줄바꿈을 허용하지 않는다 (`AiRationale` pattern `^[^\n\r]+$`)
  ④ 제안 종류는 계약의 두 값뿐이다

⚠ **왜 타입인가.** 이 서비스가 지금 내는 제안이 0건이라 「검사 대상이 0건인데 통과」가
공짜로 난다. 그래서 규격을 **응답 검사**가 아니라 **제안을 만드는 자리**에 둔다 —
아래 픽스처가 그 자리에 실제 대상을 세워 red 를 증명한다.
"""
from __future__ import annotations

import pytest

from colab_ai.domains.d10_suggestion import (CONFIDENCE_VALUES, KIND_METHOD,
                                             KIND_PARENT, Suggestion)

OK_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
OK_PARENT = "01ARZ3NDEKTSV4RRFFQ69G5FAW"


def _parent(**over):
    kw = dict(suggestion_id=OK_ID, kind=KIND_PARENT, confidence="확실",
              rationale="같은 격자·같은 기간이고 이름이 이어진다",
              parent_dataset_id=OK_PARENT, parent_dataset_name="강우 원자료")
    kw.update(over)
    return Suggestion(**kw)


def _method(**over):
    kw = dict(suggestion_id=OK_ID, kind=KIND_METHOD, confidence="애매",
              rationale="변수 이름이 일 단위 합계를 가리킨다",
              method_text="일 단위로 합쳤다")
    kw.update(over)
    return Suggestion(**kw)


# ── 대상이 실재하는 자리 (green 이어야 한다) ─────────────────────────────────
def test_정상_제안은_계약_열쇠를_갖는다() -> None:
    body = _parent().to_dict()
    assert body["kind"] == KIND_PARENT
    assert body["confidence"] in CONFIDENCE_VALUES
    assert body["rationale"]
    assert body["parentDatasetId"] == OK_PARENT
    assert body["suggestedParentRole"] == "주입력", "정본 기본값(`§5 부모 역할`)"


def test_가공_방식_제안도_같은_두_값을_지고_간다() -> None:
    body = _method().to_dict()
    assert body["confidence"] in CONFIDENCE_VALUES
    assert body["rationale"]
    assert body["methodText"] == "일 단위로 합쳤다"


# ── red 픽스처 — 규격을 어긴 제안은 **만들어지지 않는다** ────────────────────
@pytest.mark.parametrize("bad", ["높음", "", None, "확실함"])
def test_enum_밖의_확신도는_제안이_되지_않는다(bad) -> None:
    with pytest.raises(ValueError):
        _parent(confidence=bad)


@pytest.mark.parametrize("bad", [0.87, 87, 1, True])
def test_숫자_확신도는_제안이_되지_않는다(bad) -> None:
    """퍼센트 금지가 「그런 필드를 안 쓴다」가 아니라 **못 만든다**여야 한다."""
    with pytest.raises(ValueError):
        _parent(confidence=bad)


@pytest.mark.parametrize("bad", [None, "", "   "])
def test_근거가_없으면_제안이_되지_않는다(bad) -> None:
    """`근거 없는 제안은 내놓지 않는 것이 전제다` (`Policy §10`)."""
    with pytest.raises(ValueError):
        _parent(rationale=bad)


@pytest.mark.parametrize("bad", ["두 줄\n짜리 근거", "캐리지\r리턴"])
def test_근거는_한_줄이다(bad) -> None:
    with pytest.raises(ValueError):
        _parent(rationale=bad)


def test_계약에_없는_제안_종류는_만들어지지_않는다() -> None:
    with pytest.raises(ValueError):
        _parent(kind="아무거나")


def test_가공_전_데이터_제안은_부모_식별자_없이_만들어지지_않는다() -> None:
    """계약 `ParentCandidateSuggestion` 의 required 를 타입이 진다 — 지어내지 않는다."""
    with pytest.raises(ValueError):
        _parent(parent_dataset_id=None)
    with pytest.raises(ValueError):
        _parent(parent_dataset_name="")


def test_가공_방식_제안은_문장_없이_만들어지지_않는다() -> None:
    with pytest.raises(ValueError):
        _method(method_text="")


def test_가공_방식_문장은_120자를_넘지_않는다() -> None:
    """`Policy §5 가공 방식 문장 — 1~120자`."""
    with pytest.raises(ValueError):
        _method(method_text="가" * 121)


def test_직렬화된_제안에_숫자_점수_열쇠가_없다() -> None:
    body = _parent().to_dict()
    for forbidden in ("score", "confidencePercent", "probability", "percent", "rank"):
        assert forbidden not in body


def test_묶음_승인_열쇠가_제안에_없다() -> None:
    """`[모두 승인] 없음` — 묶음 상태 필드도 두지 않는다 (`PRD §5.2`)."""
    body = _parent().to_dict()
    for forbidden in ("approveAll", "approved", "batchStatus", "selected"):
        assert forbidden not in body
