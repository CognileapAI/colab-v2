"""D10 AI Services — 제안만 한다. 기록 쪽으로 쓰는 경로가 존재하지 않는다.

이 파일이 하는 일은 **조립**이다. 셋을 순서대로 부르고 계약 모양으로 접는다 —
  ① 해석기(`QueryInterpreterPort`)   자연어 → 검색어·필터. **LLM 의 일은 여기까지다**(`〈72〉-㉮`)
  ② 사전(`DictionaryPort`)            검색어를 D9 사전 3종으로 넓힌다
  ③ 실행기(`CatalogSearchPort`)       `tsvector` 로 찾고 **순위를 낸다**

**여기에 없는 것이 결정이다.**
  · 순위 규칙이 없다. 순서는 실행기가 낸 관련도 그대로이고, 동점이면 식별자 오름차순이다.
    LLM 이 순서를 정하면 같은 질의가 때마다 다른 순서를 내고 **근거 한 줄이 사후 정당화로
    전락**한다 (`〈72〉-㉮`).
  · 결과 본문 생성이 없다. 이름·요약·Lv·잠김은 core-api 가 D3·D2 에서 붙인다.
  · **접근 상태를 읽지 않는다.** 그래서 **잠긴 데이터가 결과에서 사라질 수 없다**
    (`Policy_데이터_찾기 §1.3-6` · `P-13`·`P-34`) — 뺄 재료가 이 층에 없다.
  · 경계 판단이 없다. 연구실 경계는 Postgres 층(RLS)에 남는다 (`CLAUDE.md §3-5`).
  · 확신도·점수·퍼센트 필드가 없다 (`CLAUDE.md §3 AI 응답 규격`).

**무엇 하나가 죽어도 200 이다.** 사전이 죽으면 원문 검색어로 찾고, 해석기가 죽으면 질문
그대로 찾고, 실행기가 죽으면 **뒤진 범위를 먼저 밝힌 빈 결과**를 낸다 — 「AI 없이도 v2 는
완결된 제품이다」(`CLAUDE.md §3`)를 층마다 한 번씩 지킨다.
"""
from __future__ import annotations

import base64
import binascii

from colab_ai.ports import (CatalogSearchPort, DictionaryPort, Interpretation,
                            MatchRow, QueryInterpreterPort)

#: 근거 한 줄에 열거하는 검색어 상한. 카드 한 줄이 넘치면 정본의 「한 줄 고정」이 깨진다.
MAX_TERMS_IN_RATIONALE = 3


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode()


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return 0
    return int(raw[2:]) if raw.startswith("o:") and raw[2:].isdigit() else 0


def _rationale(row: MatchRow, *, lab_name: str, searched: int, topic: str | None,
               interpretation_degraded: bool) -> str:
    """**한 줄이고, 같은 줄에서 한계도 밝힌다** (`Policy_데이터_찾기 §8` — 펼침·더보기 없음).

    맞은 말과 맞은 자리는 실행기가 준 사실이고, 뒤는 **이 검색이 못 본 것**이다.
    좋은 점만 적는 줄을 만들지 않으려고 두 절을 한 문장에 붙여 둔다.
    """
    matched = ", ".join(row.matched_terms[:MAX_TERMS_IN_RATIONALE]) or "질문의 낱말"
    where = "·".join(row.where) if row.where else "카탈로그"
    head = f"{lab_name} 안 {searched}건에서 ‘{matched}’가 {where}에 맞았다"
    if topic:
        head += f" (주제 {topic}로 좁혀 뒤졌다)"
    tail = "기간·지역·품질은 이 검색이 확인하지 못했으니 카드의 값으로 직접 보라"
    if interpretation_degraded:
        tail = "질의 해석 없이 질문의 낱말 그대로 찾았고, " + tail
    return f"{head} — {tail}."


