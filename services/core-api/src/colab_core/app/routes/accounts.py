"""서비스 운영자 전용 계정 발급·목록·재설정·비활성화와 첫 비밀번호 변경."""
from __future__ import annotations
import datetime as dt
import re
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.db_credentials import ServiceAccountRow, normalize_login_name
from ...kernel.ids import Ulid
from ...kernel.password import hash_password
from ...kernel.login_sessions import SessionStoreUnavailable
from ..deps import current_session_subject, current_subject

router = APIRouter()

class AccountCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=128)
    labId: str
    role: str
    initialPassword: str = Field(min_length=10, max_length=512)

class PasswordChange(BaseModel):
    newPassword: str = Field(min_length=10, max_length=512)

class PasswordReset(BaseModel):
    """운영자가 심는 **새 초기 비밀번호**. 길이 규칙은 발급 때와 같은 한 벌이다."""
    model_config = ConfigDict(extra="forbid")
    newPassword: str = Field(min_length=10, max_length=512)

class AccountStatusChange(BaseModel):
    """두 값뿐이다 — 세 번째 상태를 계약으로도 코드로도 열지 않는다."""
    model_config = ConfigDict(extra="forbid")
    status: Literal["active", "inactive"]

def _admin(request: Request):
    factory = request.app.state.account_admin_factory
    if factory is None:
        raise errors.ApiError(503, "ACCOUNT_ADMIN_UNAVAILABLE", "계정 관리 저장소가 설정되지 않았다.")
    return factory

def _require_operator(request: Request, subject: Subject) -> None:
    with _admin(request)() as db:
        found = db.execute(text(
            "SELECT 1 FROM account_admin.service_operator WHERE account_id=:id"),
            {"id": str(subject.account_id)}).first()
    if found is None:
        raise errors.forbidden("서비스 운영자만 계정을 관리할 수 있다.")

def _credentials(request: Request):
    store = request.app.state.database_credentials
    if store is None:
        raise errors.ApiError(503, "ACCOUNT_ADMIN_UNAVAILABLE", "계정 관리 저장소가 설정되지 않았다.")
    return store

def _account_id(value: str) -> str:
    if not Ulid.is_valid(value):
        raise errors.bad_request("계정 ID가 정규 ID가 아니다.")
    return value

def _as_json(row: ServiceAccountRow) -> dict:
    last = row.last_login_at
    if isinstance(last, dt.datetime):
        last = last.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return {"accountId": row.account_id, "email": row.email, "name": row.name,
            "labId": row.lab_id, "labName": row.lab_name, "role": row.role,
            "status": row.status, "lastLoginAt": last}

@router.get("/admin/account-options", name="getAccountOptions")
def account_options(request: Request, subject: Subject = Depends(current_subject)) -> dict:
    _require_operator(request, subject)
    with _admin(request)() as db:
        labs = [{"labId": row.id, "name": row.name} for row in db.execute(
            text("SELECT id, name FROM d1_lab ORDER BY name, id"))]
    return {"labs": labs, "roles": ["연구원", "교수"]}

@router.post("/admin/accounts", name="createServiceAccount", status_code=201)
def create_account(body: AccountCreate, request: Request,
                   subject: Subject = Depends(current_subject)) -> dict:
    _require_operator(request, subject)
    email = normalize_login_name(body.email)
    if re.fullmatch(r"[^@\s]+@(?:[^@\s.]+\.)+[^@\s.]+", email) is None:
        raise errors.bad_request("이메일 형식이 맞지 않는다.")
    if not Ulid.is_valid(body.labId):
        raise errors.bad_request("연구실 ID가 정규 ID가 아니다.")
    if body.role not in ("교수", "연구원"):
        raise errors.bad_request("역할은 교수 또는 연구원이다.")
    account_id = Ulid.generate()
    made = hash_password(body.initialPassword)
    if request.app.state.legacy_credentials.contains_normalized(email):
        raise errors.conflict("이미 사용하는 이메일이다.")
    try:
        with _admin(request).begin() as db:
            db.execute(text("SELECT pg_advisory_xact_lock(1131379081)"))
            if db.execute(text("SELECT 1 FROM d1_lab WHERE id=:id"),
                          {"id": body.labId}).first() is None:
                raise errors.not_found("연구실을 찾지 못했다.")
            if db.execute(text("SELECT 1 FROM d1_account WHERE lower(btrim(email))=:email"),
                          {"email": email}).first() is not None:
                raise errors.conflict("이미 사용하는 이메일이다.")
            db.execute(text("INSERT INTO d1_account(id,lab_id,name,email) VALUES (:id,:lab,:name,:email)"),
                       {"id": str(account_id), "lab": body.labId,
                        "name": body.name.strip(), "email": email})
            db.execute(text("INSERT INTO d2_member_role(account_id,lab_id,role) VALUES (:id,:lab,:role)"),
                       {"id": str(account_id), "lab": body.labId, "role": body.role})
            db.execute(text("""
                INSERT INTO account_admin.login_credential
                  (account_id,login_name,kdf,salt,password_hash,n,r,p)
                VALUES (:id,:email,:kdf,:salt,:hash,:n,:r,:p)
            """), {"id": str(account_id), "email": email, **made.as_dict()})
    except IntegrityError:
        raise errors.conflict("이미 사용하는 이메일이다.") from None
    return {"accountId": str(account_id), "email": email, "name": body.name.strip(),
            "labId": body.labId, "role": body.role}

