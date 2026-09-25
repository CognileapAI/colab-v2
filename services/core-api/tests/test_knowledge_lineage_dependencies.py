"""D4 incident revisions fence knowledge even when source bytes stay unchanged."""
import pytest
import importlib
from conftest import ACC_A_RES, TOKEN_RES, auth
from test_dataset_registration import make_upload, register
from test_search_changes import scoped
from colab_core.domains import d4_lineage
from colab_core.kernel.ids import Ulid
from test_knowledge_http import connected
from test_knowledge_source_authority import prepared, sources, historical_knowledge_db
from test_knowledge_http_roundtrip import roundtrip


def dataset(client):
    result=register(client,make_upload(client))
    assert result.status_code==201
    return result.json()['datasetId']


def revisions(sql, *ids):
    assert sql("SELECT to_regclass('d4_lineage_revision') AS name")[0]['name'], 'retained D4 revisions missing'
    return {r['dataset_id']:(r['revision'],r['deleted']) for r in sql(
        'SELECT * FROM d4_lineage_revision WHERE dataset_id=ANY(:ids)',{'ids':list(ids)})}


def test_empty_registration_has_revision_one_and_missing_is_not_empty(p2_client,sql,session_factory):
    child=dataset(p2_client())
    assert revisions(sql,child)=={child:(1,False)}
    with scoped(session_factory) as session:
        result=d4_lineage.LineageRevisionAdapter(session).revisions([Ulid(child),Ulid.generate()])
    assert set(result)=={child} and result[child].revision==1


def test_relationship_changes_increment_both_ends_once_and_noops_zero(p2_client,sql):
    client=p2_client(); child,parent=dataset(client),dataset(client)
    endpoint=f'/api/v1/datasets/{child}/lineage'
    assert client.post(endpoint+'/unknown-declaration',headers=auth(TOKEN_RES)).status_code==200
    assert revisions(sql,child,parent)=={child:(2,False),parent:(1,False)}
    assert client.post(endpoint+'/unknown-declaration',headers=auth(TOKEN_RES)).status_code==200
    assert revisions(sql,child)[child]==(2,False)
    assert client.post(endpoint+'/parents',json={'parentDatasetId':parent,'method':'original'},headers=auth(TOKEN_RES)).status_code==201
    assert revisions(sql,child,parent)=={child:(3,False),parent:(2,False)}
    assert sql('SELECT * FROM d4_lineage_unknown WHERE dataset_id=:id',{'id':child})==[]
    for method,want in [('original',3),('changed',4),('changed',4)]:
        assert client.patch(endpoint+'/parents/'+parent,json={'method':method},headers=auth(TOKEN_RES)).status_code==200
        assert revisions(sql,child,parent)=={child:(want,False),parent:(want-1,False)}
    assert client.delete(endpoint+'/parents/'+parent,headers=auth(TOKEN_RES)).status_code==204
    assert revisions(sql,child,parent)=={child:(5,False),parent:(4,False)}
    assert client.delete(endpoint+'/parents/'+parent,headers=auth(TOKEN_RES)).status_code==404
    assert revisions(sql,child,parent)=={child:(5,False),parent:(4,False)}


def test_revision_and_edge_rollback_together(p2_client,sql,session_factory):
    client=p2_client(); child,parent=dataset(client),dataset(client)
    before=revisions(sql,child,parent)
    with pytest.raises(RuntimeError), scoped(session_factory) as session:
        d4_lineage.add_parent(session,child_id=Ulid(child),parent_id=Ulid(parent),parent_role='주입력',
                             method=None,origin='manual',confirmed_by=Ulid(ACC_A_RES))
        raise RuntimeError('rollback')
    assert revisions(sql,child,parent)==before
    assert sql('SELECT id FROM d4_lineage_edge WHERE child_dataset_id=:id',{'id':child})==[]


