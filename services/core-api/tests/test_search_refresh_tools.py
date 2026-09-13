import pytest
from sqlalchemy import text
from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from conftest import LAB_A, ACC_A_RES
from test_search_changes import sources, scoped
from test_search_ontology import manifest


def make_tools(factory,port=None,account=ACC_A_RES):
    from colab_core.app.search_refresh_tools import SearchRefreshTools
    class Port:
        def load_manifest(self): return manifest()
    return SearchRefreshTools(factory,Subject(account_id=Ulid(account),lab_id=Ulid(LAB_A)),port or Port())


@pytest.fixture
def kit(sources,session_factory):
    with scoped(session_factory) as s:s.execute(text('DELETE FROM d3_search_ontology_head'))
    tools=make_tools(session_factory)
    tools.sync_manifest()
    return tools


def test_handle_requires_read_and_commits_fact_binding_together(kit,session_factory):
    h=kit.claim(limit=1)[0]['handle']; version=manifest()['version']
    with pytest.raises(ValueError):kit.complete(h,expected_version=version,concept_ids=[])
    data=kit.read(h)
    assert data['ontology_version']==version
    result=kit.complete(h,expected_version=version,concept_ids=[])
    assert result['status']=='ready'
    with pytest.raises(ValueError):kit.read(h)
    with scoped(session_factory) as s:
        assert s.execute(text('SELECT count(*) FROM d3_search_ontology_binding')).scalar_one()==1


def test_source_change_after_read_rejects_entire_completion(kit,sources,sql):
    jobs=kit.claim()
    h=next(j['handle'] for j in jobs if j['source_kind']=='metadata')
    kit.read(h)
    sql("UPDATE d3_dataset_description SET summary='new text' WHERE dataset_id=:id",{'id':sources[0]})
    with pytest.raises(ValueError):kit.complete(h,expected_version=manifest()['version'],concept_ids=[])
    assert sql('SELECT count(*) AS n FROM d3_search_fact_snapshot')[0]['n']==0


def test_binding_failure_rolls_back_fact_and_ack(kit,sql,monkeypatch):
    from colab_core.domains import d3_search_ontology
    h=kit.claim(limit=1)[0]['handle'];kit.read(h)
    original=d3_search_ontology.bind
    def fail(*args,**kwargs):raise ValueError('reject binding')
    monkeypatch.setattr(d3_search_ontology,'bind',fail)
    with pytest.raises(ValueError):kit.complete(h,expected_version=manifest()['version'],concept_ids=[])
    assert sql('SELECT count(*) AS n FROM d3_search_fact_snapshot')[0]['n']==0
    assert all(r['processed_version']==0 for r in sql('SELECT processed_version FROM d3_search_change'))
    monkeypatch.setattr(d3_search_ontology,'bind',original)
    assert kit.complete(h,expected_version=manifest()['version'],concept_ids=[])['status']=='ready'


def test_handles_do_not_cross_tool_instances(kit,session_factory):
    h=kit.claim(limit=1)[0]['handle']
    with pytest.raises(ValueError):make_tools(session_factory).read(h)


def test_head_change_and_expired_lease_reject_completion(kit,sql,session_factory):
    from colab_core.domains import d3_search_ontology as ontology
    h=kit.claim(limit=1)[0]['handle'];kit.read(h)
    with scoped(session_factory) as s:
        ontology.publish(s,manifest(discovery='d'*64),expected_previous=manifest()['version'])
    with pytest.raises(ValueError):kit.complete(h,expected_version=manifest()['version'],concept_ids=[])
    kit.read(h)
    sql("UPDATE d3_search_change SET lease_until=clock_timestamp()-interval '1 second' WHERE lease_until IS NOT NULL")
    with pytest.raises(ValueError):kit.complete(h,expected_version=manifest(discovery='d'*64)['version'],concept_ids=[])
    assert sql('SELECT count(*) AS n FROM d3_search_fact_snapshot')[0]['n']==0


