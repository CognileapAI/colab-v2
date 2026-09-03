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
import logging
import urllib.error
import urllib.request
from typing import Any

#: 중계 대기 시간(초). 저쪽이 안 답할 때 이쪽 요청 스레드를 무한히 잡아 두지 않는다.
RELAY_TIMEOUT_SECONDS = 10

#: 계보 제안 실패의 **감시 표면** (`03-HANDOFF §5.5 DR-19`-㉯ · `PLAN-SoT §9 〈246〉`).
#: 검색 쪽이 먼저 세운 규약과 같은 모양이다 (`routes/catalog.py:_search_log`) — 실패가
#: 사람의 눈이 아니라 **기계가 긁을 이름**으로 서야 「지금 몇 건 실패했나」를 셀 수 있다.
#: 이름 셋(로거 · `record.event` · `record.code`)은 문구가 바뀌어도 계약처럼 다룬다.
SUGGEST_LOGGER = "colab_core.suggest"
SUGGEST_REJECTED = "LINEAGE_SUGGEST_REJECTED"
SUGGEST_UNAVAILABLE = "LINEAGE_SUGGEST_UNAVAILABLE"

_suggest_log = logging.getLogger(SUGGEST_LOGGER)


class RelayUnavailable(Exception):
    """중계 대상에 닿지 못했다. **가짜 성공을 만들지 않는다** — 호출자가 봉투로 바꾼다."""


class RelayRefused(Exception):
    """저쪽이 **읽어 보고 물리쳤다** — 못 닿은 것이 아니다 (`CODE-REVIEW-20260903` #8).

    ⚠ 종전에는 이 갈래가 없어 `status not in (200, 201, 202)` 가 전부 `RelayUnavailable`
    이었고, viz-render 의 **415 NOT_RENDERABLE**(`details.renderableFormats`)·413·400 이
    core-api 에서 503 「연결하지 못했다」가 됐다. 그 결과 —
      · 사용자는 **그릴 수 없는 파일**을 「서버 장애」로 읽고 계속 재시도한다.
      · 지원 형식 목록이 화면에 영영 도달하지 않는다.
      · FE 의 `status === 415` 분기 4곳이 **죽은 코드**가 된다.

    **상태와 본문을 그대로 들고 간다.** 여기서 해석하면 저쪽이 이미 판정한 것을 두 번
    판정하는 것이 되고, 그 순간 두 서비스의 답이 갈린다.
    """

    def __init__(self, status: int, body: dict[str, Any] | None) -> None:
        super().__init__(f"viz-render 가 {status} 로 답했다.")
        self.status = status
        self.body = body


#: **저쪽이 읽어 보고 낸 거절**의 상태 집합. 그대로 화면까지 간다.
#:
#: ⚠ **401·403 은 여기 없다.** 그것은 우리 서비스 자격 증명이 틀렸다는 뜻이라 **우리 쪽
#: 고장**이고, 사용자가 고칠 수 있는 것이 아니다 — 통과시키면 화면이 「네 요청이 틀렸다」를
#: 말한다. 5xx 도 없다: 저쪽 사정은 「지금 그릴 수 없다」이지 「이건 못 그린다」가 아니다.
#: 둘 다 `RelayUnavailable` → 503 이다.
PASS_THROUGH_STATUSES = (400, 404, 410, 413, 415, 422)


def _refuse_if_client_error(status: int, body: dict[str, Any] | None) -> None:
    """통과 집합이면 `RelayRefused` 로 올린다. 아니면 아무 일도 하지 않는다."""
    if status in PASS_THROUGH_STATUSES:
        raise RelayRefused(status, body)


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


def _request_binary(url: str, *, method: str, headers: dict[str, str],
                    body: dict[str, Any] | None) -> tuple[int, bytes, str | None]:
    """**JSON 이 아닌 답을 지나 보내는 전송.** `createPreviewScreenshot` 의 200 은
    `image/png` 라 `_request` 로는 못 받는다 — `json.loads` 가 그림을 파싱하려다 죽는다.

    **바이트를 해석하지 않는다.** core-api 는 그림을 만들지도 고치지도 않고, 저쪽이 준
    본문과 `Content-Type` 을 그대로 되돌린다 (`CLAUDE.md §3-4`).
    오류(4xx/5xx)는 저쪽이 `ErrorEnvelope` JSON 으로 주므로 본문을 그대로 올려 보내고
    상태코드도 저쪽 것을 쓴다 — **저쪽이 낸 상태코드는 사실이다.**
    """
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=RELAY_TIMEOUT_SECONDS) as res:
            return res.status, res.read(), res.headers.get("Content-Type")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("Content-Type")
    except (urllib.error.URLError, TimeoutError) as e:
        raise RelayUnavailable(str(e)) from e


