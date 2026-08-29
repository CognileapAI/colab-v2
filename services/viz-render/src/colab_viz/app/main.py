"""viz-render 앱 — `core-viz.yaml` 의 표면 중 **렌더 5 op**.

등록된 것 — `createRender` · `getRender` · `getRenderTile` · `listPalettes`,
그리고 **`createScreenshot`**(P3 · `WORK-UNITS §10.2` 말미가 완료 정의로 올렸다).
없는 경로는 라우트 표에 없는 것이 정직하다 — 501 로 자리만 잡아 두지 않는다:
이 seam 에는 「미구현 표」 규약이 없다(그것은 `fe-core` 쪽 장치다).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from ..domains.d7_visualization.jobs import JobStore
from ..kernel import errors
from ..kernel.config import Settings, load_settings
from ..ports.source import FilesystemSourcePort
from .routes import renders, screenshots, style

API_PREFIX = "/viz/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(
        title="CoLAB v2 — viz-render",
        version="0.1.0",
        # 계약 정본은 contracts/seams/core-viz.yaml 이다. 앱이 계약을 만들지 않는다.
        openapi_url=None, docs_url=None, redoc_url=None,
    )
    app.state.settings = settings
    app.state.source = FilesystemSourcePort(settings.source_root)
    app.state.jobs = JobStore(execution=settings.execution,
                              tile_url_base=settings.tile_url_base,
                              ttl_seconds=settings.result_ttl_seconds,
                              tile_signing_secret=settings.tile_signing_secret,
                              signature_ttl_seconds=settings.tile_signature_ttl_seconds)

    @app.get("/healthz", include_in_schema=False)
    def _healthz() -> dict:
        # 프로세스 생존과 파일 도달성은 다른 질문이다 — 섞으면 멀쩡한 프로세스가 죽는다.
        return {"unit": "viz-render", "status": "alive", "implemented": True}

    for router in (renders.router, renders.tile_router,
                   screenshots.router, style.router):
        app.include_router(router, prefix=API_PREFIX)

    @app.exception_handler(HTTPException)
    async def _http_error(_request, exc: HTTPException):
        return errors.error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request, exc: RequestValidationError):
        return errors.error_response(
            errors.bad_request("요청 값이 규칙에 맞지 않는다.", {"errors": str(exc.errors())}))

    return app
