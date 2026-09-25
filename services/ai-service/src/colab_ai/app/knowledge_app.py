"""Separate ASGI factory: uvicorn colab_ai.app.knowledge_app:create_app --factory.

No D10 model imports or background loop. Disabled mode exposes health only.
"""
from contextlib import asynccontextmanager
import secrets
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.concurrency import run_in_threadpool
from ..kernel.knowledge_config import KnowledgeSettings
from ..kernel.knowledge_wire import KnowledgeReplaceRequest, KnowledgeReadRequest, DeletionValidateRequest
from .knowledge_writer import KnowledgeWriter, KnowledgeInvalidator
from .knowledge_reader import KnowledgeReader
from .source_authority_client import SourceAuthorityClient, RequestAuthority, DeletionAuthority


def create_app(settings=None):
    settings=KnowledgeSettings.from_env() if settings is None else settings
    engine=create_engine(settings.database_url) if settings.enabled else None
    @asynccontextmanager
    async def lifespan(app):
        try:yield
        finally:
            if engine is not None:engine.dispose()
    app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
    @app.get('/healthz')
    def health():return {'enabled':settings.enabled,'deletion_enabled':settings.enabled and settings.deletion_enabled is True}
    if not settings.enabled:return app
    factory=sessionmaker(engine)
    callback=SourceAuthorityClient(settings.source_url,token=settings.callback_token,timeout=settings.timeout)
    deletion_authority=None
    if settings.deletion_enabled:
        deletion_authority=DeletionAuthority(SourceAuthorityClient(settings.source_url,
            token=settings.deletion_token,timeout=settings.timeout))
    async def execute(request:Request,*,reading=False,deleting=False):
        def failure(status,code):return JSONResponse({'code':code,'message':code.replace('_',' ')},status_code=status,headers={'Cache-Control':'no-store'})
        credential=settings.deletion_token if deleting else settings.reader_token if reading else settings.writer_token
        if not secrets.compare_digest(request.headers.get('authorization','').encode(),('Bearer '+credential).encode()):
            return failure(401,'unauthorized')
        token=request.headers.get('x-colab-session','')
        if not deleting and (not token or len(token)>16384):return failure(401,'unauthorized')
        body=bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>1024*1024:return failure(413,'request_too_large')
        model=DeletionValidateRequest if deleting else KnowledgeReadRequest if reading else KnowledgeReplaceRequest
        try:payload=model.model_validate_json(body)
        except (ValidationError,ValueError):return failure(422,'invalid_request')
        authority=RequestAuthority(callback,token)
        try:
            if deleting:
                receipt=await run_in_threadpool(KnowledgeInvalidator(factory,deletion_authority,settings.deletion_lab).invalidate,payload.command)
            elif reading:
                receipt=await run_in_threadpool(KnowledgeReader(factory,authority).read,payload.source_key,payload.expected_receipt_id)
            else:
                receipt=await run_in_threadpool(KnowledgeWriter(factory,authority).replace,payload.command,payload.principal)
        except ValueError as exc:
            code=str(exc)
            if code=='forbidden':return failure(403,code)
            if code in {'stale_source','stale_generation','stale_release','idempotency_conflict'}:return failure(409,code)
            return failure(503,'dependency_unavailable')
        except Exception:return failure(503,'dependency_unavailable')
        return JSONResponse(receipt.model_dump(mode='json'),headers={'Cache-Control':'no-store'})
    @app.post('/internal/knowledge/replace')
    async def replace(request:Request):return await execute(request)
    @app.post('/internal/knowledge/read')
    async def read(request:Request):return await execute(request,reading=True)
    if deletion_authority is not None:
        @app.post('/internal/knowledge/invalidate')
        async def invalidate(request:Request):return await execute(request,deleting=True)
    return app
