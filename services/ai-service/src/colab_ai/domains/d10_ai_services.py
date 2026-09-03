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

import logging

from colab_ai.ports import DictionaryPort, Interpretation, QueryInterpreterPort

#: **응답에 실리는 사유는 상수다** (코드리뷰 20260903-F #3).
#: 종전에는 `f"... : {e}"` 로 원시 예외를 실었다. 사전은 DB 에서 읽으므로 그 예외는 대개
#: psycopg 의 접속 실패이고, 그 문구에는 **호스트·주소·포트·롤**이 들어 있다 — 화면은
#: 안 그려도 브라우저 네트워크 탭에는 그대로 보인다. 사유는 사용자에게 맞는 문장으로
#: 고정하고 **원인은 서버 로그로만** 보낸다(`_degraded_log`). 지우는 것이 아니라 옮긴다.
#: 계약 변경 0 — `degradedReason` 은 자유 문자열이다(`core-ai.yaml Degradable`).
DICTIONARY_UNAVAILABLE_REASON = "온톨로지 사전을 읽지 못해 질문의 낱말 그대로 찾았다."

#: 운영자가 **기계로 긁을 이름**. 규약은 core-api `app/relay.py` 의 `_record_suggest_failure`
#: 를 그대로 쓴다 — 로거 이름 · `event=` · 사유. 두 벌로 두면 한쪽이 언젠가 다른 말을 한다.
DEGRADED_LOGGER = "colab_ai.degraded"
_degraded_log = logging.getLogger(DEGRADED_LOGGER)

#: 검색어를 몇 개까지 내보내는가. 상한이 없으면 사전 확장이 질의를 통째로 넓혀 버린다.
MAX_TERMS = 24

#: **검색어에서 빼는 기능어.** Ted 판정 2026-08-26 ⑴ (`PLAN-SoT §9-〈113〉-㉲-ⓑ` 의 답).
#:
#: 왜 필터링인가 — Postgres `ts_rank_cd` 는 **말뭉치 희소도를 반영하지 않는다.** 흔한 낱말이
#: 자동으로 밀리지 않으므로 순위로는 못 푼다. 대상 12건 규모에서 통계적 가중은 신뢰도가
#: 낮다. 남는 수단이 필터링 하나다.
#:
#: **왜 이 두 낱말인가 — 실측이다** (staging `colab_platform` `d3_dataset_description`,
#: 2026-08-26). `자료:*` 가 **8건**, `데이터:*` 가 **1건**을 낸다. 그리고 적재 12건의
#: 이름·주제·설명 어디에도 이 두 낱말이 **핵심 의미로 쓰인 자리가 없다** — 전부
#: 「본 자료는」·「자료명」·「자료 제공처」·「본 데이터의 R²」 같은 두루 쓰이는 쓰임이다.
#: 핵심 의미로 쓰였으면 그 낱말은 이 목록에서 뺀다.
#:
#: **⚠ `[정본 무근거]`** — 이 목록을 정한 정본 문서가 없다. 근거는 위 실측과 Ted 판정뿐이다.
#:
#: **목록에 없는 낱말은 통과한다 — 과잉 제거 금지.** `원자료`·`관측자료`·`분석자료` 는
#: `simple` 파서가 내는 **다른 토큰**이라 여기 걸리지 않고, 걸려서도 안 된다
#: (`D-09` = GK2A/AMI NDVI 원자료 (Lv.0) 의 이름이 그 말이다).
#: 실측상 0건인 말(`전체`·`찾아줘`)은 **넣지 않았다** — 해를 재지 못한 낱말을 빼지 않는다.
FUNCTION_WORDS = ("자료", "데이터")


def strip_function_words(terms) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """`(남긴 말, 뺀 말)`. **비교는 정확 일치다** — 접두로 자르면 `원자료` 가 함께 사라진다."""
    kept, dropped = [], []
    for term in terms or ():
        (dropped if term in FUNCTION_WORDS else kept).append(term)
    return tuple(kept), tuple(dropped)


