"""Persistent grants authorize server-read evidence, never caller assertions."""
import hashlib
import importlib
import importlib.util

import pytest
from sqlalchemy import text
from conftest import LAB_A, LAB_B, ACC_A_RES, ACC_A_PROF, ACC_B_PROF
from test_search_changes import sources, scoped
from test_search_facts import evidence
from test_search_ontology import manifest
from colab_core.kernel.knowledge_wire import Principal, SourceKey, payload_digest
from colab_core.domains import d3_search_ontology, d4_lineage


def api():
    name = 'colab_core.domains.d3_knowledge_source'
    assert importlib.util.find_spec(name), 'persistent source authority is missing'
    return importlib.import_module(name)


def deletion_authority(factory, lab=LAB_A):
    module = importlib.import_module('colab_core.app.knowledge_source_authority')
    assert hasattr(module, 'DeletionAuthority'), 'body-free deletion authority missing'
    return module.DeletionAuthority(factory, lab)


def test_deleted_file_keeps_body_free_fence_without_user_session(prepared, session_factory, sql, monkeypatch):
    first = issue(session_factory, prepared)
    sql('DELETE FROM d3_file WHERE id=:id', {'id':prepared.source_id})
    revision = sql("SELECT requested_version FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id",
                   {'id':prepared.source_id})[0]['requested_version']
    authority = deletion_authority(session_factory)
    def no_body(*args, **kwargs):
        raise AssertionError('deletion attempted to read private source/ontology')
    monkeypatch.setattr(api(), '_source', no_body)
    monkeypatch.setattr(d3_search_ontology, 'current_manifest', no_body)
    deletion = authority.issue(prepared, revision, ttl_seconds=300)
    assert deletion.source_version.model_dump() == {'revision':revision,'deleted':True}
    assert deletion.processing_version.generation == first.processing_version.generation + 1
    assert authority.validate(deletion) == 'current'
    assert payload_digest(authority.issue(prepared,revision,ttl_seconds=300)) == payload_digest(deletion)
    assert validate(session_factory,first) != 'current'
    with session_factory() as session:
        assert session.execute(text('SELECT current_account_id(),current_lab_id()')).one() == (None,None)


def test_first_deletion_survives_hard_dataset_delete(prepared, session_factory, sql):
    sql('DELETE FROM d3_file WHERE id=:id', {'id':prepared.source_id})
    revision = sql("SELECT requested_version FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id",
                   {'id':prepared.source_id})[0]['requested_version']
    authority = deletion_authority(session_factory)
    first = authority.issue(prepared,revision,ttl_seconds=300)
    assert first.processing_version.generation == 1
    sql('DELETE FROM d3_dataset_description WHERE dataset_id=:id', {'id':prepared.dataset_id})
    sql('DELETE FROM d3_dataset_autometa WHERE dataset_id=:id', {'id':prepared.dataset_id})
    sql('DELETE FROM d3_dataset WHERE id=:id', {'id':prepared.dataset_id})
    assert authority.validate(first) == 'current'
    assert authority.issue(prepared,revision,ttl_seconds=300).processing_version.generation == 1


def test_deletion_rejects_missing_live_and_cross_lab(prepared, session_factory, sql):
    authority = deletion_authority(session_factory)
    with pytest.raises(ValueError):
        authority.issue(prepared,1,ttl_seconds=300)
    missing = prepared.model_copy(update={'source_id':'4'*26})
    with pytest.raises(ValueError):
        authority.issue(missing,1,ttl_seconds=300)
    other = deletion_authority(session_factory,LAB_B)
    with pytest.raises(ValueError):
        other.issue(prepared,1,ttl_seconds=300)


