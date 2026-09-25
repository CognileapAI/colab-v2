"""Real loopback core↔dedicated AI process, each with disposable PostgreSQL.

No production cross-service imports. Tokens/DB URLs travel only via request
headers/process environment; subprocess output is not included in failures.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
from threading import Thread
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
import uvicorn
from test_knowledge_http import connected, prepared, sources, headers, CALLBACK, READ, DELETION
from test_search_changes import scoped
from colab_core.domains import d3_search_ontology

ROOT=Path(__file__).resolve().parents[2]


def test_measured_file_pipeline_registration_d9_projection(roundtrip,p2_client,session_factory,sql,tmp_path):
    """Real native parser runs only in D5's interpreter; core consumes its owned receipt."""
    import struct
    from test_dataset_registration import make_upload,register
    from colab_core.kernel.knowledge_wire import SourceKey
    from colab_core.app.knowledge_projector import KnowledgeProjector
    from colab_core.domains import d3_search_changes as changes
    client,_,issued,account,core_url,ai_url,_=roundtrip
    # Valid .npy built with stdlib bytes only; no numpy/native parser imported into core.
    header=b"{'descr': '<f4', 'fortran_order': False, 'shape': (2, 2), }"
    header+=b' '*((64-(10+len(header)+1)%64)%64)+b'\n'
    payload=b'\x93NUMPY\x01\x00'+struct.pack('<H',len(header))+header+struct.pack('<4f',1,2,3,4)
    registration=p2_client()
    upload=make_upload(registration,files=[('files',('misleading.tif',payload,'application/octet-stream'))])
    file_id=upload['files'][0]['fileId']
    record=sql('''SELECT f.lab_id,f.storage_key,u.uploader_account_id FROM d5_upload_file f
                  JOIN d5_upload u ON u.id=f.upload_id WHERE f.id=:id''',{'id':file_id})[0]
    root=Path(registration.app.state.settings.upload_storage_dir)
    py=ROOT/'services/pipeline-worker/.venv/bin/python'
    assert py.is_file(),'pipeline interpreter missing; measurement was not executed'
    with session_factory() as session:
        db_url=session.get_bind().url.render_as_string(hide_password=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('COLAB_','OPENAI_','ANTHROPIC_'))}
    env.update(COLAB_PIPELINE_DB_URL=db_url,MEASUREMENT_FILE=str(root/record['storage_key']),
        MEASUREMENT_WORK=str(tmp_path/'measured-work'),MEASUREMENT_FILE_ID=file_id,
        MEASUREMENT_UPLOAD=upload['uploadId'],MEASUREMENT_LAB=record['lab_id'],MEASUREMENT_ACTOR=record['uploader_account_id'])
    code='''import os
from pathlib import Path
from sqlalchemy import create_engine,text
from sqlalchemy.orm import Session
from colab_pipeline.domains.d5_ingestion import IngestionService,SqlLedger,UploadFileWork,UploadWork
engine=create_engine(os.environ['COLAB_PIPELINE_DB_URL'])
with Session(engine) as db,db.begin():
 db.execute(text("SELECT set_config('app.current_lab',:lab,true),set_config('app.current_account','',true)"),{'lab':os.environ['MEASUREMENT_LAB']})
 source=Path(os.environ['MEASUREMENT_FILE'])
 work=UploadWork(upload_id=os.environ['MEASUREMENT_UPLOAD'],lab_id=os.environ['MEASUREMENT_LAB'],actor_account_id=os.environ['MEASUREMENT_ACTOR'],workdir=Path(os.environ['MEASUREMENT_WORK']),files=[UploadFileWork(file_id=os.environ['MEASUREMENT_FILE_ID'],path=source,kind='본체',file_name=source.name)])
 IngestionService(SqlLedger(db)).process_upload(work)
engine.dispose()
'''
    measured=subprocess.run([str(py),'-c',code],cwd=ROOT,env=env,capture_output=True,timeout=30)
    assert measured.returncode==0,'D5 real parser/receipt processing failed (output withheld)'
    receipts=sql('SELECT * FROM d5_file_measurement WHERE upload_file_id=:id',{'id':file_id})
    assert len(receipts)==1 and receipts[0]['measured_format']=='npy'
    registered=register(registration,upload)
    assert registered.status_code==201
    key=SourceKey(lab_id=record['lab_id'],dataset_id=registered.json()['datasetId'],source_kind='file',source_id=file_id)
    status,made=request(core_url+'/internal/knowledge/source/issue',{'source_key':key.model_dump()},headers(issued.token))
    assert status==200
    assert [(f['predicate'],f['value'],f['evidence_kind']) for f in made['command']['facts']]==[('format','npy','file_measurement')]
    status,receipt=request(ai_url+'/internal/knowledge/replace',made,headers(issued.token,'dedicated-writer'))
    assert status==200
    with scoped(session_factory,account=account) as db:
        claim=next(c for c in changes.claim(db,limit=100,authorized_only=True) if c.source_kind=='file' and c.source_id==file_id)
    projector=KnowledgeProjector(session_factory,client.app.state.login_sessions,client.app.state.database_credentials,
        base_url=ai_url,reader_token='dedicated-reader',timeout=2)
    assert projector.apply(claim,receipt['receipt_id'],session_token=issued.token)['status']=='applied'
    rows=sql("SELECT facts,extractor_version FROM d3_search_fact_snapshot WHERE source_kind='file' AND source_id=:id",{'id':file_id})
    assert len(rows)==1 and rows[0]['extractor_version']=='file-measurement-v1'
    assert [(f['predicate'],f['value']) for f in rows[0]['facts']]==[('format','npy')]
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:dataset,:lab,'잠김')
      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'dataset':key.dataset_id,'lab':key.lab_id})
    with pytest.raises(ValueError,match='forbidden'):
        projector.apply(claim,receipt['receipt_id'],session_token=issued.token)
    sql("UPDATE d2_dataset_access SET state='열림' WHERE dataset_id=:id",{'id':key.dataset_id})
    from conftest import TOKEN_RES,auth
    from colab_core.app.main import API_PREFIX
    added=registration.post(f'{API_PREFIX}/datasets/{key.dataset_id}/files',
        files={'file':('remaining.npy',payload,'application/octet-stream')},data={'kind':'본체'},headers=auth(TOKEN_RES))
    assert added.status_code==201
    # Dispose this fixture account's private grants while the source remains visible.
    # The later body-free deletion must not depend on retaining the human grant.
    sql('DELETE FROM d3_knowledge_grant WHERE account_id=:account AND source_id=:file',
        {'account':account,'file':file_id},account_id=account)
    deleted=registration.delete(f'{API_PREFIX}/datasets/{key.dataset_id}/files/{file_id}',headers=auth(TOKEN_RES))
    assert deleted.status_code==204
    assert sql('SELECT file_id FROM d3_file_measurement WHERE file_id=:id',{'id':file_id})==[]
    revision=sql("SELECT requested_version FROM d3_search_change WHERE source_kind='file' AND source_id=:id",{'id':file_id})[0]['requested_version']
    client.app.state.login_sessions.revoke(issued.session_id)
    deletion_auth={'Authorization':'Bearer '+DELETION}
    status,tombstone=request(core_url+'/internal/knowledge/deletion/issue',
        {'source_key':key.model_dump(),'expected_revision':revision},deletion_auth)
    assert status==200
    status,invalidated=request(ai_url+'/internal/knowledge/invalidate',{'command':tombstone},deletion_auth)
    assert status==200 and invalidated['status']=='invalidated'
    with pytest.raises(ValueError,match='forbidden'):
        projector.apply(claim,receipt['receipt_id'],session_token=issued.token)


