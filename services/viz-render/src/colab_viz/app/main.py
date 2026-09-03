"""viz-render 앱 — `core-viz.yaml` 의 표면 **6 op**.

등록된 것 — `createRender` · `getRender` · `getRenderTile` · `listPalettes`,
**`createScreenshot`**(P3 · `WORK-UNITS §10.2` 말미가 완료 정의로 올렸다),
그리고 **`lookupValue`**(`V-2` 값 조회 · `PLAN-SoT §9 〈294〉` · 15차 해제).
없는 경로는 라우트 표에 없는 것이 정직하다 — 501 로 자리만 잡아 두지 않는다:
이 seam 에는 「미구현 표」 규약이 없다(그것은 `fe-core` 쪽 장치다).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from ..domains.d7_visualization.jobs import JobStore
from ..kernel import errors
from ..kernel.config import Settings, load_settings
from ..ports.source import FilesystemSourcePort
from .trigger_bus import SpoolTriggerPort
from .trigger_loop import TriggerDrainLoop
from .routes import renders, screenshots, style, values

API_PREFIX = "/viz/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """**받는 자리에 실행자를 붙인다**(`#60`). 자리가 없으면 루프도 없다.

        `〈253〉` 이 세운 배선은 `app.state.triggers` 까지였고 그것을 **부르는 자가
        런타임에 없었다** — 버스에 봉투가 쌓여도 아무 일도 안 일어났다. 여기가 그
        호출자이고, **HTTP 표면은 한 자리도 늘지 않았다**(계약 개정 0건).
        """
        loop = None
        if app.state.triggers is not None:
            loop = TriggerDrainLoop(app.state.triggers, jobs=app.state.jobs,
                                    source=app.state.source,
                                    interval_seconds=settings.trigger_poll_seconds)
            loop.start()
        app.state.trigger_loop = loop
        try:
            yield
        finally:
            # **스레드를 남기지 않는다** — 남기면 SIGTERM 에 컨테이너가 매달린다.
            if loop is not None:
                loop.stop()

    app = FastAPI(
        lifespan=lifespan,
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
                              signature_ttl_seconds=settings.tile_signature_ttl_seconds,
                              tile_branch_enabled=settings.tile_branch_enabled)
    # **받는 자리를 앱이 들고 선다**(`〈253〉` · `Y-1`). 배포가 자리를 안 주면 `None` 이고
    # 트리거는 오지 않는다 — **자리를 지어내지 않는다.** 이 연결이 코드에 있는 것이
    # 요점이다: 배포 설정에만 있는 연결은 조용히 끊어져도 아무도 모른다(RULING ㉗ 근거).
    app.state.triggers = (SpoolTriggerPort(settings.trigger_spool)
                          if settings.trigger_spool else None)

    @app.get("/healthz", include_in_schema=False)
    def _healthz() -> dict:
        # 프로세스 생존과 파일 도달성은 다른 질문이다 — 섞으면 멀쩡한 프로세스가 죽는다.
        #
        # ⭑ **⟨2026-08-31 · `〈240〉`⟩ `tileBranch` 는 A/B 의 관측 자리다.** 「도는 스택이
        #   지금 어느 갈래인가」를 물어볼 곳이 없으면 A/B 비교는 기억에 의존한다. 이
        #   레포의 배포 판정은 이미 **헬스 본문 대조**이므로(`verify/verify-deploy.sh` —
        #   「루트 200 으로 판정하지 않는다」) 같은 자리에 싣는다.
        # ⚠ **계약 표면이 아니다** — `/healthz` 는 `include_in_schema=False` 이고
        #   `core-viz.yaml` 은 한 글자도 바뀌지 않았다(동결 해제 0건).
        # ⚠ **비밀을 싣지 않는다** — 켜짐/꺼짐 두 글자뿐이고 서명 비밀은 나가지 않는다.
        return {"unit": "viz-render", "status": "alive", "implemented": True,
                "tileBranch": "켜짐" if settings.tile_branch_enabled else "꺼짐"}

    for router in (renders.router, renders.tile_router,
                   screenshots.router, style.router, values.router):
        app.include_router(router, prefix=API_PREFIX)

    @app.exception_handler(HTTPException)
    async def _http_error(_request, exc: HTTPException):
        return errors.error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request, exc: RequestValidationError):
        return errors.error_response(
            errors.bad_request("요청 값이 규칙에 맞지 않는다.", {"errors": str(exc.errors())}))

    return app
