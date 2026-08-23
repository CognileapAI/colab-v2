"""`〈67〉` 이행 제약 ㉠·㉡ — reaper 는 **처리 중 상태를 건너뛴다**.

「시계가 처리를 앞지르지 않는다」가 정본 규칙 ②다. 이 조건이 없으면 음성 시험
㉳(만료된 업로드는 전환되지 않는다·404)가 **정상 동작에 대고 404 를 내면서 green** 을
보고한다 — 이 프로젝트가 반복해 온 「에러 없이 그럴듯한 값」의 정확한 재발이다.

㉠ 은 **두 서비스 모두**에 걸린 요구다. `core-api` 는 이미 이행했고
(`test_uploads.py::test_an_upload_still_being_processed_survives_its_expiry_time`),
이 파일이 `pipeline-worker` 쪽 같은 요구를 세운다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from colab_pipeline.domains.d5_ingestion import reap_expired_uploads
from memory_ledger import MemoryLedger

_LAB = "0000000000000000000000000A"
_ACC = "000000000000000000000000A1"
_UPL = "01JQ00000000000000000UPL01"


def _event(ledger: MemoryLedger, event_type: str, *, at: datetime) -> None:
    ledger.append_event({
        "eventId": "01JQ" + event_type[:22].ljust(22, "0"), "type": event_type,
        "schemaVersion": "1.0", "source": "pipeline-worker",
        "occurredAt": at.isoformat().replace("+00:00", "Z"),
        "labId": _LAB, "actorAccountId": _ACC, "uploadId": _UPL,
        "idempotencyKey": f"{event_type}:{_UPL}",
        "delivery": {"attempt": 1, "maxAttempts": 5,
                     "firstPublishedAt": at.isoformat().replace("+00:00", "Z"),
                     "publishedAt": at.isoformat().replace("+00:00", "Z"),
                     "redelivery": False, "deadLettered": False},
        "payload": {},
    })


def test_an_upload_still_being_processed_survives_its_expiry_time():
    """**처리 중인 업로드는 만료 시각을 지나고도 살아남는다** (`〈67〉` ㉡)."""
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, ttl_hours=1)
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    # 만료 직전까지 단계 이벤트가 계속 들어온다 = 처리가 진행 중이다.
    _event(ledger, "file.header-parsed", at=later - timedelta(minutes=5))

    gone = reap_expired_uploads(ledger, now=later)
    assert _UPL not in gone
    assert _UPL in ledger.uploads


def test_an_idle_expired_upload_is_still_reaped():
    """처리 제외가 만료를 통째로 죽이면 안 된다 — 접수만 된 것은 제때 사라진다."""
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, ttl_hours=1)
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    assert _UPL in reap_expired_uploads(ledger, now=later)
    assert _UPL not in ledger.uploads


def test_a_failed_upload_is_not_processing_and_is_reaped():
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, ttl_hours=1)
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    _event(ledger, "upload.failed", at=later - timedelta(minutes=5))
    ledger.record_status(_UPL, failed_at=later - timedelta(minutes=5))
    assert _UPL in reap_expired_uploads(ledger, now=later)


def test_a_ready_upload_is_not_processing_and_is_reaped():
    """`ready` 는 처리가 끝난 것이다 — 등록하지 않은 채 만료되면 지운다(`〈64〉-ⓒ`)."""
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, ttl_hours=1)
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    _event(ledger, "upload.ready", at=later - timedelta(minutes=5))
    ledger.record_status(_UPL, ready=True)
    assert _UPL in reap_expired_uploads(ledger, now=later)