def _scope_headers(lab_id: str, account_id: str,
                   service_token: str | None = None) -> dict[str, str]:
    """경계는 중계에도 실린다 — 큐에서 꺼낸 메시지처럼 저쪽에는 주체가 없다
    (`envelope.json labId` 주석이 같은 이유를 async 쪽에 적었다).

    ⚠ **`Authorization` 은 사람의 세션이 아니라 배포 단위 사이의 자격 증명이다**
    (`core-viz.yaml` `securitySchemes.serviceToken`). 경계 헤더와 **다른 물건**이고
    둘 다 필요하다 — 경계는 「누구 것을 그리는가」이고 자격 증명은 「부를 자격이 있는가」다.
    """
    headers = {"X-CoLAB-Lab": lab_id, "X-CoLAB-Account": account_id,
               "Accept": "application/json"}
    if service_token:
        headers["Authorization"] = f"Bearer {service_token}"
    return headers


class HttpPreviewRelay:
    """`ports.PreviewRenderPort` — viz-render 로 나가는 중계.

    ⚠ **`service_token` 이 없으면 저쪽이 전부 401 이다.** `core-viz.yaml` 이
    `security: [serviceToken]` 로 모든 렌더 표면에 bearer 를 요구하는데, 개정 전 이 중계는
    경계 헤더만 실었다 — 실서버 2대를 세워 보고서야 드러났고, 그때까지 시험용 가짜 viz 가
    자격 증명을 검사하지 않아 **계약이 요구하는 것을 아무도 안 물었다.**
    """

    def __init__(self, base_url: str, *, service_token: str | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._token = service_token

    def create(self, *, lab_id: str, account_id: str, request: dict[str, Any]) -> dict[str, Any]:
        status, body = _request(f"{self._base}/renders", method="POST",
                                headers=_scope_headers(lab_id, account_id, self._token),
                                body=request)
        # **거절과 장애를 가른다** — 415 는 「이건 못 그린다」이고 503 은 「지금 못 닿았다」다.
        _refuse_if_client_error(status, body)
        if status not in (200, 201, 202) or body is None:
            raise RelayUnavailable(f"viz-render 가 {status} 로 답했다.")
        return body

    def palettes(self, *, lab_id: str, account_id: str) -> dict[str, Any]:
        """`listPalettes` 중계 (`〈88〉` 묶음 4).

        **값 집합은 viz-render 소유다.** 여기서 목록을 만들거나, 저쪽이 못 답할 때 기본값을
        끼워 넣지 않는다 — 그러면 팔레트 정본이 core 로 옮겨 앉고 화면이 저쪽이 모르는 키를
        보내게 된다. 못 닿으면 `RelayUnavailable` 이고 라우트가 **503** 으로 낸다.
        """
        status, body = _request(f"{self._base}/palettes", method="GET",
                                headers=_scope_headers(lab_id, account_id, self._token),
                                body=None)
        _refuse_if_client_error(status, body)
        if status != 200 or body is None:
            raise RelayUnavailable(f"viz-render 가 {status} 로 답했다.")
        return body

    def lookup_value(self, *, lab_id: str, account_id: str,
                     request: dict[str, Any]) -> dict[str, Any]:
        """`lookupValue` 중계 (`〈294〉` · 15차 해제).

        **없는 것도 200 이다** — `available: false` ＋ 사유가 몸통에 실려 온다. 그것을
        여기서 값으로 바꾸거나 4xx 로 승격하지 않는다: 저쪽이 읽어 보고 낸 사실이다.
        못 닿은 것만 `RelayUnavailable` 이고 라우트가 **503** 으로 낸다.
        """
        status, body = _request(f"{self._base}/value-lookups", method="POST",
                                headers=_scope_headers(lab_id, account_id, self._token),
                                body=request)
        _refuse_if_client_error(status, body)
        if status != 200 or body is None:
            raise RelayUnavailable(f"viz-render 가 {status} 로 답했다.")
        return body

    def screenshot(self, *, lab_id: str, account_id: str,
                   request: dict[str, Any]) -> tuple[int, bytes, str | None]:
        """`createScreenshot` 중계 (`〈231〉` · 11차 해제).

        **판정하지 않고 지나 보낸다.** 200 이면 PNG 바이트, 4xx 면 저쪽의 `ErrorEnvelope`
        본문이 그대로 실려 온다 — 상태코드도 저쪽 것이다. 여기서 빈 이미지를 만들거나
        상태를 200 으로 바꾸지 않는다: **0바이트 PNG 는 「장면이 비었다」로 읽힌다.**
        못 닿으면 `RelayUnavailable` 이고 라우트가 **503** 으로 낸다.
        """
        headers = _scope_headers(lab_id, account_id, self._token)
        headers["Accept"] = "image/png, application/json"
        return _request_binary(f"{self._base}/screenshots", method="POST",
                               headers=headers, body=request)

    def get(self, *, lab_id: str, account_id: str, render_id: str) -> dict[str, Any] | None:
        status, body = _request(f"{self._base}/renders/{render_id}", method="GET",
                                headers=_scope_headers(lab_id, account_id, self._token),
                                body=None)
        if status == 404:
            return None
        if status != 200 or body is None:
            raise RelayUnavailable(f"viz-render 가 {status} 로 답했다.")
        return body


def _record_suggest_failure(*, rejected: bool, lab_id: str, status: int | None,
                            reason: str) -> None:
    """**응답은 200 인데 실은 실패한 자리**를 기계가 긁을 이름으로 남긴다 (`DR-19`-㉯).

    응답만으로는 「지금 몇 건 거부당했나」를 아무도 못 센다 — 화면은 `degraded` 로
    「모른다」까지만 말하고, 그것은 사용자에게 맞는 문장이지 운영자에게 맞는 문장이 아니다.
    **정직한 빈 상태를 깨지 않는 채로** 고장만 따로 드러내는 자리가 여기다.
    """
    event = "lineage.suggest.rejected" if rejected else "lineage.suggest.unavailable"
    code = SUGGEST_REJECTED if rejected else SUGGEST_UNAVAILABLE
    _suggest_log.log(
        logging.ERROR if rejected else logging.WARNING,
        "event=%s code=%s status=%s reason=%s", event, code, status, reason,
        extra={"event": event, "code": code, "status": status,
               "reason": reason, "labId": lab_id},
    )


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
        "expansions": {},
    }