class SearchService:
    """`core-ai.yaml searchDatasets` 의 본체."""

    def __init__(self, *, interpreter: QueryInterpreterPort, dictionaries: DictionaryPort,
                 catalog: CatalogSearchPort) -> None:
        self._interpreter = interpreter
        self._dictionaries = dictionaries
        self._catalog = catalog

    # ── 응답 조립 ───────────────────────────────────────────────────────────
    def _envelope(self, *, lab_id: str, lab_name: str, searched: int, is_data_query: bool,
                  items: list[dict], total: int, next_cursor: str | None,
                  degraded: bool, reason: str | None) -> dict:
        """**`scope` 가 먼저다.** 파이썬 dict 는 삽입 순서를 지키고 json 은 그 순서로 쓴다 —
        「뒤진 범위를 먼저 밝힌다」가 직렬화된 바이트에서도 사실이 된다."""
        body: dict = {
            "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched},
            "isDataQuery": is_data_query,
            "degraded": degraded,
            "results": {"items": items, "totalCount": total, "nextCursor": next_cursor},
        }
        if reason:
            body["degradedReason"] = reason
        return body

    def search(self, *, lab_id: str, lab_name: str, account_id: str, query: str,
               limit: int, cursor: str | None = None) -> dict:
        interpretation: Interpretation = self._interpreter.interpret(query)
        degraded = interpretation.degraded
        reason = interpretation.degraded_reason

        # ① 뒤진 범위. **못 세면 0 이라고 말하고 감추지 않는다.**
        try:
            searched = self._catalog.count_datasets(lab_id=lab_id, account_id=account_id)
        except Exception as e:                                   # noqa: BLE001
            return self._envelope(
                lab_id=lab_id, lab_name=lab_name, searched=0, is_data_query=True,
                items=[], total=0, next_cursor=None, degraded=True,
                reason=f"카탈로그 색인에 닿지 못했다: {e}")

        if not interpretation.is_data_query:
            # 오류가 아니다. 화면이 「데이터를 찾는 질문에 답해요」로 안내한다 (`§9`).
            return self._envelope(lab_id=lab_id, lab_name=lab_name, searched=searched,
                                  is_data_query=False, items=[], total=0, next_cursor=None,
                                  degraded=degraded, reason=reason)

        # ② 사전으로 넓힌다. 사전이 죽어도 원문 검색어로 간다.
        terms, topic = interpretation.terms, interpretation.topic
        try:
            expansion = self._dictionaries.expand(interpretation.terms, query)
            terms = expansion.terms
            topic = interpretation.topic or expansion.topic
        except Exception as e:                                   # noqa: BLE001
            degraded = True
            reason = reason or f"온톨로지 사전을 읽지 못해 질문의 낱말 그대로 찾았다: {e}"

        if not terms:
            return self._envelope(lab_id=lab_id, lab_name=lab_name, searched=searched,
                                  is_data_query=True, items=[], total=0, next_cursor=None,
                                  degraded=degraded, reason=reason)

        # ③ 실행기. **순위는 여기서 온다.**
        offset = _decode_cursor(cursor)
        try:
            rows, total = self._catalog.match(lab_id=lab_id, account_id=account_id,
                                              terms=terms, topic=topic,
                                              limit=limit, offset=offset)
        except Exception as e:                                   # noqa: BLE001
            return self._envelope(lab_id=lab_id, lab_name=lab_name, searched=searched,
                                  is_data_query=True, items=[], total=0, next_cursor=None,
                                  degraded=True, reason=f"카탈로그 색인에 닿지 못했다: {e}")

        # 동점은 **식별자 오름차순**으로 고정한다 — DB 가 같은 점수를 낸 두 행의 순서까지
        # 재현되어야 평가셋이 회귀를 잡는다.
        ordered = sorted(rows, key=lambda r: (-r.rank, r.dataset_id))
        top = max((r.rank for r in ordered), default=0.0)
        items = [
            {
                "datasetId": r.dataset_id,
                # 막대의 길이일 뿐이다. **화면에 숫자로 서면 정본 위반이다**
                # (`Policy_데이터_찾기 §4 용어(관련도)`).
                "relevanceBar": round(r.rank / top, 3) if top > 0 else 0.0,
                "rationale": _rationale(r, lab_name=lab_name, searched=searched, topic=topic,
                                        interpretation_degraded=interpretation.source != "llm"),
            }
            for r in ordered
        ]
        next_cursor = _encode_cursor(offset + len(items)) if offset + len(items) < total else None
        return self._envelope(lab_id=lab_id, lab_name=lab_name, searched=searched,
                              is_data_query=True, items=items, total=total,
                              next_cursor=next_cursor, degraded=degraded, reason=reason)
