"""core-api 앱 — fe-core seam **46** 오퍼레이션 전부를 등록한다.

실동작 **22 개**. P2 가 열둘을 가져왔다 (`P2-EXEC §4 W2 P2-api`) —
업로드 6(`createUpload` `getUploadStatus` `createDataset` `addDatasetFile`
`replaceDatasetGridFile` `deleteDatasetGridFile`) · 계보 확정 3(`addLineageParent`
`removeLineageParent` `confirmLineage`) · 미리보기 중계 2 · AI 제안 중계 1.
그리고 S1 이 `searchDatasets` 하나를 **신설과 동시에** 가져갔다 — `〈80〉-㉯ 5`(승인된 1회
계약 동결 해제)가 검색 진입점을 열었고, 열어 두고 안 만들면 501 이 24 → 25 가 된다.
나머지 **24 개**는 **501 + ErrorEnvelope** 로 응답한다 (NIGHT-20260823 §3) — 이 수는 S1 에서
변하지 않는다 (`〈74〉-㉱` · `C1` 통과 조건 2).
미구현에 404 를 쓰지 않는다 — 404 는 「경계 밖」의 뜻으로 이미 예약돼 있다 (PLAN-SoT §9-㊱).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from ..kernel import errors
from ..kernel.auth import SubjectRegistry
from ..kernel.config import Settings, load_settings
from ..kernel.db import make_engine, make_session_factory
from .relay import (HttpDatasetSearchRelay, HttpLineageSuggestionRelay,
                    HttpPreviewRelay)
from .routes import (catalog, identity, ingestion, lineage, members, not_implemented,
                     preview, project)

API_PREFIX = "/api/v1"


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

    for router in (identity.router, members.router, catalog.router, project.router,
                   ingestion.router, lineage.router, preview.router):
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

    return app
