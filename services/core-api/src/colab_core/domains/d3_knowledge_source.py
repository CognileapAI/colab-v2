"""Internal D3 persistence. Caller must authenticate principal before each call.

Current reviewed evidence and registered per-file measurements are supported. No caller facts, mappings, deleted
claims or arbitrary processing versions are accepted. Tombstones need the owning
domain adapter; this user-scoped path cannot authorize them.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from sqlalchemy import text

from ..kernel.ids import Ulid
from ..kernel.knowledge_wire import Principal, SourceKey, ReplaceCommand, KnowledgePayload, InvalidateCommand, payload_digest
from ..ports.lineage import LineageRevisionPort
from . import d3_search_changes as changes, d3_search_facts as facts, d3_search_ontology as ontology
from . import d3_file_measurement as measured

EXTRACTOR = 'reviewed-evidence-v1'
MAPPING = 'no-mappings-v1'
_KEY = 'lab_id=:lab_id AND dataset_id=:dataset_id AND source_kind=:source_kind AND source_id=:source_id'


def _lock(session, key):
    session.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key,0))'),
                    {'key':'knowledge:'+key.lab_id+':'+key.source_kind+':'+key.source_id})


def _fence(session, key):
    return session.execute(text('SELECT generation,source_revision,deleted FROM d3_knowledge_fence WHERE '+_KEY),
                           key.model_dump()).mappings().first()


def _save_fence(session, command):
    session.execute(text('''INSERT INTO d3_knowledge_fence
      (lab_id,dataset_id,source_kind,source_id,generation,source_revision,deleted)
      VALUES (:lab_id,:dataset_id,:source_kind,:source_id,:generation,:revision,:deleted)
      ON CONFLICT (lab_id,dataset_id,source_kind,source_id) DO UPDATE
      SET generation=EXCLUDED.generation,source_revision=EXCLUDED.source_revision,deleted=EXCLUDED.deleted'''),
      {**command.source_key.model_dump(),'generation':command.processing_version.generation,
       'revision':command.source_version.revision,'deleted':command.source_version.deleted})


def _scope(session, key, principal):
    row = session.execute(text('SELECT current_lab_id(),current_account_id()')).one()
    if tuple(row) != (principal.lab_id, principal.account_id) or key.lab_id != principal.lab_id:
        raise ValueError('forbidden')
    if key.source_kind not in {'evidence','file'}:
        raise ValueError('unsupported source kind')


def _deletion_scope(session, key):
    scope = session.execute(text("SELECT current_lab_id(),current_account_id(),current_setting('app.operator_read',true)")).one()
    if scope[0] != key.lab_id or scope[1] is not None or scope[2] != '' or key.source_kind not in {'evidence','file'}:
        raise ValueError('forbidden')


def _deleted(session, key, revision):
    row = session.execute(text('SELECT requested_version,deleted FROM d3_search_change WHERE '+_KEY),
                          key.model_dump()).mappings().first()
    return row is not None and row['deleted'] and row['requested_version'] == revision


def issue_deletion(session, key, revision, *, ttl_seconds):
    """Only committed exact-source deletion pointers authorize body-free disposal."""
    _deletion_scope(session,key)
    if type(revision) is not int or revision < 1 or type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 3600:
        raise ValueError('forbidden')
    _lock(session,key)
    if not _deleted(session,key,revision):
        raise ValueError('stale_source')
    fence = _fence(session,key)
    if fence and revision < fence['source_revision']:
        raise ValueError('stale_source')
    generation = 1 if fence is None else fence['generation'] + (not fence['deleted'] or fence['source_revision'] != revision)
    command = InvalidateCommand.model_validate({'protocol':'knowledge-lifecycle/1','grant':secrets.token_urlsafe(32),
        'source_key':key.model_dump(),'source_version':{'revision':revision,'deleted':True},
        'processing_version':{'generation':generation},'reason':'deleted'})
    _save_fence(session,command)
    session.execute(text('''INSERT INTO d3_knowledge_deletion_grant
      (grant_hash,lab_id,dataset_id,source_kind,source_id,source_revision,generation,payload_digest,expires_at)
      VALUES (:hash,:lab_id,:dataset_id,:source_kind,:source_id,:revision,:generation,:digest,
        clock_timestamp()+make_interval(secs=>:ttl))'''),
      {**key.model_dump(),'hash':hashlib.sha256(command.grant.encode()).hexdigest(),
       'revision':revision,'generation':generation,'digest':payload_digest(command),'ttl':ttl_seconds})
    return command


def validate_deletion(session, command):
    key = command.source_key
    try:
        _deletion_scope(session,key)
    except ValueError:
        return 'forbidden'
    row = session.execute(text('''SELECT payload_digest,source_revision,generation FROM d3_knowledge_deletion_grant
      WHERE '''+_KEY+''' AND grant_hash=:hash AND expires_at>clock_timestamp()'''),
      {**key.model_dump(),'hash':hashlib.sha256(command.grant.encode()).hexdigest()}).mappings().first()
    if (row is None or row['payload_digest'] != payload_digest(command)
        or row['source_revision'] != command.source_version.revision
        or row['generation'] != command.processing_version.generation):
        return 'forbidden'
    if not _deleted(session,key,command.source_version.revision):
        return 'stale_source'
    fence = _fence(session,key)
    if fence is None or not fence['deleted'] or fence['generation'] != command.processing_version.generation:
        return 'stale_generation'
    if fence['source_revision'] != command.source_version.revision:
        return 'stale_source'
    return 'current'


def _source(session, key):
    row = session.execute(text('''SELECT requested_version,deleted FROM d3_search_change
      WHERE lab_id=:lab_id AND dataset_id=:dataset_id AND source_kind=:source_kind AND source_id=:source_id'''),
      key.model_dump()).mappings().first()
    if row is None or row['deleted']:
        raise ValueError('source unavailable')
    claim = changes.Claim(key.lab_id,key.source_kind,key.source_id,key.dataset_id,row['requested_version'],0,False,0)
    source = measured.load_source(session,claim) if key.source_kind == 'file' else facts.load_source(session,claim)
    if source is None or source['status'] != 'ready':
        raise ValueError('source unavailable')
    return source, {'revision':row['requested_version'],'digest':source['source_sha256'],'deleted':False}


def lineage_dependency(key: SourceKey, lineage: LineageRevisionPort) -> dict:
    current=lineage.revisions([Ulid(key.dataset_id)]).get(key.dataset_id)
    if current is None or current.deleted:
        raise ValueError('source lineage revision unavailable')
    return {'owner':'D4','resource_id':key.dataset_id,'revision':current.revision}


def _lineage_current(key, dependencies, lineage):
    try:
        expected=lineage_dependency(key,lineage)
    except ValueError:
        return False
    return [item.model_dump() for item in dependencies if item.owner=='D4']==[expected]


def issue(session, key: SourceKey, principal: Principal, *, ttl_seconds: int,
          lineage: LineageRevisionPort) -> ReplaceCommand:
    """Build the payload from owned evidence and persist a hash-only capability."""
    _scope(session,key,principal)
    if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 3600:
        raise ValueError('ttl must be 1..3600 seconds')
    # Same source is serialized, including its first insert. No source row lock:
    # source writers lock source before recording the change queue at commit.
    _lock(session,key)
    source, version = _source(session,key)
    manifest = ontology.current_manifest(session)
    if not manifest:
        raise ValueError('current ontology required')
    dependencies=[{'owner':'D3','resource_id':key.source_id,'revision':version['revision']},
                  {'owner':'D9','resource_id':'discovery','revision':manifest['entries']['discovery']},
                  lineage_dependency(key,lineage)]
    params = key.model_dump()
    old = session.execute(text('''SELECT generation,command FROM d3_knowledge_source
      WHERE lab_id=:lab_id AND source_kind=:source_kind AND source_id=:source_id'''),params).mappings().first()
    fence = _fence(session,key)
    processing = {'generation':fence['generation'] if fence else 1,'extractor_version':measured.EXTRACTOR if key.source_kind == 'file' else EXTRACTOR,
                  'mapping_version':MAPPING,'ontology_release':manifest['version']}
    if old and fence and not fence['deleted'] and old['command']['source_version'] == version and old['command']['processing_version'] == processing and old['command']['dependencies']==dependencies:
        command = ReplaceCommand.model_validate({**old['command'],'grant':'pending'})
    else:
        if fence:
            processing['generation'] += 1
        command = ReplaceCommand.model_validate({
            'protocol':'knowledge-lifecycle/1','grant':'pending','source_key':params,
            'source_version':version,'processing_version':processing,
            'facts':[{**fact,'fact_id':str(Ulid.generate()),'source_version':version,
                      'evidence_kind':'file_measurement' if key.source_kind == 'file' else 'human_review'}
                     for fact in source['facts']],
            'mappings':[], 'dependencies':dependencies})
        session.execute(text('''INSERT INTO d3_knowledge_source
          (lab_id,dataset_id,source_kind,source_id,generation,command)
          VALUES (:lab_id,:dataset_id,:source_kind,:source_id,:generation,CAST(:command AS jsonb))
          ON CONFLICT (lab_id,source_kind,source_id) DO UPDATE
            SET generation=excluded.generation,command=excluded.command'''),
          {**params,'generation':processing['generation'],'command':json.dumps(command.model_dump(mode='json',exclude={'grant'}))})
    _save_fence(session,command)
    secret = secrets.token_urlsafe(32)
    session.execute(text('''INSERT INTO d3_knowledge_grant
      (grant_hash,lab_id,dataset_id,source_kind,source_id,account_id,session_version,generation,payload_digest,expires_at)
      VALUES (:hash,:lab_id,:dataset_id,:source_kind,:source_id,:account,:session,:generation,:digest,
              clock_timestamp()+make_interval(secs=>:ttl))'''),
      {**params,'hash':hashlib.sha256(secret.encode()).hexdigest(),'account':principal.account_id,
       'session':principal.session_version,'generation':command.processing_version.generation,
       'digest':payload_digest(command),'ttl':ttl_seconds})
    return command.model_copy(update={'grant':secret})


def validate(session, command: ReplaceCommand, principal: Principal, *, lineage: LineageRevisionPort) -> str:
    """Recheck scope, payload, current source and generation; no receipt bypass."""
    try:
        _scope(session,command.source_key,principal)
    except ValueError:
        return 'forbidden'
    row = session.execute(text('''SELECT * FROM d3_knowledge_grant
      WHERE grant_hash=:hash AND account_id=:account AND session_version=:session
        AND expires_at>clock_timestamp()'''),
      {'hash':hashlib.sha256(command.grant.encode()).hexdigest(),'account':principal.account_id,
       'session':principal.session_version}).mappings().first()
    if row is None or row['payload_digest'] != payload_digest(command):
        return 'forbidden'
    key = command.source_key
    fence = _fence(session,key)
    if fence is None or fence['deleted'] or fence['generation'] != command.processing_version.generation:
        return 'stale_generation'
    try:
        _, version = _source(session,key)
    except ValueError:
        return 'stale_source'
    if version != command.source_version.model_dump():
        return 'stale_source'
    # Dependency mismatch is stale canonical source state, not a new wire status.
    if not _lineage_current(key,command.dependencies,lineage):
        return 'stale_source'
    manifest = ontology.current_manifest(session)
    if not manifest or manifest['version'] != command.processing_version.ontology_release:
        return 'stale_release'
    return 'current'


def authorize_read(session, receipt, principal: Principal, *, lineage: LineageRevisionPort) -> str:
    """Current viewer authority; never redeem or create an issuer's grant."""
    key = receipt.source_key
    try:
        _scope(session,key,principal)
    except ValueError:
        return 'forbidden'
    row = session.execute(text('''SELECT generation,command FROM d3_knowledge_source
      WHERE lab_id=:lab_id AND dataset_id=:dataset_id AND source_kind=:source_kind AND source_id=:source_id'''),
      key.model_dump()).mappings().first()
    if row is None or receipt.status != 'replaced':
        return 'forbidden'
    fence = _fence(session,key)
    if fence is None or fence['deleted'] or fence['generation'] != receipt.processing_version.generation or row['generation'] != fence['generation']:
        return 'stale_generation'
    try:
        _, version = _source(session,key)
    except ValueError:
        return 'forbidden'
    if version != receipt.source_version.model_dump():
        return 'stale_source'
    manifest = ontology.current_manifest(session)
    if not manifest or manifest['version'] != receipt.processing_version.ontology_release:
        return 'stale_release'
    canonical = KnowledgePayload.model_validate(row['command'])
    if not _lineage_current(key,canonical.dependencies,lineage):
        return 'stale_source'
    if (canonical.source_key != key or canonical.source_version != receipt.source_version
        or canonical.processing_version != receipt.processing_version
        or payload_digest(canonical) != receipt.payload_digest):
        return 'forbidden'
    return 'current'
