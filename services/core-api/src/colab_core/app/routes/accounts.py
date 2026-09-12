"""서비스 운영자 전용 계정 발급과 첫 비밀번호 변경."""
from __future__ import annotations
import re

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.db_credentials import normalize_login_name
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
        raise errors.forbidden("서비스 운영자만 계정을 추가할 수 있다.")

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
