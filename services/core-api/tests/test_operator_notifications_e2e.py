from conftest import TOKEN_RES, auth
from colab_core.app.main import API_PREFIX

def test_project_api_commits_creation_and_deletion_snapshots(live_client, sql):
    client=live_client
    created=client.post(API_PREFIX+"/projects",json={"type":"국가과제","name":"운영 감사 E2E"},headers=auth(TOKEN_RES))
    assert created.status_code==201,created.text
    project_id=created.json()["projectId"]
    rows=sql("SELECT action,before_snapshot,after_snapshot FROM d6_operator_audit WHERE target_id=:id ORDER BY occurred_at,source_id",{"id":project_id})
    assert [row["action"] for row in rows]==["project.created"]
    assert rows[0]["after_snapshot"]["name"]=="운영 감사 E2E"
    deleted=client.delete(API_PREFIX+f"/projects/{project_id}",headers=auth(TOKEN_RES))
    assert deleted.status_code==204,deleted.text
    rows=sql("SELECT action,before_snapshot,after_snapshot FROM d6_operator_audit WHERE target_id=:id ORDER BY occurred_at,source_id",{"id":project_id})
    assert [row["action"] for row in rows]==["project.created","project.deleted"]
    assert rows[1]["before_snapshot"]["name"]=="운영 감사 E2E"
    pending=sql("SELECT count(*) AS n FROM d6_operator_export WHERE payload->>'target_id'=:id AND receipt_hash IS NULL",{"id":project_id})
    assert pending[0]["n"]==2

import datetime as dt
import json
import pathlib
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from conftest import LAB_A, LAB_B, ACC_A_RES, TOKEN_B

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

@pytest.fixture
def operator_engine(app_db_url):
    engine = create_engine(make_url(app_db_url).set(username='colab_operator_test_exporter'))
    yield engine
    engine.dispose()

@pytest.fixture
def remote():
    from scripts.tests.test_operator_aws_runtime import DynamoSDK
    from infra.notifications.aws_store import DynamoStore
    return DynamoStore(DynamoSDK(), 'operator-test')

@pytest.fixture
def sinks():
    posts = {'development': [], 'activity': []}
    servers = []
    urls = {}
    for channel in posts:
        def handler_for(destination):
            class Handler(BaseHTTPRequestHandler):
                def do_POST(self):
                    posts[destination].append(json.loads(self.rfile.read(int(self.headers['Content-Length'])))['text'])
                    self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
                def log_message(self, *args): pass
            return Handler
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(channel))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server); urls[channel] = f'http://127.0.0.1:{server.server_port}/'
    yield posts, urls
    for server in servers: server.shutdown(); server.server_close()

def test_export_requires_explicit_lab_scope(session_factory):
    from ops.operator_audit_export import ADAPTERS
    for adapter in ADAPTERS.values():
        with session_factory() as session:
            with pytest.raises(ValueError, match='scope'):
                adapter.pending_exports(session)

def test_export_rejects_application_role(app_db_url, remote):
    from ops.operator_audit_export import sync
    engine = create_engine(app_db_url)
    try:
        with pytest.raises(ValueError, match='role'):
            sync(engine, remote)
    finally: engine.dispose()

