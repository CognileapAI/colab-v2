"""Incremental indexing uses transactional pointers, never a full source scan."""
from test_dataset_registration import make_upload, register


def test_registration_records_pending_sources(p2_client, sql):
    client = p2_client()
    receipt = make_upload(client)
    response = register(client, receipt)
    assert response.status_code == 201, response.text
    assert sql("SELECT to_regclass('d3_search_change') AS name")[0]["name"], \
        "등록한 원본의 변경 기록이 없다"
    rows = sql("SELECT * FROM d3_search_change WHERE dataset_id=:id",
               {"id": response.json()["datasetId"]})
    assert {r["source_kind"] for r in rows} == {"metadata", "file"}
    assert all(r["requested_version"] > r["processed_version"] == 0 for r in rows)

from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text
from conftest import LAB_A, LAB_B, ACC_A_RES, ACC_B_PROF, ACC_A_PROF, DS_A2
from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from colab_core.kernel.scope import apply_scope


@contextmanager
def scoped(factory, lab=LAB_A, account=ACC_A_RES):
    with factory() as session, session.begin():
        apply_scope(session, Subject(account_id=Ulid(account), lab_id=Ulid(lab)))
        yield session


def consumer():
    from colab_core.domains import d3_search_changes
    return d3_search_changes


@pytest.fixture
def sources(p2_client, sql):
    client = p2_client()
    receipt = make_upload(client)
    response = register(client, receipt)
    assert response.status_code == 201, response.text
    dataset = response.json()['datasetId']
    # Only this disposable DB / this lab's derived pointers, never product data.
    sql('DELETE FROM d3_search_change WHERE dataset_id <> :id', {'id': dataset})
    return dataset, receipt['files'][0]['fileId']


def rows(sql, dataset):
    return sql('SELECT * FROM d3_search_change WHERE dataset_id=:id ORDER BY source_kind', {'id': dataset})


def test_changes_coalesce_and_rollback(sources, sql, session_factory):
    dataset, _ = sources
    before = rows(sql, dataset)
    for value in ('first', 'second'):
        sql('UPDATE d3_dataset_description SET summary=:value WHERE dataset_id=:id',
            {'id': dataset, 'value': value})
    after = rows(sql, dataset)
    assert len(after) == len(before)
    assert after[-1]['requested_version'] == before[-1]['requested_version'] + 2
    with pytest.raises(RuntimeError), scoped(session_factory) as s:
        s.execute(text('UPDATE d3_dataset_description SET summary=\'rolled back\' WHERE dataset_id=:id'), {'id': dataset})
        raise RuntimeError('abort original transaction')
    assert rows(sql, dataset) == after


def test_variable_quality_and_child_delete_are_metadata_changes(sources, sql):
    dataset, _ = sources
    sql("INSERT INTO d3_dataset_variable (dataset_id,lab_id,ordinal,name) VALUES (:id,:lab,1,'rain')",
        {'id': dataset, 'lab': LAB_A})
    before = rows(sql, dataset)[-1]['requested_version']
    sql("UPDATE d3_dataset_variable SET missing_rate='20%' WHERE dataset_id=:id", {'id': dataset})
    assert rows(sql, dataset)[-1]['requested_version'] > before
    sql('DELETE FROM d3_dataset_variable WHERE dataset_id=:id', {'id': dataset})
    assert rows(sql, dataset)[-1]['deleted'] is False
    sql('UPDATE d3_dataset SET deleted_at=now(),deleted_by_account_id=:account WHERE id=:id',
        {'id': dataset, 'account': ACC_A_RES})
    sql('DELETE FROM d3_dataset_description WHERE dataset_id=:id', {'id': dataset})
    assert rows(sql, dataset)[-1]['deleted'] is True


def test_file_replacement_and_evidence_cascade_leave_tombstones(sources, sql):
    dataset, file = sources
    sql("""INSERT INTO d3_search_evidence (lab_id,dataset_id,file_id,file_revision,revision,status,
        facts,source_label,source_locator,source_text,source_sha256)
        VALUES (:lab,:dataset,:file,1,1,'draft','{"roles":["validation"]}',
        'label','locator','secret body',repeat('a',64))""", {'lab': LAB_A, 'dataset': dataset, 'file': file})
    sql("UPDATE d3_search_evidence SET revision=2,source_text='new secret' WHERE file_id=:id", {'id': file})
    assert rows(sql, dataset)[0]['requested_version'] == 2
    before = rows(sql, dataset)[1]['requested_version']
    sql("UPDATE d3_file SET storage_key='replacement' WHERE id=:id", {'id': file})
    assert rows(sql, dataset)[1]['requested_version'] > before
    sql('DELETE FROM d3_file WHERE id=:id', {'id': file})
    result = rows(sql, dataset)
    assert {r['source_kind'] for r in result if r['deleted']} == {'file', 'evidence'}
    assert 'secret' not in str(result) and 'replacement' not in str(result)


