"""Real PostgreSQL writer isolation and source fencing; no HTTP authorization claim."""
import importlib
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import json
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from colab_ai.kernel.knowledge_wire import Principal, ReplaceCommand


def modules():
    name = 'colab_ai.app.knowledge_writer'
    assert importlib.util.find_spec(name) is not None, 'internal knowledge writer missing'
    return importlib.import_module(name)


def command(generation=1, engine=None):
    # Unique source per invocation; keep multiple generations by copying this DTO.
    from uuid import uuid4
    source = uuid4().hex[:26].upper()
    from colab_ai.app.ontology_manifest import load_manifest
    release = load_manifest(engine)['version'] if engine is not None else 'b' * 64
    return ReplaceCommand.model_validate({
        'protocol': 'knowledge-lifecycle/1', 'grant': 'secret-never-persist',
        'source_key': {'lab_id': '0' * 26, 'dataset_id': source, 'source_kind': 'file', 'source_id': source},
        'source_version': {'revision': 1, 'digest': 'a' * 64, 'deleted': False},
        'processing_version': {'generation': generation, 'extractor_version': 'v1',
                               'mapping_version': 'v1', 'ontology_release': release},
        'facts': [{'fact_id': '3' * 26, 'predicate': 'variable', 'value': 'NDVI',
                   'source_locator': 'file#/variable', 'evidence_kind': 'file_measurement',
                   'source_version': {'revision': 1, 'digest': 'a' * 64, 'deleted': False}}],
        'mappings': [], 'dependencies': []})


PRINCIPAL = Principal(account_id='1' * 26, lab_id='0' * 26, session_version=1)


@pytest.mark.parametrize('root,data,want', [
    ('/pgdata', '/pgdata/db', 0),
    ('/var/lib/postgresql/data', '/var/lib/postgresql/data/db', 0),
    (None, '/pgdata/db', 1), ('/other', '/other/db', 1),
    ('/pgdata', '/pgdata-other/db', 1), ('/pgdata', '/persistent/db', 1),
])
def test_fixture_refuses_non_disposable_storage(root, data, want):
    probe = Path(__file__).parent / 'fixtures/disposable_db.py'
    assert probe.is_file(), 'disposable fixture validator missing'
    inspection = [{'HostConfig': {'Tmpfs': {root: ''} if root else {}},
                   'Mounts': [{'Type': 'tmpfs', 'Destination': root}] if root else [],
                   'Config': {'Env': ['PGDATA=' + data]}}]
    result = subprocess.run([sys.executable, str(probe)], input=json.dumps(inspection),
                            text=True, capture_output=True)
    assert result.returncode == want


@pytest.mark.parametrize('kind,destination', [('bind','/pgdata/db'), ('volume','/pgdata/db'),
                                            ('bind','/pgdata/db/base')])
def test_fixture_rejects_persistent_mount_beneath_tmpfs(kind, destination):
    inspection = [{'HostConfig': {'Tmpfs': {'/pgdata': ''}},
                   'Mounts': [{'Type': 'tmpfs', 'Destination': '/pgdata'},
                              {'Type': kind, 'Destination': destination}],
                   'Config': {'Env': ['PGDATA=/pgdata/db']}}]
    result = subprocess.run([sys.executable, str(Path(__file__).parent / 'fixtures/disposable_db.py')],
                            input=json.dumps(inspection), text=True, capture_output=True)
    assert result.returncode == 1


def test_fixture_accepts_docker_implicit_tmpfs_with_unrelated_image_volume():
    inspection = [{'HostConfig': {'Tmpfs': {'/pgdata': 'uid=70,gid=70'}},
                   'Mounts': [{'Type':'volume','Destination':'/var/lib/postgresql/data'}],
                   'Config': {'Env': ['PGDATA=/pgdata/db']}}]
    result = subprocess.run([sys.executable, str(Path(__file__).parent / 'fixtures/disposable_db.py')],
                            input=json.dumps(inspection), text=True, capture_output=True)
    assert result.returncode == 0


class Authority:
    def __init__(self, result='current'):
        self.result = result

    def validate(self, body, principal):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture
def writer_engine(knowledge_db_url):
    engine = create_engine(knowledge_db_url, pool_size=1, max_overflow=0)
    yield engine
    engine.dispose()