class SearchService:
    """`core-ai.yaml searchDatasets` 의 본체 — **질의 해석 절반**."""

    def __init__(self, *, interpreter: QueryInterpreterPort,
                 dictionaries: DictionaryPort) -> None:
        self._interpreter = interpreter
        self._dictionaries = dictionaries

    @staticmethod
    def _expansions(terms: tuple[str, ...], hops) -> list[dict]:
        """그래프가 데려온 말만, **실제로 나가는 검색어에 한해** 적는다.

        `MAX_TERMS` 로 잘린 말의 근거를 남기면 core-api 가 오지 않은 말을 근거에 적게 된다.
        「적을 수 없으면 확장하지 않는다」의 대우다 (`sessions/K1b-ONTOLOGY-CONTENT §D-6`).
        """
        live = set(terms)
        return [{"term": h.term, "relation": h.relation, "parent": h.parent}
                for h in (hops or ()) if h.term in live]

    def _envelope(self, *, lab_id: str, lab_name: str, searched: int, is_data_query: bool,
                  terms: tuple[str, ...], topic: str | None, source: str,
                  degraded: bool, reason: str | None, expansions: list[dict] | None = None) -> dict:
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
        # **빈 배열을 싣지 않는다.** 그래프가 한 일이 없을 때 빈 칸이 서면 화면과 근거가
        # 「그래프가 돌았는데 아무것도 못 찾았다」와 「그래프가 안 돌았다」를 못 가른다.
        if expansions:
            body["interpretation"]["expansions"] = expansions
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

        # **기능어를 먼저 뺀다** (Ted 판정 2026-08-26 ⑴). 넓히기 전에 빼는 이유 —
        # 사전이 기능어를 동의어로 넓히면 뺀 말이 다른 표기로 되돌아온다.
        kept, dropped = strip_function_words(interpretation.terms)
        if not kept:
            # **「찾았으나 없음」이 아니라 「찾을 말이 없음」이다.** 둘은 다른 상태이고,
            # 같은 응답으로 내면 화면이 「우리 연구실에 그런 자료가 없다」고 답한다.
            # ⛔ **전건 반환 금지** — 검색어가 비면 core-api 는 한 건도 뒤지지 않는다
            #    (`d3_catalog._websearch`). 여기서 원문을 되돌려 놓으면 뺀 뜻이 없다.
            # `degraded: true` 로 서는 근거 = `core-ai.yaml Degradable.degraded`
            # (*「결과가 온전하지 않다 — 결과 배열은 비어 있거나 부분적이다」*).
            # **뺀 말을 문구가 이름으로 밝힌다** — 「몰래 제거」 상태를 두지 않는다.
            names = "·".join(f"‘{t}’" for t in dropped)
            return self._envelope(
                lab_id=lab_id, lab_name=lab_name, searched=searched_count,
                is_data_query=True, terms=(), topic=None, source=interpretation.source,
                degraded=True,
                reason=(f"질문에 찾을 말이 없다 — {names} 는 무엇을 찾든 붙는 말이라 "
                        "검색어에서 뺐다. 찾는 자료의 이름·주제·지역·기간을 넣어 다시 물어보라."))

        # 사전으로 넓힌다. **사전이 죽어도 원문 검색어로 간다** — 검색이 멈추지 않는다.
        terms, topic = kept, interpretation.topic
        hops: tuple = ()
        try:
            expansion = self._dictionaries.expand(kept, query)
            terms = expansion.terms
            topic = interpretation.topic or expansion.topic
            hops = getattr(expansion, "graph_hops", ())
        except Exception as e:                                   # noqa: BLE001
            # **원시 예외는 로그로만 간다** — 응답에는 안정된 문구가 나간다(위 상수 주석).
            _degraded_log.warning(
                "event=search.dictionary.unavailable labId=%s exc=%s: %s",
                lab_id, type(e).__name__, e)
            degraded = True
            reason = reason or DICTIONARY_UNAVAILABLE_REASON

        # **넓힌 뒤에 한 번 더 뺀다.** 확장이 기능어를 되데려오면 앞의 필터가 있으나 마나다.
        widened, _ = strip_function_words(terms)
        cut = tuple(widened)[:MAX_TERMS]
        return self._envelope(lab_id=lab_id, lab_name=lab_name, searched=searched_count,
                              is_data_query=True, terms=cut, topic=topic,
                              source=interpretation.source, degraded=degraded, reason=reason,
                              expansions=self._expansions(cut, hops))
