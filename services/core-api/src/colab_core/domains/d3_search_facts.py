"""Deterministic source facts: input tools for later agent/KG orchestration.

No ontology writes, raw file access or LLM execution. Callers own transactions.
Ready means eligible for authorized retrieval, not globally public knowledge.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from . import d3_search_changes as changes
from . import d3_file_measurement as measured

EXTRACTOR_VERSION = 'structured-v1'


class CommitRejected(RuntimeError):
    """Snapshot and queue completion were rolled back together."""


def _version(value: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 100:
        raise ValueError('extractor version must contain 1..100 characters')


def load_source(session: Session, item: changes.Claim) -> dict | None:
    """Read one authorized source, without a source row lock or file storage key."""
    params = asdict(item)
    parent = session.execute(text('''SELECT id,source_label FROM d3_dataset
        WHERE id=:dataset_id AND lab_id=:lab_id AND deleted_at IS NULL'''), params).mappings().first()
    if parent is None:
        return None
    if item.source_kind == 'metadata':
        if item.source_id != item.dataset_id:
            return None
        desc = session.execute(text('''SELECT name,summary,category,data_type,topic
            FROM d3_dataset_description WHERE dataset_id=:dataset_id'''), params).mappings().first()
        auto = session.execute(text('''SELECT format,period_start,period_end,crs,grid
            FROM d3_dataset_autometa WHERE dataset_id=:dataset_id'''), params).mappings().first()
        variables = session.execute(text('''SELECT name,unit,value_range,missing_rate,is_representative
            FROM d3_dataset_variable WHERE dataset_id=:dataset_id ORDER BY ordinal'''), params).mappings()
        grid = session.execute(text('''SELECT west,south,east,north,map_state FROM d3_dataset_grid_profile
            WHERE dataset_id=:dataset_id'''), params).mappings().first()
        body = {**dict(desc or {}), 'source_label': parent['source_label'],
                'autometa': dict(auto or {}), 'variables': [dict(v) for v in variables],
                'grid_profile': dict(grid or {})}
        file_revision = evidence_revision = None
        status = 'ready'
        locator = 'metadata'
    elif item.source_kind in {'file', 'evidence'}:
        file = session.execute(text('''SELECT file_name,kind,content_revision FROM d3_file
            WHERE id=:source_id AND dataset_id=:dataset_id AND lab_id=:lab_id'''), params).mappings().first()
        if file is None:
            return None
        file_revision = file['content_revision']
        evidence_revision = None
        body = {'file_name': file['file_name'], 'kind': file['kind']}
        status, locator = 'ready', 'file'
        if item.source_kind == 'evidence':
            evidence = session.execute(text('''SELECT revision,file_revision,status,facts,
                source_locator,source_text,source_sha256 FROM d3_search_evidence
                WHERE file_id=:source_id AND dataset_id=:dataset_id AND lab_id=:lab_id'''), params).mappings().first()
            if evidence is None or evidence['file_revision'] != file_revision:
                return None
            if hashlib.sha256(evidence['source_text'].encode()).hexdigest() != evidence['source_sha256']:
                return None
            body = dict(evidence['facts'])
            evidence_revision = evidence['revision']
            status = 'ready' if evidence['status'] == 'reviewed' else 'candidate'
            locator = evidence['source_locator']
            # Include provenance in the digest, without duplicating the raw source text.
            body_digest_extra = [evidence['source_sha256'], locator, evidence['status']]
    else:
        return None
    # Timestamps become ISO strings; the same conversion is used for source hashing and facts.
    body = json.loads(json.dumps(body, ensure_ascii=False, sort_keys=True, default=str))
    extra = body_digest_extra if item.source_kind == 'evidence' else []
    digest = hashlib.sha256(json.dumps([body,file_revision,evidence_revision,extra],
        ensure_ascii=False,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
    fact_rows = [{'predicate':key, 'value':value,
                  'source_locator':locator+'#/'+key.replace('~','~0').replace('/','~1')}
                 for key,value in body.items() if value is not None and value != [] and value != {}]
    return {'source_sha256':digest,'file_revision':file_revision,
            'evidence_revision':evidence_revision,'status':status,'facts':fact_rows}


def process(session: Session, item: changes.Claim, *, extractor_version: str = EXTRACTOR_VERSION) -> str:
    """Consume one claim atomically; stale or inaccessible input never becomes ready."""
    _version(extractor_version)
    with session.begin_nested():
        # Queue lock only. Source writers acquire their source locks first and queue at
        # commit; taking a source write lock below would invert that ordering.
        queue = session.execute(text('''SELECT * FROM d3_search_change
            WHERE lab_id=:lab_id AND source_kind=:source_kind AND source_id=:source_id
            FOR UPDATE'''), asdict(item)).mappings().first()
        valid = session.execute(text('''SELECT 1 FROM d3_search_change
            WHERE lab_id=:lab_id AND source_kind=:source_kind AND source_id=:source_id
              AND dataset_id=:dataset_id AND requested_version=:claimed_version
              AND claimed_version=:claimed_version AND lease_generation=:lease_generation
              AND lease_until>clock_timestamp()'''), asdict(item)).first()
        if not valid:
            return 'stale'
        parent = session.execute(text('''SELECT deleted_at FROM d3_dataset
            WHERE id=:dataset_id AND lab_id=:lab_id'''), asdict(item)).mappings().first()
        if queue['deleted'] or (parent is not None and parent['deleted_at'] is not None):
            if not changes.ack(session,item):
                raise CommitRejected('expired before tombstone completion')
            return 'deleted'
        source = measured.load_source(session,item) if extractor_version == measured.EXTRACTOR else load_source(session,item)
        if source is None:
            changes.fail(session,item,error_code='source_unavailable')
            return 'source_unavailable'
        session.execute(text('''INSERT INTO d3_search_fact_snapshot
            (id,lab_id,dataset_id,source_kind,source_id,source_version,file_revision,evidence_revision,
             source_sha256,extractor_version,status,facts)
            VALUES (:id,:lab_id,:dataset_id,:source_kind,:source_id,:claimed_version,
              :file_revision,:evidence_revision,:source_sha256,:extractor,:status,CAST(:facts AS jsonb))
            ON CONFLICT (lab_id,source_kind,source_id,source_version,extractor_version) DO NOTHING'''),
            {**asdict(item),**source,'id':str(Ulid.generate()),'extractor':extractor_version,
             'facts':json.dumps(source['facts'],ensure_ascii=False)})
        if not changes.ack(session,item):
            raise CommitRejected('expired before snapshot completion')
        return source['status']


def read_current(session: Session, dataset_id: str, *, extractor_version: str = EXTRACTOR_VERSION) -> list[dict]:
    """Only ready, current, authorized facts. RLS also protects raw table reads."""
    _version(extractor_version)
    rows = session.execute(text('''SELECT * FROM d3_search_fact_snapshot
        WHERE dataset_id=:dataset AND status='ready' AND extractor_version=:extractor
        ORDER BY source_kind,source_id'''), {'dataset':str(Ulid(dataset_id)), 'extractor':extractor_version}).mappings()
    out = []
    for row in rows:
        item = changes.Claim(row['lab_id'],row['source_kind'],row['source_id'],row['dataset_id'],
                             row['source_version'],0,False,0)
        source = measured.load_source(session,item) if extractor_version == measured.EXTRACTOR else load_source(session,item)
        if source and source['status']=='ready' and source['source_sha256']==row['source_sha256']:
            out.append(dict(row))
    return out


def reconcile(session: Session, *, extractor_version: str = EXTRACTOR_VERSION,
              limit: int = 100) -> list[str]:
    """Requeue bounded completed snapshots from older extractors; never read bodies.

    Call until empty in the authorized scope. Initial missing sources use the separate
    changes.bootstrap ID pages. Ontology dependency invalidation is not connected yet.
    """
    _version(extractor_version)
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    return list(session.execute(text('''WITH pending AS (
        SELECT q.lab_id,q.source_kind,q.source_id FROM d3_search_change q
        WHERE q.requested_version=q.processed_version AND q.lease_until IS NULL AND NOT q.deleted
          AND EXISTS (SELECT 1 FROM d3_search_fact_snapshot f WHERE f.lab_id=q.lab_id
            AND f.source_kind=q.source_kind AND f.source_id=q.source_id
            AND f.source_version=q.requested_version AND f.extractor_version<>:extractor)
          AND NOT EXISTS (SELECT 1 FROM d3_search_fact_snapshot f WHERE f.lab_id=q.lab_id
            AND f.source_kind=q.source_kind AND f.source_id=q.source_id
            AND f.source_version=q.requested_version AND f.extractor_version=:extractor)
        ORDER BY q.source_kind,q.source_id LIMIT :limit FOR UPDATE OF q SKIP LOCKED
      ) UPDATE d3_search_change q SET requested_version=q.requested_version+1,
          updated_at=clock_timestamp(),retry_after=clock_timestamp()
        FROM pending p WHERE (q.lab_id,q.source_kind,q.source_id)=(p.lab_id,p.source_kind,p.source_id)
        RETURNING q.source_id'''), {'extractor':extractor_version,'limit':limit}).scalars())


def source_deleted(session: Session, item: changes.Claim) -> bool:
    """Deletion proof only; unavailable/private is never inferred to be deleted.

    The caller must validate the captured change lease before using this proof.
    """
    if item.deleted:
        return True
    parent=session.execute(text('SELECT deleted_at FROM d3_dataset WHERE id=:id AND lab_id=:lab'),
                           {'id':item.dataset_id,'lab':item.lab_id}).mappings().first()
    return parent is not None and parent['deleted_at'] is not None
