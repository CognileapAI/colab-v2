"""데이터 오류 분류·재전달 계수를 **실물 원장**에서 확인한다 (코드리뷰 20260903 #4·부록).

단위 시험은 `MemoryLedger` 대역으로 돈다. 여기서 보는 것은 대역이 흉내낼 수 없는 둘이다 —

  ⓐ `record_data_failure` 가 적은 `failed_at` 이 **`pending_uploads` 의 조건에 실제로
     걸리는가.** 크래시 루프의 정체는 「롤백으로 `ready=false` 가 남아 같은 건이 다시
     먼저 온다」였고, 그것을 끊는 것은 대역이 아니라 **이 SQL** 이다.
  ⓑ `record_delivery_failure` 의 `attempt = attempt + 1` 이 `CHECK (attempt >= 1)` 아래에서
     서고, 다음 `unpublished()` 봉투가 `redelivery: true` 로 나오는가.

DB URL 은 `COLAB_PIPELINE_DB_URL` 로 받는다. **미지정이면 skip 이 아니라 fail** 이다.
"""
from __future__ import annotations

import os

import pytest
from colab_pipeline.d5.axis import AxisUndeterminedError
from colab_pipeline.domains.d5_ingestion import (
    IngestionService,
    SqlLedger,
    UploadWork,
    relay_unpublished,
)

pytestmark = pytest.mark.dbint

_ENV = "COLAB_PIPELINE_DB_URL"
# 시드(`services/core-api/tests/fixtures/seed.sql`)의 A 연구실·계정 — `d5_*` 의 FK 가 요구한다.
_LAB = "0000000000000000000000000A"
_ACC = "000000000000000000000000A1"


@pytest.fixture()
def session():
    url = os.environ.get(_ENV)
    if not url:
        pytest.fail(f"{_ENV} 가 없다 — DB 시험을 DB 없이 green 으로 세지 않는다 (CLAUDE.md §4).")
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker

    from colab_pipeline.kernel.db import make_engine

    engine = make_engine(url)
    s = sessionmaker(bind=engine, future=True)()
    s.begin()
    s.execute(text("SELECT set_config('app.current_lab', :v, true)"), {"v": _LAB})
    s.execute(text("SELECT set_config('app.current_account', :v, true)"), {"v": _ACC})
    try:
        yield s
    finally:
        s.rollback()
        s.close()
        engine.dispose()


def _ulid(tail: str) -> str:
    return ("01JQ" + "0" * 22)[: 26 - len(tail)] + tail


def _accept(session, upload_id: str) -> None:
    from sqlalchemy import text
    session.execute(text("""
        INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at)
        VALUES (:id, :lab, :acc, now() + interval '24 hours')
    """), {"id": upload_id, "lab": _LAB, "acc": _ACC})
    session.execute(text("""
        INSERT INTO d5_pipeline_event
          (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
           idempotency_key, payload)
        VALUES (:eid, :lab, :acc, :uid, 'upload.accepted', '1.0', 'core-api',
                :key, '{"files": []}'::jsonb)
    """), {"eid": _ulid(upload_id[-4:] + "A"), "lab": _LAB, "acc": _ACC, "uid": upload_id,
           "key": f"upload.accepted:{upload_id}"})


def _work(upload_id: str, tmp_path) -> UploadWork:
    return UploadWork(upload_id=upload_id, lab_id=_LAB, actor_account_id=_ACC,
                      workdir=tmp_path / "w", files=[])


def test_데이터_오류를_적으면_같은_업로드를_다시_집지_않는다(session, tmp_path):
    upload_id = _ulid("D001")
    _accept(session, upload_id)
    ledger = SqlLedger(session)
    assert upload_id in [r["id"] for r in ledger.pending_uploads()]

    IngestionService(ledger).record_data_failure(
        _work(upload_id, tmp_path), AxisUndeterminedError("2차원이 아니다: shape=(2881,)"))

    assert upload_id not in [r["id"] for r in ledger.pending_uploads()], (
        "실패를 적었는데 대기 집합에 남아 있다 — 크래시 루프가 그대로다")


