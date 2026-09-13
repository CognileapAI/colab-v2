"""Source-backed facts must remain current, authorized and reproducible."""
from test_search_changes import sources, scoped  # noqa: F401


def facts():
    from colab_core.domains import d3_search_facts
    return d3_search_facts


def test_source_snapshot_storage_exists(sql):
    assert sql("SELECT to_regclass('d3_search_fact_snapshot') AS name")[0]['name'], '출처/버전별 사실 저장소가 없다'


def test_materialize_metadata_with_provenance(sources, session_factory):
    from colab_core.domains import d3_search_changes
    api = facts()
    with scoped(session_factory) as s:
        pending = d3_search_changes.claim(s)
    with scoped(session_factory) as s:
        for item in pending:
            assert api.process(s, item) == 'ready'
        result = api.read_current(s, sources[0])
        assert {r['source_kind'] for r in result} == {'metadata', 'file'}
        assert all(r['source_sha256'] and r['extractor_version'] and r['facts'] for r in result)
        assert all(r['ontology_snapshot_id'] is None for r in result)
        meta = next(r for r in result if r['source_kind'] == 'metadata')
        assert any(f['predicate'] == 'name' and f['value'] == '등록 시험 데이터셋' for f in meta['facts'])
        assert all(f['source_locator'] for r in result for f in r['facts'])

import hashlib
import pytest
from sqlalchemy import text
from conftest import LAB_A, LAB_B, ACC_A_RES, ACC_A_PROF, ACC_B_PROF
from colab_core.domains import d3_search_changes as changes


def claim_all(factory):
    with scoped(factory) as s:
        return changes.claim(s)


def materialize(factory):
    for item in claim_all(factory):
        with scoped(factory) as s:
            facts().process(s, item)


def evidence(sql, dataset, file, status='reviewed'):
    sql("""INSERT INTO d3_search_evidence(lab_id,dataset_id,file_id,file_revision,revision,status,
      facts,source_label,source_locator,source_text,source_sha256,reviewed_by,reviewed_at)
      VALUES (:lab,:dataset,:file,1,1,:status,'{"roles":["validation"]}',
      'readme','readme:1','validation',:hash,
      CASE WHEN :status='reviewed' THEN CAST(:account AS ulid) ELSE NULL END,
      CASE WHEN :status='reviewed' THEN now() ELSE NULL END)""",
      {'lab':LAB_A,'dataset':dataset,'file':file,'status':status,'account':ACC_A_RES,
       'hash':hashlib.sha256(b'validation').hexdigest()})


@pytest.mark.parametrize('status,expected', [('draft','candidate'),('reviewed','ready')])
def test_evidence_status_and_file_replacement(sources, sql, session_factory, status, expected):
    evidence(sql,*sources,status)
    for item in claim_all(session_factory):
        with scoped(session_factory) as s:
            result=facts().process(s,item)
            if item.source_kind=='evidence':
                assert result==expected
    with scoped(session_factory) as s:
        results=facts().read_current(s,sources[0])
        assert any(r['source_kind']=='evidence' for r in results)==(expected=='ready')
    sql("UPDATE d3_file SET storage_key='new-key' WHERE id=:id",{'id':sources[1]})
    with scoped(session_factory) as s:
        assert not any(r['source_kind'] in ('file','evidence') for r in facts().read_current(s,sources[0]))
    materialize(session_factory)
    with scoped(session_factory) as s:
        assert not any(r['source_kind']=='evidence' for r in facts().read_current(s,sources[0]))


def test_later_change_rejects_old_result_without_ack(sources, sql, session_factory):
    items=claim_all(session_factory)
    item=next(i for i in items if i.source_kind=='metadata')
    sql("UPDATE d3_dataset_description SET summary='changed after claim' WHERE dataset_id=:id",{'id':sources[0]})
    with scoped(session_factory) as s:
        assert facts().process(s,item)=='stale'
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot')).scalar_one()==0
    assert sql("SELECT processed_version FROM d3_search_change WHERE source_kind='metadata' AND source_id=:id",{'id':sources[0]})[0]['processed_version']==0


def test_expired_worker_cannot_write_results(sources, sql, session_factory):
    item=claim_all(session_factory)[0]
    sql("UPDATE d3_search_change SET lease_until=clock_timestamp()-interval '1 second'")
    replacement=claim_all(session_factory)
    with scoped(session_factory) as s:
        assert facts().process(s,item)=='stale'
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot')).scalar_one()==0
        assert all(facts().process(s,new)=='ready' for new in replacement)


def test_result_and_ack_rollback_together(sources, session_factory, monkeypatch):
    item=claim_all(session_factory)[0]
    api=facts()
    with scoped(session_factory) as s:
        with monkeypatch.context() as patch:
            patch.setattr(changes,'ack',lambda *args:False)
            with pytest.raises(api.CommitRejected):
                api.process(s,item)
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot')).scalar_one()==0
        assert api.process(s,item)=='ready'
        assert api.process(s,item)=='stale'
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot')).scalar_one()==1


def test_snapshot_write_failure_does_not_ack(sources, session_factory):
    item=claim_all(session_factory)[0]
    with pytest.raises(RuntimeError), scoped(session_factory) as s:
        assert facts().process(s,item)=='ready'
        raise RuntimeError('abort original transaction')
    with scoped(session_factory) as s:
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot')).scalar_one()==0
        assert facts().process(s,item)=='ready'


