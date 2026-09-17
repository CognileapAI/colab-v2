"""Internal source routes require service identity AND a tracked DB session."""
import dataclasses
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from conftest import LAB_A, ACC_A_RES
from test_knowledge_source_authority import prepared, sources
from colab_core.kernel.ids import Ulid
from colab_core.kernel.auth import Subject

CALLBACK = 'dedicated-source-callback'
READ = 'existing-ontology-read'
DELETION = 'dedicated-deletion-only'


@pytest.fixture
def connected(prepared, p2_client, sql):
    base = p2_client(session_secret='knowledge-session-signing')
    configured = hasattr(base.app.state.settings, 'knowledge_source_enabled')
    assert configured, 'internal source configuration missing'
    from colab_core.app.main import create_app
    settings = dataclasses.replace(base.app.state.settings, knowledge_source_enabled=True,
                                   knowledge_callback_token=CALLBACK, ai_service_token=READ,
                                   knowledge_deletion_token=DELETION,knowledge_deletion_lab=LAB_A,
                                   knowledge_deletion_enabled=True)
    app = create_app(settings)
    account = str(Ulid.generate())
    sql('INSERT INTO d1_account(id,lab_id,name,email) VALUES (:id,:lab,\'knowledge-http\',:email)',
        {'id':account,'lab':LAB_A,'email':account+'@example.test'})
    with app.state.account_admin_factory.begin() as db:
        db.execute(text("""INSERT INTO account_admin.login_credential
          (account_id,login_name,kdf,salt,password_hash,n,r,p,must_change_password,session_version,status)
          VALUES (:id,:name,'scrypt','00','00',16384,8,1,false,1,'active')"""), {'id':account,'name':account.lower()})
    issued = app.state.login_sessions.issue(Subject(Ulid(account),Ulid(LAB_A)),
        credential_kind='database',credential_version=1,purpose='normal')
    try:
        with TestClient(app) as client:
            yield client, prepared, issued, account
    finally:
        app.state.login_sessions.revoke(issued.session_id)
        # Only this fixture's new dataset: restore access before scoped cleanup.
        sql("UPDATE d2_dataset_access SET state='열림' WHERE dataset_id=:id", {'id':prepared.dataset_id})
        sql('DELETE FROM d3_knowledge_grant WHERE account_id=:id', {'id':account}, account_id=account)
        sql('DELETE FROM d1_account WHERE id=:id', {'id':account})


def headers(token, service=CALLBACK):
    return {'Authorization':'Bearer '+service,'X-CoLAB-Session':token}


@pytest.mark.parametrize('change',[{'knowledge_deletion_enabled':None},
    {'knowledge_deletion_token':None},{'knowledge_deletion_lab':None},
    {'knowledge_deletion_token':CALLBACK},{'knowledge_deletion_token':READ}])
def test_deletion_startup_requires_explicit_mode_and_distinct_scoped_capability(connected,change):
    from colab_core.app.main import create_app
    client,*_=connected
    with pytest.raises(ValueError):
        create_app(dataclasses.replace(client.app.state.settings,**change))


def test_explicitly_disabled_deletion_preserves_source_routes(connected):
    from colab_core.app.main import create_app
    client,key,issued,_=connected
    app=create_app(dataclasses.replace(client.app.state.settings,knowledge_deletion_enabled=False,
        knowledge_deletion_token=None,knowledge_deletion_lab=None))
    with TestClient(app) as other:
        assert other.post('/internal/knowledge/deletion/issue',json={}).status_code==404
        assert other.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump()},headers=headers(issued.token)).status_code==200


def test_issue_and_validate_use_real_tracked_session(connected):
    client,key,issued,account = connected
    made = client.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump()},headers=headers(issued.token))
    assert made.status_code == 200, made.text
    assert made.json()['principal']['account_id'] == account
    checked = client.post('/internal/knowledge/source/validate',json={'command':made.json()['command']},headers=headers(issued.token))
    assert checked.status_code == 200 and checked.json()['status'] == 'current'
    client.app.state.login_sessions.revoke(issued.session_id)
    assert client.post('/internal/knowledge/source/validate',json={'command':made.json()['command']},headers=headers(issued.token)).status_code == 401