#: 그래프 확장의 관계 3값. `core-ai.yaml SearchInterpretation.expansions.items.relation`
#: enum 과 같은 값이고, 그 원본은 `d9_concept_edge.relation` CHECK 다.
#: **모르는 관계는 버린다** — 근거 한 줄이 저쪽이 새로 지어낸 말을 사용자에게 옮기지 않는다.
_EXPANSION_RELATIONS = ("같은 말이다", "~의 한 가지다", "안에 있다")


def _read_expansions(raw: Any, terms: tuple[str, ...]) -> dict[str, tuple[str, str]]:
    """`expansions` 를 `검색어 → (관계, 부모)` 로 접는다. **믿고 쓰지 않고 검사하고 쓴다.**

    버리는 것 셋 — ① 모양이 계약과 다른 행 ② 관계가 3값 밖인 행 ③ **`terms` 에 없는 말**.
    ③ 이 중요하다. 이 값은 근거 한 줄에 그대로 실려 사용자가 읽으므로, 실제로 뒤진 말이
    아닌 것이 여기 섞이면 **근거가 하지 않은 검색을 말한다.**
    """
    if not isinstance(raw, list):
        return {}
    live = set(terms)
    out: dict[str, tuple[str, str]] = {}
    for row in raw:
        if not isinstance(row, dict):
            continue
        term, relation, parent = row.get("term"), row.get("relation"), row.get("parent")
        if not all(isinstance(v, str) and v.strip() for v in (term, relation, parent)):
            continue
        if relation not in _EXPANSION_RELATIONS or term not in live:
            continue
        out.setdefault(term, (relation, parent))
    return out


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
            "expansions": _read_expansions(interpretation.get("expansions"), terms),
        }


