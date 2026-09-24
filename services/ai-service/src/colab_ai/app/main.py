"""ai-service 조립 루트 — `core-ai.yaml` 의 표면을 세운다.

**계약의 두 표면을 다 연다** — `searchDatasets`(`POST /searches`) ·
`suggestLineage`(`POST /lineage-suggestions`).

⚠ **계보 제안의 후보는 요청이 지고 온다** (⟨2026-09-24 · K3 WU0 — Ted 서명⟩).
이 배포 단위는 여전히 카탈로그(D3)를 읽지 못한다(`〈72〉-㉮`) — 달라진 것은 **core-api 가
고른 후보를 계약의 선택 필드 `candidates` 로 실어 보낸다**는 점이다. 그래서 이 표면의 일은
**받은 후보에 순위·근거 한 줄·3값 확신도를 붙이는 것까지**이고, 후보 밖의 데이터셋은
제안될 수 없다. 후보가 없으면 모델을 **부르지 않고** 0건 + 사유로 답한다 —
하지 않은 판정을 했다고 주장하지 않는다.

**기본은 끈 쪽이다.** `COLAB_AI_LINEAGE_SUGGESTION` 이 `llm` 이고 키가 있어야 모델이
선다(`kernel/config.py`). 그 전까지는 빈 제안이고, 그것은 고장이 아니라 결정이다.

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

import json

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from colab_ai.app.dictionaries import SqlDictionaries
from colab_ai.app.interpret import LiteralInterpreter, LlmQueryInterpreter
from colab_ai.app.ledger import build_ledger
from colab_ai.app.suggest import EmptyLineageSuggester, LlmLineageSuggester
from colab_ai.domains.d10_ai_services import SearchService
from colab_ai.domains.d10_suggestion import SuggestionEnvelope
from colab_ai.kernel.config import Settings
from colab_ai.kernel.db import make_engine
from colab_ai.kernel.ids import is_valid_ulid
from colab_ai.kernel.observability import TraceMiddleware
from colab_ai.ports import REASON_NO_CREDENTIALS, LineageSuggesterPort, ParentCandidate

#: `Policy_데이터_찾기 §5 검색 질문 — 1~200자`. 계약(`SearchRequest.query`)과 같은 값이다.
MAX_QUERY = 200
#: `core-ai.yaml LineageSuggestionRequest` 의 열쇠 전부. 계약이 `additionalProperties: false`
#: 라 **여기 없는 열쇠가 오면 400 이다** — 소비자의 표류를 표면이 잡는다.
SUGGEST_KEYS = {"scope", "datasetNameDraft", "subject", "file", "candidates"}
#: `UploadedFileMeta` 의 열쇠 전부. 같은 이유로 닫혀 있다.
FILE_KEYS = {"fileName", "kind", "format", "variables", "crs", "gridDescription",
             "periodStart", "periodEnd", "partCount", "sourceNoteDraft"}
#: `LineageParentCandidate` 의 열쇠 전부. **후보 항목도 닫혀 있다** — 바깥 열쇠가 섞여
#: 들어오면 근거 판정의 오라클(J3)이 흐려지고, 그 어긋남은 아무도 세지 않는다.
CANDIDATE_KEYS = {"datasetId", "name", "topic", "summary", "sourceLabel",
                  "processingLevel", "periodStart", "periodEnd"}
#: 계약이 `type: string · minLength: 1` 로 적은 후보의 **선택** 열쇠들. 열쇠 집합만 닫고
#: 값의 모양을 안 보면 숫자·배열이 그대로 아래로 흘러 `candidate_payload` 의
#: `c.summary[:200]` 에서 `TypeError` 가 되고, **계약대로면 400 일 요청이 500 이 된다** —
#: 소비자의 표류가 이쪽 고장으로 뒤바뀌는 자리다(게이트 ② 판정 2026-09-24).
CANDIDATE_TEXT_KEYS = ("topic", "summary", "sourceLabel", "periodStart", "periodEnd")
#: 계약 `candidates.maxItems`. 상한을 표면이 실제로 요구한다.
MAX_CANDIDATES = 20
#: `common.json#FileKind` 의 두 값.
FILE_KINDS = ("본체", "기준 격자 파일")
MAX_LIMIT = 100
DEFAULT_LIMIT = 20


def build_suggester(settings: Settings, ledger=None) -> LineageSuggesterPort:
    """제안 생산자 고르기 — **설정이 정한다.** 키 유무가 아니다 (`〈136〉` 과 같은 규율).

    ⚠ 조립 규칙이 해석기와 같다 — `llm` 인데 키가 없으면 「켜려 했으나 못 켰다」이므로
    고장 쪽 문구가 맞고, `off` 는 **결정으로 고른 상태**라 고장을 뜻하는 말을 쓰지 않는다
    (`interpret.py:111-136`).

    ⭑ **실행 원장도 같은 선에서 갈린다** — `llm` 두 갈래에만 붙는다. `off` 는 부를 생각이
    없던 회차라 「왜 안 불렀나」를 적을 호출 자체가 없다.
    """
    if settings.suggest_lineage_mode == "llm":
        if settings.openai_api_key:
            return LlmLineageSuggester(
                api_key=settings.openai_api_key, model=settings.model,
                timeout_seconds=settings.model_timeout_seconds, ledger=ledger)
        return EmptyLineageSuggester(
            EmptyLineageSuggester.NO_CREDENTIALS_REASON, ledger=ledger,
            not_called_reason=REASON_NO_CREDENTIALS, model=settings.model)
    return EmptyLineageSuggester(EmptyLineageSuggester.BY_DESIGN_REASON)


def _candidates(raw: object) -> tuple[ParentCandidate, ...] | str:
    """계약대로면 후보들, 아니면 **사유 문자열**(400 이 된다).

    계약 밖 열쇠·정규 ID 아님·상한 초과는 전부 400 이다. 요구하지 않으면 소비자가 계약과
    다른 모양을 보내도 아무도 모른다 — 실제로 그런 상태였다(`uploadId` 선례).
    """
    if raw is None:
        return ()
    if not isinstance(raw, list):
        return "candidates 는 배열이다."
    if len(raw) > MAX_CANDIDATES:
        return f"후보는 최대 {MAX_CANDIDATES}건이다 — 계약 maxItems."
    out = []
    for item in raw:
        if not isinstance(item, dict):
            return "후보 항목이 객체가 아니다."
        unknown = set(item) - CANDIDATE_KEYS
        if unknown:
            return f"후보에 계약에 없는 열쇠다: {sorted(unknown)} — 계약이 닫혀 있다."
        name = item.get("name")
        if not is_valid_ulid(item.get("datasetId")):
            return "후보의 datasetId 가 정규 ID 가 아니다 — 지어내지 않는다."
        if not isinstance(name, str) or not name.strip():
            return "후보의 name 이 계약대로가 아니다."
        level = item.get("processingLevel")
        if level is not None and (isinstance(level, bool) or not isinstance(level, int)
                                  or level < 0):
            return "후보의 processingLevel 이 계약 밖이다 — 0 이상 정수다."
        for key in CANDIDATE_TEXT_KEYS:
            text = item.get(key)
            if text is None:
                continue                      # 모르는 값은 열쇠가 없다 — 그것이 계약이다
            if not isinstance(text, str) or not text.strip():
                return f"후보의 {key} 가 계약대로가 아니다 — 1자 이상 문자열이다."
        out.append(ParentCandidate(
            dataset_id=item["datasetId"], name=name, topic=item.get("topic"),
            summary=item.get("summary"), source_label=item.get("sourceLabel"),
            processing_level=level, period_start=item.get("periodStart"),
            period_end=item.get("periodEnd")))
    return tuple(out)


def _error(status: int, code: str, message: str) -> JSONResponse:
    """모든 4xx/5xx 는 한 형태다 (`common.json#ErrorEnvelope`)."""
    return JSONResponse(status_code=status, content={"code": code, "message": message})


class _UnavailableDictionaries:
    def expand(self, terms, query):
        raise RuntimeError("온톨로지 사전 주소가 배선되지 않았다")


async def _raw_body(request: Request) -> bytes:
    """본문 바이트만 읽는 **비동기 의존**. 읽기는 루프에서, 판단은 스레드풀에서.

    ⭑ **왜 `Body(...)` 가 아니라 의존인가.** 본문을 FastAPI 의 body 파라미터로 선언하면
    프레임워크가 요청의 `content-type` 을 보고 **먼저 JSON 으로 해석**하고, 실패를
    `RequestValidationError`(422)로 낸다 — 이 표면이 계약대로 내던 「본문이 JSON 이
    아니다」 400(`common.json#ErrorEnvelope`)이 사라진다. 바이트만 받아 오면 해석은
    라우트가 그대로 한다. 그리고 body 파라미터가 없으므로 라우트를 `def` 로 둘 수 있다.
    """
    return await request.body()


def create_app(settings: Settings | None = None,
               suggester: LineageSuggesterPort | None = None) -> FastAPI:
    """`suggester` 는 **시험 주입구**다 — 실운전에서는 `build_suggester` 가 고른다.
    게이트가 모델을 부르지 않으려면 전송을 갈아끼울 자리가 조립에 있어야 한다.
    """
    settings = settings or Settings.from_env()
    app = FastAPI(title="CoLAB v2 ai-service", version="0.1.0")
    app.add_middleware(TraceMiddleware, service_name="ai-service")

    dictionaries = (SqlDictionaries(make_engine(settings.dict_db_url))
                    if settings.dict_db_url else _UnavailableDictionaries())
    # 해석 방식은 **설정이 정한다** — 키 유무가 아니다 (`PLAN-SoT §9 〈136〉`).
    # 이번 릴리즈의 기본은 `literal` 이고, 그건 고장이 아니라 결정이라 사유 문구도 다르다.
    # LLM 은 **스위치와 키가 둘 다** 있어야 선다 — 스위치만 켜고 키가 없으면 낱말 검색으로
    # 남되, 그때는 「쓰기로 했는데 못 썼다」이므로 기본(고장) 문구가 맞다.
    # **실행 원장은 모델을 부를 수 있는 조립에만 붙는다** (intent
    # `2026-09-24-d10-model-call-ledger`). 주소가 없으면 빈 원장이고, 빈 원장은
    # 터지지 않는다 — 「설정이 하나도 없어도 뜬다」가 원장 때문에 거짓이 되지 않는다.
    ledger = build_ledger(settings)
    use_llm = settings.query_interpretation == "llm" and bool(settings.openai_api_key)
    if use_llm:
        interpreter = LlmQueryInterpreter(
            api_key=settings.openai_api_key, model=settings.model,
            timeout_seconds=settings.model_timeout_seconds, ledger=ledger)
    elif settings.query_interpretation == "llm":
        # 켜려 했으나 키가 없다 = 고장 문구.
        #
        # ⚠ **알고 남긴 비대칭이다.** 제안 쪽의 같은 갈래(`build_suggester`)는
        # `not_called / no_credentials` 행을 남기는데 여기는 남기지 않는다 — 이 자리에서
        # 행을 남기려면 `LlmQueryInterpreter(api_key=None, …)` 를 세워야 하고, 그러면
        # 사용자가 읽는 `degradedReason` 문구가 바뀐다(「쓰지 않았다」→「자격 증명이 없다」).
        # 원장 회차가 화면 문구를 바꾸지 않는다. **Ted 판정 대기** — 문구를 정정할지,
        # 이 갈래는 행 없이 둘지.
        interpreter = LiteralInterpreter()
    else:
        interpreter = LiteralInterpreter(LiteralInterpreter.BY_DESIGN_REASON)
    service = SearchService(interpreter=interpreter, dictionaries=dictionaries)
    suggester = suggester or build_suggester(settings, ledger)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"unit": "ai-service", "status": "alive", "implemented": True}

    @app.post("/searches")
    def search_datasets(request: Request, body: bytes = Depends(_raw_body)):
        """⭑ **`def` 다 — 코루틴이 아니다** (코드리뷰 20260903 #10 형제).

        이 함수는 막는 일을 한다: `dictionaries.py` 의 사전 조회는 동기 psycopg 로
        5 SELECT 를 돌고, `llm` 모드에서는 `interpret.py` 의 `urlopen(timeout=8)` 이
        최대 8초를 붙든다. 코루틴으로 두면 그동안 **이벤트 루프가 통째로 멈추고**,
        워커가 하나라 같은 프로세스의 `/healthz` 까지 답을 못 한다 — compose 의
        헬스 체크(3초)가 그 사이에 지나간다. `def` 로 선언하면 FastAPI 가
        **스레드풀에서** 부르므로 루프는 계속 돈다.
        """
        try:
            payload = json.loads(body)
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
    def suggest_lineage(request: Request, body: bytes = Depends(_raw_body)):
        """`core-ai.yaml suggestLineage` — **제안만 한다. 저장하지 않는다.**

        이 함수 안에 쓰기가 없는 것이 `CLAUDE.md §3-2` 의 코드 쪽 표현이고, 게이트
        `ai-no-lineage-write` 가 같은 것을 세 층에서 본다.

        **계약을 표면이 실제로 요구한다.** `file` 이 required 이고 열쇠 집합이 닫혀 있다 —
        요구하지 않으면 소비자가 계약과 다른 모양을 보내도 아무도 모른다. 실제로 그런
        상태였다(중계가 계약에 없는 열쇠를 보냈고 생산자가 없어 거절한 적이 없었다).

        ⭑ **`def` 로 바뀌었다 — 코루틴이 아니다** (`/searches` 와 같은 사유). 제안
        생산자가 켜지면 이 함수가 `urlopen(timeout=8)` 을 붙든다. 코루틴으로 두면 그동안
        **이벤트 루프가 통째로 멈추고** 같은 프로세스의 `/healthz` 까지 답을 못 한다.
        """
        try:
            payload = json.loads(body)
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

        candidates = _candidates(payload.get("candidates"))
        if isinstance(candidates, str):
            return _error(400, "bad_request", candidates)

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
        # **생산자는 예외를 던지지 않는다** — 못 하면 빈 제안 + 사유다. 0건이 나오는 이유를
        # 사유 문구가 이름으로 말한다(「후보가 없다」·「켜지 않았다」·「닿지 못했다」는
        # 사용자에게 다른 사실이고, 두 갈래를 같은 값으로 접지 않는다).
        outcome = suggester.suggest(
            file_meta=meta, candidates=candidates,
            dataset_name_draft=payload.get("datasetNameDraft"),
            subject=payload.get("subject"))
        return JSONResponse(content=envelope.build(
            suggestions=list(outcome.suggestions),
            empty_declaration=outcome.empty_declaration))

    return app
