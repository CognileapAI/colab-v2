"""Worker must retain source ownership until core coordinates source reclamation."""
import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from colab_pipeline.domains.d5_ingestion import SqlLedger
from colab_pipeline.kernel.db import apply_scope, make_engine, make_session_factory
from colab_pipeline.kernel.ids import new_ulid

pytestmark = pytest.mark.dbint


def test_worker_does_not_delete_expired_source_ledger():
    url = os.environ.get("COLAB_PIPELINE_DB_URL")
    assert url, "Real DB URL required"
    engine = make_engine(url)
    session = make_session_factory(engine)()
    try:
        session.begin()
        apply_scope(session, lab_id="0000000000000000000000000A", account_id="000000000000000000000000A1")
        uid = new_ulid()
        session.execute(text("""INSERT INTO d5_upload(id,lab_id,uploader_account_id,expires_at,ready)
            VALUES (:u,current_lab_id(),current_account_id(),now()+interval '1 hour',true)"""), {"u":uid})
        assert SqlLedger(session).expire(datetime.now(timezone.utc)+timedelta(days=2)) == []
        assert session.execute(text("SELECT count(*) FROM d5_upload WHERE id=:u"), {"u":uid}).scalar_one() == 1
    finally:
        session.rollback()
        session.close()
        engine.dispose()


def test_worker_reaper_is_observation_only_for_memory_ledgers():
    from colab_pipeline.domains.d5_ingestion import reap_expired_uploads
    from memory_ledger import MemoryLedger

    ledger = MemoryLedger()
    uid = new_ulid()
    ledger.accept(upload_id=uid, lab_id="0000000000000000000000000A",
                  actor_account_id="000000000000000000000000A1", ttl_hours=1)
    assert reap_expired_uploads(
        ledger, now=datetime.now(timezone.utc)+timedelta(days=2)) == []
    assert uid in ledger.uploads