def writer(engine, authority=None):
    return modules().KnowledgeWriter(sessionmaker(engine), authority or Authority())


@pytest.mark.parametrize('existing',[False,True])
def test_invalidation_persists_body_free_fence_and_rejects_late_replace(writer_engine,monkeypatch,existing):
    from colab_ai.kernel.knowledge_wire import InvalidateCommand
    from colab_ai.app.knowledge_reader import KnowledgeReader
    body = command(engine=writer_engine)
    if existing:
        writer(writer_engine).replace(body,PRINCIPAL)
    deletion = InvalidateCommand.model_validate({'protocol':body.protocol,'grant':'deletion-secret',
        'source_key':body.source_key.model_dump(),'source_version':{'revision':2,'deleted':True},
        'processing_version':{'generation':2},'reason':'deleted'})
    assert hasattr(modules(),'KnowledgeInvalidator'), 'dedicated invalidation adapter missing'
    class DeletedAuthority:
        def validate(self,command): return 'current'
    invalidator = modules().KnowledgeInvalidator(sessionmaker(writer_engine),DeletedAuthority(),PRINCIPAL.lab_id)
    def unavailable(*args): raise RuntimeError('ontology offline')
    monkeypatch.setattr(modules(),'load_manifest',unavailable)
    receipt = invalidator.invalidate(deletion)
    assert receipt.status == 'invalidated'
    assert receipt.publication_sequence == (2 if existing else 1)
    assert invalidator.invalidate(deletion) == receipt
    assert modules().KnowledgeInvalidator(sessionmaker(writer_engine),DeletedAuthority(),PRINCIPAL.lab_id).invalidate(deletion)==receipt
    lower=deletion.model_copy(deep=True);lower.processing_version.generation=1
    with pytest.raises(ValueError,match='stale_generation'):invalidator.invalidate(lower)
    conflict=deletion.model_copy(deep=True);conflict.source_version.revision=3
    with pytest.raises(ValueError,match='idempotency_conflict'):invalidator.invalidate(conflict)
    cross=deletion.model_copy(deep=True);cross.source_key.lab_id='1'*26
    with pytest.raises(ValueError,match='forbidden'):invalidator.invalidate(cross)
    with pytest.raises(ValueError,match='forbidden'):
        KnowledgeReader(sessionmaker(writer_engine),None).read(body.source_key,receipt.receipt_id)
    from colab_ai.domains import d9_dataset_knowledge
    with sessionmaker(writer_engine).begin() as session:
        row = d9_dataset_knowledge.read(session,body.source_key,include_payload=True)
        assert row['payload'] == deletion.model_dump(mode='json',exclude={'grant'})
        assert 'deletion-secret' not in str(row)
        with pytest.raises(ValueError,match='stale_source'):
            d9_dataset_knowledge.replace(session,body)


@pytest.mark.parametrize('verdict',['forbidden','stale_source','stale_generation',RuntimeError('offline')])
def test_invalidation_fails_closed_before_sql(verdict):
    from colab_ai.kernel.knowledge_wire import InvalidateCommand
    body=command()
    deletion=InvalidateCommand.model_validate({'protocol':body.protocol,'grant':'secret',
      'source_key':body.source_key.model_dump(),'source_version':{'revision':2,'deleted':True},
      'processing_version':{'generation':2},'reason':'deleted'})
    assert hasattr(modules(),'KnowledgeInvalidator'), 'dedicated invalidation adapter missing'
    class DeletedAuthority:
        def validate(self,command):
            if isinstance(verdict,Exception): raise verdict
            return verdict
    class NoSQL:
        def begin(self): raise AssertionError('SQL before deletion proof')
    with pytest.raises(ValueError):
        modules().KnowledgeInvalidator(NoSQL(),DeletedAuthority(),PRINCIPAL.lab_id).invalidate(deletion)