def test_two_labs_api_export_daily_reaches_only_activity(live_client, sql, operator_engine, remote, sinks):
    from ops.operator_audit_export import sync
    from infra.notifications.aws_store import DynamoArchive
    from infra.notifications import jobs
    from infra.notifications.delivery import process
    from infra.notifications.http_sender import HttpSender
    for token, name in [(TOKEN_RES, '일일보고 연구실 A'), (TOKEN_B, '일일보고 연구실 B')]:
        response = live_client.post(API_PREFIX+'/projects', json={'type':'국가과제','name':name}, headers=auth(token))
        assert response.status_code == 201, response.text
        response = live_client.delete(API_PREFIX+'/projects/'+response.json()['projectId'], headers=auth(token))
        assert response.status_code == 204
    assert sync(operator_engine, remote) >= 4
    archive = DynamoArchive(remote)
    collection = archive.snapshot()['collection']
    assert collection['status'] == 'complete'
    assert {lab['id'] for lab in collection['labs']} >= {LAB_A, LAB_B}
    assert len(collection['sources']) == 5 * len(collection['labs'])
    assert all(source['pending'] == 0 for source in collection['sources'])
    assert sync(operator_engine, remote) == 0
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    day = now.date()
    report_at = dt.datetime.combine(day+dt.timedelta(days=1), dt.time(8), now.tzinfo)
    # The injected collection clock models the next successful minute after midnight.
    collection['collected_at'] = report_at.isoformat(); archive.record_collection(collection)
    manifest = {'environment':'dev','usage':'live','sources':['d2','d3','d5','d6','d8'],
        'coverage_started_at':dt.datetime.combine(day,dt.time(),now.tzinfo).isoformat(),
        'test_exclusions':{'lab_ids':[],'account_ids':[],'effective_at':dt.datetime.combine(day,dt.time(),now.tzinfo).isoformat()}}
    assert jobs.run(report_at-dt.timedelta(seconds=1), manifest, archive) == []
    parts = jobs.run(report_at, manifest, archive); assert parts
    jobs.publish(parts, manifest, archive, remote)
    posts, urls = sinks
    sender = HttpSender(urls, local_only=True)
    for i, event_id in enumerate(remote.due(report_at)):
        assert process(event_id, remote, sender, report_at+dt.timedelta(seconds=i*2)) == 'sent'
    jobs.reconcile(archive, remote)
    assert not posts['development']
    body = '\n'.join(posts['activity'])
    assert '일일보고 연구실 A' in body and '일일보고 연구실 B' in body
    assert LAB_A in body and LAB_B in body
    assert '집계 완료' in body
    assert jobs.run(report_at, manifest, archive) == []
    assert archive.snapshot()['reports'][day.isoformat()]['complete']

def test_dataset_purge_requires_actor_and_retains_snapshot(p2_client, sql, app_db_url, tmp_path):
    from test_download import _dataset
    from ops.purge_datasets import main
    client = p2_client(session_secret='operator-test')
    dataset_id, _ = _dataset(client, name='삭제 후에도 남는 이름')
    url_file = tmp_path/'db.url'
    url_file.write_text(app_db_url); url_file.chmod(0o600)
    args=['--db-url-file',str(url_file),'--lab',LAB_A,'--id',dataset_id,'--yes-delete']
    assert main(args) == 2
    assert sql('SELECT id FROM d3_dataset WHERE id=:id', {'id':dataset_id})
    assert main(args+['--actor-id',ACC_A_RES]) == 0
    assert not sql('SELECT id FROM d3_dataset WHERE id=:id', {'id':dataset_id})
    rows=sql("SELECT before_snapshot,after_snapshot FROM d3_operator_audit WHERE target_id=:id AND action='dataset.deleted'", {'id':dataset_id})
    assert len(rows)==1 and rows[0]['before_snapshot']['name']=='삭제 후에도 남는 이름'
    assert rows[0]['after_snapshot'] is None
    assert sql("SELECT source_id FROM d3_operator_export WHERE payload->>'target_id'=:id AND payload->>'action'='dataset.deleted'", {'id':dataset_id})

def test_committed_snapshot_exports_but_rollback_does_not(session_factory, operator_engine, remote):
    from conftest import scoped_ro
    from colab_core.domains.d3_audit import append_snapshot
    from ops.operator_audit_export import sync
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        source=append_snapshot(session,actor_id=ACC_A_RES,target_id=LAB_A,action='dataset.updated',before={},after={'name':'rolled back'})
    sync(operator_engine, remote)
    assert remote._read('audit#'+source)[0] is None

def test_source_failure_is_incomplete_and_retains_unacked_rows(live_client, sql, operator_engine, remote, monkeypatch):
    from ops.operator_audit_export import sync
    from infra.notifications.aws_store import DynamoArchive
    created=live_client.post(API_PREFIX+'/projects',json={'type':'국가과제','name':'원격 접수 실패'},headers=auth(TOKEN_RES))
    assert created.status_code==201
    target=created.json()['projectId']
    original=remote.accept_archive
    def fail_target(row):
        if row['target_id']==target: raise OSError('remote unavailable')
        return original(row)
    monkeypatch.setattr(remote,'accept_archive',fail_target)
    with pytest.raises(RuntimeError,match='incomplete'): sync(operator_engine,remote)
    assert DynamoArchive(remote).snapshot()['collection']['status']=='partial'
    assert sql("SELECT source_id FROM d6_operator_export WHERE payload->>'target_id'=:id AND receipt_hash IS NULL",{'id':target})
    monkeypatch.setattr(remote,'accept_archive',original)
    assert sync(operator_engine,remote)>=1
    assert DynamoArchive(remote).snapshot()['collection']['status']=='complete'

