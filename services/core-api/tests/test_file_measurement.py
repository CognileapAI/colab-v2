"""Registration binds canonical D5 proof to verified final bytes, not human metadata."""
import hashlib
import json
from functools import partial
import pytest

from conftest import LAB_A
from test_dataset_registration import make_upload, register
from test_search_changes import scoped
from test_search_ontology import manifest
from test_knowledge_source_authority import issue, validate, read_check, receipt_for
from colab_core.kernel.ids import Ulid
from colab_core.kernel.knowledge_wire import SourceKey
from colab_core.domains import d3_search_ontology, d4_lineage


def measured_upload(client, sql, *, mixed=False):
    body = b"\x93NUMPYmeasured-test-body"
    files=[("files", ("misleading.tif", body, "application/octet-stream"))]
    if mixed:
        files.append(("files",("unmeasured.tif",body,"application/octet-stream")))
    upload = make_upload(client, files=files)
    file_id = upload["files"][0]["fileId"]
    receipt_id = str(Ulid.generate())
    sql("""INSERT INTO d5_file_measurement
      (id,lab_id,upload_id,upload_file_id,parser_version,storage_key,source_digest,byte_size,measured_format)
      SELECT :receipt,lab_id,upload_id,id,'file-measurement-v1',storage_key,:digest,:size,'npy'
      FROM d5_upload_file WHERE id=:file""",
      {"receipt":receipt_id,"file":file_id,"digest":hashlib.sha256(body).hexdigest(),"size":len(body)})
    return upload, file_id, receipt_id


@pytest.fixture
def isolated_measurement_lab(p2_client, sql, tmp_path):
    """Static subjects are unit-test authority fixtures, not tracked HTTP sessions."""
    from conftest import TOKEN_RES
    from test_knowledge_source_authority import principal
    lab, account, viewer = (str(Ulid.generate()) for _ in range(3))
    sql("INSERT INTO d1_lab(id,name,opened_at) VALUES (:lab,'measurement isolation',now())", {'lab':lab})
    own_sql = partial(sql, lab_id=lab, account_id=account)
    own_sql("INSERT INTO d1_lab_profile(lab_id,default_visibility) VALUES (:lab,'열림')", {'lab':lab})
    for member in (account, viewer):
        own_sql("INSERT INTO d1_account(id,lab_id,name,email) VALUES (:id,:lab,'measurement viewer',:email)",
                {'id':member,'lab':lab,'email':member+'@example.invalid'})
        own_sql("INSERT INTO d2_member_role(account_id,lab_id,role) VALUES (:id,:lab,'교수')",
                {'id':member,'lab':lab})
    subjects = tmp_path / 'measurement-subjects.json'
    subjects.write_text(json.dumps({TOKEN_RES:{'accountId':account,'labId':lab}}))
    client = p2_client(subjects_file_override=str(subjects))
    return client, own_sql, principal(account,lab), principal(viewer,lab)


@pytest.mark.parametrize('preceding_other_lab', [0, 101])
def test_registration_binds_canonical_receipt_and_grants_only_measured_format(
        isolated_measurement_lab, sql, session_factory, preceding_other_lab):
    client, own_sql, who, viewer = isolated_measurement_lab
    # The production lease stays bounded at 100; other labs must not consume it.
    backlog_dataset = str(Ulid.generate())
    for _ in range(preceding_other_lab):
        sql("""INSERT INTO d3_search_change(lab_id,source_kind,source_id,dataset_id,deleted,retry_after)
          VALUES (:lab,'file',:id,:dataset,true,clock_timestamp()-interval '1 day')""",
          {'lab':LAB_A,'id':str(Ulid.generate()),'dataset':backlog_dataset})
    backlog_query = 'SELECT * FROM d3_search_change WHERE dataset_id=:id ORDER BY source_id'
    before = sql(backlog_query, {'id':backlog_dataset})
    assert len(before) == preceding_other_lab
    own_scope = partial(scoped, lab=who.lab_id, account=who.account_id)
    upload, file_id, receipt_id = measured_upload(client,own_sql)
    response = register(client,upload)
    assert response.status_code == 201, response.text
    dataset = response.json()["datasetId"]
    binding = own_sql("SELECT * FROM d3_file_measurement WHERE file_id=:file", {"file":file_id})
    assert len(binding) == 1 and binding[0]["receipt_id"] == receipt_id
    with own_scope(session_factory) as session:
        previous = d3_search_ontology.current_manifest(session)
        d3_search_ontology.publish(session,manifest(),expected_previous=previous["version"] if previous else None)
    key = SourceKey(lab_id=who.lab_id,dataset_id=dataset,source_kind="file",source_id=file_id)
    command = issue(session_factory,key,who)
    assert [(fact.predicate,fact.value,fact.evidence_kind) for fact in command.facts] == [
        ("format","npy","file_measurement")]
    assert command.mappings == []
    assert validate(session_factory,command,who) == "current"
    from colab_core.domains import d3_search_changes, d3_knowledge_projection, d3_search_facts
    from colab_core.kernel.knowledge_wire import AuthorizedKnowledge
    with own_scope(session_factory) as session:
        claims=d3_search_changes.claim(session,limit=100,authorized_only=True)
    assert all(item.lab_id == who.lab_id for item in claims)
    claim=next(item for item in claims if item.source_id==file_id and item.source_kind=='file')
    result=AuthorizedKnowledge(payload=command.model_dump(exclude={'grant'}),receipt=receipt_for(command))
    with own_scope(session_factory) as session:
        assert d3_knowledge_projection.apply(session,claim,result,who,
            lineage=d4_lineage.LineageRevisionAdapter(session))['status']=='applied'
        snapshots=d3_search_facts.read_current(session,dataset,extractor_version='file-measurement-v1')
    assert len(snapshots)==1
    assert [(fact['predicate'],fact['value']) for fact in snapshots[0]['facts']]==[('format','npy')]
    # Registration copied bounded canonical proof; later authorized viewers don't need D5 rows.
    own_sql("DELETE FROM d5_file_measurement WHERE id=:id", {"id":receipt_id})
    assert read_check(session_factory,receipt_for(command),viewer) == "current"
    own_sql("UPDATE d3_file SET storage_key=storage_key||'.replaced' WHERE id=:id", {"id":file_id})
    assert validate(session_factory,command,who) != "current"
    assert sql(backlog_query, {'id':backlog_dataset}) == before