def test_reader_returns_coherent_grant_free_payload_without_writes(writer_engine):
    from colab_ai.app.knowledge_reader import KnowledgeReader
    from sqlalchemy import event
    body = command(engine=writer_engine)
    saved = writer(writer_engine).replace(body,PRINCIPAL)
    class Viewer:
        def authorize_read(self,receipt):
            assert receipt == saved
            return PRINCIPAL
    read = KnowledgeReader(sessionmaker(writer_engine),Viewer())
    observed=[]
    def check_readonly(connection,cursor,statement,parameters,context,executemany):
        if statement.startswith('SELECT ') and ('d9_' in statement):
            cursor.execute('SHOW transaction_read_only')
            observed.append(cursor.fetchone()[0])
    event.listen(writer_engine,'before_cursor_execute',check_readonly)
    try:
        result = read.read(body.source_key,saved.receipt_id)
    finally:
        event.remove(writer_engine,'before_cursor_execute',check_readonly)
    assert len(observed)==3 and set(observed)=={'on'}
    assert result.receipt == saved
    assert result.payload.model_dump() == body.model_dump(exclude={'grant'})
    assert writer(writer_engine).replace(body,PRINCIPAL) == saved


@pytest.mark.parametrize('change',['replacement','sequence','digest'])
def test_reader_denies_replaced_row(writer_engine,change):
    from colab_ai.app.knowledge_reader import KnowledgeReader
    body = command(engine=writer_engine)
    saved = writer(writer_engine).replace(body,PRINCIPAL)
    class Viewer:
        def authorize_read(self,receipt):
            if change=='replacement':
                newer = body.model_copy(deep=True)
                newer.processing_version.generation += 1
                writer(writer_engine).replace(newer,PRINCIPAL)
            else:
                with writer_engine.begin() as db:
                    for field,value in body.source_key.model_dump().items():
                        db.execute(text('SELECT set_config(:name,:value,true)'),{'name':'knowledge.'+field,'value':value})
                    assignment='publication_sequence=publication_sequence+1' if change=='sequence' else "payload_digest='"+'f'*64+"'"
                    db.execute(text('UPDATE knowledge.d9_knowledge_source SET '+assignment))
            return PRINCIPAL
    with pytest.raises(ValueError,match='forbidden'):
        KnowledgeReader(sessionmaker(writer_engine),Viewer()).read(body.source_key,saved.receipt_id)


@pytest.mark.parametrize('corruption', ['payload','source_key','processing','row_digest','sequence'])
def test_reader_rejects_corrupt_stored_content(writer_engine,corruption):
    from colab_ai.app.knowledge_reader import KnowledgeReader
    body=command(engine=writer_engine)
    saved=writer(writer_engine).replace(body,PRINCIPAL)
    assignments={
        'payload': "payload=jsonb_set(payload,'{facts,0,value}','\"tampered\"')",
        'source_key': "payload=jsonb_set(payload,'{source_key,lab_id}','\"99999999999999999999999999\"')",
        'processing': "payload=jsonb_set(payload,'{processing_version,generation}','2')",
        'row_digest': "payload_digest='"+'f'*64+"'",
        'sequence': 'publication_sequence=publication_sequence+1',
    }
    with writer_engine.begin() as db:
        for field,value in body.source_key.model_dump().items():
            db.execute(text('SELECT set_config(:name,:value,true)'),{'name':'knowledge.'+field,'value':value})
        db.execute(text('UPDATE knowledge.d9_knowledge_source SET '+assignments[corruption]))
    class Viewer:
        def authorize_read(self,receipt):return PRINCIPAL
    with pytest.raises(ValueError):
        KnowledgeReader(sessionmaker(writer_engine),Viewer()).read(body.source_key,saved.receipt_id)


def test_reader_callback_failure_never_loads_payload(writer_engine,monkeypatch):
    from colab_ai.app.knowledge_reader import KnowledgeReader
    from colab_ai.domains import d9_dataset_knowledge
    body=command(engine=writer_engine)
    saved=writer(writer_engine).replace(body,PRINCIPAL)
    original=d9_dataset_knowledge.read
    calls=[]
    def observed(session,key,*,include_payload=False):
        calls.append(include_payload)
        return original(session,key,include_payload=include_payload)
    monkeypatch.setattr(d9_dataset_knowledge,'read',observed)
    class Viewer:
        def authorize_read(self,receipt):raise ValueError('forbidden')
    with pytest.raises(ValueError,match='forbidden'):
        KnowledgeReader(sessionmaker(writer_engine),Viewer()).read(body.source_key,saved.receipt_id)
    assert calls==[False]