def test_upload_metadata_download_and_approval_snapshots(p2_client, live_client, sql):
    from test_download import _dataset
    from conftest import DS_A2, TOKEN_PROF
    client=p2_client(session_secret='operator-test')
    target,_=_dataset(client,name='업로드 감사')
    changed=client.patch(API_PREFIX+'/datasets/'+target,json={'name':'변경된 이름','summary':'새 요약'},headers=auth(TOKEN_RES))
    assert changed.status_code==200,changed.text
    ticket=client.get(API_PREFIX+'/datasets/'+target+'/download',headers=auth(TOKEN_RES))
    assert ticket.status_code==200
    updated=sql("SELECT before_snapshot,after_snapshot FROM d3_operator_audit WHERE target_id=:id AND action='dataset.updated'",{'id':target})
    assert updated[-1]['before_snapshot']['name']=='업로드 감사'
    assert updated[-1]['after_snapshot']['name']=='변경된 이름'
    assert sql("SELECT source_id FROM d8_operator_export WHERE payload->>'target_id'=:id AND payload->>'action'='download.ticket_issued'",{'id':target})
    requested=live_client.post(API_PREFIX+f'/datasets/{DS_A2}/access-requests',headers=auth(TOKEN_RES))
    assert requested.status_code==201,requested.text
    request_id=requested.json()['requestId']
    approved=live_client.post(API_PREFIX+f'/access-requests/{request_id}/approval',headers=auth(TOKEN_PROF))
    assert approved.status_code==200,approved.text
    rows=sql("SELECT source_id,before_snapshot,after_snapshot FROM d2_operator_audit WHERE action='access.approved' ORDER BY occurred_at DESC,source_id DESC LIMIT 1")
    assert rows
    original=rows[0]
    sql("UPDATE d2_dataset_access_grant SET expires_at=approved_at+interval '1 day' WHERE dataset_id=:id",{'id':DS_A2})
    saved=sql('SELECT before_snapshot,after_snapshot FROM d2_operator_audit WHERE source_id=:id',{'id':original['source_id']})[0]
    assert saved['after_snapshot']==original['after_snapshot']

def test_late_commit_over_two_days_corrects_original_report(session_factory, operator_engine, remote):
    from colab_core.domains.d3_audit import append_snapshot
    from colab_core.kernel.scope import apply_scope
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from ops.operator_audit_export import sync
    from infra.notifications.aws_store import DynamoArchive
    from infra.notifications import jobs
    from infra.notifications.delivery import process
    now=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).replace(hour=9)
    at=now-dt.timedelta(days=3)
    start=at.replace(hour=0,minute=0,second=0,microsecond=0)
    manifest={'environment':'dev','usage':'live','sources':['d2','d3','d5','d6','d8'],
        'coverage_started_at':start.isoformat(),'test_exclusions':{'lab_ids':[],'account_ids':[],'effective_at':start.isoformat()}}
    with session_factory() as session:
        apply_scope(session,Subject(account_id=Ulid(ACC_A_RES),lab_id=Ulid(LAB_A)))
        source=append_snapshot(session,actor_id=ACC_A_RES,target_id=LAB_A,action='dataset.deleted',before={'name':'늦게 확정된 삭제'},after=None,occurred_at=at)
        sync(operator_engine,remote)
        assert remote._read('audit#'+source)[0] is None
        archive=DynamoArchive(remote)
        first=jobs.run(now,manifest,archive); jobs.publish(first,manifest,archive,remote)
        for i,identity in enumerate(remote.due(now)):
            process(identity,remote,lambda *a:(200,'ok',None),now+dt.timedelta(seconds=i*2))
        jobs.reconcile(archive,remote)
        session.commit()
    assert sync(operator_engine,remote)>=1
    corrected=jobs.run(now,manifest,DynamoArchive(remote))
    original_day=[p for p in corrected if p['report_date']==at.date().isoformat()]
    assert original_day and original_day[0]['revision']==2
    assert '늦게 확정된 삭제' in '\n'.join(p['text'] for p in original_day)