def test_claim_ack_preserves_new_change_and_finished_is_not_claimed(sources, sql, session_factory):
    api = consumer()
    with scoped(session_factory) as s:
        claimed = api.claim(s, limit=10, lease_seconds=60)
    assert len(claimed) == 2
    dataset, _ = sources
    sql("UPDATE d3_dataset_description SET summary='during processing' WHERE dataset_id=:id", {'id': dataset})
    with scoped(session_factory) as s:
        assert all(api.ack(s, item) for item in claimed)
        again = api.claim(s, limit=10, lease_seconds=60)
        assert len(again) == 1 and again[0].source_kind == 'metadata'
        assert api.ack(s, again[0])
        assert api.claim(s, limit=10, lease_seconds=60) == []


def expire(sql):
    sql("UPDATE d3_search_change SET lease_until=clock_timestamp()-interval '1 second' WHERE lease_until IS NOT NULL")


def test_expired_and_reclaimed_workers_cannot_mutate(sources, sql, session_factory):
    api = consumer()
    with scoped(session_factory) as s:
        old = api.claim(s, limit=1, lease_seconds=60)[0]
    expire(sql)
    with scoped(session_factory) as s:
        assert not api.ack(s, old)
        assert not api.fail(s, old, error_code='transient', retry_seconds=1)
        assert not api.renew(s, old, lease_seconds=60)
        current = api.claim(s, limit=10, lease_seconds=60)
        replacement = next(i for i in current if i.source_id == old.source_id)
        assert replacement.lease_generation == old.lease_generation + 1
        assert not api.ack(s, old)
        assert not api.fail(s, old, error_code='transient', retry_seconds=1)
        assert not api.renew(s, old, lease_seconds=60)
        assert api.renew(s, replacement, lease_seconds=120)
        assert api.ack(s, replacement)


def test_failure_backoff_and_latest_retry(sources, sql, session_factory):
    api = consumer()
    with scoped(session_factory) as s:
        claimed = api.claim(s, limit=10, lease_seconds=60)
        for item in claimed:
            assert api.fail(s, item, error_code='transient', retry_seconds=30)
        assert api.claim(s, limit=10, lease_seconds=60) == []
    sql("UPDATE d3_dataset_description SET summary='new while backed off' WHERE dataset_id=:id", {'id': sources[0]})
    latest = rows(sql, sources[0])[-1]['requested_version']
    sql("UPDATE d3_search_change SET retry_after=clock_timestamp()-interval '1 second'")
    with scoped(session_factory) as s:
        retried = api.claim(s, limit=10, lease_seconds=60)
        assert len(retried) == 2
        assert all(i.attempts == 2 for i in retried)
        assert next(i for i in retried if i.source_kind == 'metadata').claimed_version == latest


def test_concurrent_claim_skips_locked_rows(sources, session_factory):
    api = consumer()
    with scoped(session_factory) as first:
        a = api.claim(first, limit=1, lease_seconds=60)
        with scoped(session_factory) as second:
            second.execute(text("SET LOCAL statement_timeout='2s'"))
            b = api.claim(second, limit=10, lease_seconds=60)
            assert len(a) == len(b) == 1
            assert a[0].source_kind != b[0].source_kind


def test_concurrent_updates_do_not_lose_generations(sources, sql, session_factory):
    dataset, _ = sources
    before = rows(sql, dataset)[-1]['requested_version']
    def update(n):
        with scoped(session_factory) as s:
            s.execute(text('UPDATE d3_dataset_description SET summary=:s WHERE dataset_id=:id'),
                      {'s': str(n), 'id': dataset})
    with ThreadPoolExecutor(max_workers=2) as workers:
        list(workers.map(update, range(6)))
    assert rows(sql, dataset)[-1]['requested_version'] == before + 6


def test_other_lab_cannot_read_claim_or_finish(sources, session_factory):
    api = consumer()
    with scoped(session_factory) as s:
        item = api.claim(s, limit=1, lease_seconds=60)[0]
    with scoped(session_factory, LAB_B, ACC_B_PROF) as s:
        assert s.execute(text('SELECT count(*) FROM d3_search_change WHERE lab_id=:lab'), {'lab': LAB_A}).scalar_one() == 0
        # Lab B seeded sources may also be pending; none may point to lab A.
        assert all(i.lab_id == LAB_B for i in api.claim(s, limit=100, lease_seconds=60))
        assert not api.ack(s, item)
        assert not api.fail(s, item, error_code='transient', retry_seconds=1)
        assert not api.renew(s, item, lease_seconds=60)
    with session_factory() as s:
        assert api.claim(s, limit=10, lease_seconds=60) == []