@router.get("/admin/accounts", name="listServiceAccounts")
def list_accounts(request: Request,
                  labId: str | None = Query(default=None),
                  status: str | None = Query(default=None),
                  role: str | None = Query(default=None),
                  email: str | None = Query(default=None, max_length=320),
                  subject: Subject = Depends(current_subject)) -> dict:
    """전 연구실 한 목록. **운영자 전용 경로의 등재된 경계 예외**다 — 이 목록이 연구실로
    좁혀지면 운영자가 다른 연구실 계정을 되살릴 길이 없다.
    """
    _require_operator(request, subject)
    if labId is not None and not Ulid.is_valid(labId):
        raise errors.bad_request("연구실 ID가 정규 ID가 아니다.")
    if status is not None and status not in ("active", "inactive"):
        raise errors.bad_request("상태는 active 또는 inactive 다.")
    if role is not None and role not in ("교수", "연구원"):
        raise errors.bad_request("역할은 교수 또는 연구원이다.")
    rows = _credentials(request).list_accounts(
        lab_id=labId, status=status, role=role, email=email)
    return {"accounts": [_as_json(row) for row in rows]}


@router.post("/admin/accounts/{accountId}/password-reset",
             name="resetServiceAccountPassword")
def reset_account_password(accountId: str, body: PasswordReset, request: Request,
                           subject: Subject = Depends(current_subject)) -> dict:
    """새 초기 비밀번호를 운영자가 직접 심는다. 첫 로그인 변경이 다시 강제되고 전 기기가 끊긴다.

    **응답에 비밀번호 필드가 없다** — 운영자는 자기가 입력한 값을 이미 알고 있고,
    되돌려 주는 순간 그 값이 화면·로그·프록시에 남는다.
    """
    _require_operator(request, subject)
    if _credentials(request).reset_password(_account_id(accountId), body.newPassword) is None:
        raise errors.not_found("서비스 계정 자격을 찾지 못했다.")
    return {"accountId": accountId, "mustChangePassword": True}


@router.post("/admin/accounts/{accountId}/status", name="setServiceAccountStatus")
def set_account_status(accountId: str, body: AccountStatusChange, request: Request,
                       subject: Subject = Depends(current_subject)) -> dict:
    """비활성화/재활성화. 행을 지우지 않아 데이터·소유권은 그대로 남는다."""
    _require_operator(request, subject)
    account_id = _account_id(accountId)
    if body.status == "inactive" and account_id == str(subject.account_id):
        # 자기를 끄면 되살릴 사람이 없다 — 운영자 지정은 아직 SQL 수동이다.
        raise errors.bad_request("자기 계정은 비활성화할 수 없다.")
    status = _credentials(request).set_status(account_id, body.status)
    if status is None:
        raise errors.not_found("서비스 계정 자격을 찾지 못했다.")
    return {"accountId": accountId, "status": status}


@router.put("/me/password", name="changeOwnPassword")
def change_password(body: PasswordChange, request: Request,
                    subject: Subject = Depends(current_session_subject)) -> dict:
    sessions = request.app.state.login_sessions
    claims = getattr(request.state, "session_claims", None)
    if sessions is None or claims is None or subject.credential_version is None:
        raise errors.forbidden("DB 서비스 계정만 이 비밀번호를 변경할 수 있다.")
    if not subject.must_change_password:
        raise errors.forbidden("최초 비밀번호 변경 세션이 아니다.")
    try:
        changed = sessions.change_initial_password(claims, body.newPassword)
    except ValueError:
        raise errors.bad_request("새 비밀번호는 초기 비밀번호와 달라야 한다.") from None
    except SessionStoreUnavailable:
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소에 연결할 수 없다.") from None
    if changed is None:
        raise errors.unauthorized("세션이 만료됐거나 이미 사용됐다.")
    return {"token": changed.token,
            "expiresAt": changed.expires_at.isoformat().replace("+00:00", "Z"),
            "sessionId": str(changed.session_id)}