def test_softdelete_retains_relationship_and_advances_neighbors(p2_client,sql):
    client=p2_client(); child,parent=dataset(client),dataset(client)
    assert client.post(f'/api/v1/datasets/{child}/lineage/parents',
        json={'parentDatasetId':parent},headers=auth(TOKEN_RES)).status_code==201
    edges=sql('SELECT * FROM d4_lineage_edge WHERE child_dataset_id=:id',{'id':child})
    assert client.delete(f'/api/v1/datasets/{parent}',headers=auth(TOKEN_RES)).status_code==204
    assert revisions(sql,child,parent)=={child:(3,False),parent:(3,True)}
    assert sql('SELECT * FROM d4_lineage_edge WHERE child_dataset_id=:id',{'id':child})==edges


def test_lineage_change_invalidates_grant_and_reader_without_source_change(p2_client,sql,session_factory):
    from conftest import LAB_A
    from test_search_facts import evidence
    from test_search_ontology import manifest
    from test_knowledge_source_authority import issue,validate,read_check,receipt_for
    from colab_core.domains import d3_search_ontology
    from colab_core.kernel.knowledge_wire import SourceKey
    client=p2_client(); upload=make_upload(client)
    child=register(client,upload).json()['datasetId']; file_id=upload['files'][0]['fileId']
    evidence(sql,child,file_id)
    with scoped(session_factory) as session:
        previous=d3_search_ontology.current_manifest(session)
        d3_search_ontology.publish(session,manifest(),expected_previous=previous['version'] if previous else None)
    key=SourceKey(lab_id=LAB_A,dataset_id=child,source_kind='evidence',source_id=file_id)
    first=issue(session_factory,key)
    assert any(d.owner=='D4' and d.resource_id==child and d.revision==1 for d in first.dependencies)
    assert validate(session_factory,first)=='current'
    assert client.post(f'/api/v1/datasets/{child}/lineage/unknown-declaration',headers=auth(TOKEN_RES)).status_code==200
    # Existing wire status: a changed dependency makes canonical source state stale.
    assert validate(session_factory,first)=='stale_source'
    assert read_check(session_factory,receipt_for(first))=='stale_source'
    second=issue(session_factory,key)
    assert second.source_version==first.source_version
    assert second.processing_version.generation>first.processing_version.generation
    assert any(d.owner=='D4' and d.revision==2 for d in second.dependencies)


def refresher(client, factory):
    name='colab_core.app.knowledge_dependency_refresh'
    assert importlib.util.find_spec(name), 'tracked dependency refresh missing'
    return importlib.import_module(name).KnowledgeDependencyRefresh(
        factory,client.app.state.login_sessions,client.app.state.database_credentials)


def test_dependency_sweep_replays_and_recaptures_changes_behind_cursor(connected,session_factory,sql):
    client,key,issued,_=connected
    runner=refresher(client,session_factory)
    first=runner.run_once(issued.token,after_source=None,limit=1)
    assert first['requeued']==1 and first['after_source'] is not None
    before=sql('SELECT requested_version FROM d3_search_change WHERE source_id=:id AND source_kind=:kind',
               {'id':key.source_id,'kind':key.source_kind})[0]['requested_version']
    from conftest import ACC_A_RES
    with scoped(session_factory) as session:
        d4_lineage.mark_unknown(session,dataset_id=Ulid(key.dataset_id),actor_id=Ulid(ACC_A_RES))
    cursor=first['after_source']
    for _ in range(3):
        result=runner.run_once(issued.token,after_source=cursor,limit=1);cursor=result['after_source']
        if cursor is None:break
    assert cursor is None
    replay=runner.run_once(issued.token,after_source=None,limit=1)
    assert replay['requeued']==1
    assert sql('SELECT requested_version FROM d3_search_change WHERE source_id=:id AND source_kind=:kind',
               {'id':key.source_id,'kind':key.source_kind})[0]['requested_version']==before
    assert runner.run_once(issued.token,after_source=None,limit=1)['requeued']==0
    client.app.state.login_sessions.revoke(issued.session_id)
    rows=sql('SELECT * FROM d3_knowledge_dependency')
    with pytest.raises(ValueError,match='forbidden'):
        runner.run_once(issued.token,after_source=None,limit=1)
    assert sql('SELECT * FROM d3_knowledge_dependency')==rows


