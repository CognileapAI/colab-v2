"""D10 AI Services — **해석만 한다.** 기록 쪽으로 쓰는 경로도, 기록 쪽을 읽는 경로도 없다.

⚠ **2026-08-25 판정 ㈎ 로 이 단위의 몫이 줄었다.** `K4-a` 는 여기서 D3 카탈로그 테이블에
직접 붙어 `tsvector` 질의를 던졌고, 그것이 `CLAUDE.md §3-1` 위반이었다(넘은 것이 파이썬
import 가 아니라 **DB 커넥션**이라 `import-boundary` 가 못 잡았다). Ted 가 ㈎ 를 골랐다 —
**질의는 D3 의 주인인 core-api 가 실행한다.** 여기 남는 것은 `〈72〉-㉮` 가 LLM 에게 준 몫,
즉 **자연어 → 검색어·필터**까지다.

이 파일이 하는 일은 **조립**이다. 둘을 순서대로 부르고 계약 모양으로 접는다 —
  ① 해석기(`QueryInterpreterPort`)   자연어 → 검색어·필터. **LLM 의 일은 여기까지다**
  ② 사전(`DictionaryPort`)            검색어를 D9 사전 3종으로 넓힌다. **D9 는 자기 도메인이다**

**여기에 없는 것이 결정이다.**
  · 카탈로그 커넥션이 없다. D3 를 읽지도 쓰지도 못한다 — 경계가 코드에 없는 것으로 지켜진다.
  · 순위 규칙이 없다. 순서는 core-api 의 `ts_rank_cd` 가 낸다 (`〈72〉-㉮`).
  · 결과 본문 생성이 없다. 이름·요약·Lv·잠김은 core-api 가 D3·D2 에서 붙인다.
  · 확신도·점수·퍼센트 필드가 없다 (`CLAUDE.md §3 AI 응답 규격`).

**무엇 하나가 죽어도 200 이다.** 사전이 죽으면 원문 검색어를 그대로 내주고, 해석기가 죽으면
질문을 낱말로 잘라 내준다 — **어느 쪽이든 core-api 는 그 낱말로 실제 검색을 돌린다.**
「AI 없이도 v2 는 완결된 제품이다」(`CLAUDE.md §3`)가 층마다 한 번씩 지켜진다.
"""
from __future__ import annotations

from colab_ai.ports import DictionaryPort, Interpretation, QueryInterpreterPort

#: 검색어를 몇 개까지 내보내는가. 상한이 없으면 사전 확장이 질의를 통째로 넓혀 버린다.
MAX_TERMS = 24


class SearchService:
    """`core-ai.yaml searchDatasets` 의 본체 — **질의 해석 절반**."""

    def __init__(self, *, interpreter: QueryInterpreterPort,
                 dictionaries: DictionaryPort) -> None:
        self._interpreter = interpreter
        self._dictionaries = dictionaries

    def _envelope(self, *, lab_id: str, lab_name: str, searched: int, is_data_query: bool,
                  terms: tuple[str, ...], topic: str | None, source: str,
                  degraded: bool, reason: str | None) -> dict:
        """**`scope` 가 먼저다.** 파이썬 dict 는 삽입 순서를 지키고 json 은 그 순서로 쓴다 —
        「뒤진 범위를 먼저 밝힌다」가 직렬화된 바이트에서도 사실이 된다.

        `results` 는 계약(`SearchResponse.results`)이 required 라 **빈 봉투로 선다.**
        이 단위는 이제 후보를 뽑지 않는다 — 실제 결과는 core-api 가 `tsvector` 로 만든다.
        `interpretation` 은 그 core-api 가 **이 응답에서 읽는 유일한 값**이다.
        **2026-08-25 세 번째 동결 해제(`〈87〉-㉮`)로 계약에 실렸다** — `SearchResponse` 의
        선택 속성 `interpretation`(`SearchInterpretation`)이고, 같은 회차에 산문이 반대
        방향으로 낡아 있던 것(「AI 가 식별자·관련도를 돌려준다」)도 함께 정정됐다.
        ⚠ **`interpretation` 을 빼면 core-api 는 0건이 아니라 503 으로 답한다**(`〈87〉-㉯`) —
        검색어가 없으면 한 건도 뒤지지 못한 것이고, 그것을 0건으로 내면 화면이 거짓말을 한다.

        `searchedCount` 는 **호출자가 보낸 값을 그대로 되비춘다.** 세는 것은 D3 의 일이고
        이 단위는 D3 를 못 읽는다 — 여기서 지어내면 화면의 범위 표시줄이 거짓이 된다.
        """
        body: dict = {
            "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched},
            "isDataQuery": is_data_query,
            "degraded": degraded,
            "results": {"items": [], "totalCount": 0, "nextCursor": None},
            "interpretation": {"terms": list(terms), "topic": topic, "source": source},
        }
        if reason:
            body["degradedReason"] = reason
        return body

    def search(self, *, lab_id: str, lab_name: str, query: str,
               searched_count: int = 0) -> dict:
        interpretation: Interpretation = self._interpreter.interpret(query)
        degraded = interpretation.degraded
        reason = interpretation.degraded_reason

        if not interpretation.is_data_query:
            # 오류가 아니다. 화면이 「데이터를 찾는 질문에 답해요」로 안내한다 (`§9`).
            return self._envelope(lab_id=lab_id, lab_name=lab_name, searched=searched_count,
                                  is_data_query=False, terms=(), topic=None,
                                  source=interpretation.source, degraded=degraded, reason=reason)

        # 사전으로 넓힌다. **사전이 죽어도 원문 검색어로 간다** — 검색이 멈추지 않는다.
        terms, topic = interpretation.terms, interpretation.topic
        try:
            expansion = self._dictionaries.expand(interpretation.terms, query)
            terms = expansion.terms
            topic = interpretation.topic or expansion.topic
        except Exception as e:                                   # noqa: BLE001
            degraded = True
            reason = reason or f"온톨로지 사전을 읽지 못해 질문의 낱말 그대로 찾았다: {e}"

        return self._envelope(lab_id=lab_id, lab_name=lab_name, searched=searched_count,
                              is_data_query=True, terms=tuple(terms)[:MAX_TERMS], topic=topic,
                              source=interpretation.source, degraded=degraded, reason=reason)
