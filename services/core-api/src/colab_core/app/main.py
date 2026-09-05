"""core-api 앱 — fe-core seam **64** 오퍼레이션 전부를 등록한다 (2026-08-29 실측 · `test_route_table.py`).

실동작 **45 개**, 나머지 **19 개**는 **501 + ErrorEnvelope** 로 응답한다 (NIGHT-20260823 §3 ·
표는 `routes/not_implemented.py`). 미구현에 404 를 쓰지 않는다 — 404 는 「경계 밖」의 뜻으로
이미 예약돼 있다 (PLAN-SoT §9-㊱).

⭑ 이 머리말의 수는 여러 번 낡았다(「54 · 22 · 24」가 8차 해제 뒤에도 남아 있었다). 정본은
`tests/test_route_table.py`(계약 64)와 `tests/test_not_implemented.py`(501 표 19)이고, 여기는
그 둘을 옮겨 적을 뿐이다 — 두 시험이 red 면 이 줄도 낡은 것이다.

가져온 이력 — P2 가 열둘(업로드 6 · 계보 확정 3 · 미리보기 중계 2 · AI 제안 중계 1),
S1 이 `searchDatasets`·`listPalettes`·`listDatasetFieldSuggestions` 를 **신설과 동시에**
(`〈80〉-㉯ 5` — 열어 두고 안 만들면 501 이 는다), P5 가 프로젝트 셋, `〈90〉` 세션 둘,
`〈127〉`·`〈150〉` 수정 op 셋, 8차 해제(`〈338〉`)가 프리사인드 전송 9 op(local 모드에서는
정직한 501), 9차 해제 C2(`〈339〉-(다)`)가 다운로드 셋(`download.router` — 티켓 둘 + 바이트 하나,
바이트 op 은 `security: []` 로 **티켓이 곧 자격**이다).
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from ..kernel import aws_credentials, errors
from ..kernel import authn
from ..kernel.auth import SubjectRegistry
from ..kernel.credentials import CredentialStore
from ..kernel.throttle import AttemptLimiter
from ..kernel.config import Settings, load_settings
from ..kernel.db import make_engine, make_session_factory
from ..kernel.download_ticket import DownloadTicketSigner
from ..kernel.session_token import SessionSigner
from .relay import (HttpDatasetSearchRelay, HttpLineageSuggestionRelay,
                    HttpPreviewRelay)
from .routes import (access, catalog, download, identity, ingestion, insight, lineage,
                     members, not_implemented, preview, project, session, upload_transfers)

API_PREFIX = "/api/v1"

#: 저장 규칙 위반의 **감시 표면**. 본문에서 뺀 사유는 여기로 간다 — 빼기만 하고 남기지
#: 않으면 「값이 안 맞는다」만 남고 **무엇이 안 맞았는지 아무도 못 센다.**
_integrity_log = logging.getLogger("colab_core.integrity")

#: 사용자 오류로 갈라 내는 SQLSTATE **둘뿐**이다 (psycopg 3 `Error.sqlstate` · PostgreSQL
#: class 23). 나머지 무결성 위반(외래키 `23503` · not-null `23502` …)은 **다시 던진다** —
#: 그것들은 사용자가 고칠 수 있는 값이 아니라 **우리 코드가 잘못 쓴 것**이고, 4xx 로 접는
#: 순간 감시에서 사라진다. 상수가 psycopg 실물과 갈리지 않는지는
#: `tests/test_input_error_paths.py` 가 psycopg 예외 클래스와 대조해 못 박는다.
SQLSTATE_UNIQUE_VIOLATION = "23505"
SQLSTATE_CHECK_VIOLATION = "23514"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(
        title="CoLAB v2 — core-api",
        version="0.1.0",
        openapi_url=None,   # 계약 정본은 contracts/seams/fe-core.yaml 이다. 앱이 계약을 만들지 않는다.
        docs_url=None,
        redoc_url=None,
    )
    engine = make_engine(settings.database_url)
    app.state.engine = engine
    app.state.settings = settings
    app.state.session_factory = make_session_factory(engine)
    app.state.subjects = SubjectRegistry.from_file(settings.subjects_file)
    # 인증 수단의 **교체 지점은 `kernel/authn.py::build` 하나**다 (`PLAN-SoT §9 〈90〉-㉮`).
    # 여기서는 설정을 넘기기만 한다 — 앱은 수단이 몇 개인지도 알 필요가 없다.
    #
    # 서명 비밀값이 없으면 세션 어댑터도 발급기도 서지 않는다. **그래도 심어 둔 주체 표는
    # 그대로 돈다**(병존 · `〈90〉-㉱`) — 로그인을 못 세운 것이 기존 도구를 끊는 이유가 되면 안 된다.
    _signer = (SessionSigner(settings.session_secret,
                             ttl_minutes=settings.session_ttl_minutes)
               if settings.session_secret else None)
    app.state.authenticators, app.state.session_issuer = authn.build(
        registry=app.state.subjects, signer=_signer,
        credentials=CredentialStore.from_file(settings.credentials_file))
    # 다운로드 티켓 서명기 — **같은 비밀값**으로 선다 (`〈339〉-(다)`). 비밀값이 없으면 세우지
    # 않고 다운로드 op 셋이 503 을 낸다(`routes/download.py`). 조용한 기본 키는 없다.
    app.state.download_tickets = (DownloadTicketSigner(settings.session_secret)
                                  if settings.session_secret else None)
    # 시도 제한은 **프로세스 안에서만** 센다 — 한계는 `kernel/throttle.py` 가 적었다.
    app.state.login_limiter = AttemptLimiter(
        max_failures=settings.login_max_failures,
        window_seconds=settings.login_window_seconds)
    # 중계 두 곳. viz-render 주소가 없으면 **중계를 만들지 않는다** — 없는 것을 있는 척하지
    # 않고, 미리보기 op 이 503 봉투로 정직하게 답한다. 그래도 등록·계보 확정은 그대로 돈다.
    #
    # ⚠ **자격 증명도 주소와 똑같이 다룬다.** `core-viz.yaml` 은 `security: [serviceToken]` 로
    # 모든 렌더 표면에 bearer 를 요구한다 — 토큰이 없으면 중계를 세워 봐야 저쪽에서 401 이고,
    # 그것은 화면에 「그리는 서버에 못 닿았다」로만 보인다. **없으면 안 세운다.**
    app.state.previews = (HttpPreviewRelay(settings.viz_base_url,
                                           service_token=settings.viz_service_token)
                          if settings.viz_base_url and settings.viz_service_token else None)
    # ai-service 는 주소가 없어도 중계를 세운다 — 그쪽이 **0건 + degraded** 를 만들어 낸다.
    # 「AI 가 없다」가 「업로드를 못 한다」가 되면 안 된다 (CLAUDE.md §3).
    app.state.suggestions = HttpLineageSuggestionRelay(settings.ai_base_url)
    # 검색도 같은 규칙이다 — 주소가 없으면 **0건 + degraded** 로 답하고 화면은 산다
    # (`〈80〉-㉯ 5`). 「AI 가 없다」가 「검색 화면이 죽는다」가 되면 안 된다.
    app.state.searches = HttpDatasetSearchRelay(settings.ai_base_url)

    # liveness — 배포 배관이다. 계약(fe-core.yaml) 밖 경로이므로 API_PREFIX 아래에 두지 않는다.
    # 라우트 표 오라클(tests/test_route_table.py)은 API_PREFIX 로 시작하는 라우트만 세므로 34 는 그대로다.
    # **DB 를 건드리지 않는다** — 프로세스 생존과 DB 도달성은 다른 질문이고, 섞으면
    # DB 가 잠깐 흔들릴 때 오케스트레이터가 멀쩡한 프로세스를 죽인다.
    @app.get("/healthz", include_in_schema=False)
    def _healthz() -> dict:
        return {"unit": "core-api", "status": "alive", "implemented": True}

    # 저장 배관 진단 — 배포 검사기(`ops/deploy_doctor.py` ⑪)가 「앱이 어떤 자격증명으로 S3 에 가는가」를
    # 묻는 자리다 (`PLAN-SoT §9 〈342〉-㉲`). 역시 계약 밖 · `/api/v1` 밖. **키 값은 절대 싣지 않는다** —
    # 출처(`env|ecs|imds`)와 만료 시각만. 자격증명 사슬이 1초 안에 답하지 않으면 `credentialSource: null`
    # 과 사유 한 줄로 답한다 — 헬스 경로가 IMDS 타임아웃에 매달리면 오케스트레이터가 멀쩡한 프로세스를 죽인다.
    @app.get("/healthz/storage", include_in_schema=False)
    def _healthz_storage(request: Request) -> dict:
        s = request.app.state.settings
        if s.storage_mode != "s3":
            return {"storageMode": s.storage_mode}
        out: dict = {"storageMode": "s3", "bucket": s.s3_bucket, "region": s.s3_region}
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            creds, source = pool.submit(aws_credentials.load_credentials).result(timeout=1.0)
        except FutureTimeout:
            out.update(credentialSource=None, error="자격증명 조회가 1초 안에 끝나지 않았다 (env→ECS→IMDSv2)")
        except RuntimeError:
            out.update(credentialSource=None, error="자격증명을 찾지 못했다 (env→ECS→IMDSv2 — S3.md §1)")
        else:
            out["credentialSource"] = source
            if creds.expires_at is not None:
                out["expiresAt"] = creds.expires_at.isoformat()
        finally:
            pool.shutdown(wait=False)
        return out

    for router in (session.router, identity.router, members.router, catalog.router,
                   # 다운로드 셋 — 경로가 다른 라우터의 글자 경로와 겹치지 않는다(`/datasets/{id}/download`
                   # · `/datasets/{id}/files/{id}/download` 는 세그먼트 수가 다르고 `/downloads/` 는
                   # 이 라우터뿐). 순서는 뜻이 없지만 카탈로그 옆에 둔다 — 같은 `catalog` 태그다.
                   download.router,
                   project.router,
                   upload_transfers.router,  # /uploads/transfers 가 /uploads/{uploadId} 보다 먼저
                   ingestion.router, lineage.router, preview.router, access.router,
                   insight.router):
        app.include_router(router, prefix=API_PREFIX)
    not_implemented.register(app, prefix=API_PREFIX)

    @app.exception_handler(HTTPException)
    async def _http_error(_request, exc: HTTPException):
        return errors.error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request, exc: RequestValidationError):
        return errors.error_response(
            errors.bad_request("요청 값이 규칙에 맞지 않는다.", {"errors": str(exc.errors())})
        )

    # ── 입력 오류 · 저장 규칙 위반 (`CODE-REVIEW-20260903` #12) ──────────────
    # 종전에는 핸들러가 위 둘뿐이라, 손검사를 빠뜨린 자리에서 **사용자의 오타가 500** 이
    # 됐다. 500 은 「서버가 깨졌다」는 뜻이고 그 문장은 사람을 재시도하게 만든다 —
    # 다시 보내도 같은 500 이다. 400·409 는 **누구 잘못인가**를 정확히 말한다.
    #
    # ⚠ 가드가 먼저다. 이 두 핸들러는 **가드가 놓친 것을 받는 그물**이지 가드의 대체가
    # 아니다 — 그물만 두면 어느 자리가 검사를 안 하는지 아무도 모른다.
    @app.exception_handler(errors.InputError)
    async def _input_error(_request, exc: errors.InputError):
        return errors.input_error_response(exc)

    @app.exception_handler(IntegrityError)
    async def _integrity_error(_request, exc: IntegrityError):
        # **SQLSTATE 로 가른다** — 종전에는 `IntegrityError` 전부가 409 한 갈래였다.
        # 그물이 너무 넓으면 **우리 코드의 결함까지 삼킨다**: 외래키 위반·not-null 위반은
        # 사용자가 고칠 수 있는 값이 아니라 우리가 잘못 쓴 것인데, 409 로 접히면
        # 「이미 있어요」로 위장한 채 5xx 계수·경보에서 사라진다.
        orig = exc.orig
        sqlstate = getattr(orig, "sqlstate", None)
        if sqlstate not in (SQLSTATE_UNIQUE_VIOLATION, SQLSTATE_CHECK_VIOLATION):
            # **다시 던진다.** 모르는 것을 아는 척 접지 않는다 — 500 으로 남아 눈에 보이는
            # 편이, 이름 붙은 4xx 로 조용히 사라지는 것보다 싸다.
            raise exc
        # **사유는 서버에만 남긴다.** 본문에 실으면 표·열·제약 이름이 화면까지 간다.
        # ⚠ `str(exc.orig)` 를 쓰지 않는다 — psycopg 의 `DETAIL:` 줄은 **사용자가 넣은 값**
        # (키·컬럼값)을 그대로 담고, 로그는 덤프·티켓·화면 캡처를 따라다닌다. 남길 것은
        # **무엇이 안 맞았는지**(SQLSTATE · 제약 이름)이지 **어떤 값이었는지**가 아니다.
        _integrity_log.warning(
            "event=%s sqlstate=%s constraint=%s", "db.integrity_error", sqlstate,
            getattr(getattr(orig, "diag", None), "constraint_name", None))
        if sqlstate == SQLSTATE_CHECK_VIOLATION:
            # CHECK 위반은 「두 번 일어날 수 없다」가 아니라 **「그 값이 아니다」**이다.
            # 409 로 접으면 화면은 「이미 있어요」로 읽고 사용자는 고칠 수 있는 값을 안 고친다.
            return errors.input_error_response(
                errors.InputError(errors.INTEGRITY_INPUT_MESSAGE))
        return errors.integrity_error_response()

    return app