def test_실패_사유가_계약의_어휘로_원장에_남는다(session, tmp_path):
    from sqlalchemy import text
    upload_id = _ulid("D002")
    _accept(session, upload_id)
    IngestionService(SqlLedger(session)).record_data_failure(
        _work(upload_id, tmp_path), ValueError("배열 형상이 이상하다"))

    row = session.execute(text(
        "SELECT ready, failed_at, failure_class, failure_reason FROM d5_upload WHERE id = :u"
    ), {"u": upload_id}).one()
    assert row[0] is False and row[1] is not None
    assert (row[2], row[3]) == ("영구", "내부 오류")

    payload = session.execute(text(
        "SELECT payload FROM d5_pipeline_event "
        " WHERE upload_id = :u AND event_type = 'upload.failed'"
    ), {"u": upload_id}).scalar_one()
    assert payload["failure"]["reason"] == "내부 오류"
    assert payload["failure"]["detail"].startswith("ValueError:")


def test_실패_봉투가_계약을_만족한다(session, tmp_path, event_validator):
    """봉투는 계약 파일이 오라클이다 — 새 발행 경로가 계약 밖으로 나가지 않는다."""
    upload_id = _ulid("D003")
    _accept(session, upload_id)
    ledger = SqlLedger(session)
    IngestionService(ledger).record_data_failure(
        _work(upload_id, tmp_path), AxisUndeterminedError("깨진 격자"))

    sent: list[dict] = []
    relay_unpublished(ledger, publish=sent.append)
    failed = [e for e in sent if e["type"] == "upload.failed" and e["uploadId"] == upload_id]
    assert len(failed) == 1
    assert event_validator(failed[0]) == []


def test_발행_실패가_전달_횟수를_올리고_재전달로_나간다(session, tmp_path):
    from sqlalchemy import text
    upload_id = _ulid("D004")
    _accept(session, upload_id)
    ledger = SqlLedger(session)
    IngestionService(ledger).record_data_failure(
        _work(upload_id, tmp_path), AxisUndeterminedError("깨진 격자"))

    def _fail_once(env):
        raise RuntimeError("브로커에 닿지 못했다")

    assert relay_unpublished(ledger, publish=_fail_once) == 0

    attempt = session.execute(text(
        "SELECT attempt FROM d5_pipeline_event "
        " WHERE upload_id = :u AND event_type = 'upload.failed'"
    ), {"u": upload_id}).scalar_one()
    assert attempt == 2, "전달 횟수가 오르지 않았다 — 재전달이 첫 전달의 얼굴로 나간다"

    sent: list[dict] = []
    relay_unpublished(ledger, publish=sent.append)
    env = next(e for e in sent if e["uploadId"] == upload_id
               and e["type"] == "upload.failed")
    assert env["delivery"]["attempt"] == 2
    assert env["delivery"]["redelivery"] is True


def test_못_보낸_이벤트는_발행_시각을_안_찍는다(session, tmp_path):
    """at-least-once — 못 보낸 것을 보냈다고 적으면 조용히 유실된다."""
    from sqlalchemy import text
    upload_id = _ulid("D005")
    _accept(session, upload_id)
    ledger = SqlLedger(session)
    IngestionService(ledger).record_data_failure(
        _work(upload_id, tmp_path), AxisUndeterminedError("깨진 격자"))

    def _always_fail(env):
        raise RuntimeError("브로커가 없다")

    relay_unpublished(ledger, publish=_always_fail)
    pub = session.execute(text(
        "SELECT published_at FROM d5_pipeline_event "
        " WHERE upload_id = :u AND event_type = 'upload.failed'"
    ), {"u": upload_id}).scalar_one()
    assert pub is None