def test_export_drains_multiple_pages_without_timestamp_watermark(session_factory, operator_engine, remote):
    from colab_core.domains.d3_audit import append_snapshot
    from colab_core.kernel.scope import apply_scope
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from ops.operator_audit_export import sync
    sources=[]
    with session_factory() as session,session.begin():
        apply_scope(session,Subject(account_id=Ulid(ACC_A_RES),lab_id=Ulid(LAB_A)))
        for index in range(501):
            sources.append(append_snapshot(session,actor_id=ACC_A_RES,target_id=LAB_A,action='dataset.updated',before={},after={'name':f'page-{index}'}))
    assert sync(operator_engine,remote)>=501
    assert all(remote._read('audit#'+source)[0] for source in sources)
    assert sync(operator_engine,remote)==0

def test_permission_snapshot_uses_effective_default(session_factory):
    from conftest import scoped_ro, ACC_A_PROF
    from colab_core.domains.d2_access import apply_switch
    from colab_core.kernel.ids import Ulid
    with scoped_ro(session_factory,ACC_A_PROF,LAB_A) as session:
        session.execute(text("DELETE FROM d2_permission_switch WHERE account_id=:id AND switch='승인 위임'"),{'id':ACC_A_RES})
        apply_switch(session,actor_id=Ulid(ACC_A_PROF),target_id=Ulid(ACC_A_RES),switch='승인 위임',enabled=True)
        snapshot=session.execute(text("SELECT before_snapshot,after_snapshot FROM d2_operator_audit WHERE action='permission.changed' AND target_id=:id ORDER BY occurred_at DESC,source_id DESC LIMIT 1"),{'id':ACC_A_RES}).mappings().one()
        assert snapshot['before_snapshot']['enabled'] is False
        assert snapshot['after_snapshot']['enabled'] is True

def test_rejection_audit_is_committed_only_after_valid_decision(live_client, sql):
    from conftest import DS_A2, TOKEN_PROF
    requested=live_client.post(API_PREFIX+f'/datasets/{DS_A2}/access-requests',headers=auth(TOKEN_RES))
    assert requested.status_code==201
    request_id=requested.json()['requestId']
    url=API_PREFIX+f'/access-requests/{request_id}/rejection'
    assert live_client.post(url,json={'reason':''},headers=auth(TOKEN_PROF)).status_code==400
    query="SELECT after_snapshot FROM d2_operator_audit WHERE action='access.rejected' AND after_snapshot->>'request_id'=:id"
    assert not sql(query,{'id':request_id})
    assert live_client.post(url,json={'reason':'대상 확인 필요'},headers=auth(TOKEN_PROF)).status_code==204
    rows=sql(query,{'id':request_id})
    assert len(rows)==1 and rows[0]['after_snapshot']['state']=='거절됨'

def test_test_actor_exclusion_applies_to_actual_exported_activity(live_client, sql, operator_engine, remote):
    from ops.operator_audit_export import sync
    from infra.notifications.aws_store import DynamoArchive
    from infra.notifications.digest import build
    response=live_client.post(API_PREFIX+'/projects',json={'type':'국가과제','name':'제외할 시험 사용자'},headers=auth(TOKEN_RES))
    assert response.status_code==201
    target=response.json()['projectId']
    assert live_client.delete(API_PREFIX+'/projects/'+target,headers=auth(TOKEN_RES)).status_code==204
    sync(operator_engine,remote)
    now=dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    start=now.replace(hour=0,minute=0,second=0,microsecond=0)
    manifest={'environment':'dev','usage':'live','sources':['d2','d3','d5','d6','d8'],'coverage_started_at':start.isoformat(),
        'test_exclusions':{'lab_ids':[],'account_ids':[ACC_A_RES],'effective_at':start.isoformat()}}
    parts=build(now.date().isoformat(),manifest,DynamoArchive(remote))
    body='\n'.join(p['text'] for p in parts)
    assert '제외할 시험 사용자' not in body
    assert ACC_A_RES not in body