def test_unmeasured_registration_does_not_invent_binding(p2_client,sql):
    client=p2_client()
    upload=make_upload(client)
    assert register(client,upload).status_code == 201
    assert sql("SELECT * FROM d3_file_measurement WHERE file_id=:file", {"file":upload["files"][0]["fileId"]}) == []


def test_registered_measurement_snapshot_is_immutable(p2_client,sql):
    from sqlalchemy.exc import IntegrityError
    client=p2_client()
    upload,file_id,_=measured_upload(client,sql)
    assert register(client,upload).status_code==201
    with pytest.raises(IntegrityError) as error:
        sql("UPDATE d3_file_measurement SET measured_format='tif' WHERE file_id=:id",{'id':file_id})
    assert error.value.orig.sqlstate=='23514'


def test_registration_digest_mismatch_rolls_back_dataset_and_preserves_source(p2_client,sql):
    from pathlib import Path
    client=p2_client()
    upload,file_id,_=measured_upload(client,sql)
    key=sql('SELECT storage_key FROM d5_upload_file WHERE id=:id',{'id':file_id})[0]['storage_key']
    path=Path(client.app.state.settings.upload_storage_dir)/key
    different=b'x'*path.stat().st_size
    path.write_bytes(different)
    assert register(client,upload).status_code==500
    assert path.read_bytes()==different
    assert sql('SELECT id FROM d3_file WHERE id=:id',{'id':file_id})==[]
    assert sql('SELECT file_id FROM d3_file_measurement WHERE file_id=:id',{'id':file_id})==[]
    assert sql('SELECT registered_at FROM d5_upload WHERE id=:id',{'id':upload['uploadId']})[0]['registered_at'] is None


@pytest.mark.parametrize('phase',['binding','activity','commit'])
@pytest.mark.parametrize('mixed',[False,True])
def test_database_failure_preserves_measured_original_and_retry_binding(p2_client,sql,monkeypatch,phase,mixed):
    from pathlib import Path
    from sqlalchemy.orm import Session
    from colab_core.domains import d3_file_measurement,d8_insight
    client=p2_client()
    upload,file_id,_=measured_upload(client,sql,mixed=mixed)
    key=sql('SELECT storage_key FROM d5_upload_file WHERE id=:id',{'id':file_id})[0]['storage_key']
    source=Path(client.app.state.settings.upload_storage_dir)/key
    original=source.read_bytes()
    paths=[Path(client.app.state.settings.upload_storage_dir)/row['storage_key'] for row in
           sql('SELECT storage_key FROM d5_upload_file WHERE upload_id=:id',{'id':upload['uploadId']})]
    def fail(*args,**kwargs):
        raise RuntimeError('injected database failure')
    with monkeypatch.context() as patch:
        if phase=='binding':
            patch.setattr(d3_file_measurement,'bind',fail)
        elif phase=='activity':
            patch.setattr(d8_insight,'record_activity',fail)
        else:
            patch.setattr(Session,'commit',fail)
        assert register(client,upload).status_code==500
    assert source.is_file(),'DB failure removed the only retryable source bytes'
    assert source.read_bytes()==original
    assert all(path.read_bytes()==original for path in paths)
    assert sql('SELECT id FROM d3_file WHERE id=:id',{'id':file_id})==[]
    retried=register(client,upload)
    assert retried.status_code==201
    assert len(sql('SELECT file_id FROM d3_file_measurement WHERE file_id=:id',{'id':file_id}))==1


