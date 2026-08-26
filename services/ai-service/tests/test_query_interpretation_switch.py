"""이번 릴리즈의 검색은 **낱말 그대로**다 — 결정으로 그렇게 둔 것이지 무너진 것이 아니다.

`PLAN-SoT §9 〈136〉`(Ted 2026-08-27 · ㈎ 채택). 정본 결정 2-5 = 「이번 릴리즈는 조건
검색만. 자연어 검색은 넣지 않는다」. 다만 결정문 스스로 **「빼는 결정이 아니라 순서
결정」**이라 적었으므로, **인프라·평가셋·회귀 게이트는 살려 두고 해석만 끈다.**

**왜 키를 빼는 방식으로 하지 않는가.**
종전 선택 규칙은 「`OPENAI_API_KEY` 가 있으면 LLM」이었다. 키를 빼서 끄면
① 결정이 **코드에 안 보이고** ② Phase 2 에 **켤 자리가 안 남으며**
③ 「키를 못 넣은 것」과 「안 쓰기로 한 것」이 **같은 상태로 보인다.**
`〈136〉-㉲` 가 요구한 것은 그 반대다 — **켜는 시점을 값으로 정할 수 있어야 한다.**

**그리고 사용자에게 「무너졌다」고 말하지 않는다.**
`degraded` 는 원래 「해석이 실패했다」는 뜻이라 사유 문구도 그렇게 적혀 있다. 일부러
낱말 검색을 고른 회차에 그 문구를 그대로 내면 **화면이 거짓말을 한다** — 사용자는
「지금 고장 났구나, 나중에 다시 해야지」로 읽는다.
"""
from __future__ import annotations

from colab_ai.app.interpret import LiteralInterpreter, LlmQueryInterpreter
from colab_ai.kernel.config import Settings


def test_default_is_literal_even_when_a_model_key_is_present():
    """**키가 있어도 기본은 낱말 검색이다** — 이번 릴리즈의 결정이 기본값이다."""
    s = Settings.from_env({"OPENAI_API_KEY": "sk-테스트"})
    assert s.query_interpretation == "literal"


def test_llm_is_opt_in_and_needs_both_the_switch_and_the_key():
    """Phase 2 에서 켤 자리. **스위치 하나로 켜지지 않는다 — 키도 있어야 한다.**"""
    switched = Settings.from_env({"COLAB_AI_QUERY_INTERPRETATION": "llm",
                                  "OPENAI_API_KEY": "sk-테스트"})
    assert switched.query_interpretation == "llm"

    keyless = Settings.from_env({"COLAB_AI_QUERY_INTERPRETATION": "llm"})
    assert keyless.query_interpretation == "llm", "설정은 설정대로 읽힌다"
    assert keyless.openai_api_key is None, "키가 없으면 조립이 문자열 해석으로 남는다"


def test_an_unknown_value_falls_back_to_literal_and_does_not_crash():
    """모르는 값이 오면 **끈 쪽으로** 떨어진다 — 오타가 검색을 몰래 켜지 않는다."""
    assert Settings.from_env(
        {"COLAB_AI_QUERY_INTERPRETATION": "llm-ish"}).query_interpretation == "literal"


def test_the_reason_says_it_is_a_decision_not_a_breakage():
    """**사용자가 읽는 문장이다.** 일부러 고른 상태를 「못 했다」로 말하지 않는다."""
    reason = LiteralInterpreter.BY_DESIGN_REASON
    assert "낱말" in reason
    for broken in ("실패", "무너", "오류", "안 되", "못 했"):
        assert broken not in reason, f"결정을 고장으로 말하고 있다: {reason}"


def test_the_breakage_reason_still_exists_and_is_different():
    """**둘을 접지 않는다.** 진짜로 해석이 실패한 회차는 여전히 그렇게 말해야 한다."""
    fallback = LiteralInterpreter()
    by_design = LiteralInterpreter(LiteralInterpreter.BY_DESIGN_REASON)
    assert fallback.interpret("강수").degraded_reason \
        != by_design.interpret("강수").degraded_reason


def test_literal_interpretation_still_finds_words_and_never_judges_the_question():
    """끈 상태에서도 **검색은 진짜로 돈다.** 0건이 아니라 낱말로 찾는다."""
    r = LiteralInterpreter(LiteralInterpreter.BY_DESIGN_REASON).interpret("한강 강수 자료")
    assert r.terms == ("한강", "강수", "자료")
    assert r.is_data_query is True, "판정한 적 없는 것을 말하지 않는다"
    assert r.source == "literal"


def test_the_llm_interpreter_class_is_not_deleted():
    """**되돌리기가 아니라 순서다** — Phase 2 가 쓸 코드를 지우지 않는다(`〈136〉-㉰`)."""
    assert LlmQueryInterpreter is not None
