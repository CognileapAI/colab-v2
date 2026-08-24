"""중계 구현 — `ports/relay.py` 의 전송 절반. **조립 루트에 둔다.**

왜 `domains/` 가 아닌가
  중계는 도메인 사실이 아니라 배관이다. D7·D10 의 사실은 저쪽 배포 단위가 소유하고,
  core-api 는 **해석하지 않고 지나 보낸다.**

왜 `urllib` 인가
  표준 라이브러리다. HTTP 클라이언트 하나를 새로 얹지 않으려고 그렇게 한다 —
  `services/core-api/requirements.in` 은 이 레인의 소유 디렉터리가 아니다.
  **geo 라이브러리는 한 줄도 들어오지 않는다** (`CLAUDE.md §3-4` · `banned-import`).

내려가지 않는 것
  · **타일 URL 을 중계하지 않는다.** `RenderResult.tileUrlTemplate` 은 응답 안에 그대로
    실려 나가지만 core-api 가 그 경로를 대신 열어 주지 않는다 — 지도 위젯이 직접 부른다.
  · 요청/응답 스키마를 **재선언하지 않는다.** `core-viz.yaml` · `core-ai.yaml` 정의가 정본이다.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

#: 중계 대기 시간(초). 저쪽이 안 답할 때 이쪽 요청 스레드를 무한히 잡아 두지 않는다.
RELAY_TIMEOUT_SECONDS = 10


class RelayUnavailable(Exception):
    """중계 대상에 닿지 못했다. **가짜 성공을 만들지 않는다** — 호출자가 봉투로 바꾼다."""


def _request(url: str, *, method: str, headers: dict[str, str],
             body: dict[str, Any] | None) -> tuple[int, dict[str, Any] | None]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=RELAY_TIMEOUT_SECONDS) as res:
            raw = res.read()
            return res.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:          # 저쪽이 낸 상태코드는 사실이다 — 그대로 쓴다
        raw = e.read()
        try:
            return e.code, (json.loads(raw) if raw else None)
        except json.JSONDecodeError:
            return e.code, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise RelayUnavailable(str(e)) from e


def _scope_headers(lab_id: str, account_id: str) -> dict[str, str]:
    """경계는 중계에도 실린다 — 큐에서 꺼낸 메시지처럼 저쪽에는 주체가 없다
    (`envelope.json labId` 주석이 같은 이유를 async 쪽에 적었다)."""
    return {"X-CoLAB-Lab": lab_id, "X-CoLAB-Account": account_id, "Accept": "application/json"}


class HttpPreviewRelay:
    """`ports.PreviewRenderPort` — viz-render 로 나가는 중계."""

    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    def create(self, *, lab_id: str, account_id: str, request: dict[str, Any]) -> dict[str, Any]:
        status, body = _request(f"{self._base}/renders", method="POST",
                                headers=_scope_headers(lab_id, account_id), body=request)
        if status not in (200, 201, 202) or body is None:
            raise RelayUnavailable(f"viz-render 가 {status} 로 답했다.")
        return body

    def get(self, *, lab_id: str, account_id: str, render_id: str) -> dict[str, Any] | None:
        status, body = _request(f"{self._base}/renders/{render_id}", method="GET",
                                headers=_scope_headers(lab_id, account_id), body=None)
        if status == 404:
            return None
        if status != 200 or body is None:
            raise RelayUnavailable(f"viz-render 가 {status} 로 답했다.")
        return body


def honest_empty_suggestions(*, lab_id: str, lab_name: str, searched_count: int,
                             reason: str) -> dict[str, Any]:
    """**정직한 빈 상태** — 뒤진 범위를 먼저 밝히고 제안은 0건이다.

    `ai-service` 가 아직 비어 있다는 사실을 200 + 0건으로 말한다. 5xx 로 끝내면
    「AI 가 없으면 업로드도 못 한다」가 되는데, **AI 없이도 v2 는 완결된 제품이다**
    (`CLAUDE.md §3`). 억지 제안은 만들지 않는다.
    """
    return {
        "degraded": True,
        "degradedReason": reason,
        "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched_count},
        "rawDataLikely": False,
        "suggestions": [],
    }


def unreadable_interpretation(reason: str) -> dict[str, Any]:
    """**해석을 못 받았다 — 그러므로 한 건도 뒤지지 않았다.**

    ⚠ **2026-08-25 Ted 판정 `〈87〉-㉯` 로 이 값의 뜻이 바뀌었다.** 이전 판은 이것을
    「0건 + degraded」로 접었다. 그런데 **0건은 「뒤졌는데 없다」는 뜻**이고 여기서 참인 것은
    **「뒤지지도 못했다」**다. 둘을 같은 응답으로 내면 화면이 정확히 거짓말을 한다 —
    사용자는 「우리 연구실에 그런 자료가 없구나」로 읽는다.
    **폴백을 두지 않는다. 죽으면 「동작하지 않음」이 드러나야 한다.**

    ① `unavailable: True` 가 그 사실이다 — 호출자(라우트)가 **503 + `SEARCH_UNAVAILABLE`** 로
       바꾸고, FE 의 `unavailable` 상태가 그 위에 선다(`useSearch.ts` — 이미 있는 자리다).
    ② `isDataQuery` 를 `true` 로 둔다 — **질의를 판정한 것은 AI 이고 우리는 판정하지 못했다.**
       `false` 로 두면 「데이터를 찾는 질문이 아니다」라는 **하지 않은 판정**을 말하는 것이 된다.
    ③ **`degraded`(해석만 무너짐)와 접지 않는다.** 저쪽이 `source: "literal"` 로 답했다면
       검색어가 **있고** core-api 가 **진짜로 뒤졌고 결과는 진짜 결과다** — 그것은 200 이다.
    """
    return {
        "unavailable": True,
        "unavailableReason": reason,
        "degraded": True,
        "degradedReason": reason,
        "isDataQuery": True,
        "terms": (),
        "topic": None,
        "source": None,
    }


class HttpDatasetSearchRelay:
    """`ports.QueryInterpretationPort` — ai-service 로 나가는 **질의 해석** 중계.

    ⚠ **2026-08-25 판정 ㈎ 로 이 중계가 받아 오는 것이 바뀌었다.** `K4-a` 까지는
    저쪽이 `tsvector` 를 직접 던져 **후보와 순위**를 돌려줬다 — D10 이 D3 테이블에 붙는
    `CLAUDE.md §3-1` 위반이었다. 이제 받아 오는 것은 **검색어·주제·해석 출처**뿐이고,
    찾고 매기는 일은 D3 의 주인인 core-api 가 한다 (`〈72〉-㉮`).

    ⚠ **계보 제안 중계와 규칙이 갈린다** (2026-08-25 Ted 판정 `〈87〉-㉯`). 저쪽은 못 닿아도
    200 + 0건이면 된다 — 「제안이 없다」와 「제안을 못 받았다」의 결과가 같기 때문이다
    (사람이 계보를 직접 적으면 된다). **검색은 다르다.** 0건이 곧 「연구실에 그런 자료가
    없다」는 **답**이라, 못 닿은 것을 0건으로 내면 답이 거짓이 된다. 그래서 주소가 없거나,
    못 닿거나, 범위가 다르거나, 해석을 못 읽으면 **`unavailable`** 을 세우고 라우트가
    **503** 으로 낸다. **「AI 없이도 v2 는 완결된 제품」은 그대로다** — 카탈로그·업로드는
    도는 채이고 화면이 카탈로그로 안내한다 (`CLAUDE.md §3`).

    **저쪽이 얹어 보낸 `results.items` 를 읽지 않는다.** 읽으면 순서가 모델의 것이 되고,
    같은 질의가 때마다 다른 답을 내며, 근거 한 줄이 사후 정당화가 된다 (`〈72〉-㉮`).
    """

    def __init__(self, base_url: str | None) -> None:
        self._base = None if not base_url else base_url.rstrip("/")

    def interpret(self, *, lab_id: str, lab_name: str, account_id: str, query: str,
                  limit: int, cursor: str | None, searched_count: int) -> dict[str, Any]:
        if self._base is None:
            return unreadable_interpretation(
                "검색 서비스가 아직 연결되지 않았다 — 목록에서 조건으로 찾을 수 있다.")
        payload: dict[str, Any] = {
            "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched_count},
            "query": query,
            "limit": limit,
        }
        if cursor:
            payload["cursor"] = cursor
        try:
            status, body = _request(f"{self._base}/searches", method="POST",
                                    headers=_scope_headers(lab_id, account_id), body=payload)
        except RelayUnavailable as e:
            return unreadable_interpretation(f"검색 서비스에 닿지 못했다: {e}")
        if status != 200 or not isinstance(body, dict):
            return unreadable_interpretation(f"검색 서비스가 {status} 로 답했다.")
        # **요청의 범위와 다르면 응답을 버린다** (`core-ai.yaml SearchResponse.scope`).
        # 다른 연구실을 보고 온 해석을 이 화면에 세우면 경계가 응답 한 줄로 무너진다.
        scope = body.get("scope")
        if not isinstance(scope, dict) or scope.get("labId") != lab_id:
            return unreadable_interpretation("검색 응답의 범위가 요청과 달라 버렸다.")

        interpretation = body.get("interpretation")
        if not isinstance(interpretation, dict):
            return unreadable_interpretation("검색 서비스의 질의 해석을 읽지 못했다.")
        raw_terms = interpretation.get("terms")
        terms = tuple(t.strip() for t in raw_terms
                      if isinstance(t, str) and t.strip()) if isinstance(raw_terms, list) else ()
        topic = interpretation.get("topic")
        source = interpretation.get("source")
        return {
            "unavailable": False,
            "degraded": bool(body.get("degraded", False)),
            "degradedReason": body.get("degradedReason"),
            "isDataQuery": bool(body.get("isDataQuery", True)),
            "terms": terms,
            "topic": topic if isinstance(topic, str) and topic else None,
            "source": source if isinstance(source, str) else None,
        }


class HttpLineageSuggestionRelay:
    """`ports.LineageSuggestionPort` — ai-service 로 나가는 중계.

    `base_url` 이 없으면 나가지 않고 정직한 빈 상태를 만든다. 닿았는데 못 답해도 마찬가지다.
    """

    def __init__(self, base_url: str | None) -> None:
        self._base = None if not base_url else base_url.rstrip("/")

    def suggest(self, *, lab_id: str, lab_name: str, account_id: str, upload_id: str,
                searched_count: int, dataset_name_draft: str | None,
                subject: str | None) -> dict[str, Any]:
        if self._base is None:
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count,
                reason="계보 제안 서비스가 아직 연결되지 않았다 — 제안 없이 등록할 수 있다.")
        payload: dict[str, Any] = {
            "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched_count},
            "uploadId": upload_id,
        }
        if dataset_name_draft:
            payload["datasetNameDraft"] = dataset_name_draft
        if subject:
            payload["subject"] = subject
        try:
            status, body = _request(f"{self._base}/lineage-suggestions", method="POST",
                                    headers=_scope_headers(lab_id, account_id), body=payload)
        except RelayUnavailable as e:
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count,
                reason=f"계보 제안 서비스에 닿지 못했다: {e}")
        if status != 200 or body is None:
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count,
                reason=f"계보 제안 서비스가 {status} 로 답했다.")
        # **요청의 범위와 다르면 응답을 버린다** (`core-ai.yaml` LineageSuggestionResponse.scope).
        scope = body.get("scope") if isinstance(body, dict) else None
        if not isinstance(scope, dict) or scope.get("labId") != lab_id:
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count,
                reason="제안 응답의 범위가 요청과 달라 버렸다.")
        return body
