"""ai-service 조립 루트 — `core-ai.yaml` 의 표면을 세운다.

**여는 것은 `searchDatasets`(`POST /searches`) 하나다.** `suggestLineage` 는 `K3` 의 자리이고
여기서 흉내 내지 않는다 — 계약에 있는 것과 구현된 것이 다르면 그 사실이 보여야 한다.

⚠ **2026-08-25 판정 ㈎ 이후 `/searches` 는 질의를 해석해 돌려줄 뿐 카탈로그를 뒤지지 않는다.**
찾고 매기는 것은 D3 의 주인인 core-api 다 (`CLAUDE.md §3-1` · `〈72〉-㉮`).

**경계를 두 번 받는다.** 본문의 `scope.labId` 와 헤더 `X-CoLAB-Lab` 이다(core-api 중계가
둘 다 보낸다). **둘이 다르면 뒤지지 않고 400 이다** — 어느 쪽을 믿을지 이쪽이 고르면
경계가 이 파일의 판단이 되고, 그 순간 `CLAUDE.md §3-5` 가 막으려던 「경계가 두 곳에서
정해지는 상황」이 된다.

**설정이 하나도 없어도 뜬다.** 사전 DB URL 도 모델 키도 없으면 `/searches` 는 5xx 가 아니라
**질문의 낱말 그대로 + `degraded`** 를 낸다 — core-api 는 그 낱말로 실제 검색을 돌린다
(`CLAUDE.md §3` — AI 없이도 v2 는 완결된 제품이다).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from colab_ai.app.dictionaries import SqlDictionaries
from colab_ai.app.interpret import LiteralInterpreter, LlmQueryInterpreter
from colab_ai.domains.d10_ai_services import SearchService
from colab_ai.kernel.config import Settings
from colab_ai.kernel.db import make_engine
from colab_ai.kernel.ids import is_valid_ulid

#: `Policy_데이터_찾기 §5 검색 질문 — 1~200자`. 계약(`SearchRequest.query`)과 같은 값이다.
MAX_QUERY = 200
MAX_LIMIT = 100
DEFAULT_LIMIT = 20


def _error(status: int, code: str, message: str) -> JSONResponse:
    """모든 4xx/5xx 는 한 형태다 (`common.json#ErrorEnvelope`)."""
    return JSONResponse(status_code=status, content={"code": code, "message": message})


class _UnavailableDictionaries:
    def expand(self, terms, query):
        raise RuntimeError("온톨로지 사전 주소가 배선되지 않았다")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="CoLAB v2 ai-service", version="0.1.0")

    dictionaries = (SqlDictionaries(make_engine(settings.dict_db_url))
                    if settings.dict_db_url else _UnavailableDictionaries())
    # 해석 방식은 **설정이 정한다** — 키 유무가 아니다 (`PLAN-SoT §9 〈136〉`).
    # 이번 릴리즈의 기본은 `literal` 이고, 그건 고장이 아니라 결정이라 사유 문구도 다르다.
    # LLM 은 **스위치와 키가 둘 다** 있어야 선다 — 스위치만 켜고 키가 없으면 낱말 검색으로
    # 남되, 그때는 「쓰기로 했는데 못 썼다」이므로 기본(고장) 문구가 맞다.
    use_llm = settings.query_interpretation == "llm" and bool(settings.openai_api_key)
    if use_llm:
        interpreter = LlmQueryInterpreter(
            api_key=settings.openai_api_key, model=settings.model,
            timeout_seconds=settings.model_timeout_seconds)
    elif settings.query_interpretation == "llm":
        interpreter = LiteralInterpreter()          # 켜려 했으나 키가 없다 = 고장 문구
    else:
        interpreter = LiteralInterpreter(LiteralInterpreter.BY_DESIGN_REASON)
    service = SearchService(interpreter=interpreter, dictionaries=dictionaries)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"unit": "ai-service", "status": "alive", "implemented": True}

    @app.post("/searches")
    async def search_datasets(request: Request):
        try:
            payload = await request.json()
        except Exception:                                        # noqa: BLE001
            return _error(400, "bad_request", "본문이 JSON 이 아니다.")
        if not isinstance(payload, dict):
            return _error(400, "bad_request", "본문이 객체가 아니다.")

        scope = payload.get("scope")
        if not isinstance(scope, dict):
            return _error(400, "bad_request", "scope 가 없다 — 경계 없이 뒤지지 않는다.")
        lab_id, lab_name = scope.get("labId"), scope.get("labName")
        if not is_valid_ulid(lab_id) or not isinstance(lab_name, str) or not lab_name.strip():
            return _error(400, "bad_request", "scope.labId · scope.labName 이 계약대로가 아니다.")

        header_lab = request.headers.get("X-CoLAB-Lab")
        account_id = request.headers.get("X-CoLAB-Account")
        if header_lab and header_lab != lab_id:
            return _error(400, "bad_request",
                          "요청 본문의 연구실과 헤더의 연구실이 다르다 — 경계를 이쪽이 고르지 않는다.")
        if not is_valid_ulid(account_id):
            return _error(401, "unauthorized", "주체가 없다 — 경계 없이 뒤지지 않는다.")

        query = payload.get("query")
        if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY:
            return _error(400, "bad_request", f"검색 질문은 1~{MAX_QUERY}자다.")
        # **`searchedCount` 는 호출자(core-api)가 실제로 센 값이다.** 계약의 `RequestedScope` 에는
        # 없지만 core-api 가 실측으로 얹어 보낸다 — 이 단위는 D3 를 못 읽으므로 되비출 뿐이다.
        searched = scope.get("searchedCount")
        if not isinstance(searched, int) or isinstance(searched, bool) or searched < 0:
            searched = 0

        limit = payload.get("limit", DEFAULT_LIMIT)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_LIMIT:
            return _error(400, "bad_request", f"limit 은 1~{MAX_LIMIT} 이다.")
        cursor = payload.get("cursor")
        if cursor is not None and not isinstance(cursor, str):
            return _error(400, "bad_request", "cursor 는 문자열이다.")

        # `limit`·`cursor` 는 계약이 허용하는 값이라 규칙만 지키고 **쓰지는 않는다** —
        # 쪽 나누기는 결과를 가진 쪽(core-api)의 일이다.
        body = service.search(lab_id=lab_id, lab_name=lab_name,
                              query=query.strip(), searched_count=searched)
        # `scope` 를 먼저 쓴 dict 를 그대로 직렬화한다 — 뒤진 범위가 바이트에서도 먼저다.
        return JSONResponse(content=body)

    return app