def test_projection_roundtrip_recovers_committed_receipt_and_reauthenticates(roundtrip,session_factory,sql,monkeypatch):
    from colab_core.app.knowledge_projector import KnowledgeProjector
    from colab_core.app.knowledge_client import KnowledgeHttpClient
    from colab_core.domains import d3_search_changes as changes
    client,key,issued,account,core_url,ai_url,_=roundtrip
    status,made=request(core_url+'/internal/knowledge/source/issue',{'source_key':key.model_dump()},headers(issued.token))
    assert status==200
    status,receipt=request(ai_url+'/internal/knowledge/replace',made,headers(issued.token,'dedicated-writer'))
    assert status==200
    with scoped(session_factory,account=account) as db:
        abandoned=next(c for c in changes.claim(db,limit=100) if c.source_kind=='evidence' and c.source_id==key.source_id)
    # Process loss after D9 commit, before any local projection; same receipt survives.
    sql("UPDATE d3_search_change SET lease_until=clock_timestamp()-interval '1 second' WHERE source_kind='evidence' AND source_id=:id",{'id':key.source_id})
    with scoped(session_factory,account=account) as db:
        fresh=next(c for c in changes.claim(db,limit=100) if c.source_kind=='evidence' and c.source_id==key.source_id)
    assert fresh.lease_generation==abandoned.lease_generation+1
    assert not sql('SELECT * FROM d3_knowledge_projection')
    projector=KnowledgeProjector(session_factory,client.app.state.login_sessions,client.app.state.database_credentials,
        base_url=ai_url,reader_token='dedicated-reader',timeout=2)
    original=KnowledgeHttpClient.read
    def unlocked_read(self,*args,**kwargs):
        with scoped(session_factory,account=account) as db:
            assert db.execute(text("SELECT pg_try_advisory_xact_lock(hashtextextended('ontology:'||:lab,0))"),{'lab':key.lab_id}).scalar_one()
            assert db.execute(text("SELECT 1 FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id FOR UPDATE NOWAIT"),{'id':key.source_id}).scalar_one()==1
        return original(self,*args,**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(KnowledgeHttpClient,'read',unlocked_read)
        result=projector.apply(fresh,receipt['receipt_id'],session_token=issued.token)
    assert result['status']=='applied'
    ledger=sql('SELECT * FROM d3_knowledge_projection')
    assert len(ledger)==1 and ledger[0]['receipt_id']==receipt['receipt_id']
    assert ledger[0]['snapshot_id']==result['fact_id']
    assert projector.apply(fresh,receipt['receipt_id'],session_token=issued.token)['status']=='already_applied'
    def logout_after_http(self,*args,**kwargs):
        body=original(self,*args,**kwargs)
        client.app.state.login_sessions.revoke(issued.session_id)
        return body
    with monkeypatch.context() as patch:
        patch.setattr(KnowledgeHttpClient,'read',logout_after_http)
        with pytest.raises(ValueError,match='forbidden'):
            projector.apply(fresh,receipt['receipt_id'],session_token=issued.token)
    assert ledger==sql('SELECT * FROM d3_knowledge_projection')


def request(url,payload=None,headers=None):
    req=Request(url,data=None if payload is None else json.dumps(payload).encode(),
                headers={'Content-Type':'application/json',**(headers or {})})
    try:
        with urlopen(req,timeout=5) as response:return response.status,json.load(response)
    except HTTPError as exc:
        with exc:return exc.code,json.load(exc)


@pytest.fixture
def roundtrip(connected,session_factory):
    client,key,issued,account=connected
    py=ROOT/'services/ai-service/.venv/bin/python'
    if not py.is_file():pytest.fail('AI Python environment missing; roundtrip not executed')
    # The helper owns only its newly created tmpfs container and trap cleanup.
    script='''set -e
source gates/tools/_pg.sh
pg_start knowledge-http-roundtrip || exit 78
trap pg_cleanup EXIT
docker exec "$PGC" createdb -U postgres knowledge_http
CONTAINER="$PGC" DB=knowledge_http bash services/ai-service/tests/fixtures/setup-db.sh
read -r finish
'''
    dbproc=subprocess.Popen(['bash','-c',script],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    engine=server=server_thread=ai=core_socket=ai_socket=None
    try:
        # setup-db emits exactly its disposable read URL, captured not logged.
        line=dbproc.stdout.readline().strip()
        if not line.startswith('postgresql+psycopg://'):pytest.fail('disposable AI setup unavailable')
        read_url=make_url(line)
        writer_url=read_url.set(username='colab_knowledge_writer',password='knowledge-test-only')
        # Read the actual D9 manifest in its own interpreter; no core import of AI.
        loaded=subprocess.run([str(py),'-c',
            'import os,json;from sqlalchemy import create_engine;from colab_ai.app.ontology_manifest import load_manifest;e=create_engine(os.environ["COLAB_AI_DB_URL"]);print(json.dumps(load_manifest(e)));e.dispose()'],
            cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'services/ai-service/src'),'COLAB_AI_DB_URL':line},capture_output=True,text=True)
        if loaded.returncode:pytest.fail('AI manifest read failed')
        manifest=json.loads(loaded.stdout)
        with scoped(session_factory) as session:
            previous=d3_search_ontology.current_manifest(session)
            d3_search_ontology.publish(session,manifest,expected_previous=previous['version'])
        core_socket=socket.socket();core_socket.bind(('127.0.0.1',0));core_socket.listen()
        core_url='http://127.0.0.1:'+str(core_socket.getsockname()[1])
        server=uvicorn.Server(uvicorn.Config(client.app,log_level='critical',access_log=False))
        server_thread=Thread(target=lambda:server.run(sockets=[core_socket]),daemon=True);server_thread.start()
        ai_socket=socket.socket();ai_socket.bind(('127.0.0.1',0));ai_socket.listen()
        ai_url='http://127.0.0.1:'+str(ai_socket.getsockname()[1])
        env={k:v for k,v in os.environ.items() if not k.startswith(('COLAB_','OPENAI_','ANTHROPIC_'))}
        env.update(PYTHONPATH=str(ROOT/'services/ai-service/src'),COLAB_KNOWLEDGE_ENABLED='true',
            COLAB_AI_KNOWLEDGE_WRITER_DB_URL=writer_url.render_as_string(hide_password=False),
            COLAB_KNOWLEDGE_WRITER_TOKEN='dedicated-writer',COLAB_KNOWLEDGE_READER_TOKEN='dedicated-reader',COLAB_KNOWLEDGE_CALLBACK_TOKEN=CALLBACK,
            COLAB_AI_SERVICE_TOKEN=READ,COLAB_KNOWLEDGE_SOURCE_URL=core_url,COLAB_KNOWLEDGE_TIMEOUT_SECONDS='2',
            COLAB_KNOWLEDGE_DELETION_TOKEN=DELETION,COLAB_KNOWLEDGE_DELETION_LAB=key.lab_id,
            COLAB_KNOWLEDGE_DELETION_ENABLED='true')
        ai=subprocess.Popen([str(py),'-m','uvicorn','colab_ai.app.knowledge_app:create_app','--factory','--fd',str(ai_socket.fileno()),
            '--log-level','critical','--no-access-log'],cwd=ROOT,env=env,pass_fds=(ai_socket.fileno(),),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            if ai.poll() is not None:pytest.fail('dedicated AI entrypoint startup failed')
            try:
                if server.started and request(ai_url+'/healthz')[0]==200:break
            except (URLError,TimeoutError):pass
            time.sleep(.05)
        else:pytest.fail('loopback services did not become ready')
        engine=create_engine(writer_url)
        yield client,key,issued,account,core_url,ai_url,engine
    finally:
        if ai is not None:
            ai.terminate()
            try:ai.wait(timeout=10)
            except subprocess.TimeoutExpired:ai.kill();ai.wait(timeout=5)
        if server is not None:server.should_exit=True
        if server_thread is not None:server_thread.join(timeout=10)
        for sock in (core_socket,ai_socket):
            if sock is not None:sock.close()
        if engine is not None:engine.dispose()
        try:dbproc.communicate('finish\n',timeout=15)
        except subprocess.TimeoutExpired:
            dbproc.terminate();dbproc.wait(timeout=15)


def test_deletion_roundtrip_survives_logout_and_denies_other_capabilities(roundtrip,sql,monkeypatch):
    client,key,issued,account,core_url,ai_url,engine=roundtrip
    status,made=request(core_url+'/internal/knowledge/source/issue',{'source_key':key.model_dump()},headers(issued.token))
    assert status==200
    assert request(ai_url+'/internal/knowledge/replace',made,headers(issued.token,'dedicated-writer'))[0]==200
    # The original human grant is unnecessary for disposal and may be gone.
    sql('DELETE FROM d3_knowledge_grant WHERE account_id=:id',{'id':account},account_id=account)
    sql('DELETE FROM d3_file WHERE id=:id',{'id':key.source_id})
    revision=sql("SELECT requested_version FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id",{'id':key.source_id})[0]['requested_version']
    client.app.state.login_sessions.revoke(issued.session_id)
    auth={'Authorization':'Bearer '+DELETION}
    def unavailable(*args,**kwargs):raise AssertionError('deletion accessed user/ontology/body')
    monkeypatch.setattr(client.app.state.login_sessions,'authenticate',unavailable)
    monkeypatch.setattr(d3_search_ontology,'current_manifest',unavailable)
    status,deletion=request(core_url+'/internal/knowledge/deletion/issue',
                            {'source_key':key.model_dump(),'expected_revision':revision},auth)
    assert status==200
    target=ai_url+'/internal/knowledge/invalidate'
    status,receipt=request(target,{'command':deletion},auth)
    assert status==200 and receipt['status']=='invalidated' and receipt['publication_sequence']==2
    assert request(target,{'command':deletion},auth)==(200,receipt)
    for base,path in ((core_url,'source/issue'),(core_url,'source/read'),(core_url,'source/validate'),
                      (ai_url,'replace'),(ai_url,'read')):
        assert request(base+'/internal/knowledge/'+path,{},auth)[0]==401
    for wrong in (CALLBACK,READ,'dedicated-writer','dedicated-reader'):
        assert request(target,{'command':deletion},{'Authorization':'Bearer '+wrong})[0]==401
        assert request(core_url+'/internal/knowledge/deletion/issue',{}, {'Authorization':'Bearer '+wrong})[0]==401
    with engine.begin() as session:
        for field,value in key.model_dump().items():
            session.execute(text('SELECT set_config(:key,:value,true)'),{'key':'knowledge.'+field,'value':value})
        body=session.execute(text('SELECT payload FROM knowledge.d9_knowledge_source')).scalar_one()
        assert body=={k:v for k,v in deletion.items() if k!='grant'}


def test_authenticated_roundtrip_replay_forgery_and_logout(roundtrip,monkeypatch,sql):
    client,key,issued,account,core_url,ai_url,engine=roundtrip
    status,made=request(core_url+'/internal/knowledge/source/issue',{'source_key':key.model_dump()},headers(issued.token))
    assert status==200
    target=ai_url+'/internal/knowledge/replace'
    auth=headers(issued.token,'dedicated-writer')
    def unavailable(*args):raise RuntimeError('test dependency outage')
    with monkeypatch.context() as patch:
        patch.setattr(client.app.state.knowledge_source,'validate',unavailable)
        assert request(target,made,auth)[0]==503
    with engine.begin() as session:
        for field,value in key.model_dump().items():
            session.execute(text('SELECT set_config(:key,:value,true)'),{'key':'knowledge.'+field,'value':value})
        assert session.execute(text('SELECT count(*) FROM knowledge.d9_knowledge_source')).scalar_one()==0
    status,receipt=request(target,made,auth)
    assert status==200 and receipt['publication_sequence']==1
    status,replay=request(target,made,auth)
    assert status==200 and replay==receipt
    forged=json.loads(json.dumps(made));forged['principal']['account_id']='00000000000000000000000AP1'
    assert request(target,forged,auth)[0]==403
    forged['principal']['lab_id']='0000000000000000000000000B'
    assert request(target,forged,auth)[0]==403
    for wrong in (CALLBACK,READ):assert request(target,made,headers(issued.token,wrong))[0]==401
    assert request(target,{**made,'authority_url':'http://127.0.0.1:1'},auth)[0]==422
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':key.dataset_id,'lab':key.lab_id})
    assert request(target,made,auth)[0]==403
    client.app.state.login_sessions.revoke(issued.session_id)
    assert request(target,made,auth)[0]==403
    # Rejected requests did not alter the one existing scoped record.
    with engine.begin() as session:
        for field,value in key.model_dump().items():
            session.execute(text('SELECT set_config(:key,:value,true)'),{'key':'knowledge.'+field,'value':value})
        assert session.execute(text('SELECT count(*) FROM knowledge.d9_knowledge_source')).scalar_one()==1
        assert session.execute(text('SELECT publication_sequence FROM knowledge.d9_knowledge_source')).scalar_one()==1


def test_current_other_viewer_reads_expired_grant_and_denials(roundtrip,sql,monkeypatch):
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.auth import Subject
    client,key,issued,account,core_url,ai_url,engine=roundtrip
    status,made=request(core_url+'/internal/knowledge/source/issue',{'source_key':key.model_dump()},headers(issued.token))
    assert status==200
    status,receipt=request(ai_url+'/internal/knowledge/replace',made,headers(issued.token,'dedicated-writer'))
    assert status==200
    viewer=str(Ulid.generate())
    sql("INSERT INTO d1_account(id,lab_id,name,email) VALUES (:id,:lab,'reader',:email)",
        {'id':viewer,'lab':key.lab_id,'email':viewer+'@example.test'})
    session=None
    try:
        with client.app.state.account_admin_factory.begin() as db:
            db.execute(text("""INSERT INTO account_admin.login_credential
              (account_id,login_name,kdf,salt,password_hash,n,r,p,must_change_password,session_version,status)
              VALUES (:id,:name,'scrypt','00','00',16384,8,1,false,1,'active')"""),{'id':viewer,'name':viewer.lower()})
        session=client.app.state.login_sessions.issue(Subject(Ulid(viewer),Ulid(key.lab_id)),
            credential_kind='database',credential_version=1,purpose='normal')
        sql("UPDATE d3_knowledge_grant SET expires_at=clock_timestamp()-interval '1 second' WHERE account_id=:id",
            {'id':account},account_id=account)
        before=sql('SELECT generation,command FROM d3_knowledge_source WHERE source_id=:id',{'id':key.source_id})
        grants=sql('SELECT * FROM d3_knowledge_grant WHERE account_id=:id',{'id':account},account_id=account)
        target=ai_url+'/internal/knowledge/read'
        body={'source_key':key.model_dump(),'expected_receipt_id':receipt['receipt_id']}
        auth=headers(session.token,'dedicated-reader')
        status,result=request(target,body,auth)
        assert status==200 and result['receipt']==receipt
        assert result['payload']=={k:v for k,v in made['command'].items() if k!='grant'}
        assert viewer!=account and 'grant' not in result['payload']
        assert before==sql('SELECT generation,command FROM d3_knowledge_source WHERE source_id=:id',{'id':key.source_id})
        assert grants==sql('SELECT * FROM d3_knowledge_grant WHERE account_id=:id',{'id':account},account_id=account)
        for wrong in (READ,CALLBACK,'dedicated-writer'):
            assert request(target,body,headers(session.token,wrong))[0]==401
        assert request(ai_url+'/internal/knowledge/replace',made,auth)[0]==401
        assert request(target,{**body,'expected_receipt_id':'4'*26},auth)[0]==403
        assert request(target,{**body,'principal':made['principal']},auth)[0]==422
        other={**body,'source_key':{**body['source_key'],'lab_id':'0000000000000000000000000B'}}
        assert request(target,other,auth)[0]==403
        def unavailable(*args):raise RuntimeError('test unavailable')
        with monkeypatch.context() as patch:
            patch.setattr(client.app.state.knowledge_source,'authorize_read',unavailable)
            assert request(target,body,auth)[0]==503
        sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
          ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""",{'id':key.dataset_id,'lab':key.lab_id})
        assert request(target,body,auth)[0]==403
        sql("UPDATE d2_dataset_access SET state='열림' WHERE dataset_id=:id",{'id':key.dataset_id})
        for assignment,restore in [('must_change_password=true','must_change_password=false'),
                                   ('session_version=2','session_version=1'),("status='inactive'","status='active'")]:
            with client.app.state.account_admin_factory.begin() as db:
                db.execute(text('UPDATE account_admin.login_credential SET '+assignment+' WHERE account_id=:id'),{'id':viewer})
            assert request(target,body,auth)[0]==403
            with client.app.state.account_admin_factory.begin() as db:
                db.execute(text('UPDATE account_admin.login_credential SET '+restore+' WHERE account_id=:id'),{'id':viewer})
        sql('UPDATE d3_search_evidence SET revision=revision+1 WHERE file_id=:id',{'id':key.source_id})
        assert request(target,body,auth)[0]==409
        client.app.state.login_sessions.revoke(session.session_id)
        assert request(target,body,auth)[0]==403
        with engine.begin() as db:
            for field,value in key.model_dump().items():
                db.execute(text('SELECT set_config(:key,:value,true)'),{'key':'knowledge.'+field,'value':value})
            assert db.execute(text('SELECT receipt FROM knowledge.d9_knowledge_source')).scalar_one()==receipt
    finally:
        if session is not None:client.app.state.login_sessions.revoke(session.session_id)
        sql('DELETE FROM d1_account WHERE id=:id',{'id':viewer})