def test_partial_refresh_failure_and_revocation_leave_no_success_progress(connected,session_factory,sql,monkeypatch):
    client,key,issued,_=connected
    runner=refresher(client,session_factory)
    from colab_core.domains import d3_knowledge_dependencies
    original=d3_knowledge_dependencies.requeue_if_lineage_changed
    calls=[]
    def fail_second(*args):
        calls.append(1)
        if len(calls)==2:raise RuntimeError('injected mid-batch failure')
        return original(*args)
    before=sql('SELECT * FROM d3_search_change ORDER BY source_kind,source_id')
    with monkeypatch.context() as patch:
        patch.setattr(d3_knowledge_dependencies,'requeue_if_lineage_changed',fail_second)
        with pytest.raises(RuntimeError):runner.run_once(issued.token,limit=100)
    assert len(calls)==2
    assert sql('SELECT * FROM d3_knowledge_dependency')==[]
    assert sql('SELECT * FROM d3_search_change ORDER BY source_kind,source_id')==before
    assert runner.run_once(issued.token,limit=100)['requeued']==2


@pytest.mark.parametrize('operation',['add','registration'])
def test_lineage_add_rechecks_deleted_parent_after_waiting_on_lab_lock(p2_client,session_factory,sql,monkeypatch,operation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from colab_core.domains import d3_catalog
    client=p2_client(); child,parent=dataset(client),dataset(client)
    upload=make_upload(client) if operation=='registration' else None
    reached=Event(); original=d4_lineage.lock_lab_for_lineage_write
    with scoped(session_factory) as session:
        original(session)
        def observed(db):
            if db is not session:reached.set()
            return original(db)
        with monkeypatch.context() as patch,ThreadPoolExecutor(max_workers=1) as pool:
            patch.setattr(d4_lineage,'lock_lab_for_lineage_write',observed)
            if operation=='registration':
                pending=pool.submit(register,client,upload,lineageParents=[{'parentDatasetId':parent,'origin':'manual'}])
            else:
                pending=pool.submit(client.post,f'/api/v1/datasets/{child}/lineage/parents',
                    json={'parentDatasetId':parent},headers=auth(TOKEN_RES))
            try:
                assert reached.wait(5)
                assert not pending.done()
                # Same lab-locked delete producer TX; the HTTP waiter must reread after commit.
                assert d3_catalog.tombstone_dataset(session,dataset_id=Ulid(parent),actor_id=Ulid(ACC_A_RES))
                d4_lineage.mark_dataset_deleted(session,Ulid(parent))
                session.commit()
            finally:
                if session.in_transaction():session.rollback()
            # Registration's existing invalid-parent contract is 400; add uses 404.
            assert pending.result(timeout=5).status_code==(400 if operation=='registration' else 404)
    assert sql('SELECT * FROM d4_lineage_edge WHERE child_dataset_id=:id',{'id':child})==[]
    if upload:
        assert sql('SELECT registered_at FROM d5_upload WHERE id=:id',{'id':upload['uploadId']})[0]['registered_at'] is None


@pytest.mark.parametrize('operation',['registration','deletion'])
def test_lab_lock_precedes_first_registration_write_and_delete_row_lock(p2_client,session_factory,monkeypatch,operation):
    from sqlalchemy import text
    from colab_core.domains import d3_catalog
    client=p2_client();target=dataset(client)
    called=[]
    name='register_dataset' if operation=='registration' else 'lock_dataset'
    original=getattr(d3_catalog,name)
    def observe(*args,**kwargs):
        with scoped(session_factory) as other:
            assert other.execute(text('SELECT pg_try_advisory_xact_lock(hashtext(current_lab_id()::text))')).scalar_one() is False
        called.append(True)
        return original(*args,**kwargs)
    monkeypatch.setattr(d3_catalog,name,observe)
    result=register(client,make_upload(client)) if operation=='registration' else client.delete(
        f'/api/v1/datasets/{target}',headers=auth(TOKEN_RES))
    assert result.status_code==(201 if operation=='registration' else 204)
    assert called==[True]


def test_0041_backfills_live_and_hidden_deleted_datasets_and_restores_rls(historical_knowledge_db):
    from sqlalchemy import text
    from conftest import LAB_A,LAB_B,ACC_B_PROF
    factory,upgrade=historical_knowledge_db
    assert upgrade('0040_file_measurement')==0
    ids=[]
    for lab,account,deleted in [(LAB_A,ACC_A_RES,False),(LAB_B,ACC_B_PROF,True)]:
        value=str(Ulid.generate());ids.append(value)
        with scoped(factory,lab=lab,account=account) as db:
            db.execute(text("INSERT INTO d1_lab(id,name,opened_at) VALUES (:lab,'backfill',now())"),{'lab':lab})
            db.execute(text("INSERT INTO d1_account(id,lab_id,name,email) VALUES (:account,:lab,'backfill','backfill@example.invalid')"),{'account':account,'lab':lab})
            db.execute(text('''INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id,deleted_at,deleted_by_account_id)
              VALUES (:id,:lab,:account,:account,CASE WHEN :deleted THEN now() ELSE NULL END,
                CASE WHEN :deleted THEN CAST(:account AS ulid) ELSE NULL END)'''),
              {'id':value,'lab':lab,'account':account,'deleted':deleted})
    with factory() as db:
        assert db.execute(text('SELECT count(*) FROM d3_dataset')).scalar_one()==0
        assert db.execute(text('SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user')).scalar_one() is False
    assert upgrade('0041_lineage_dependencies')==0
    for lab,account,value,deleted in [(LAB_A,ACC_A_RES,ids[0],False),(LAB_B,ACC_B_PROF,ids[1],True)]:
        with scoped(factory,lab=lab,account=account) as db:
            rows=db.execute(text('SELECT dataset_id,revision,deleted FROM d4_lineage_revision')).all()
            assert rows==[(value,1,deleted)]
            assert db.execute(text("SELECT relrowsecurity AND relforcerowsecurity FROM pg_class WHERE relname='d3_dataset'")).scalar_one() is True
    with factory() as db:
        assert db.execute(text('SELECT count(*) FROM d3_dataset')).scalar_one()==0
        assert db.execute(text('SELECT count(*) FROM d4_lineage_revision')).scalar_one()==0


@pytest.mark.parametrize('denial',['missing_marker','access_revoked_after_selection'])
def test_refresh_denial_never_invents_initial_revision(connected,session_factory,sql,monkeypatch,denial):
    client,key,issued,_=connected
    runner=refresher(client,session_factory)
    if denial=='missing_marker':
        sql('DELETE FROM d4_lineage_revision WHERE dataset_id=:id',{'id':key.dataset_id})
    else:
        from colab_core.domains import d3_knowledge_dependencies
        original=d3_knowledge_dependencies.page
        def revoke_after_selection(*args,**kwargs):
            keys=original(*args,**kwargs)
            sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
              ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':key.dataset_id,'lab':key.lab_id})
            return keys
        monkeypatch.setattr(d3_knowledge_dependencies,'page',revoke_after_selection)
    before=sql('SELECT * FROM d3_search_change ORDER BY source_kind,source_id')
    with pytest.raises(ValueError,match='stale_source|forbidden'):
        runner.run_once(issued.token,limit=100)
    assert sql('SELECT * FROM d3_knowledge_dependency')==[]
    assert sql('SELECT * FROM d3_search_change ORDER BY source_kind,source_id')==before


def test_hidden_leading_source_does_not_starve_visible_source(connected,p2_client,session_factory,sql):
    from test_search_facts import evidence
    client,key,issued,_=connected
    uploader=p2_client(); upload=make_upload(uploader)
    public=register(uploader,upload).json()['datasetId']; public_file=upload['files'][0]['fileId']
    evidence(sql,public,public_file)
    assert key.source_id<public_file
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':key.dataset_id,'lab':key.lab_id})
    hidden_before=sql('SELECT * FROM d3_search_change WHERE dataset_id=:id ORDER BY source_kind',{'id':key.dataset_id})
    result=refresher(client,session_factory).run_once(issued.token,limit=1)
    assert result['scanned']==result['requeued']==1
    assert result['after_source']['source_id']==public_file
    assert sql('SELECT * FROM d3_search_change WHERE dataset_id=:id ORDER BY source_kind',{'id':key.dataset_id})==hidden_before
    assert sql('SELECT * FROM d3_knowledge_dependency WHERE dataset_id=:id',{'id':key.dataset_id})==[]


def test_sweep_issue_and_projection_do_not_form_three_transaction_cycle(connected,p2_client,session_factory,sql,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event,local
    from time import monotonic,sleep
    from sqlalchemy import text
    from colab_core.domains import d3_knowledge_source as source,d3_knowledge_projection as projection,d3_search_ontology as ontology,d3_search_changes as changes
    from colab_core.kernel.knowledge_wire import AuthorizedKnowledge
    from test_knowledge_source_authority import issue,principal,receipt_for
    from test_search_facts import evidence
    client,a,issued,account=connected
    uploader=p2_client(); upload=make_upload(uploader); dataset_b=register(uploader,upload).json()['datasetId']
    evidence(sql,dataset_b,upload['files'][0]['fileId'])
    b=a.model_copy(update={'dataset_id':dataset_b,'source_id':upload['files'][0]['fileId']})
    assert a.source_id<b.source_id
    who=principal(account);command=issue(session_factory,a,who)
    result=AuthorizedKnowledge(payload=command.model_dump(exclude={'grant'}),receipt=receipt_for(command))
    with scoped(session_factory,account=account) as db:
        claim=next(c for c in changes.claim(db,limit=100,authorized_only=True) if c.source_kind=='evidence' and c.source_id==a.source_id)
    role=local();a_held=Event();b_held=Event();ontology_held=Event();sweep_b=Event();pids={}
    original_lock=source._lock;original_manifest=ontology.current_manifest
    def lock(db,key):
        name=getattr(role,'name',None)
        db.execute(text("SET LOCAL statement_timeout='8s'"))
        pids[name]=db.execute(text('SELECT pg_backend_pid()')).scalar_one()
        if name=='sweep' and key==b:sweep_b.set()
        original_lock(db,key)
        if name=='sweep' and key==a:
            a_held.set();assert b_held.wait(5) and ontology_held.wait(5)
        if name=='issue' and key==b:
            b_held.set();assert ontology_held.wait(5)
    def manifest(db):
        answer=original_manifest(db)
        if getattr(role,'name',None)=='projection' and not ontology_held.is_set():
            ontology_held.set();assert sweep_b.wait(5)
            # Observe the real B advisory-lock wait, not merely a thread start.
            deadline=monotonic()+5
            with session_factory() as observer:
                while monotonic()<deadline:
                    blockers=observer.execute(text('SELECT pg_blocking_pids(:pid)'),{'pid':pids['sweep']}).scalar_one()
                    if pids['issue'] in blockers:break
                    sleep(.01)
                else:raise AssertionError('sweep never waited on issue B')
        return answer
    def sweep():
        role.name='sweep'
        return refresher(client,session_factory).run_once(issued.token,limit=2)
    def issue_b():
        role.name='issue';assert a_held.wait(5)
        return issue(session_factory,b,who)
    def project_a():
        role.name='projection';assert b_held.wait(5)
        with scoped(session_factory,account=account) as db:
            db.execute(text("SET LOCAL statement_timeout='8s'"))
            return projection.apply(db,claim,result,who,lineage=d4_lineage.LineageRevisionAdapter(db))
    monkeypatch.setattr(source,'_lock',lock);monkeypatch.setattr(ontology,'current_manifest',manifest)
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending=[pool.submit(f) for f in (sweep,issue_b,project_a)]
        outcomes=[]
        for future in pending:
            try:outcomes.append(future.result(timeout=15))
            except Exception as exc:outcomes.append(exc)
    failures=[(type(x).__name__,getattr(getattr(x,'orig',None),'sqlstate',None)) for x in outcomes if isinstance(x,Exception)]
    assert failures==[],failures
    assert outcomes[0]['requeued']==2 and outcomes[2]['status']=='applied'


@pytest.mark.parametrize('change',['revision','access'])
def test_sweep_rereads_revision_and_access_after_knowledge_lock_wait(connected,session_factory,sql,monkeypatch,change):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from colab_core.domains import d3_knowledge_source as source
    client,key,issued,_=connected
    reached=Event();original=source._lock
    runner=refresher(client,session_factory)
    before=sql('SELECT * FROM d3_search_change ORDER BY source_kind,source_id')
    with scoped(session_factory) as blocker:
        original(blocker,key)
        def observed(db,value):
            if db is not blocker and value==key:reached.set()
            return original(db,value)
        monkeypatch.setattr(source,'_lock',observed)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(runner.run_once,issued.token,limit=1)
            try:
                assert reached.wait(5) and not pending.done()
                if change=='revision':
                    with scoped(session_factory) as db:
                        d4_lineage.mark_unknown(db,dataset_id=Ulid(key.dataset_id),actor_id=Ulid(ACC_A_RES))
                else:
                    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
                      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':key.dataset_id,'lab':key.lab_id})
            finally:blocker.rollback()
            if change=='revision':
                assert pending.result(timeout=5)['requeued']==1
            else:
                with pytest.raises(ValueError,match='forbidden'):pending.result(timeout=5)
    if change=='revision':
        assert sql('SELECT lineage_revision FROM d3_knowledge_dependency WHERE source_id=:id',{'id':key.source_id})==[{'lineage_revision':2}]
    else:
        assert sql('SELECT * FROM d3_knowledge_dependency')==[]
        assert sql('SELECT * FROM d3_search_change ORDER BY source_kind,source_id')==before


def test_concurrent_sweeps_share_one_sorted_batch_and_commit_progress_once(connected,session_factory,sql,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier,local
    from colab_core.domains import d3_knowledge_dependencies as dependencies
    client,key,issued,_=connected
    ready=Barrier(2);role=local();original=dependencies.page
    def selected(*args,**kwargs):
        keys=original(*args,**kwargs)
        ready.wait(timeout=5)
        # Input order is not a lock-order guarantee; both calls must normalize it.
        return list(reversed(keys)) if role.reverse else keys
    monkeypatch.setattr(dependencies,'page',selected)
    def run(reverse):
        role.reverse=reverse
        return refresher(client,session_factory).run_once(issued.token,limit=100)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending=[pool.submit(run,reverse) for reverse in (False,True)]
        results=[f.result(timeout=10) for f in pending]
    assert sorted(r['requeued'] for r in results)==[0,2]
    assert all(r['scanned']==2 and r['after_source'] is None for r in results)
    assert len(sql('SELECT * FROM d3_knowledge_dependency'))==2


def test_actual_d9_http_rejects_old_dependency_before_read_and_projection(roundtrip,session_factory,sql):
    from knowledge_http_roundtrip import request
    from test_knowledge_http import headers
    from colab_core.app.knowledge_projector import KnowledgeProjector
    from colab_core.domains import d3_search_changes
    client,key,issued,account,core_url,ai_url,_=roundtrip
    status,made=request(core_url+'/internal/knowledge/source/issue',{'source_key':key.model_dump()},headers(issued.token))
    assert status==200
    status,receipt=request(ai_url+'/internal/knowledge/replace',made,headers(issued.token,'dedicated-writer'))
    assert status==200
    with scoped(session_factory,account=account) as db:
        claim=next(c for c in d3_search_changes.claim(db,limit=100) if c.source_kind=='evidence' and c.source_id==key.source_id)
    with scoped(session_factory) as db:
        d4_lineage.mark_unknown(db,dataset_id=Ulid(key.dataset_id),actor_id=Ulid(ACC_A_RES))
    status,verdict=request(core_url+'/internal/knowledge/source/validate',
        {'command':made['command']},headers(issued.token))
    assert status==200 and verdict['status']=='stale_source'
    assert request(ai_url+'/internal/knowledge/replace',made,headers(issued.token,'dedicated-writer'))[0]==409
    projector=KnowledgeProjector(session_factory,client.app.state.login_sessions,client.app.state.database_credentials,
        base_url=ai_url,reader_token='dedicated-reader',timeout=2)
    with pytest.raises(ValueError):projector.apply(claim,receipt['receipt_id'],session_token=issued.token)
    assert sql('SELECT * FROM d3_knowledge_projection')==[]
