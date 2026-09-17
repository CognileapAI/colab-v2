"""Versioned dependency receipts must not turn stale knowledge into current results."""
import hashlib
import json
import pytest
from sqlalchemy import text
from conftest import LAB_B, ACC_B_PROF
from test_search_changes import sources, scoped
from test_search_facts import claim_all, facts


def api():
    from colab_core.domains import d3_search_ontology
    return d3_search_ontology


def manifest(**changes):
    entries={'discovery':'a'*64,'concept:rain':'b'*64,'concept:ndvi':'c'*64,**changes}
    body={'protocol':'ontology-manifest-v1','entries':entries}
    version=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {**body,'version':version}


@pytest.fixture
def ready(sources,session_factory):
    with scoped(session_factory) as s:
        # Reset only the disposable lab's current pointer. Historical bindings remain
        # retained (and may be hidden by source RLS), so never delete their releases.
        s.execute(text('DELETE FROM d3_search_ontology_head'))
    for item in claim_all(session_factory):
        with scoped(session_factory) as s: facts().process(s,item)
    with scoped(session_factory) as s:
        rows=facts().read_current(s,sources[0])
    return sources[0], {r['source_kind']:r['id'] for r in rows}


def test_ontology_receipt_store_exists(sql):
    assert sql("SELECT to_regclass('d3_search_ontology_release') AS name")[0]['name']


def test_publish_compare_and_swap_and_validation(ready,session_factory):
    a=manifest(); b=manifest(**{'concept:rain':'d'*64})
    with scoped(session_factory) as s:
        assert api().publish(s,a,expected_previous=None)==a['version']
        assert api().publish(s,a,expected_previous=None)==a['version']
        with pytest.raises(ValueError): api().publish(s,b,expected_previous=None)
        bad={**b,'version':'0'*64}
        with pytest.raises(ValueError): api().publish(s,bad,expected_previous=a['version'])
        assert api().publish(s,b,expected_previous=a['version'])==b['version']


def test_only_changed_dependencies_requeue_and_pages_are_idempotent(ready,session_factory):
    dataset,ids=ready; a=manifest(); b=manifest(**{'concept:rain':'d'*64})
    with scoped(session_factory) as s:
        api().publish(s,a,expected_previous=None)
        api().bind(s,ids['metadata'],expected_version=a['version'],concept_ids=['rain'])
        api().bind(s,ids['file'],expected_version=a['version'],concept_ids=['ndvi'])
        api().publish(s,b,expected_previous=a['version'])
        assert [r['fact_snapshot_id'] for r in api().current_bindings(s,dataset)]==[ids['file']]
        assert len(api().requeue(s,limit=1))==1
        assert api().requeue(s,limit=1)==[]
        assert len(api().current_bindings(s,dataset))==1


def test_discovery_change_invalidates_matched_and_unmatched(ready,session_factory):
    dataset,ids=ready; a=manifest(); b=manifest(discovery='d'*64)
    with scoped(session_factory) as s:
        api().publish(s,a,expected_previous=None)
        api().bind(s,ids['metadata'],expected_version=a['version'],concept_ids=[])
        api().bind(s,ids['file'],expected_version=a['version'],concept_ids=['rain'])
        api().publish(s,b,expected_previous=a['version'])
        assert api().current_bindings(s,dataset)==[]
        assert len(api().requeue(s,limit=1))==1
        assert len(api().requeue(s,limit=1))==1
        assert api().requeue(s)==[]


def test_stale_source_or_manifest_cannot_bind(ready,sql,session_factory):
    dataset,ids=ready; a=manifest(); b=manifest(discovery='d'*64)
    with scoped(session_factory) as s:
        api().publish(s,a,expected_previous=None)
        api().publish(s,b,expected_previous=a['version'])
        with pytest.raises(ValueError): api().bind(s,ids['file'],expected_version=a['version'],concept_ids=[])
        with pytest.raises(ValueError): api().bind(s,ids['file'],expected_version=b['version'],concept_ids=['missing'])
    sql("UPDATE d3_dataset_description SET summary='new source' WHERE dataset_id=:id",{'id':dataset})
    with scoped(session_factory) as s:
        with pytest.raises(ValueError): api().bind(s,ids['metadata'],expected_version=b['version'],concept_ids=[])