def test_reader_checks_own_release_even_when_source_callback_accepts(writer_engine):
    from colab_ai.app.knowledge_reader import KnowledgeReader
    from colab_ai.domains import d9_dataset_knowledge
    body=command()  # Deliberately not the actual seeded D9 release.
    with sessionmaker(writer_engine).begin() as session:
        saved=d9_dataset_knowledge.replace(session,body)
    class Viewer:
        def authorize_read(self,receipt):return PRINCIPAL
    with pytest.raises(ValueError,match='stale_release'):
        KnowledgeReader(sessionmaker(writer_engine),Viewer()).read(body.source_key,saved.receipt_id)


def test_authority_failure_never_opens_database():
    module = modules()
    def forbidden_factory():
        pytest.fail('database accessed before authority validation')
    for result in ('forbidden', 'stale_source', 'stale_generation', RuntimeError('offline')):
        with pytest.raises(ValueError):
            module.KnowledgeWriter(forbidden_factory, Authority(result)).replace(command(), PRINCIPAL)


def test_cross_lab_principal_is_rejected_before_database():
    module = modules()
    def forbidden_factory():
        pytest.fail('database accessed with cross-lab principal')
    other = PRINCIPAL.model_copy(update={'lab_id': '9' * 26})
    with pytest.raises(ValueError, match='forbidden'):
        module.KnowledgeWriter(forbidden_factory, Authority()).replace(command(), other)


def test_identical_retry_and_new_process_keep_receipt(writer_engine):
    body = command(engine=writer_engine)
    first = writer(writer_engine).replace(body, PRINCIPAL)
    assert first.publication_sequence == 1
    assert writer(writer_engine).replace(body, PRINCIPAL) == first
    with writer_engine.begin() as connection:
        assert connection.execute(text('SELECT count(*) FROM knowledge.d9_knowledge_source')).scalar() == 0


def test_stale_generation_and_conflicting_payload_preserve_receipt(writer_engine):
    body = command(2, engine=writer_engine)
    saved = writer(writer_engine).replace(body, PRINCIPAL)
    stale = body.model_copy(deep=True)
    stale.processing_version.generation = 1
    with pytest.raises(ValueError, match='stale_generation'):
        writer(writer_engine).replace(stale, PRINCIPAL)
    changed = body.model_copy(deep=True)
    changed.facts[0].value = 'LST'
    with pytest.raises(ValueError, match='idempotency_conflict'):
        writer(writer_engine).replace(changed, PRINCIPAL)
    assert writer(writer_engine).replace(body, PRINCIPAL) == saved
    newer = body.model_copy(deep=True)
    newer.processing_version.generation = 3
    assert writer(writer_engine).replace(newer, PRINCIPAL).publication_sequence == 2


def test_concurrent_same_payload_converges(writer_engine):
    body = command(engine=writer_engine)
    engine = create_engine(writer_engine.url, pool_size=2)
    barrier = Barrier(2)
    class ConcurrentAuthority(Authority):
        def validate(self, body, principal):
            barrier.wait(timeout=10)
            return 'current'
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            receipts = list(pool.map(lambda _: writer(engine, ConcurrentAuthority()).replace(body, PRINCIPAL), range(2)))
        assert receipts[0] == receipts[1]
    finally:
        engine.dispose()


def test_read_role_cannot_read_or_write_knowledge(dict_db_url):
    engine = create_engine(dict_db_url)
    try:
        for query in ('SELECT * FROM knowledge.d9_knowledge_source', 'DELETE FROM knowledge.d9_knowledge_source'):
            with pytest.raises(DBAPIError) as error, engine.begin() as connection:
                connection.execute(text(query))
            assert error.value.orig.sqlstate == '42501'
    finally:
        engine.dispose()


def test_writer_cannot_change_ontology_or_schema_or_bypass_rls(writer_engine):
    for query in ('DELETE FROM public.d9_concept', 'CREATE TABLE public.bad (id int)',
                  'INSERT INTO public.d9_concept SELECT * FROM public.d9_concept WHERE false',
                  'UPDATE public.d9_concept SET source_note=source_note WHERE false',
                  'TRUNCATE public.d9_concept CASCADE',
                  'CREATE TABLE knowledge.bad (id int)', 'ALTER ROLE colab_knowledge_writer BYPASSRLS',
                  'SET ROLE colab_owner'):
        with pytest.raises(DBAPIError) as error, writer_engine.begin() as connection:
            connection.execute(text(query))
        assert error.value.orig.sqlstate == '42501'
    with writer_engine.begin() as connection:
        assert connection.execute(text('''SELECT count(*) FROM pg_auth_members
          WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user)''')).scalar() == 0