def test_delete_and_permission_revocation_hide_raw_facts(sources, sql, session_factory):
    materialize(session_factory)
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':sources[0],'lab':LAB_A})
    with scoped(session_factory,account=ACC_A_PROF) as s:
        assert s.execute(text("SELECT count(*) FROM d3_search_fact_snapshot WHERE source_kind='file'")).scalar_one()==0
        assert not any(r['source_kind']=='file' for r in facts().read_current(s,sources[0]))
    sql('DELETE FROM d3_file WHERE id=:id',{'id':sources[1]})
    materialize(session_factory)
    sql('UPDATE d3_dataset SET deleted_at=now(),deleted_by_account_id=:account WHERE id=:id',{'account':ACC_A_RES,'id':sources[0]})
    with scoped(session_factory) as s:
        assert facts().read_current(s,sources[0])==[]
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot')).scalar_one()==0
    materialize(session_factory)


def test_unavailable_private_source_is_not_treated_as_deleted(sources, sql, session_factory):
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':sources[0],'lab':LAB_A})
    with scoped(session_factory,account=ACC_A_PROF) as s:
        item=next(i for i in changes.claim(s) if i.source_kind=='file')
        assert facts().process(s,item)=='source_unavailable'
    row=sql("SELECT processed_version,deleted,last_error_code FROM d3_search_change WHERE source_kind='file' AND source_id=:id",{'id':sources[1]})[0]
    assert row=={'processed_version':0,'deleted':False,'last_error_code':'source_unavailable'}


def test_other_lab_cannot_read_or_process(sources, session_factory):
    from sqlalchemy.exc import DBAPIError
    from colab_core.kernel.ids import Ulid
    items=claim_all(session_factory)
    with scoped(session_factory) as s:
        assert all(facts().process(s,i)=='ready' for i in items)
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot')).scalar_one()==2
    with scoped(session_factory,LAB_B,ACC_B_PROF) as s:
        assert all(facts().process(s,i)=='stale' for i in items)
        assert facts().read_current(s,sources[0])==[]
        assert s.execute(text('SELECT count(*) FROM d3_search_fact_snapshot WHERE lab_id=:lab'),{'lab':LAB_A}).scalar_one()==0
    item=next(i for i in items if i.source_kind=='metadata')
    with pytest.raises(DBAPIError) as denied, scoped(session_factory,LAB_B,ACC_B_PROF) as s:
        s.execute(text("""INSERT INTO d3_search_fact_snapshot
            (id,lab_id,dataset_id,source_kind,source_id,source_version,source_sha256,extractor_version,status,facts)
            VALUES (:id,:lab,:dataset,'metadata',:dataset,:version,repeat('a',64),'forged','ready','[]')"""),
            {'id':str(Ulid.generate()),'lab':LAB_A,'dataset':sources[0],'version':item.claimed_version})
    assert denied.value.orig.sqlstate=='42501'


def test_source_writer_and_fact_writer_do_not_invert_locks(sources, session_factory):
    items=claim_all(session_factory)
    item=next(i for i in items if i.source_kind=='file')
    with scoped(session_factory) as writer:
        writer.execute(text("UPDATE d3_file SET file_name='concurrent.nc' WHERE id=:id"),{'id':sources[1]})
        with scoped(session_factory) as worker:
            worker.execute(text("SET LOCAL lock_timeout='1s'"))
            assert facts().process(worker,item)=='ready'
    with scoped(session_factory) as s:
        assert facts().read_current(s,sources[0])==[]


def test_extractor_revision_requeues_only_completed_old_work(sources, session_factory):
    materialize(session_factory)
    with scoped(session_factory) as s:
        assert facts().reconcile(s,extractor_version='structured-v1')==[]
        assert len(facts().reconcile(s,extractor_version='structured-v2',limit=1))==1
        assert len(facts().reconcile(s,extractor_version='structured-v2',limit=1))==1
        assert facts().reconcile(s,extractor_version='structured-v2')==[]
    for item in claim_all(session_factory):
        with scoped(session_factory) as s:
            assert facts().process(s,item,extractor_version='structured-v2')=='ready'
    with scoped(session_factory) as s:
        assert facts().reconcile(s,extractor_version='structured-v2')==[]
        result=facts().read_current(s,sources[0],extractor_version='structured-v2')
        assert len(result)==2
        assert all(r['extractor_version']=='structured-v2' for r in result)


def test_deleted_parent_completes_child_work_without_endless_retry(sources, sql, session_factory):
    evidence(sql,*sources)
    sql('UPDATE d3_dataset SET deleted_at=now(),deleted_by_account_id=:account WHERE id=:id',
        {'id':sources[0],'account':ACC_A_RES})
    items=claim_all(session_factory)
    assert {i.source_kind for i in items}=={'metadata','file','evidence'}
    with scoped(session_factory) as s:
        assert [facts().process(s,i) for i in items]==['deleted']*3
        assert changes.claim(s)==[]


def test_cleanup_tracks_new_ids_even_when_record_times_precede_marker(p2_client, sql, session_factory, request):
    """Dataset counts must not depend on timestamps used by the cleanup fixture."""
    from conftest import _rollback_p2_rows
    from test_dataset_registration import make_upload, register
    cleanup = _rollback_p2_rows.__wrapped__(request, session_factory)
    next(cleanup)
    client=p2_client()
    response=register(client,make_upload(client))
    assert response.status_code==201,response.text
    dataset=response.json()['datasetId']
    # Controlled reproduction of the timestamp-based cleanup blind spot.
    for table,column,key in [('d3_file','created_at','dataset_id'),
                              ('d3_dataset_description','updated_at','dataset_id'),
                              ('d3_dataset_autometa','updated_at','dataset_id'),
                              ('d3_dataset','uploaded_at','id')]:
        sql(f"UPDATE {table} SET {column}=clock_timestamp()-interval '1 day' WHERE {key}=:id",{'id':dataset})
    next(cleanup,None)
    assert sql('SELECT id FROM d3_dataset WHERE id=:id',{'id':dataset})==[]