def test_cross_lab_isolation_and_rollback(ready,session_factory):
    dataset,ids=ready; a=manifest()
    with scoped(session_factory) as s:
        api().publish(s,a,expected_previous=None)
        api().bind(s,ids['file'],expected_version=a['version'],concept_ids=[])
    with scoped(session_factory,lab=LAB_B,account=ACC_B_PROF) as s:
        assert api().current_bindings(s,dataset)==[]
        assert s.execute(text('SELECT count(*) FROM d3_search_ontology_release')).scalar_one()==0
        with pytest.raises(ValueError): api().bind(s,ids['file'],expected_version=a['version'],concept_ids=[])
    with pytest.raises(RuntimeError), scoped(session_factory) as s:
        api().publish(s,manifest(discovery='d'*64),expected_previous=a['version'])
        raise RuntimeError('caller rollback')
    with scoped(session_factory) as s: assert len(api().current_bindings(s,dataset))==1


def test_receipt_idempotence_and_source_access_revocation(ready,sql,session_factory):
    dataset,ids=ready; a=manifest()
    with scoped(session_factory) as s:
        api().publish(s,a,expected_previous=None)
        first=api().bind(s,ids['file'],expected_version=a['version'],concept_ids=['rain'])
        assert api().bind(s,ids['file'],expected_version=a['version'],concept_ids=['rain','rain'])==first
        with pytest.raises(ValueError): api().bind(s,ids['file'],expected_version=a['version'],concept_ids=[])
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,current_lab_id(),'잠김')
      ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'""",{'id':dataset})
    # The owner still has access; a different member in the same lab does not.
    from conftest import ACC_A_OUTSIDER
    with scoped(session_factory,account=ACC_A_OUTSIDER) as s:
        assert api().current_bindings(s,dataset)==[]
        assert s.execute(text('SELECT count(*) FROM d3_search_ontology_binding')).scalar_one()==0
        assert s.execute(text('SELECT count(*) FROM d3_search_ontology_dependency')).scalar_one()==0
    sql('UPDATE d3_dataset SET deleted_at=clock_timestamp(),deleted_by_account_id=current_account_id() WHERE id=:id',{'id':dataset})
    with scoped(session_factory) as s:
        assert api().current_bindings(s,dataset)==[]
        assert s.execute(text('SELECT count(*) FROM d3_search_ontology_binding')).scalar_one()==0


def test_new_result_stops_requeue(ready,session_factory):
    dataset,ids=ready; a=manifest(); b=manifest(**{'concept:rain':'d'*64})
    with scoped(session_factory) as s:
        api().publish(s,a,expected_previous=None)
        api().bind(s,ids['metadata'],expected_version=a['version'],concept_ids=['rain'])
        api().publish(s,b,expected_previous=a['version'])
        assert len(api().requeue(s))==1
    for item in claim_all(session_factory):
        with scoped(session_factory) as s: facts().process(s,item)
    with scoped(session_factory) as s:
        new=next(r for r in facts().read_current(s,dataset) if r['source_kind']=='metadata')
        api().bind(s,new['id'],expected_version=b['version'],concept_ids=['rain'])
        assert api().requeue(s)==[]
        assert len(api().current_bindings(s,dataset))==1


def test_missing_concept_dependency_is_not_a_valid_receipt(ready,session_factory):
    dataset,ids=ready; a=manifest()
    with scoped(session_factory) as s:
        api().publish(s,a,expected_previous=None)
        binding=api().bind(s,ids['metadata'],expected_version=a['version'],concept_ids=['rain'])
        s.execute(text("DELETE FROM d3_search_ontology_dependency WHERE binding_id=:id AND dependency_key='concept:rain'"),{'id':binding})
        assert api().current_bindings(s,dataset)==[]
        assert len(api().requeue(s))==1


def test_publication_cannot_overtake_an_inflight_binding_read(ready,session_factory,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event, Lock
    dataset,ids=ready; a=manifest(); b=manifest(discovery='d'*64); module=api()
    with scoped(session_factory) as s:
        module.publish(s,a,expected_previous=None)
        module.bind(s,ids['metadata'],expected_version=a['version'],concept_ids=[])
    read_head=Event(); resume=Event(); started=Event(); guard=Lock(); paused=False
    original=module._head
    def pause_once(s):
        nonlocal paused
        value=original(s)
        with guard:
            pause=not paused
            paused=True
        if pause:
            read_head.set()
            assert resume.wait(10)
        return value
    monkeypatch.setattr(module,'_head',pause_once)
    def read():
        with scoped(session_factory) as s: return module.current_bindings(s,dataset)
    def publish():
        with scoped(session_factory) as s:
            started.set()
            return module.publish(s,b,expected_previous=a['version'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        reader=pool.submit(read)
        try:
            assert read_head.wait(10)
            publisher=pool.submit(publish)
            assert started.wait(10)
            with pytest.raises(TimeoutError): publisher.result(timeout=0.3)
        finally:
            resume.set()
        assert len(reader.result(timeout=10))==1
        assert publisher.result(timeout=10)==b['version']
    with scoped(session_factory) as s: assert module.current_bindings(s,dataset)==[]