class HttpLineageSuggestionRelay:
    """`ports.LineageSuggestionPort` — ai-service 로 나가는 중계.

    `base_url` 이 없으면 나가지 않고 정직한 빈 상태를 만든다. 닿았는데 못 답해도 마찬가지다.
    """

    def __init__(self, base_url: str | None) -> None:
        self._base = None if not base_url else base_url.rstrip("/")

    def suggest(self, *, lab_id: str, lab_name: str, account_id: str,
                file_meta: dict[str, Any], searched_count: int,
                dataset_name_draft: str | None,
                subject: str | None) -> dict[str, Any]:
        """⭑ **⟨정정 2026-08-30⟩ 나가는 본문이 계약과 어긋나 있었다.**

        계약(`core-ai.yaml LineageSuggestionRequest`, 2026-08-22 동결)은 `file` 을
        required 로 두고 `additionalProperties: false` 인데, 이 중계는 2026-08-23 부터
        `file` 없이 **계약에 없는 `uploadId`** 를 보내고 있었다. 아무도 못 잡은 이유는
        **생산자가 없어 거절할 쪽이 없었기 때문**이다 — 계약 게이트는 정적 스펙만 보고
        실제 요청 바이트를 보지 않는다. 동결이 먼저이므로 **정본은 계약이고 고친 쪽은 여기다.**
        """
        if self._base is None:
            # **아직 연결되지 않은 것은 고장이 아니다** — `K3` 는 착수 전이고, 그것이
            # 결정된 상태다. 여기에 실패를 기록하면 매 업로드가 오류 한 줄을 내고
            # 「AI 없이도 v2 는 완결된 제품」이 감시에서 사고처럼 보인다.
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count,
                reason="계보 제안 서비스가 아직 연결되지 않았다 — 제안 없이 등록할 수 있다.")
        payload: dict[str, Any] = {
            "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched_count},
            "file": file_meta,
        }
        if dataset_name_draft:
            payload["datasetNameDraft"] = dataset_name_draft
        if subject:
            payload["subject"] = subject
        try:
            status, body = _request(f"{self._base}/lineage-suggestions", method="POST",
                                    headers=_scope_headers(lab_id, account_id), body=payload)
        except RelayUnavailable as e:
            reason = f"계보 제안 서비스에 닿지 못했다: {e}"
            _record_suggest_failure(rejected=False, lab_id=lab_id, status=None, reason=reason)
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count, reason=reason)
        if status != 200 or body is None:
            # **거부와 장애를 같은 줄로 접지 않는다.** 4xx 는 저쪽이 우리 요청을 물리친 것이라
            # **우리 쪽 고장**이고 재시도로 낫지 않는다 — 계약 표류가 여기로 떨어진다(`DR-19`).
            # 5xx·빈 본문은 저쪽 사정이다. 화면은 둘 다 「모른다」로 같지만 고칠 사람이 다르다.
            reason = f"계보 제안 서비스가 {status} 로 답했다."
            _record_suggest_failure(rejected=400 <= status < 500,
                                    lab_id=lab_id, status=status, reason=reason)
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count, reason=reason)
        # **요청의 범위와 다르면 응답을 버린다** (`core-ai.yaml` LineageSuggestionResponse.scope).
        scope = body.get("scope") if isinstance(body, dict) else None
        if not isinstance(scope, dict) or scope.get("labId") != lab_id:
            reason = "제안 응답의 범위가 요청과 달라 버렸다."
            _record_suggest_failure(rejected=True, lab_id=lab_id, status=status, reason=reason)
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count, reason=reason)
        # **여기부터가 정직한 빈 상태의 자리다** — 저쪽이 답했고 0건이면 그것이 참인 답이다.
        # 그 자리에는 실패 기록을 남기지 않는다. 남기면 「없다」와 「못 물어봤다」가
        # 기록에서 다시 붙고, 감시가 매 업로드마다 울어 아무도 보지 않게 된다.
        return body
