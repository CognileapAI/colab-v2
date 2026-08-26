"""질의 해석기 — **LLM 의 일은 여기까지다** (`PLAN-SoT §9-〈72〉-㉮`).

지키는 것 넷
  ① LLM 은 자연어를 **검색어·필터**로만 바꾼다. 순위도 결과 본문도 만들지 않는다.
  ② **키가 없으면 해석기는 조용히 원문을 넘긴다** — 검색 자체는 산다
     (`CLAUDE.md §3` 「AI 없이도 v2 는 완결된 제품이다」).
  ③ LLM 이 이상한 것을 답하면(순위·데이터셋 id·숫자 점수) **버린다.** 지어낸 순서를 받지 않는다.
  ④ 해석이 LLM 없이 이뤄졌다는 사실을 **숨기지 않는다** (`degraded`).
"""
from __future__ import annotations

import json

import pytest

from colab_ai.app.interpret import (SYSTEM_PROMPT, LiteralInterpreter, LlmQueryInterpreter,
                                    _SEED)


def test_llm_없으면_원문이_그대로_검색어가_된다() -> None:
    """**이 시험이 「AI 없이도 검색이 돈다」의 1층이다.**"""
    out = LiteralInterpreter().interpret("낙동강 유역 강우 데이터")
    assert out.is_data_query is True
    assert out.terms == ("낙동강", "유역", "강우", "데이터")
    assert out.topic is None
    assert out.source == "literal"
    assert out.degraded is True
    assert out.degraded_reason


def test_키가_없으면_LLM_해석기가_바로_문자열_해석으로_떨어진다() -> None:
    interp = LlmQueryInterpreter(api_key=None, model="gpt-5.6-luna")
    out = interp.interpret("금강 염분 자료 있나요")
    assert out.source == "literal" and out.degraded is True
    assert "금강" in out.terms


def test_LLM_응답을_검색어와_주제로만_읽는다() -> None:
    body = {"isDataQuery": True, "terms": ["강우", "강수량"], "topic": "강우·강수",
            # ↓ 계약에 없는 것을 LLM 이 얹어도 **읽지 않는다**
            "ranking": ["DSA2", "DSA1"], "score": 0.93, "answer": "이걸 쓰세요"}
    interp = LlmQueryInterpreter(api_key="k", model="m",
                                 transport=lambda payload: json.dumps(body, ensure_ascii=False))
    out = interp.interpret("강수량 데이터 찾아줘")
    assert out.source == "llm" and out.degraded is False
    assert out.terms == ("강우", "강수량")
    assert out.topic == "강우·강수"
    assert not hasattr(out, "ranking") and not hasattr(out, "score")


def test_LLM_이_4값_밖_주제를_말하면_버린다() -> None:
    body = {"isDataQuery": True, "terms": ["가뭄"], "topic": "가뭄지수"}
    interp = LlmQueryInterpreter(api_key="k", model="m",
                                 transport=lambda payload: json.dumps(body, ensure_ascii=False))
    out = interp.interpret("가뭄지수")
    assert out.topic is None          # 4값 CHECK 밖은 조용히 버린다 — 없는 주제를 만들지 않는다
    assert out.terms == ("가뭄",)


def test_LLM_이_데이터_질문이_아니라고_판정할_수_있다() -> None:
    body = {"isDataQuery": False, "terms": [], "topic": None}
    interp = LlmQueryInterpreter(api_key="k", model="m",
                                 transport=lambda payload: json.dumps(body, ensure_ascii=False))
    out = interp.interpret("오늘 점심 뭐 먹지")
    assert out.is_data_query is False and out.degraded is False


@pytest.mark.parametrize("raw", ["", "그건 좀 어렵네요", "{\"terms\": \"강우\"}", "null"])
def test_LLM_이_못_읽을_것을_주면_문자열_해석으로_떨어진다(raw: str) -> None:
    interp = LlmQueryInterpreter(api_key="k", model="m", transport=lambda payload: raw)
    out = interp.interpret("강우 데이터")
    assert out.source == "literal" and out.degraded is True
    assert out.terms == ("강우", "데이터")


def test_LLM_호출이_예외를_던져도_검색어는_남는다() -> None:
    def boom(payload):
        raise TimeoutError("모델이 안 답한다")
    interp = LlmQueryInterpreter(api_key="k", model="m", transport=boom)
    out = interp.interpret("강우 데이터")
    assert out.source == "literal" and out.degraded is True
    assert "모델" in out.degraded_reason or "해석" in out.degraded_reason


def test_프롬프트가_기능어를_검색어로_만들지_말라고_지시한다() -> None:
    """Ted 판정 2026-08-26 ⑴ 첫째 수단. **억제는 모델 쪽에서 한 번 건다.**
    ⚠ 이것만으로는 안 닫힌다 — 모델은 지시를 어길 수 있고, 그래서 서버 필터가 뒤에 선다
    (`d10_ai_services.FUNCTION_WORDS`). 두 겹이 같은 두 낱말을 이름으로 적는다."""
    assert "자료" in SYSTEM_PROMPT and "데이터" in SYSTEM_PROMPT
    assert "기능어" in SYSTEM_PROMPT


def test_프롬프트_정정_3건이_그대로_남아_있다() -> None:
    """`〈112〉-㉳` 의 정정 — 「표기 변형」 절 삭제 · `isDataQuery` 기준 · `seed` 고정.
    기능어 절을 더하면서 앞의 셋을 건드리지 않았다는 것을 값으로 잡는다."""
    assert "표기 변형·동의어·상하위어를 만들지 않는다" in SYSTEM_PROMPT
    assert "isDataQuery 는 다음 기준으로만 정한다" in SYSTEM_PROMPT
    assert _SEED == 20260826
