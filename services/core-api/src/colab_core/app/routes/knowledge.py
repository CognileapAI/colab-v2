"""Fixed internal callback: service bearer plus tracked user session required."""
import secrets
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from ...kernel.knowledge_wire import Principal, SourceIssueRequest, SourceValidateRequest, SourceReadRequest
from ...kernel.knowledge_wire import DeletionIssueRequest, DeletionValidateRequest
from ...kernel.ids import Ulid
from ..knowledge_source_authority import SourceAuthority, DeletionAuthority

router = APIRouter(prefix='/internal/knowledge/source')
deletion_router = APIRouter(prefix='/internal/knowledge/deletion')
MAX_BYTES = 1024 * 1024


def configure(app):
    settings=app.state.settings
    deletion=settings.knowledge_deletion_token
    if (settings.knowledge_source_enabled or deletion is not None or settings.knowledge_deletion_lab is not None
        or settings.knowledge_deletion_enabled is not None) and type(settings.knowledge_deletion_enabled) is not bool:
        raise ValueError('explicit deletion mode required')
    if settings.knowledge_deletion_enabled:
        if (not isinstance(deletion,str) or not deletion.strip() or any(c in deletion for c in '\r\n')
            or deletion in {settings.knowledge_callback_token,settings.ai_service_token}
            or not Ulid.is_valid(settings.knowledge_deletion_lab)):
            raise ValueError('deletion capability configuration incomplete')
        app.state.knowledge_deletion=DeletionAuthority(app.state.session_factory,settings.knowledge_deletion_lab)
        app.include_router(deletion_router)
    if not settings.knowledge_source_enabled:
        return
    token=settings.knowledge_callback_token
    if (not isinstance(token,str) or not token.strip() or any(c in token for c in '\r\n')
        or not settings.ai_service_token or token == settings.ai_service_token
        or app.state.login_sessions is None or app.state.database_credentials is None):
        raise ValueError('knowledge source configuration incomplete')
    app.state.knowledge_source=SourceAuthority(app.state.session_factory,app.state.database_credentials)
    app.include_router(router)


async def _input(request, model):
    expected=request.app.state.settings.knowledge_callback_token
    if not secrets.compare_digest(request.headers.get('authorization','').encode(),('Bearer '+expected).encode()):
        raise HTTPException(401,'unauthorized')
    try:
        subject=await run_in_threadpool(request.app.state.login_sessions.authenticate,request.headers.get('x-colab-session',''))
    except Exception:
        raise HTTPException(503,'source authority unavailable') from None
    if subject is None or subject.must_change_password or subject.credential_version is None:
        raise HTTPException(401,'unauthorized')
    principal=Principal(account_id=str(subject.account_id),lab_id=str(subject.lab_id),session_version=subject.credential_version)
    return await _body(request,model),principal


async def _body(request,model):
    body=bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body)>MAX_BYTES:
            raise HTTPException(413,'request too large')
    try:
        payload=model.model_validate_json(body)
    except (ValidationError,ValueError):
        raise HTTPException(422,'invalid request') from None
    return payload


async def _deletion_input(request,model):
    expected=request.app.state.settings.knowledge_deletion_token
    if not secrets.compare_digest(request.headers.get('authorization','').encode(),('Bearer '+expected).encode()):
        raise HTTPException(401,'unauthorized')
    return await _body(request,model)


@deletion_router.post('/issue')
async def issue_deletion(request: Request):
    payload=await _deletion_input(request,DeletionIssueRequest)
    try:
        command=await run_in_threadpool(request.app.state.knowledge_deletion.issue,
            payload.source_key,payload.expected_revision,ttl_seconds=300)
    except ValueError:
        raise HTTPException(403,'source unavailable') from None
    except Exception:
        raise HTTPException(503,'source authority unavailable') from None
    return JSONResponse(command.model_dump(mode='json'),headers={'Cache-Control':'no-store'})


@deletion_router.post('/validate')
async def validate_deletion(request: Request):
    payload=await _deletion_input(request,DeletionValidateRequest)
    try:
        status=await run_in_threadpool(request.app.state.knowledge_deletion.validate,payload.command)
    except ValueError:
        raise HTTPException(403,'source unavailable') from None
    except Exception:
        raise HTTPException(503,'source authority unavailable') from None
    return JSONResponse({'status':status},headers={'Cache-Control':'no-store'})


@router.post('/issue')
async def issue(request: Request):
    payload,principal=await _input(request,SourceIssueRequest)
    try:
        command=await run_in_threadpool(request.app.state.knowledge_source.issue,payload.source_key,principal,ttl_seconds=300)
    except ValueError:
        raise HTTPException(403,'source unavailable') from None
    except Exception:
        raise HTTPException(503,'source authority unavailable') from None
    return JSONResponse({'command':command.model_dump(mode='json'),'principal':principal.model_dump()},headers={'Cache-Control':'no-store'})


@router.post('/validate')
async def validate(request: Request):
    payload,principal=await _input(request,SourceValidateRequest)
    try:
        status=await run_in_threadpool(request.app.state.knowledge_source.validate,payload.command,principal)
    except Exception:
        raise HTTPException(503,'source authority unavailable') from None
    return JSONResponse({'status':status,'principal':principal.model_dump()},headers={'Cache-Control':'no-store'})


@router.post('/read')
async def read(request: Request):
    payload,principal=await _input(request,SourceReadRequest)
    try:
        status=await run_in_threadpool(request.app.state.knowledge_source.authorize_read,payload.receipt,principal)
    except Exception:
        raise HTTPException(503,'source authority unavailable') from None
    return JSONResponse({'status':status,'principal':principal.model_dump()},headers={'Cache-Control':'no-store'})
