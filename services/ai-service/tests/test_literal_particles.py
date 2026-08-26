"""낱말 해석에서 **홀로 선 조사**를 검색어로 만들지 않는다 (`PLAN-SoT §9 〈142〉`).

`〈136〉` 으로 LLM 해석을 끄자 **회귀가 하나 드러났다.** 조사를 걷어 주던 것이
모델이었고, 낱말 해석은 공백·구두점에서만 자르므로 **조사가 검색어로 살아남는다.**

**배포 실물로 잡았다** (staging, 2026-08-27) — 「Bilinear 로 만든 자료」가 **3건**을
냈고 정답은 하나다. 세 번째 행의 근거가 「**‘로’**가 맞았다」뿐이었다. 조사 하나가
엉뚱한 데이터셋을 끌어온 것이다.

⚠ **조사를 불용어 목록으로 막는 것은 틀린 접근이다 — 재 보고 알았다.**
검색은 **접두 질의**라(`〈89〉-㉮①`) 한 글자가 낱말의 앞을 잡는다. 실측(적재 12건):
`이` 6건(「이름」) · `한` 6건(「한반도」) · `가` 5건(「가공」) · `의` 5건. 이것들을
불용어로 빼면 **진짜 검색이 죽는다.**

**그래서 「홀로 선 것」만 뺀다.** 공백으로 잘려 혼자 남은 한 음절 조사는 검색 의도를
담을 수 없다. 같은 글자가 낱말 안에 있을 때는 건드리지 않는다 — 자르는 단위가 다르다.
"""
from __future__ import annotations

from colab_ai.app.interpret import LiteralInterpreter


def _terms(query: str) -> tuple[str, ...]:
    return LiteralInterpreter(LiteralInterpreter.BY_DESIGN_REASON).interpret(query).terms


def test_a_standalone_particle_is_not_a_search_term(query="Bilinear 로 만든 자료") -> None:
    """**배포 실물에서 잡힌 그 질의다.**"""
    terms = _terms(query)
    assert "로" not in terms, f"조사가 검색어로 남았다: {terms}"
    assert "Bilinear" in terms, "정작 찾으려던 말은 남아야 한다"


def test_particles_inside_a_word_are_untouched() -> None:
    """**같은 글자라도 낱말 안이면 건드리지 않는다.** 자르는 단위가 다르다."""
    assert "한반도" in _terms("한반도 강수")
    assert "이름" in _terms("이름 으로 찾기")
    assert "가공" in _terms("가공 단계")


def test_a_single_word_query_is_never_emptied() -> None:
    """**사용자가 친 유일한 낱말은 빼지 않는다.**

    이 규칙이 없으면 「의」 한 글자를 친 사람에게 「찾을 말이 없다」가 아니라
    **아무 일도 안 일어난 것처럼** 보인다. 뺄 수는 있어도 **비울 수는 없다.**
    """
    assert _terms("로") == ("로",)
    assert _terms("의") == ("의",)


def test_a_query_of_only_particles_keeps_something() -> None:
    """전부 조사여도 **빈 검색어를 만들지 않는다** — 그 판정은 상위 필터의 몫이다."""
    terms = _terms("의 를 로")
    assert terms, "검색어가 통째로 비었다 — 「찾을 말이 없다」 판정을 여기서 하지 않는다"


def test_meaningful_words_survive() -> None:
    """**과잉 제거 금지** — `FUNCTION_WORDS` 주석이 세운 규율 그대로다."""
    terms = _terms("천리안위성2A호 자료")
    assert "천리안위성2A호" in terms
    terms2 = _terms("한강 유역 강수 자료")
    for word in ("한강", "유역", "강수"):
        assert word in terms2, f"{word} 가 사라졌다"