def _start_historical_db(*, hang_on_finish=False):
    import os
    import subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[3]
    env={k:v for k,v in os.environ.items() if not k.startswith('COLAB_')}
    script='''set -e
source gates/tools/_pg.sh
pg_start knowledge-historical-migration || exit 78
cleanup_history() {
  trap '' TERM INT
  task_container="$PGC"
  pg_cleanup
  if docker inspect "$task_container" >/dev/null 2>&1; then exit 78; fi
}
trap cleanup_history EXIT
trap 'exit 78' TERM INT
docker exec "$PGC" psql -U postgres -v ON_ERROR_STOP=1 -q -c 'CREATE ROLE historical_owner LOGIN NOSUPERUSER NOBYPASSRLS' >/dev/null
docker exec "$PGC" createdb -U postgres -O historical_owner knowledge_history
task_pg_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$PGC")
printf 'postgresql+psycopg://historical_owner@%s:5432/knowledge_history\\n' "$task_pg_ip"
printf '%s\\n' "$PGC"
read -r finish
'''
    if hang_on_finish:
        script=script.replace('read -r finish', 'while :; do read -r finish || :; done')
    proc=subprocess.Popen(['bash','-c',script],cwd=root,env=env,stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    return proc,root,env


def _finish_historical_db(proc, container, *, timeout=30):
    import subprocess
    timed_out=False
    if proc.poll() is None:
        try:
            proc.communicate('finished\n',timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            proc.terminate()  # TERM runs this child's EXIT cleanup before bounded reap.
            try:
                proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    pytest.exit(f'historical child could not be reaped; owned container: {container}',returncode=78)
    if container:
        assert container.startswith('colab_v2_gatepg_') and container.replace('_','').isalnum()
        try:
            remaining=subprocess.run(['docker','ps','-aq','--filter',f'name=^/{container}$'],capture_output=True,timeout=5)
        except subprocess.TimeoutExpired:
            pytest.exit(f'historical disposable cleanup could not be confirmed: {container}',returncode=78)
        if remaining.returncode:
            pytest.exit(f'historical disposable cleanup could not be confirmed: {container}',returncode=78)
        if remaining.stdout.strip():
            pytest.exit(f'historical disposable container remains: {container}',returncode=78)
    if timed_out or proc.returncode:
        pytest.exit('historical disposable DB preparation/cleanup failed; child reaped',returncode=78)


@pytest.mark.parametrize('termination', ['timeout','signal'])
def test_historical_db_termination_cleans_owned_container_and_reaps(termination):
    import subprocess
    from _pytest.outcomes import Exit
    proc,_,_=_start_historical_db(hang_on_finish=termination=='timeout')
    container=''
    try:
        assert proc.stdout.readline().startswith('postgresql+psycopg://historical_owner@')
        container=proc.stdout.readline().strip()
        assert container.startswith('colab_v2_gatepg_') and container.replace('_','').isalnum()
        if termination=='signal':proc.terminate()
        with pytest.raises(Exit) as error:
            _finish_historical_db(proc,container,timeout=.1)
        assert error.value.returncode==78
        assert proc.poll() is not None
        remaining=subprocess.run(['docker','ps','-aq','--filter',f'name=^/{container}$'],capture_output=True)
        assert remaining.returncode==0 and not remaining.stdout.strip()
    finally:
        # Test-owned exact disposable only; also clean a deliberately failing RED.
        if proc.poll() is None:
            proc.terminate()
            try:proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill();proc.communicate(timeout=5)
        if container:
            subprocess.run(['docker','rm','-f',container],capture_output=True)


@pytest.fixture
def historical_knowledge_db():
    """Own tmpfs DB at actual 0037, never downgrade or mutate the shared current DB."""
    import subprocess
    import sys
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    proc,root,env=_start_historical_db()
    container=''
    engine=None
    try:
        url=proc.stdout.readline().strip()
        if not url.startswith('postgresql+psycopg://historical_owner@'):
            pytest.exit('historical migration disposable DB unavailable; not executed',returncode=78)
        container=proc.stdout.readline().strip()
        def upgrade(revision):
            result=subprocess.run([sys.executable,'-m','alembic','-c','alembic.ini','upgrade',revision],
                cwd=root/'db/platform',env={**env,'COLAB_PLATFORM_DB_URL':url},capture_output=True,text=True)
            return result.returncode
        if upgrade('0037_knowledge_source_grants'):
            pytest.exit('historical 0037 preparation failed; migration test not executed',returncode=78)
        engine=create_engine(url)
        yield sessionmaker(bind=engine), upgrade
    finally:
        if engine is not None:engine.dispose()
        _finish_historical_db(proc,container)


def test_migration_backfills_hidden_canonical_generation_and_restores_rls(historical_knowledge_db):
    import json
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.knowledge_wire import KnowledgePayload
    factory,upgrade=historical_knowledge_db
    dataset,file_id,fact_id=(str(Ulid.generate()) for _ in range(3))
    # Literal pre-fence contract; the current authority requires 0038 and cannot seed 0037.
    version={'revision':7,'digest':'a'*64,'deleted':False}
    canonical=KnowledgePayload.model_validate({
        'protocol':'knowledge-lifecycle/1',
        'source_key':{'lab_id':LAB_A,'dataset_id':dataset,'source_kind':'evidence','source_id':file_id},
        'source_version':version,
        'processing_version':{'generation':9,'extractor_version':'reviewed-evidence-v1',
                              'mapping_version':'no-mappings-v1','ontology_release':'b'*64},
        'facts':[{'fact_id':fact_id,'predicate':'format','value':'npy','source_locator':'evidence:/format',
                  'source_version':version,'evidence_kind':'human_review'}],
        'mappings':[],'dependencies':[]})
    with scoped(factory) as session:
        assert session.execute(text('SELECT version_num FROM alembic_version_platform')).scalar_one()=='0037_knowledge_source_grants'
        assert session.execute(text('SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user')).scalar_one() is False
        assert session.execute(text("SELECT tableowner=current_user FROM pg_tables WHERE tablename='d3_knowledge_source'")).scalar_one() is True
        session.execute(text("INSERT INTO d1_lab(id,name,opened_at) VALUES (:lab,'historical',now())"),{'lab':LAB_A})
        session.execute(text("INSERT INTO d1_account(id,lab_id,name,email) VALUES (:account,:lab,'historical','historical@example.invalid')"),{'account':ACC_A_RES,'lab':LAB_A})
        session.execute(text('INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id) VALUES (:dataset,:lab,:account,:account)'),{'dataset':dataset,'lab':LAB_A,'account':ACC_A_RES})
        session.execute(text("INSERT INTO d3_file(id,lab_id,dataset_id,kind,file_name,storage_key) VALUES (:file,:lab,:dataset,'본체','historical.npy','historical/file')"),{'file':file_id,'lab':LAB_A,'dataset':dataset})
        session.execute(text("INSERT INTO d3_knowledge_source(lab_id,dataset_id,source_kind,source_id,generation,command) VALUES (:lab,:dataset,'evidence',:file,9,CAST(:command AS jsonb))"),{'lab':LAB_A,'dataset':dataset,'file':file_id,'command':json.dumps(canonical.model_dump())})
        assert session.execute(text('SELECT count(*) FROM d3_knowledge_source')).scalar_one()==1
    with scoped(factory) as session:
        assert session.execute(text('DELETE FROM d3_file WHERE id=:file'),{'file':file_id}).rowcount==1
    with scoped(factory) as session:
        assert session.execute(text('SELECT count(*) FROM d3_knowledge_source')).scalar_one()==0
    assert upgrade('0038_knowledge_deletion')==0, '0038 owner upgrade failed (diagnostic output withheld)'
    with scoped(factory) as session:
        assert session.execute(text('SELECT version_num FROM alembic_version_platform')).scalar_one()=='0038_knowledge_deletion'
        assert session.execute(text('SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user')).scalar_one() is False
        assert session.execute(text('SELECT generation,source_revision,deleted FROM d3_knowledge_fence')).one()==(9,7,False)
        assert session.execute(text('SELECT count(*) FROM d3_knowledge_source')).scalar_one()==0
        policies=session.execute(text("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('d3_knowledge_source','d3_knowledge_fence','d3_knowledge_deletion_grant')")).all()
        assert len(policies)==3 and all(tuple(row)==(True,True) for row in policies)


def test_reinserted_evidence_rejects_old_delete_and_advances_fence(prepared,session_factory,sql):
    original = issue(session_factory,prepared)
    sql('DELETE FROM d3_search_evidence WHERE file_id=:id', {'id':prepared.source_id})
    revision = sql("SELECT requested_version FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id",
                   {'id':prepared.source_id})[0]['requested_version']
    authority = deletion_authority(session_factory)
    deletion = authority.issue(prepared,revision,ttl_seconds=300)
    evidence(sql,prepared.dataset_id,prepared.source_id)
    assert authority.validate(deletion) == 'stale_source'
    with pytest.raises(ValueError):
        authority.issue(prepared,revision,ttl_seconds=300)
    current = issue(session_factory,prepared)
    assert current.processing_version.generation == original.processing_version.generation + 2


def test_deletion_proof_requires_commit_and_rejects_tampering(prepared,session_factory,sql):
    authority=deletion_authority(session_factory)
    with scoped(session_factory) as session:
        session.execute(text('DELETE FROM d3_search_evidence WHERE file_id=:id'),{'id':prepared.source_id})
        with pytest.raises(ValueError):
            authority.issue(prepared,2,ttl_seconds=300)
    revision=sql("SELECT requested_version FROM d3_search_change WHERE source_kind='evidence' AND source_id=:id",{'id':prepared.source_id})[0]['requested_version']
    command=authority.issue(prepared,revision,ttl_seconds=300)
    for attribute,value in (('source_version',{'revision':revision+1,'deleted':True}),
                            ('processing_version',{'generation':2}),('grant','unknown')):
        from colab_core.kernel.knowledge_wire import InvalidateCommand
        altered=InvalidateCommand.model_validate({**command.model_dump(),attribute:value})
        assert authority.validate(altered)=='forbidden'
    with pytest.raises(ValueError,match='forbidden'):
        deletion_authority(session_factory,LAB_B).validate(command)
    with session_factory.begin() as session:
        session.execute(text("SELECT set_config('app.current_lab',:lab,true),set_config('app.current_account','',true)"),{'lab':LAB_A})
        session.execute(text("UPDATE d3_knowledge_deletion_grant SET expires_at=clock_timestamp()-interval '1 second' WHERE source_id=:id"),{'id':prepared.source_id})
    assert authority.validate(command)=='forbidden'


def principal(account=ACC_A_RES, lab=LAB_A, version=1):
    return Principal(account_id=account, lab_id=lab, session_version=version)


@pytest.fixture
def prepared(sources, sql, session_factory):
    evidence(sql, *sources)
    with scoped(session_factory) as s:
        previous = d3_search_ontology.current_manifest(s)
        d3_search_ontology.publish(s, manifest(), expected_previous=previous['version'] if previous else None)
    return SourceKey(lab_id=LAB_A, dataset_id=sources[0], source_kind='evidence', source_id=sources[1])


def issue(factory, key, who=None):
    who = who or principal()
    with scoped(factory, lab=who.lab_id, account=who.account_id) as s:
        return api().issue(s, key, who, ttl_seconds=300,lineage=d4_lineage.LineageRevisionAdapter(s))


def validate(factory, command, who=None):
    who = who or principal()
    with scoped(factory, lab=who.lab_id, account=who.account_id) as s:
        return api().validate(s, command, who,lineage=d4_lineage.LineageRevisionAdapter(s))


def test_storage_exists(sql):
    assert sql("SELECT to_regclass('d3_knowledge_grant') AS name")[0]['name'], 'persistent grant storage missing'


def receipt_for(command):
    from colab_core.kernel.knowledge_wire import KnowledgeReceipt
    return KnowledgeReceipt(protocol=command.protocol,issuer='D9',receipt_id='4'*26,
        source_key=command.source_key,source_version=command.source_version,
        processing_version=command.processing_version,publication_sequence=1,
        payload_digest=payload_digest(command),status='replaced')


def read_check(factory, receipt, who=None):
    who = who or principal(ACC_A_PROF)
    with scoped(factory,lab=who.lab_id,account=who.account_id) as s:
        s.execute(text('SET TRANSACTION READ ONLY'))
        return api().authorize_read(s,receipt,who,lineage=d4_lineage.LineageRevisionAdapter(s))


def test_reader_uses_current_viewer_not_expired_grant(prepared,session_factory,sql):
    command = issue(session_factory,prepared)
    sql('UPDATE d3_knowledge_grant SET expires_at=clock_timestamp()-interval \'1 second\' WHERE dataset_id=:id',{'id':prepared.dataset_id})
    before = sql('SELECT generation,command FROM d3_knowledge_source WHERE source_id=:id',{'id':prepared.source_id})
    grants = sql('SELECT * FROM d3_knowledge_grant WHERE dataset_id=:id',{'id':prepared.dataset_id})
    assert read_check(session_factory,receipt_for(command)) == 'current'
    assert before == sql('SELECT generation,command FROM d3_knowledge_source WHERE source_id=:id',{'id':prepared.source_id})
    assert grants == sql('SELECT * FROM d3_knowledge_grant WHERE dataset_id=:id',{'id':prepared.dataset_id})


@pytest.mark.parametrize('change,expected', [('digest','forbidden'),('source','stale_source'),('generation','stale_generation'),('release','stale_release'),('lab','forbidden')])
def test_reader_checks_current_canonical_source(prepared,session_factory,sql,change,expected):
    command = issue(session_factory,prepared)
    receipt = receipt_for(command)
    if change == 'digest': receipt.payload_digest = 'f'*64
    elif change == 'source':
        sql('UPDATE d3_search_evidence SET revision=revision+1 WHERE file_id=:id',{'id':prepared.source_id})
    elif change == 'generation':
        sql('UPDATE d3_knowledge_source SET generation=generation+1 WHERE source_id=:id',{'id':prepared.source_id})
    elif change == 'release':
        with scoped(session_factory) as s:
            d3_search_ontology.publish(s,manifest(discovery='d'*64),expected_previous=manifest()['version'])
    else: receipt.source_key.lab_id = LAB_B
    assert read_check(session_factory,receipt) == expected


def test_restart_keeps_canonical_facts_and_stores_only_secret_hash(prepared, session_factory, sql):
    first = issue(session_factory, prepared)
    assert [(f.predicate, f.value, f.evidence_kind) for f in first.facts] == [('roles', ['validation'], 'human_review')]
    assert first.mappings == []
    importlib.reload(api())
    second = issue(session_factory, prepared)
    assert first.grant != second.grant
    assert payload_digest(first) == payload_digest(second)
    assert validate(session_factory, first) == 'current'
    rows = sql('SELECT * FROM d3_knowledge_grant WHERE dataset_id=:id', {'id': prepared.dataset_id})
    assert len(rows) == 2
    assert rows[0]['grant_hash'] in {hashlib.sha256(c.grant.encode()).hexdigest() for c in (first, second)}
    assert all(first.grant not in str(row) and second.grant not in str(row) for row in rows)


def test_payload_and_session_tampering_are_rejected(prepared, session_factory):
    command = issue(session_factory, prepared)
    altered = command.model_copy(deep=True)
    altered.facts[0].value = ['prediction']
    assert validate(session_factory, altered) == 'forbidden'
    assert validate(session_factory, command, principal(version=2)) == 'forbidden'
    altered = command.model_copy(update={'grant': 'unknown'})
    assert validate(session_factory, altered) == 'forbidden'


def test_source_change_and_new_generation_fence(prepared, session_factory, sql):
    first = issue(session_factory, prepared)
    sql("UPDATE d3_search_evidence SET revision=revision+1,facts='{\"roles\":[\"prediction\"]}' WHERE file_id=:id", {'id': prepared.source_id})
    assert validate(session_factory, first) == 'stale_source'
    second = issue(session_factory, prepared)
    assert second.processing_version.generation == first.processing_version.generation + 1
    assert validate(session_factory, first) == 'stale_generation'
    assert validate(session_factory, second) == 'current'


def test_manifest_change_invalidates_then_advances_generation(prepared, session_factory):
    first = issue(session_factory, prepared)
    with scoped(session_factory) as s:
        d3_search_ontology.publish(s, manifest(discovery='d'*64), expected_previous=manifest()['version'])
    assert validate(session_factory, first) == 'stale_release'
    second = issue(session_factory, prepared)
    assert second.processing_version.generation == first.processing_version.generation + 1


def test_other_account_and_lab_cannot_redeem_grant(prepared, session_factory):
    command = issue(session_factory, prepared)
    assert validate(session_factory, command, principal(ACC_A_PROF)) == 'forbidden'
    assert validate(session_factory, command, principal(ACC_B_PROF, LAB_B)) == 'forbidden'
    with pytest.raises(ValueError):
        issue(session_factory, prepared, principal(ACC_B_PROF, LAB_B))


@pytest.mark.parametrize('change', ['draft', 'file', 'deleted'])
def test_unready_replaced_or_deleted_source_cannot_issue(prepared, session_factory, sql, change):
    first = issue(session_factory, prepared)
    if change == 'draft':
        sql("UPDATE d3_search_evidence SET status='draft',reviewed_by=NULL,reviewed_at=NULL WHERE file_id=:id", {'id': prepared.source_id})
    elif change == 'file':
        sql("UPDATE d3_file SET storage_key='replacement' WHERE id=:id", {'id': prepared.source_id})
    else:
        sql('UPDATE d3_dataset SET deleted_at=now(),deleted_by_account_id=:account WHERE id=:id', {'account': ACC_A_RES, 'id': prepared.dataset_id})
    assert validate(session_factory, first) != 'current'
    with pytest.raises(ValueError):
        issue(session_factory, prepared)


def test_expired_grant_cannot_be_redeemed(prepared, session_factory, sql):
    command = issue(session_factory, prepared)
    sql("UPDATE d3_knowledge_grant SET expires_at=clock_timestamp()-interval '1 second' WHERE dataset_id=:id", {'id': prepared.dataset_id})
    assert validate(session_factory, command) == 'forbidden'


def test_real_credential_adapter_rechecks_revocation(prepared, session_factory, admin_db_url, sql, monkeypatch):
    from colab_core.kernel.db import make_engine, make_session_factory
    from colab_core.kernel.db_credentials import DatabaseCredentialStore
    from colab_core.kernel.ids import Ulid
    name = 'colab_core.app.knowledge_source_authority'
    assert importlib.util.find_spec(name), 'mandatory credential adapter missing'
    adapter = importlib.import_module(name).SourceAuthority
    account = str(Ulid.generate())
    actor = principal(account)
    sql('INSERT INTO d1_account(id,lab_id,name,email) VALUES (:id,:lab,\'knowledge\',:email)',
        {'id':account,'lab':LAB_A,'email':account+'@example.test'})
    # Disposable fixture credential; password is never used to authenticate this internal port.
    engine = make_engine(admin_db_url)
    def credential_sql(statement):
        with engine.begin() as db:
            return db.execute(text(statement), {'id': account})
    credential_sql("""INSERT INTO account_admin.login_credential
      (account_id,login_name,kdf,salt,password_hash,n,r,p,must_change_password,session_version,status)
      VALUES (:id,'knowledge-fixture','scrypt','00','00',16384,8,1,false,1,'active')""")
    try:
        authority = adapter(session_factory, DatabaseCredentialStore(make_session_factory(engine)))
        command = authority.issue(prepared, actor, ttl_seconds=300)
        restarted = adapter(session_factory, DatabaseCredentialStore(make_session_factory(engine)))
        assert restarted.validate(command, actor) == 'current'
        # Revoke between token_is_current's first SELECT and its subsequent find.
        original_find = authority._credentials.find
        def revoke_before_find(login_name):
            credential_sql('UPDATE account_admin.login_credential SET session_version=2 WHERE account_id=:id')
            return original_find(login_name)
        with monkeypatch.context() as patch:
            patch.setattr(authority._credentials, 'find', revoke_before_find)
            assert authority.validate(command, actor) == 'forbidden'
        assert authority.validate(command, actor) == 'forbidden'
        with pytest.raises(ValueError):
            authority.issue(prepared, actor, ttl_seconds=300)
    finally:
        sql('DELETE FROM d3_knowledge_grant WHERE account_id=:id', {'id':account}, account_id=account)
        sql('DELETE FROM d1_account WHERE id=:id', {'id':account})
        engine.dispose()


def test_concurrent_issue_converges_on_one_generation_and_payload(prepared, session_factory, sql):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    barrier = Barrier(2)
    def run():
        barrier.wait(timeout=10)
        return issue(session_factory, prepared)
    with ThreadPoolExecutor(max_workers=2) as pool:
        commands = list(pool.map(lambda _: run(), range(2)))
    assert {c.processing_version.generation for c in commands} == {1}
    assert len({payload_digest(c) for c in commands}) == 1
    assert sql('SELECT count(*) AS n FROM d3_knowledge_source WHERE dataset_id=:id', {'id': prepared.dataset_id})[0]['n'] == 1


def test_private_access_revocation_hides_payload_and_denies_issue(prepared, session_factory, sql):
    actor = principal(ACC_A_PROF)
    command = issue(session_factory, prepared, actor)
    sql("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김')
      ON CONFLICT (dataset_id) DO UPDATE SET state='잠김'""", {'id':prepared.dataset_id,'lab':LAB_A})
    assert validate(session_factory, command, actor) == 'forbidden'
    with pytest.raises(ValueError):
        issue(session_factory, prepared, actor)
    with scoped(session_factory, account=ACC_A_PROF) as s:
        for table in ('d3_knowledge_source','d3_knowledge_grant'):
            assert s.execute(text(f'SELECT count(*) FROM {table} WHERE dataset_id=:id'), {'id':prepared.dataset_id}).scalar_one() == 0


def test_source_changes_during_issue_cannot_validate_late_payload(prepared, session_factory, sql, monkeypatch):
    # Pause after the real source read, mutate through a separate committed DB
    # connection, then allow issuance to finish. Cross-transaction atomicity is
    # not promised: the late grant must fail latest-source validation.
    original = api()._source
    def change_after_read(session, key):
        result = original(session, key)
        sql("UPDATE d3_search_evidence SET revision=revision+1,facts='{\"roles\":[\"prediction\"]}' WHERE file_id=:id", {'id':prepared.source_id})
        return result
    with monkeypatch.context() as patch:
        patch.setattr(api(), '_source', change_after_read)
        late = issue(session_factory, prepared)
    assert validate(session_factory, late) == 'stale_source'
    latest = issue(session_factory, prepared)
    assert latest.processing_version.generation > late.processing_version.generation
    assert validate(session_factory, latest) == 'current'
