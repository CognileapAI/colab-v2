"""ai-service 조립 루트 — `core-ai.yaml` 의 표면을 세운다.

**계약의 두 표면을 다 연다** — `searchDatasets`(`POST /searches`) ·
`suggestLineage`(`POST /lineage-suggestions`).

⚠ **계보 제안 표면은 지금 참인 답이 언제나 0건이고, 그 사실을 응답이 스스로 말한다.**
부모 후보의 출처가 정해지지 않았기 때문이다 — 계약 `LineageSuggestionRequest` 에 후보를
실을 자리가 없고, 이 배포 단위는 카탈로그(D3)를 읽지 못한다(`〈72〉-㉮`). 그래서 0건을
`degraded: false`(살펴봤는데 없더라)가 아니라 **`degraded: true` + 사유**로 낸다 —
하지 않은 판정을 했다고 주장하지 않는다.

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
from colab_ai.domains.d10_suggestion import SuggestionEnvelope
from colab_ai.kernel.config import Settings
from colab_ai.kernel.db import make_engine
from colab_ai.kernel.ids import is_valid_ulid

#: `Policy_데이터_찾기 §5 검색 질문 — 1~200자`. 계약(`SearchRequest.query`)과 같은 값이다.
MAX_QUERY = 200
#: `core-ai.yaml LineageSuggestionRequest` 의 열쇠 전부. 계약이 `additionalProperties: false`
#: 라 **여기 없는 열쇠가 오면 400 이다** — 소비자의 표류를 표면이 잡는다.
SUGGEST_KEYS = {"scope", "datasetNameDraft", "subject", "file"}
#: `UploadedFileMeta` 의 열쇠 전부. 같은 이유로 닫혀 있다.
FILE_KEYS = {"fileName", "kind", "format", "variables", "crs", "gridDescription",
             "periodStart", "periodEnd", "partCount", "sourceNoteDraft"}
#: `common.json#FileKind` 의 두 값.
FILE_KINDS = ("본체", "기준 격자 파일")
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

    @app.post("/lineage-suggestions")
    async def suggest_lineage(request: Request):
        """`core-ai.yaml suggestLineage` — **제안만 한다. 저장하지 않는다.**

        이 함수 안에 쓰기가 없는 것이 `CLAUDE.md §3-2` 의 코드 쪽 표현이고, 게이트
        `ai-no-lineage-write` 가 같은 것을 세 층에서 본다.

        **계약을 표면이 실제로 요구한다.** `file` 이 required 이고 열쇠 집합이 닫혀 있다 —
        요구하지 않으면 소비자가 계약과 다른 모양을 보내도 아무도 모른다. 실제로 그런
        상태였다(중계가 계약에 없는 열쇠를 보냈고 생산자가 없어 거절한 적이 없었다).
        """
        try:
            payload = await request.json()
        except Exception:                                        # noqa: BLE001
            return _error(400, "bad_request", "본문이 JSON 이 아니다.")
        if not isinstance(payload, dict):
            return _error(400, "bad_request", "본문이 객체가 아니다.")
        unknown = set(payload) - SUGGEST_KEYS
        if unknown:
            return _error(400, "bad_request",
                          f"계약에 없는 열쇠다: {sorted(unknown)} — 계약이 닫혀 있다.")

        scope = payload.get("scope")
        if not isinstance(scope, dict):
            return _error(400, "bad_request", "scope 가 없다 — 경계 없이 제안하지 않는다.")
        lab_id, lab_name = scope.get("labId"), scope.get("labName")
        if not is_valid_ulid(lab_id) or not isinstance(lab_name, str) or not lab_name.strip():
            return _error(400, "bad_request", "scope.labId · scope.labName 이 계약대로가 아니다.")

        header_lab = request.headers.get("X-CoLAB-Lab")
        account_id = request.headers.get("X-CoLAB-Account")
        if header_lab and header_lab != lab_id:
            return _error(400, "bad_request",
                          "요청 본문의 연구실과 헤더의 연구실이 다르다 — 경계를 이쪽이 고르지 않는다.")
        if not is_valid_ulid(account_id):
            return _error(401, "unauthorized", "주체가 없다 — 경계 없이 제안하지 않는다.")

        meta = payload.get("file")
        if not isinstance(meta, dict):
            return _error(400, "bad_request",
                          "file 이 없다 — 계약의 required 다. 파일 메타 없이 무엇도 추정하지 않는다.")
        unknown_file = set(meta) - FILE_KEYS
        if unknown_file:
            return _error(400, "bad_request", f"file 에 계약에 없는 열쇠다: {sorted(unknown_file)}")
        file_name = meta.get("fileName")
        if not isinstance(file_name, str) or not file_name.strip():
            return _error(400, "bad_request", "file.fileName 이 계약대로가 아니다.")
        if meta.get("kind") not in FILE_KINDS:
            return _error(400, "bad_request",
                          f"file.kind 가 계약 밖이다 — 허용은 {list(FILE_KINDS)}.")

        searched = scope.get("searchedCount")
        if not isinstance(searched, int) or isinstance(searched, bool) or searched < 0:
            searched = 0

        envelope = SuggestionEnvelope(lab_id=lab_id, lab_name=lab_name,
                                      searched_count=searched,
                                      # **원자료라고 주장하지 않는다.** 정본(`Policy §8`)은
                                      # 「가공 흔적이 없어 원자료로 판정되면」이라고만 적고
                                      # **판정 방법을 적지 않았다.** 지어내면 화면이
                                      # 「원천 표기만 남기면 된다」를 근거 없이 띄운다.
                                      raw_data_likely=False)
        # **0건이 나오는 이유를 코드가 이름으로 말한다.** 「없더라」가 아니라
        # 「물어볼 재료가 요청에 없다」다 — 두 갈래를 같은 값으로 접지 않는다.
        body = envelope.build(
            suggestions=[],
            empty_declaration=(
                "부모 후보를 실을 자리가 요청에 없고 이 단위는 카탈로그를 읽지 못한다 — "
                "살펴보고 못 찾은 것이 아니라 살펴볼 재료를 받지 못한 것이다. "
                "제안 없이 직접 골라 등록할 수 있다."))
        return JSONResponse(content=body)

    return app
