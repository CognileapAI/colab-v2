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


def honest_empty_search(*, lab_id: str, lab_name: str, searched_count: int,
                        reason: str) -> dict[str, Any]:
    """**정직한 빈 상태** — 검색판 (`〈80〉-㉯ 5`).

    ① **뒤진 범위가 먼저다** (`Policy_데이터_찾기 §3.3`). 0건이어도 어디를 몇 개 뒤졌는지가 먼저다.
    ② **0건은 오류가 아니다** — 막다른 길이 아니라 다음 행동을 안내할 상태다(`§1.3-7`).
    ③ `isDataQuery` 를 `true` 로 둔다 — **질의를 판정한 것은 AI 이고 우리는 판정하지 못했다.**
       `false` 로 두면 「데이터를 찾는 질문이 아니다」라는 **하지 않은 판정**을 말하는 것이 된다.
    """
    return {
        "degraded": True,
        "degradedReason": reason,
        "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched_count},
        "isDataQuery": True,
        "items": [],
        "totalCount": 0,
        "nextCursor": None,
    }


class HttpDatasetSearchRelay:
    """`ports.DatasetSearchPort` — ai-service 로 나가는 자연어 검색 중계.

    `HttpLineageSuggestionRelay` 와 같은 규칙이다 — 주소가 없어도, 못 닿아도, 범위가 달라도
    **200 + 빈 결과**다. 「AI 가 없다」가 「검색 화면이 죽는다」가 되면 안 된다 (`CLAUDE.md §3`).
    """

    def __init__(self, base_url: str | None) -> None:
        self._base = None if not base_url else base_url.rstrip("/")

    def search(self, *, lab_id: str, lab_name: str, account_id: str, query: str,
               limit: int, cursor: str | None, searched_count: int) -> dict[str, Any]:
        def empty(reason: str) -> dict[str, Any]:
            return honest_empty_search(lab_id=lab_id, lab_name=lab_name,
                                       searched_count=searched_count, reason=reason)

        if self._base is None:
            return empty("검색 서비스가 아직 연결되지 않았다 — 목록에서 조건으로 찾을 수 있다.")
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
            return empty(f"검색 서비스에 닿지 못했다: {e}")
        if status != 200 or not isinstance(body, dict):
            return empty(f"검색 서비스가 {status} 로 답했다.")
        # **요청의 범위와 다르면 응답을 버린다** (`core-ai.yaml SearchResponse.scope`).
        # 다른 연구실을 뒤진 결과를 이 화면에 세우면 경계가 응답 한 줄로 무너진다.
        scope = body.get("scope")
        if not isinstance(scope, dict) or scope.get("labId") != lab_id:
            return empty("검색 응답의 범위가 요청과 달라 버렸다.")
        results = body.get("results")
        items = results.get("items") if isinstance(results, dict) else None
        return {
            "degraded": bool(body.get("degraded", False)),
            "degradedReason": body.get("degradedReason"),
            "scope": scope,
            "isDataQuery": bool(body.get("isDataQuery", True)),
            "items": items if isinstance(items, list) else [],
            "nextCursor": results.get("nextCursor") if isinstance(results, dict) else None,
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
