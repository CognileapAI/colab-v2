"""core-api 앱 — fe-core seam 34 오퍼레이션 전부를 등록한다.

실질의 5개(`getCurrentAccount` `getLab` `listDatasets` `listDatasetFiles` `createProject`)만
DB 를 읽고, 나머지 29 개는 **501 + ErrorEnvelope** 로 응답한다 (NIGHT-20260823 §3).
미구현에 404 를 쓰지 않는다 — 404 는 「경계 밖」의 뜻으로 이미 예약돼 있다 (PLAN-SoT §9-㊱).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from ..kernel import errors
from ..kernel.auth import SubjectRegistry
from ..kernel.config import Settings, load_settings
from ..kernel.db import make_engine, make_session_factory
from .routes import catalog, identity, not_implemented, project

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
    app.state.session_factory = make_session_factory(engine)
    app.state.subjects = SubjectRegistry.from_file(settings.subjects_file)

    # liveness — 배포 배관이다. 계약(fe-core.yaml) 밖 경로이므로 API_PREFIX 아래에 두지 않는다.
    # 라우트 표 오라클(tests/test_route_table.py)은 API_PREFIX 로 시작하는 라우트만 세므로 34 는 그대로다.
    # **DB 를 건드리지 않는다** — 프로세스 생존과 DB 도달성은 다른 질문이고, 섞으면
    # DB 가 잠깐 흔들릴 때 오케스트레이터가 멀쩡한 프로세스를 죽인다.
    @app.get("/healthz", include_in_schema=False)
    def _healthz() -> dict:
        return {"unit": "core-api", "status": "alive", "implemented": True}

    for router in (identity.router, catalog.router, project.router):
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