def test_bootstrap_is_bounded_idempotent_and_preserves_progress(sources, sql, session_factory):
    api = consumer()
    with scoped(session_factory) as s:
        done = api.claim(s, limit=10, lease_seconds=60)
        for item in done:
            assert api.ack(s, item)
    before = rows(sql, sources[0])
    sql("DELETE FROM d3_search_change WHERE source_kind='file' AND source_id=:id", {'id': sources[1]})
    with scoped(session_factory) as s:
        cursor = None
        scanned = 0
        while True:
            page = api.bootstrap(s, source_kind='file', after=cursor, limit=1)
            scanned += len(page)
            if not page:
                break
            assert len(page) == 1
            cursor = page[-1]
        assert scanned > 0
        api.bootstrap(s, source_kind='metadata', limit=100)
    after = rows(sql, sources[0])
    assert after[-1] == before[-1]
    assert after[0]['processed_version'] == 0
    with scoped(session_factory) as s:
        api.bootstrap(s, source_kind='file', limit=100)
    assert rows(sql, sources[0]) == after


def test_summary_and_source_label_updates_do_not_invert_locks(sources, session_factory):
    dataset, _ = sources
    # Reproduce update_dataset's description -> touch order while a source-label
    # edit holds the dataset row. Source-label must commit before the final touch.
    with scoped(session_factory) as a:
        a.execute(text("UPDATE d3_dataset_description SET summary='parallel summary' WHERE dataset_id=:id"), {'id': dataset})
        with scoped(session_factory) as b:
            b.execute(text("SET LOCAL lock_timeout='1s'"))
            b.execute(text("UPDATE d3_dataset SET source_label='parallel source' WHERE id=:id"), {'id': dataset})
        a.execute(text('UPDATE d3_dataset SET last_modified_at=clock_timestamp() WHERE id=:id'), {'id': dataset})


@pytest.mark.parametrize('operation', ['ack', 'fail', 'renew'])
def test_expiry_while_waiting_for_row_lock_rejects_worker(sources, session_factory, operation):
    import time
    api = consumer()
    with scoped(session_factory) as s:
        item = api.claim(s, limit=1, lease_seconds=2)[0]
    def finish():
        with scoped(session_factory) as s:
            s.execute(text("SET LOCAL application_name='search-lease-wait-test'"))
            if operation == 'fail':
                return api.fail(s, item, error_code='transient')
            return getattr(api, operation)(s, item)
    with ThreadPoolExecutor(max_workers=1) as worker:
        with scoped(session_factory) as holder:
            holder.execute(text('SELECT 1 FROM d3_search_change WHERE source_kind=:kind AND source_id=:id FOR UPDATE'),
                           {'kind': item.source_kind, 'id': item.source_id})
            future = worker.submit(finish)
            deadline = time.monotonic() + 1.5
            while not holder.execute(text("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='search-lease-wait-test' AND wait_event_type='Lock')")).scalar_one():
                assert time.monotonic() < deadline, 'worker did not wait for the row lock'
                time.sleep(.01)
                holder.execute(text('SELECT pg_stat_clear_snapshot()'))
            holder.execute(text('SELECT pg_sleep(2.1)'))
        assert future.result(timeout=5) is False


def test_bootstrap_evidence_obeys_private_body_scope(sources, sql, session_factory):
    api = consumer()
    private_file = '00000000000000000000000FA3'
    sql("""INSERT INTO d3_search_evidence (lab_id,dataset_id,file_id,file_revision,revision,status,
        facts,source_label,source_locator,source_text,source_sha256)
        VALUES (:lab,:dataset,:file,1,1,'draft','{"roles":["validation"]}',
        'private','private','private content',repeat('b',64))""",
        {'lab': LAB_A, 'dataset': DS_A2, 'file': private_file}, account_id=ACC_A_PROF)
    sql("DELETE FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id", {'id': private_file})
    with scoped(session_factory) as s:
        assert private_file not in api.bootstrap(s, source_kind='file')
        assert private_file not in api.bootstrap(s, source_kind='evidence')
    assert sql("SELECT * FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id", {'id': private_file}) == []
    with scoped(session_factory, account=ACC_A_PROF) as s:
        assert private_file in api.bootstrap(s, source_kind='evidence')
    assert sql("SELECT requested_version FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id", {'id': private_file}) == [{'requested_version': 1}]


@pytest.mark.parametrize('arguments', [
    {'limit': 0}, {'limit': 1001}, {'limit': True}, {'lease_seconds': 0}, {'lease_seconds': 3601},
])
def test_invalid_claim_limits_are_rejected(session_factory, arguments):
    with scoped(session_factory) as s, pytest.raises(ValueError):
        consumer().claim(s, **arguments)


def test_ledger_rejects_cross_lab_insert(sources, session_factory):
    from sqlalchemy.exc import DBAPIError
    with pytest.raises(DBAPIError), scoped(session_factory) as s:
        s.execute(text("INSERT INTO d3_search_change(lab_id,source_kind,source_id,dataset_id) VALUES (:lab,'metadata',:id,:id)"),
                  {'lab': LAB_B, 'id': sources[0]})
