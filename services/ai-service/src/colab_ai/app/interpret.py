"""질의 해석기 — `ports.QueryInterpreterPort` 의 구현 둘.

`〈72〉-㉮` 가 그은 선을 코드로 옮긴 파일이다. **LLM 이 하는 일은 자연어를 검색어·필터로
바꾸는 것까지다.** 그래서 이 파일은 응답에서 **딱 세 값만 읽는다** — `isDataQuery` ·
`terms` · `topic`. 모델이 순위·데이터셋 식별자·점수·결과 문장을 얹어 보내도 **읽지 않는다.**
읽는 순간 순서가 모델의 것이 되고, 같은 질의가 때마다 다른 답을 내며, 근거 한 줄이
사후 정당화가 된다.

**두 해석기가 같은 표면을 갖는다.**
  · `LlmQueryInterpreter` — 키가 있고 모델이 답할 때. 실패하면 **예외 대신** 아래로 떨어진다.
  · `LiteralInterpreter`  — 질문을 낱말로 자르는 것이 전부. **키가 없어도 검색은 여기서 산다.**

`OPENAI_API_KEY` 는 이미 배선돼 있다(`infra/staging/compose.i2.yml` · `PLAN-SoT §9-㊷`).
없을 때가 예외 상황이 아니라 **지원되는 상태**라는 것이 이 파일의 요지다.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Callable

from colab_ai.ports import TOPICS, Interpretation

#: 모델에게 주는 지시. **답의 모양을 여기서 닫는다** — 셋 말고는 요구하지 않는다.
SYSTEM_PROMPT = (
    "너는 수문학 연구실 데이터 검색의 **질의 해석기**다. 답을 고르지 않는다. "
    "사용자의 한국어 질문을 검색어와 주제 필터로만 바꾼다. "
    'JSON 하나만 출력한다: {"isDataQuery": bool, "terms": [string], "topic": string|null}. '
    "terms 는 질문에 실제로 있는 말만이다 — 표기 변형·동의어·상하위어를 만들지 않는다. "
    "표기가 다른 같은 말을 잇는 것은 사전·그래프의 일이다. "
    "「자료」·「데이터」처럼 무엇을 찾든 붙는 기능어는 terms 에 싣지 않는다 — "
    "그 말은 찾을 대상을 좁히지 못하고 무관한 데이터셋을 통째로 부른다. "
    "찾을 대상을 가리키는 말(이름·주제·지역·기간·기법)만 남긴다. "
    "isDataQuery 는 다음 기준으로만 정한다 — 질문이 자료·데이터를 찾는 뜻이면 true. "
    "낱말 하나, 잘려 쓴 말, 오타, 뜻을 모르는 말도 true 다 — 찾을 대상으로 그대로 넘긴다. "
    "false 는 인사·잡담·이 시스템 사용법 질문처럼 찾을 대상이 없는 경우뿐이다. "
    f"topic 은 다음 넷 중 하나이거나 null 이다: {', '.join(TOPICS)}. "
    "순위·설명·데이터셋 이름·점수를 만들지 않는다."
)

#: 요청 본문에 고정으로 싣는 `seed`. 값 자체에 뜻은 없다 — 회차 간 같기만 하면 된다.
_SEED = 20260826

#: 낱말 자르기. 공백과 흔한 구두점에서만 자른다 — `·` 는 주제 표기(`강우·강수`)의 일부라 남긴다.
_SPLIT = re.compile(r"[\s,.;:!?\"'()\[\]{}/\\|]+")


#: **홀로 선 조사.** 공백으로 잘려 혼자 남았을 때만 뺀다 (`PLAN-SoT §9 〈142〉`).
#:
#: `〈136〉` 으로 모델 해석을 끄자 회귀가 드러났다 — 조사를 걷어 주던 것이 모델이었고,
#: 낱말 해석은 공백·구두점에서만 자르므로 **조사가 검색어로 살아남는다.**
#: 배포 실물에서 「Bilinear 로 만든 자료」가 3건을 냈고 정답은 하나였다. 세 번째 행의
#: 근거가 「‘로’가 맞았다」뿐 — **조사 하나가 엉뚱한 데이터셋을 끌어왔다.**
#:
#: ⚠ **불용어 목록으로 막는 것은 틀린 접근이다 — 재 보고 알았다.** 검색은 접두 질의라
#: (`〈89〉-㉮①`) 한 글자가 낱말의 앞을 잡는다. 실측(적재 12건) — `이` 6건(「이름」) ·
#: `한` 6건(「한반도」) · `가` 5건(「가공」) · `의` 5건. 이것들을 통째로 빼면 **진짜
#: 검색이 죽는다.** 그래서 **자른 뒤 혼자 남은 토큰**에만 적용한다. 낱말 안의 같은
#: 글자는 건드리지 않는다 — 자르는 단위가 다르다.
_STANDALONE_PARTICLES = frozenset({
    "이", "가", "은", "는", "을", "를", "의", "에", "에서", "에게", "께",
    "와", "과", "로", "으로", "도", "만", "부터", "까지", "보다", "처럼",
    "라", "이라", "한", "및",
})


def _tokens(query: str) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for raw in _SPLIT.split(query or ""):
        token = raw.strip()
        if token:
            seen.setdefault(token, None)
    tokens = tuple(seen)
    kept = tuple(t for t in tokens if t not in _STANDALONE_PARTICLES)
    # **뺄 수는 있어도 비울 수는 없다.** 사용자가 친 유일한 낱말이 조사여도 그대로 둔다 —
    # 여기서 비우면 「찾을 말이 없다」 판정을 이 함수가 몰래 내리는 것이 되고,
    # 그 판정은 상위 필터(`strip_function_words` 뒤)의 몫이다.
    return kept or tokens


class LiteralInterpreter:
    """**모델 없이 하는 해석.** 질문을 낱말로 자르고 끝이다.

    `is_data_query` 를 언제나 참으로 둔다 — 「데이터를 찾는 질문이 아니다」는 **판정**이고,
    판정한 적 없는 것을 말하지 않는다 (core-api `unreadable_interpretation` 과 같은 규율).

    ⚠ **사유 문구가 두 가지다. 접지 않는다** (`〈136〉`).
    같은 「낱말 그대로 찾음」이라도 **해석이 실패해서 떨어진 것**과 **이번 릴리즈가 그렇게
    하기로 한 것**은 사용자에게 다른 사실이다. 기본 문구를 결정 회차에 그대로 내면
    화면이 거짓말을 한다 — 사용자는 「지금 고장 났구나, 나중에 다시 해야지」로 읽고
    **되지도 않을 재시도를 한다.**
    """

    #: **결정으로 고른 상태**의 사유. `〈136〉` ㈎ 회차가 쓴다.
    #: 고장을 뜻하는 말(실패·무너짐·오류)을 쓰지 않는다 — 이 문장은 사용자가 읽는다.
    BY_DESIGN_REASON = (
        "이번에는 질문의 낱말 그대로 찾아요. 적혀 있을 법한 말로 물어보면 잘 나와요.")

    def __init__(self, reason: str | None = None) -> None:
        self._reason = reason or "질의 해석 모델을 쓰지 않았다 — 질문의 낱말 그대로 찾았다."

    def interpret(self, query: str) -> Interpretation:
        return Interpretation(is_data_query=True, terms=_tokens(query), topic=None,
                              source="literal", degraded=True, degraded_reason=self._reason)


class LlmQueryInterpreter:
    """모델로 해석하고, **안 되면 조용히 문자열 해석으로 떨어진다.**"""

    def __init__(self, *, api_key: str | None, model: str,
                 transport: Callable[[dict], str] | None = None,
                 timeout_seconds: float = 8.0,
                 base_url: str = "https://api.openai.com/v1/chat/completions") -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._base_url = base_url
        self._transport = transport or self._http_transport

    # ── 전송 ────────────────────────────────────────────────────────────────
    def _http_transport(self, payload: dict) -> str:
        req = urllib.request.Request(
            self._base_url, method="POST",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self._api_key}"})
        with urllib.request.urlopen(req, timeout=self._timeout) as res:
            body = json.loads(res.read() or b"{}")
        return body["choices"][0]["message"]["content"]

    # ── 해석 ────────────────────────────────────────────────────────────────
    def interpret(self, query: str) -> Interpretation:
        if not self._api_key:
            return LiteralInterpreter(
                "질의 해석 모델 자격 증명이 없다 — 질문의 낱말 그대로 찾았다.").interpret(query)
        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": query}],
            "response_format": {"type": "json_object"},
            # 진동 완화. **결정성 보장이 아니다** — 공급자 무보증이고, 종단 결정성은
            # `〈112〉` 로 요구 대상 밖이다. `temperature` 는 넣지 않는다 —
            # `gpt-5.6-luna` 가 `temperature: 0` 을 400 `unsupported_value` 로 거부한다(2026-08-26 실측).
            "seed": _SEED,
        }
        try:
            raw = self._transport(payload)
        except (urllib.error.URLError, TimeoutError, OSError, KeyError,
                ValueError, IndexError) as e:
            return LiteralInterpreter(
                f"질의 해석 모델에 닿지 못했다({e}) — 질문의 낱말 그대로 찾았다.").interpret(query)
        parsed = self._read(raw)
        if parsed is None:
            return LiteralInterpreter(
                "질의 해석 모델의 답을 읽지 못했다 — 질문의 낱말 그대로 찾았다.").interpret(query)
        return parsed

    @staticmethod
    def _read(raw: str) -> Interpretation | None:
        """**세 값만 읽는다.** 나머지는 있어도 없는 것이다."""
        try:
            body = json.loads(raw or "")
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(body, dict):
            return None
        terms = body.get("terms")
        is_data_query = body.get("isDataQuery")
        if not isinstance(terms, list) or not isinstance(is_data_query, bool):
            return None
        clean = tuple(dict.fromkeys(
            t.strip() for t in terms if isinstance(t, str) and t.strip()))
        if is_data_query and not clean:
            return None                       # 데이터 질문이라면서 검색어가 없다 — 못 읽은 것이다
        topic = body.get("topic")
        topic = topic if isinstance(topic, str) and topic in TOPICS else None
        return Interpretation(is_data_query=is_data_query, terms=clean, topic=topic,
                              source="llm", degraded=False, degraded_reason=None)