def test_late_manifest_response_cannot_revert_new_head(kit,session_factory):
    from colab_core.domains import d3_search_ontology as ontology
    newer=manifest(discovery='e'*64)
    class SlowPort:
        def load_manifest(self):
            with scoped(session_factory) as s:
                ontology.publish(s,newer,expected_previous=manifest()['version'])
            return manifest(discovery='d'*64)
    other=make_tools(session_factory,SlowPort())
    with pytest.raises(ValueError):other.sync_manifest()
    with scoped(session_factory) as s:assert ontology.current_manifest(s)['version']==newer['version']


def test_commit_failure_keeps_handle_and_rolls_back(kit,session_factory,sql):
    from sqlalchemy import event
    h=kit.claim(limit=1)[0]['handle'];kit.read(h);failed=[]
    def factory():
        session=session_factory()
        def reject_commit(s):
            if not s.in_nested_transaction() and not failed:
                failed.append(True);raise RuntimeError('simulated commit failure')
        event.listen(session,'before_commit',reject_commit)
        return session
    kit._factory=factory
    with pytest.raises(RuntimeError):kit.complete(h,expected_version=manifest()['version'],concept_ids=[])
    assert sql('SELECT count(*) AS n FROM d3_search_fact_snapshot')[0]['n']==0
    assert kit.complete(h,expected_version=manifest()['version'],concept_ids=[])['status']=='ready'


def test_deleted_source_finishes_without_semantic_binding(kit,sources,sql):
    sql('UPDATE d3_dataset SET deleted_at=clock_timestamp(),deleted_by_account_id=current_account_id() WHERE id=:id',{'id':sources[0]})
    jobs=kit.claim()
    for job in jobs:
        read=kit.read(job['handle'])
        assert read['source']['deleted'] is True
        assert kit.complete(job['handle'],expected_version=manifest()['version'],concept_ids=[])['status']=='deleted'
    assert all(r['requested_version']==r['processed_version'] for r in sql('SELECT * FROM d3_search_change'))


def test_draft_evidence_stays_candidate_without_binding(kit,sources,sql):
    from test_search_facts import evidence
    evidence(sql,*sources,status='draft')
    h=next(j['handle'] for j in kit.claim() if j['source_kind']=='evidence')
    assert kit.read(h)['source']['status']=='candidate'
    assert kit.complete(h,expected_version=manifest()['version'],concept_ids=[])['status']=='candidate'
    assert sql('SELECT count(*) AS n FROM d3_search_ontology_binding')[0]['n']==0
    assert sql("SELECT status FROM d3_search_fact_snapshot WHERE source_kind='evidence'")[0]['status']=='candidate'


def test_access_revoked_after_read_rejects_completion(kit,sources,sql,session_factory):
    from conftest import ACC_A_PROF
    other=make_tools(session_factory,account=ACC_A_PROF)
    h=next(j['handle'] for j in other.claim() if j['source_kind']=='file')
    other.read(h)
    sql("INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,current_lab_id(),'잠김') ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'",{'id':sources[0]})
    with pytest.raises(ValueError):other.complete(h,expected_version=manifest()['version'],concept_ids=[])
    assert sql('SELECT count(*) AS n FROM d3_search_fact_snapshot')[0]['n']==0


def test_expired_memory_handle_and_invalid_claim_limits_are_rejected(kit,monkeypatch):
    from colab_core.app import search_refresh_tools
    from types import SimpleNamespace
    for limit in [0,101,True]:
        with pytest.raises(ValueError):kit.claim(limit=limit)
    h=kit.claim(limit=1)[0]['handle']
    now=search_refresh_tools.time.monotonic()
    monkeypatch.setattr(search_refresh_tools,'time',SimpleNamespace(monotonic=lambda:now+301))
    with pytest.raises(ValueError):kit.read(h)


def test_returned_source_cannot_mutate_the_stored_read_proof(kit):
    h=kit.claim(limit=1)[0]['handle'];source=kit.read(h)
    source['source']['facts'].append({'predicate':'invented','value':'not real','source_locator':'fake'})
    assert kit.complete(h,expected_version=manifest()['version'],concept_ids=[])['status']=='ready'