@pytest.mark.parametrize('service,session', [(READ,'tracked'),('writer-token','tracked'),(CALLBACK,'a1-res-token'),(CALLBACK,'')])
def test_token_types_are_not_interchangeable(connected,service,session):
    client,key,issued,_ = connected
    token=issued.token if session=='tracked' else session
    assert client.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump()},headers=headers(token,service)).status_code == 401


def test_principal_injection_and_oversize_body_are_rejected(connected):
    client,key,issued,_ = connected
    assert client.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump(),'principal':{}},headers=headers(issued.token)).status_code == 422
    assert client.post('/internal/knowledge/source/issue',content=b' '*1048577,headers=headers(issued.token)).status_code == 413


def test_enabled_configuration_missing_credentials_fails_startup(p2_client):
    base=p2_client()
    configured = hasattr(base.app.state.settings, 'knowledge_source_enabled')
    assert configured, 'configuration missing'
    from colab_core.app.main import create_app
    with pytest.raises(ValueError):
        create_app(dataclasses.replace(base.app.state.settings,knowledge_source_enabled=True))


@pytest.mark.parametrize('change',['version','password','inactive'])
def test_current_credential_changes_reject_old_session(connected,change):
    client,key,issued,account=connected
    assignment={'version':'session_version=session_version+1','password':'must_change_password=true','inactive':"status='inactive'"}[change]
    with client.app.state.account_admin_factory.begin() as db:
        db.execute(text('UPDATE account_admin.login_credential SET '+assignment+' WHERE account_id=:id'),{'id':account})
    response=client.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump()},headers=headers(issued.token))
    assert response.status_code in {401,403}


def test_same_lab_private_and_other_lab_sources_are_denied(connected,sql):
    client,key,issued,account=connected
    other=key.model_dump();other['lab_id']='0000000000000000000000000B'
    assert client.post('/internal/knowledge/source/issue',json={'source_key':other},headers=headers(issued.token)).status_code==403
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':key.dataset_id,'lab':LAB_A})
    assert client.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump()},headers=headers(issued.token)).status_code==403


def test_disabled_core_has_no_callback(p2_client):
    assert p2_client().post('/internal/knowledge/source/issue',json={}).status_code==404


def test_non_ascii_service_header_is_unauthorized_and_no_store(connected):
    client,key,issued,_=connected
    response=client.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump()},
        headers=[(b'authorization',b'Bearer \xff'),(b'x-colab-session',issued.token.encode())])
    assert response.status_code==401
    assert set(response.json()) >= {'code','message'}
    assert response.headers['cache-control']=='no-store'


@pytest.mark.parametrize('operation',['authenticate','issue','validate','authorize_read'])
def test_slow_source_database_does_not_block_health(connected,monkeypatch,operation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    client,key,issued,_=connected
    made=client.post('/internal/knowledge/source/issue',json={'source_key':key.model_dump()},headers=headers(issued.token)).json()
    target=client.app.state.login_sessions if operation=='authenticate' else client.app.state.knowledge_source
    original=getattr(target,operation)
    entered,release=Event(),Event()
    def slow(*args,**kwargs):
        entered.set();release.wait(timeout=5)
        return original(*args,**kwargs)
    with monkeypatch.context() as patch,ThreadPoolExecutor(max_workers=2) as pool:
        patch.setattr(target,operation,slow)
        path='read' if operation=='authorize_read' else 'validate' if operation=='validate' else 'issue'
        payload={'command':made['command']} if path=='validate' else {'source_key':key.model_dump()}
        if path=='read':
            from test_knowledge_source_authority import receipt_for
            from colab_core.kernel.knowledge_wire import ReplaceCommand
            payload={'receipt':receipt_for(ReplaceCommand.model_validate(made['command'])).model_dump(mode='json')}
        pending=pool.submit(client.post,'/internal/knowledge/source/'+path,json=payload,headers=headers(issued.token))
        try:
            assert entered.wait(timeout=2)
            assert pool.submit(client.get,'/healthz').result(timeout=1).status_code==200
        finally:release.set()
        assert pending.result(timeout=5).status_code==200