def test_rls_requires_entire_source_key_and_scope_expires(writer_engine):
    body = command(engine=writer_engine)
    writer(writer_engine).replace(body, PRINCIPAL)
    key = body.source_key.model_dump()
    for missing in [None, *key]:
        with writer_engine.begin() as connection:
            for name, value in key.items():
                if name != missing:
                    connection.execute(text("SELECT set_config(:name,:value,true)"),
                                       {'name': 'knowledge.' + name, 'value': value})
            assert connection.execute(text('SELECT count(*) FROM knowledge.d9_knowledge_source')).scalar() == (1 if missing is None else 0)
    with writer_engine.begin() as connection:
        assert connection.execute(text('SELECT count(*) FROM knowledge.d9_knowledge_source')).scalar() == 0
    with writer_engine.begin() as connection:
        for name, value in key.items():
            connection.execute(text('SELECT set_config(:name,:value,true)'),
                               {'name':'knowledge.'+name, 'value':'9'*26 if name == 'source_id' else value})
        assert connection.execute(text('SELECT count(*) FROM knowledge.d9_knowledge_source')).scalar() == 0


def test_payload_excludes_grant_and_forged_scope_cannot_update(writer_engine):
    body = command(engine=writer_engine)
    writer(writer_engine).replace(body, PRINCIPAL)
    with writer_engine.begin() as connection:
        for name, value in body.source_key.model_dump().items():
            connection.execute(text('SELECT set_config(:name,:value,true)'), {'name':'knowledge.'+name,'value':value})
        payload = connection.execute(text('SELECT payload FROM knowledge.d9_knowledge_source')).scalar()
        assert 'grant' not in payload
        assert body.grant not in str(payload)
        with pytest.raises(DBAPIError) as error, connection.begin_nested():
            connection.execute(text("UPDATE knowledge.d9_knowledge_source SET dataset_id=:id"), {'id': '9' * 26})
        assert error.value.orig.sqlstate == '42501'


@pytest.mark.parametrize('invalid_field', ['lab_id','dataset_id','source_id'])
def test_database_rejects_noncanonical_source_ids_even_in_matching_scope(writer_engine, invalid_field):
    key = command().source_key.model_dump()
    key[invalid_field] = 'not-an-id'
    with writer_engine.begin() as connection:
        for name,value in key.items():
            connection.execute(text('SELECT set_config(:name,:value,true)'), {'name':'knowledge.'+name,'value':value})
        with pytest.raises(DBAPIError) as error, connection.begin_nested():
            connection.execute(text('''INSERT INTO knowledge.d9_knowledge_source
              (lab_id,dataset_id,source_kind,source_id,generation,source_revision,publication_sequence,payload_digest,payload,receipt)
              VALUES (:lab_id,:dataset_id,:source_kind,:source_id,1,1,1,:digest,'{}','{}')'''),
              {**key,'digest':'a'*64})
        assert error.value.orig.sqlstate == '23514'


def test_changed_d9_manifest_blocks_new_write_and_old_receipt(writer_engine):
    body = command(engine=writer_engine)
    writer(writer_engine).replace(body, PRINCIPAL)
    new_body = command(engine=writer_engine)
    owner = create_engine(writer_engine.url.set(username='postgres', password=None))
    try:
        with owner.begin() as connection:
            row = connection.execute(text("SELECT concept_id,source_note FROM d9_concept ORDER BY concept_id LIMIT 1")).one()
            connection.execute(text("UPDATE d9_concept SET source_note=source_note || ' revision' WHERE concept_id=:id"), {'id': row.concept_id})
        for stale in (body, new_body):
            with pytest.raises(ValueError, match='stale_release'):
                writer(writer_engine).replace(stale, PRINCIPAL)
    finally:
        with owner.begin() as connection:
            connection.execute(text("UPDATE d9_concept SET source_note=:note WHERE concept_id=:id"), {'id': row.concept_id, 'note': row.source_note})
        owner.dispose()
