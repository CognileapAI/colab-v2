"""D2 조립 — 승인 처리 (WU-P6). 접근 요청 4 op · Verified 4 op.

**정본은 `Policy_승인_처리` v1.7 하나다.** 이 파일이 판정하는 것은 전부 거기 축자로 있다 —
처리 권한(§1.2 §6) · 사유 길이(§5) · 6개월(§1.3-6) · 전이(§7.1 §7.2) · 오류 문구(§9).

**경계를 어떻게 건너나** (`CLAUDE.md §3-1`). 요청 한 줄은 D2 의 사실이지만 화면이 받는
`AccessRequest` 는 데이터셋 이름(D3)과 요청자 이름(D1)을 함께 든다. `d2_access.py` 는 그
둘을 하나도 읽지 않고 식별자만 내놓고, **이 조립 루트**가 각 도메인의 모듈 함수로 채운다.
`routes/project.py` 가 소속 데이터셋 표를 채우는 것과 같은 무늬이고, 그래서 새 Port 가 필요 없다.

**두 갈래의 처리 권한이 다르다.**
  · 접근 요청 = 교수 + `승인 위임` 연구원  (§1.2 §6)
  · Verified  = **교수만, 위임 불가**       (§1.2 · P-22)
판정은 `d2_access.can_decide_access` · `can_decide_verification` 둘이 하고 여기서 다시
쓰지 않는다 — 같은 규칙을 두 곳에 적으면 한쪽만 고쳐진다.

⛔ **[모두 승인] 을 만들지 않는다** (`CLAUDE.md §3` · 계약 `approveAccessRequest` 산문 축자
「사람 단위·연구실 단위 일괄 승인 엔드포인트를 두지 않는다」). 승인·거절 op 은 **대상 하나를
경로에 갖는 것만** 있다. 목록을 몸통으로 받는 자리를 새로 만들지 않는다.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query, Response
from sqlalchemy.orm import Session

from ...domains import d1_identity, d2_access, d3_catalog, d8_insight
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db
from .catalog import PAGE_SIZE, _account_ref, _decode_cursor, _encode_cursor, _iso

router = APIRouter()

#: 요청 사유 0~300자 **선택** · 거절 사유 1~300자 **필수** · 취소 사유 0~120자 **선택** (§5).
_REASON_MAX = 300
_CANCEL_REASON_MAX = 120


def _optional_reason(body: dict | None, *, field: str = "reason", limit: int = _REASON_MAX):
    """선택 사유를 읽는다. **빈 문자열은 없음으로 접는다** — DB 는 1자 이상만 받는다.

    화면이 빈 칸을 그대로 보내는 것은 「안 적었다」이지 「빈 문자열을 적었다」가 아니다.
    """
    if body is None:
        return None
    value = body.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise errors.bad_request(f"{field} 는 문자열이다.")
    value = value.strip()
    if not value:
        return None
    if len(value) > limit:
        raise errors.bad_request(f"{field} 는 {limit}자를 넘지 않는다 (Policy_승인_처리 §5).")
    return value


def _living_dataset(db: Session, datasetId: str) -> Ulid:
    """경계 밖·묘비는 **404** 다 — 존재를 알리지 않는다 (P-9·P-10).

    403 을 쓰지 않는 이유: 남의 연구실 식별자에 403 을 주면 「그 식별자는 있다」가 새어 나간다.
    """
    dataset_id = Ulid(datasetId)
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found()
    return dataset_id


def _dataset_ref(db: Session, dataset_id: str) -> dict:
    core = d3_catalog.find_dataset_core(db, Ulid(dataset_id))
    # 이름이 없는 데이터셋은 없다(`d3_dataset_description.name` NOT NULL). 그래도 묘비가 된
    # 뒤의 요청 행은 남을 수 있으므로 지어내지 않고 식별자만 든다.
    return {"datasetId": dataset_id, "name": core.name if core else dataset_id}


def _account(db: Session, account_id: str) -> dict:
    row = d1_identity.find_account(db, Ulid(account_id))
    return {"accountId": account_id, "name": (row or {}).get("name") or account_id}


def _page(rows: list, cursor: str | None) -> tuple[list, int, str | None]:
    total = len(rows)
    offset = _decode_cursor(cursor)
    page = rows[offset:offset + PAGE_SIZE]
    return page, total, (_encode_cursor(offset + PAGE_SIZE)
                         if offset + PAGE_SIZE < total else None)


# ════════════════════════════════════════════════════════════════════════════
# 접근 요청 (§7.2)
# ════════════════════════════════════════════════════════════════════════════

@router.post("/datasets/{datasetId}/access-requests", name="createAccessRequest",
             status_code=201)
def create_access_request(datasetId: str, body: dict | None = Body(default=None),
                          subject: Subject = Depends(current_subject),
                          db: Session = Depends(scoped_db)) -> dict:
    """잠긴 데이터를 만난 자리에서 요청한다 (§1.3-5).

    **요청은 잠긴 상세에서 한다** — 카탈로그 행에는 이 버튼이 없다
    (`Policy_데이터_찾기:152` 축자 「행에는 접근 요청 버튼을 두지 않는다 · 행을 누르면
    잠긴 상세로 가고 요청은 거기서 한다」). 그 규칙은 화면이 지키고, 서버는 어느 화면에서
    왔는지 묻지 않는다 — 물으면 화면 구조가 서버 계약에 새어 들어간다.
    """
    dataset_id = _living_dataset(db, datasetId)
    reason = _optional_reason(body)

    access = d2_access.DatasetAccessAdapter(db).dataset_access([dataset_id]).get(datasetId)
    if access is not None and access.body_accessible:
        # 「이미 볼 수 있는 데이터다」 (계약 409). 요청할 자리가 없다.
        raise errors.conflict("이미 볼 수 있는 데이터예요.")
    if d2_access.pending_access_request_of(db, dataset_id, subject.account_id) is not None:
        raise errors.conflict("이미 검토 대기 중이에요.")

    row = d2_access.create_access_request(
        db, dataset_id=dataset_id, requester_id=subject.account_id, reason=reason)
    return {
        "requestId": row["id"],
        "dataset": _dataset_ref(db, row["dataset_id"]),
        "requester": _account(db, row["requester_account_id"]),
        "requestedAt": _iso(row["requested_at"]),
        "reason": row["reason"],
    }


@router.get("/access-requests/pending", name="listPendingAccessRequests")
def list_pending_access_requests(subject: Subject = Depends(current_subject),
                                 db: Session = Depends(scoped_db),
                                 cursor: str | None = Query(default=None)) -> dict:
    """받은 접근 요청 — 교수와 `승인 위임` 연구원만 받는다 (§6). **오래된 순** (§1.3).

    화면 상한(5건 + `+N건 더 보기`)은 화면이 정한다 — 서버는 봉투 그대로 준다 (계약 산문).
    """
    if not d2_access.can_decide_access(db, subject.account_id):
        raise errors.forbidden("접근 요청을 처리할 권한이 없다 (Policy_승인_처리 §6).")
    rows = d2_access.pending_access_requests(db)
    page, total, next_cursor = _page(rows, cursor)
    return {
        "items": [{
            "requestId": r["id"],
            "dataset": _dataset_ref(db, r["dataset_id"]),
            "requester": _account(db, r["requester_account_id"]),
            "requestedAt": _iso(r["requested_at"]),
            "reason": r["reason"],
        } for r in page],
        "totalCount": total,
        "nextCursor": next_cursor,
    }


def _decidable_request(db: Session, subject: Subject, requestId: str):
    """처리 대상 한 줄을 집는다. **404 와 403 의 순서가 규칙이다.**

    경계 밖이면 RLS 가 이미 행을 지웠으므로 **권한을 보기 전에** 404 다 — 권한을 먼저 보면
    남의 연구실 요청에 403 이 나가고 그 403 이 「그 요청은 있다」를 알린다.
    """
    row = d2_access.access_request_row(db, requestId)
    if row is None:
        raise errors.not_found()
    if not d2_access.can_decide_access(db, subject.account_id):
        raise errors.forbidden("접근 요청을 처리할 권한이 없다 (Policy_승인_처리 §6).")
    return row


@router.post("/access-requests/{requestId}/approval", name="approveAccessRequest")
def approve_access_request(requestId: str, subject: Subject = Depends(current_subject),
                           db: Session = Depends(scoped_db)) -> dict:
    """승인 — 허용 목록에 넣고 **만료일 = 승인일 + 6개월** (§1.3-6 · §7.2 · P-25).

    **승인의 단위는 데이터 한 건이다.** 이 op 은 요청 하나만 받고, 여러 건을 받는 형제를
    만들지 않는다 (`CLAUDE.md §3`).
    """
    _decidable_request(db, subject, requestId)
    result = d2_access.decide_access_request(
        db, request_id=requestId, decider_id=subject.account_id,
        approve=True, rejection_reason=None)
    if result is None:
        raise errors.conflict("이미 처리된 요청이에요.")
    return {
        "dataset": _dataset_ref(db, result["dataset_id"]),
        "grantee": _account(db, result["grantee"]),
        "approver": _account(db, str(subject.account_id)),
        "approvedAt": _iso(result["approved_at"]),
        "expiresAt": _iso(result["expires_at"]),
    }


@router.post("/access-requests/{requestId}/rejection", name="rejectAccessRequest",
             status_code=204)
def reject_access_request(requestId: str, body: dict | None = Body(default=None),
                          subject: Subject = Depends(current_subject),
                          db: Session = Depends(scoped_db)) -> Response:
    """거절 — **사유 1~300자 필수**이고 요청자에게 그대로 전달된다 (§5 · P-26).

    사유를 안 적으면 400 이다. 화면 문구는 §9 가 정본이다 —
    「사유를 적어 주세요. 요청한 사람에게 그대로 전달돼요.」
    """
    reason = _optional_reason(body)
    if reason is None:
        raise errors.bad_request(
            "사유를 적어 주세요. 요청한 사람에게 그대로 전달돼요 (Policy_승인_처리 §9).")
    _decidable_request(db, subject, requestId)
    result = d2_access.decide_access_request(
        db, request_id=requestId, decider_id=subject.account_id,
        approve=False, rejection_reason=reason)
    if result is None:
        raise errors.conflict("이미 처리된 요청이에요.")
    return Response(status_code=204)


# ════════════════════════════════════════════════════════════════════════════
# Verified (§7.1) — 교수만. 거절이 없다.
# ════════════════════════════════════════════════════════════════════════════

@router.post("/datasets/{datasetId}/verification-request", name="requestVerification",
             status_code=202)
def request_verification(datasetId: str, subject: Subject = Depends(current_subject),
                         db: Session = Depends(scoped_db)) -> dict:
    """올린 사람·소유자가 상세 헤더에서 직접 누른다 (§1.2 §7.1 · 계약 산문).

    **자동으로 검토 대기에 들어가지 않는다.** 그래서 이 op 이 있다.
    """
    dataset_id = _living_dataset(db, datasetId)
    core = d3_catalog.find_dataset_core(db, dataset_id)
    account = str(subject.account_id)
    if account not in (core.owner_id, core.uploader_id):
        raise errors.forbidden("올린 사람·소유자만 승인을 요청한다 (Policy_승인_처리 §1.2).")
    access = d2_access.DatasetAccessAdapter(db).dataset_access([dataset_id]).get(datasetId)
    if access is not None and not access.body_accessible:
        raise errors.forbidden("잠긴 데이터이고 허용 목록 밖이다.")
    if d2_access.verified_state(db, dataset_id):
        raise errors.conflict("이미 승인된 데이터예요.")
    if d2_access.pending_verification_of(db, dataset_id) is not None:
        raise errors.conflict("이미 검토 대기 중이에요.")

    row = d2_access.create_verification_request(
        db, dataset_id=dataset_id, requester_id=subject.account_id)
    return {
        "dataset": _dataset_ref(db, row["dataset_id"]),
        "requester": _account(db, row["requester_account_id"]),
        "requestedAt": _iso(row["requested_at"]),
    }


@router.get("/verification-requests/pending", name="listPendingVerificationRequests")
def list_pending_verification_requests(subject: Subject = Depends(current_subject),
                                       db: Session = Depends(scoped_db),
                                       cursor: str | None = Query(default=None)) -> dict:
    """**교수만.** `승인 위임` 으로 위임되지 않는다 (P-5·P-22 · 계약 산문).

    항목은 링크만 갖는다 — **할 일 함에서 바로 승인하지 않는다** (§1.3-2). 그래서 이
    응답에는 승인 토큰도 처리 자리도 없고, 화면은 상세로 보내기만 한다.
    """
    if not d2_access.can_decide_verification(db, subject.account_id):
        raise errors.forbidden("Verified 는 교수만 처리한다 (Policy_승인_처리 §1.2).")
    rows = d2_access.pending_verification_requests(db)
    page, total, next_cursor = _page(rows, cursor)
    return {
        "items": [{
            "dataset": _dataset_ref(db, r["dataset_id"]),
            "requester": _account(db, r["requester_account_id"]),
            "requestedAt": _iso(r["requested_at"]),
        } for r in page],
        "totalCount": total,
        "nextCursor": next_cursor,
    }


def _verification_record(db: Session, dataset_id: Ulid) -> dict:
    record = d2_access.DatasetAccessAdapter(db).verification([dataset_id]).get(str(dataset_id))
    if record is None:
        raise errors.not_found()
    return {
        "verified": record.verified,
        "approver": _account_ref(record.approver_id, record.approver_name),
        "approvedAt": _iso(record.approved_at),
        "cancelledBy": _account_ref(record.cancelled_by_id, record.cancelled_by_name),
        "cancelledAt": _iso(record.cancelled_at),
        "cancellationReason": record.cancellation_reason,
    }


@router.post("/datasets/{datasetId}/verification", name="approveVerification")
def approve_verification(datasetId: str, subject: Subject = Depends(current_subject),
                         db: Session = Depends(scoped_db)) -> dict:
    """승인 — **교수 전용이고 위임되지 않는다** (P-5·P-22). 데이터 한 건씩만.

    404 → 403 → 409 순서다. 경계 밖을 권한보다 먼저 보는 이유는 위 `_decidable_request` 와 같다.
    """
    dataset_id = _living_dataset(db, datasetId)
    if not d2_access.can_decide_verification(db, subject.account_id):
        raise errors.forbidden("Verified 는 교수만 처리한다 (Policy_승인_처리 §1.2).")
    if d2_access.verified_state(db, dataset_id):
        raise errors.conflict("이미 승인된 데이터예요.")
    d2_access.approve_verification(db, dataset_id=dataset_id, approver_id=subject.account_id)
    # **승인이 최근 활동을 만든다** (계약 `listActivities` 산문 · WU-P7).
    # 취소는 적지 않는다 — 계약 산문이 든 다섯에 없고, 없는 값을 여기서 발명하지 않는다.
    d8_insight.record_activity(db, actor_id=subject.account_id,
                               action=d8_insight.ACTION_VERIFIED_APPROVED,
                               target_kind="데이터셋", target_id=dataset_id)
    return _verification_record(db, dataset_id)


@router.post("/datasets/{datasetId}/verification-cancellation", name="cancelVerification")
def cancel_verification(datasetId: str, body: dict | None = Body(default=None),
                        subject: Subject = Depends(current_subject),
                        db: Session = Depends(scoped_db)) -> dict:
    """취소 — **막지 않는다** (P-28 · §7.1). 파급 안내는 화면이 먼저 보여준다.

    데이터와 계보는 남고 **배지만 사라진다** (§1.3-9). 그래서 이 op 은 `d2_verified` 한 줄만
    만지고 다른 표를 하나도 건드리지 않는다 — 파생 데이터에는 표시하지 않는다는 조항이
    「아무것도 안 쓴다」로 지켜진다.
    """
    dataset_id = _living_dataset(db, datasetId)
    if not d2_access.can_decide_verification(db, subject.account_id):
        raise errors.forbidden("Verified 는 교수만 처리한다 (Policy_승인_처리 §1.2).")
    reason = _optional_reason(body, limit=_CANCEL_REASON_MAX)
    if not d2_access.cancel_verification(db, dataset_id=dataset_id,
                                         actor_id=subject.account_id, reason=reason):
        raise errors.conflict("승인된 데이터가 아니에요.")
    return _verification_record(db, dataset_id)