@pytest.mark.parametrize('outcome',['commit','rollback','reused_root','nested_reservation'])
def test_registration_cleanup_is_owned_by_exact_outer_transaction(session_factory,monkeypatch,outcome):
    from types import SimpleNamespace
    from colab_core.app import deps
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.storage_backends import PreparedRegistration
    from conftest import ACC_A_RES
    session=session_factory()
    request=SimpleNamespace(headers={},app=SimpleNamespace(state=SimpleNamespace(session_factory=lambda:session)))
    monkeypatch.setattr(deps,'current_subject',lambda *args:Subject(Ulid(ACC_A_RES),Ulid(LAB_A)))
    called=[]
    gen=deps.registration_db(request)
    assert next(gen) is session
    prepared=PreparedRegistration(frozenset(),lambda:called.append('cleaned'))
    if outcome=='nested_reservation':
        with session.begin_nested(),pytest.raises(ValueError,match='root transaction'):
            deps.defer_registration_cleanup(session,prepared)
    else:
        deps.defer_registration_cleanup(session,prepared)
        with session.begin_nested():
            pass
    assert called==[]  # SAVEPOINT success is never registration commit.
    if outcome=='rollback':
        with pytest.raises(RuntimeError):
            gen.throw(RuntimeError('outer rollback'))
    elif outcome=='reused_root':
        session.rollback();session.begin()
        with pytest.raises(ValueError,match='root transaction changed'):
            next(gen)
    else:
        with pytest.raises(StopIteration):
            next(gen)
    assert called==(['cleaned'] if outcome=='commit' else [])
    called.clear()
    second=deps.registration_db(request)
    next(second)
    with pytest.raises(StopIteration):
        next(second)
    assert called==[]  # Even deliberate Session-object reuse cannot redeem old cleanup.


def test_post_commit_cleanup_failure_keeps_success_and_original(p2_client,sql,monkeypatch,caplog):
    from pathlib import Path
    client=p2_client()
    upload,file_id,_=measured_upload(client,sql)
    key=sql('SELECT storage_key FROM d5_upload_file WHERE id=:id',{'id':file_id})[0]['storage_key']
    source=Path(client.app.state.settings.upload_storage_dir)/key
    unlink=type(source).unlink
    def refuse_original(path,*args,**kwargs):
        if path==source:
            raise PermissionError('never disclose credential-or-path')
        return unlink(path,*args,**kwargs)
    monkeypatch.setattr(type(source),'unlink',refuse_original)
    assert register(client,upload).status_code==201
    assert source.is_file()
    assert len(sql('SELECT file_id FROM d3_file_measurement WHERE file_id=:id',{'id':file_id}))==1
    assert 'registration_source_cleanup_deferred' in caplog.text
    assert 'never disclose' not in caplog.text


def test_late_measurement_binding_cannot_attach_after_file_replacement(p2_client,sql,session_factory):
    from colab_core.domains.d5_ingestion import UploadLedgerAdapter
    from colab_core.domains.d3_file_measurement import bind
    client=p2_client()
    upload,file_id,_=measured_upload(client,sql)
    with scoped(session_factory) as session:
        receipt=UploadLedgerAdapter(session).measurements(upload['uploadId'])[file_id]
    dataset=register(client,upload).json()['datasetId']
    sql("UPDATE d3_file SET storage_key=storage_key||'.new' WHERE id=:id",{'id':file_id})
    key=sql('SELECT storage_key FROM d3_file WHERE id=:id',{'id':file_id})[0]['storage_key']
    with scoped(session_factory) as session,pytest.raises(ValueError,match='binding rejected'):
        bind(session,receipt=receipt,dataset_id=dataset,storage_key=key)


def test_multiple_files_do_not_share_first_receipt(p2_client,sql):
    client=p2_client()
    body=b'\x93NUMPYtest-only'
    upload=make_upload(client,files=[('files',(name,body,'application/octet-stream')) for name in ('a.npy','b.npy')])
    first,second=[row['fileId'] for row in upload['files']]
    sql("""INSERT INTO d5_file_measurement
      (id,lab_id,upload_id,upload_file_id,parser_version,storage_key,source_digest,byte_size,measured_format)
      SELECT :receipt,lab_id,upload_id,id,'file-measurement-v1',storage_key,:digest,:size,'npy'
      FROM d5_upload_file WHERE id=:file""",
      {'receipt':str(Ulid.generate()),'file':first,'digest':hashlib.sha256(body).hexdigest(),'size':len(body)})
    assert register(client,upload).status_code==201
    assert [row['file_id'] for row in sql('SELECT file_id FROM d3_file_measurement WHERE file_id IN (:first,:second)',
                                         {'first':first,'second':second})]==[first]
