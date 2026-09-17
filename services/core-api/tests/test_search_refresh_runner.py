import pytest
from sqlalchemy import text
from test_search_changes import sources, scoped
from test_search_refresh_tools import make_tools
from test_ontology_lookup import fixture


def tools(factory):
    manifest,lookup=fixture()
    class Port:
        def load_manifest(self):return manifest
        def lookup(self,**kwargs):return lookup
        def propose(self,source,concepts):
            rows=source['facts']
            return {'selections':[{'concept_id':'rain','predicate':'summary','quote':'강수'}]} if any(r['predicate']=='summary' and '강수' in str(r['value']) for r in rows) else {'selections':[]}
    return make_tools(factory,Port())


def test_runner_persists_grounded_selection_and_unchanged_work_is_not_reprocessed(sources,sql,session_factory):
    from colab_core.app.search_refresh_runner import run_batch
    sql("UPDATE d3_dataset_description SET summary='강수 자료입니다' WHERE dataset_id=:id",{'id':sources[0]})
    kit=tools(session_factory)
    first=run_batch(kit,max_jobs=10)
    assert first['ready']==2 and first['failed']==0
    assert run_batch(kit,max_jobs=10)['processed']==0
    with scoped(session_factory) as s:
        rows=s.execute(text('SELECT * FROM d3_search_concept_match WHERE dataset_id=:id'),{'id':sources[0]}).mappings().all()
        assert len(rows)==1 and rows[0]['quote']=='강수' and rows[0]['concept_id']=='rain'


def test_failed_model_releases_lease_and_records_retry(sources,sql,session_factory):
    from colab_core.app.search_refresh_runner import run_batch
    kit=tools(session_factory)
    def bad(*args,**kwargs):raise ValueError('private source or token should not be logged')
    kit._port.propose=bad
    result=run_batch(kit,max_jobs=1)
    assert result['failed']==1
    rows=sql("SELECT last_error_code,lease_until FROM d3_search_change WHERE last_error_code IS NOT NULL")
    assert rows and rows[0]['last_error_code']=='processing_failed' and rows[0]['lease_until'] is None


def test_lookup_then_source_edit_cannot_commit_annotation(sources,sql,session_factory):
    kit=tools(session_factory);kit.sync_manifest()
    h=next(j['handle'] for j in kit.claim() if j['source_kind']=='metadata')
    kit.read(h);kit.lookup(h)
    sql("UPDATE d3_dataset_description SET summary='changed' WHERE dataset_id=:id",{'id':sources[0]})
    with pytest.raises(ValueError):kit.complete(h,expected_version=fixture()[0]['version'],concept_ids=['rain'],selections=[])


def test_daily_run_fences_duplicates_and_persists_retry(sources,session_factory):
    from colab_core.domains import d3_search_runs as runs
    with scoped(session_factory) as s:
        first=runs.claim_run(s)
        assert first is not None
    with scoped(session_factory) as s:
        assert runs.claim_run(s) is None
        assert not runs.finish(s,first+1,summary={'processed':0},pending=False)
        assert runs.finish(s,first,summary={'processed':0},pending=False)
    with scoped(session_factory) as s:
        assert runs.claim_run(s) is None
        assert runs.status(s)['status']=='complete'


def test_legacy_binding_is_selected_once_even_when_selection_is_empty(sources,session_factory):
    from colab_core.app.search_refresh_runner import run_batch
    kit=tools(session_factory);kit.sync_manifest()
    for job in kit.claim():
        read=kit.read(job['handle'])
        kit.complete(job['handle'],expected_version=read['ontology_version'],concept_ids=[])
    # Old receipt predates selector execution; zero selection must still be recorded once.
    assert run_batch(kit,max_jobs=10)['processed']==2
    assert run_batch(kit,max_jobs=10)['processed']==0


def test_revoked_source_is_not_sent_to_concept_lookup(sources,sql,session_factory):
    from conftest import ACC_A_OUTSIDER
    kit=tools(session_factory);kit._subject=make_tools(session_factory,account=ACC_A_OUTSIDER)._subject
    kit.sync_manifest()
    h=next(j['handle'] for j in kit.claim() if j['source_kind']=='file');kit.read(h)
    sent=[];kit._port.lookup=lambda **kw:sent.append(kw)
    sql("INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,current_lab_id(),'잠김') ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'",{'id':sources[0]})
    with pytest.raises(ValueError):kit.lookup(h)
    assert sent==[]


def test_private_file_is_not_leased_by_an_unrelated_account(sources,sql,session_factory):
    from conftest import ACC_A_OUTSIDER
    sql("INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,current_lab_id(),'잠김') ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'",{'id':sources[0]})
    other=make_tools(session_factory,account=ACC_A_OUTSIDER)
    assert all(j['source_kind']!='file' for j in other.claim())
    assert any(j['source_kind']=='file' for j in tools(session_factory).claim())


def test_bootstrap_checkpoint_and_enqueue_rollback_together(sources,session_factory):
    from colab_core.domains import d3_search_runs as runs
    with scoped(session_factory) as s:
        s.execute(text('DELETE FROM d3_search_refresh_run'))
        generation=runs.claim_run(s)
    with pytest.raises(RuntimeError),scoped(session_factory) as s:
        runs.bootstrap_page(s,generation,limit=1)
        raise RuntimeError('crash before checkpoint commit')
    with scoped(session_factory) as s:
        assert runs.status(s)['bootstrap']=={}
        s.execute(text("UPDATE d3_search_refresh_run SET lease_until=clock_timestamp()-interval '1 second'"))
    with scoped(session_factory) as s:
        replacement=runs.claim_run(s)
        assert replacement==generation+1
        with pytest.raises(ValueError):runs.bootstrap_page(s,generation)
    with scoped(session_factory) as s:s.execute(text('DELETE FROM d3_search_refresh_run'))


@pytest.fixture(autouse=True)
def isolated_run_state(session_factory,sources):
    with scoped(session_factory) as s:s.execute(text('DELETE FROM d3_search_refresh_run'))
    yield
    with scoped(session_factory) as s:s.execute(text('DELETE FROM d3_search_refresh_run'))


def test_daily_bootstrap_resumes_and_manifest_is_read_once_per_day(sources,session_factory):
    from colab_core.app.search_refresh_runner import run_due
    from colab_core.domains import d3_search_runs as runs
    kit=tools(session_factory);calls=[]
    original=kit._port.load_manifest
    kit._port.load_manifest=lambda:(calls.append(True),original())[1]
    states=[]
    for _ in range(3):
        result=run_due(kit,max_jobs=100);states.append(result['status'])
        assert result.get('failed',0)==0
        with scoped(session_factory) as s:
            state=runs.status(s)
            if state['status']!='complete':s.execute(text('UPDATE d3_search_refresh_run SET next_run=clock_timestamp()'))
    assert states==['pending','pending','complete']
    assert len(calls)==1
    assert run_due(kit)=={'status':'not_due'}


def test_future_retry_is_pending_and_not_reported_complete(sources,session_factory):
    from colab_core.domains import d3_search_runs as runs
    with scoped(session_factory) as s:
        generation=runs.claim_run(s)
        s.execute(text("UPDATE d3_search_change SET retry_after=clock_timestamp()+interval '10 minutes'"))
        assert runs.pending(s)>0
        assert runs.finish(s,generation,summary={'processed':0},pending=True)
        state=runs.status(s)
        assert state['status']=='pending'
        assert s.execute(text("SELECT next_run < clock_timestamp()+interval '2 minutes' FROM d3_search_refresh_run")).scalar_one()
