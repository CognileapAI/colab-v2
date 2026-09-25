"""Content-version receipts and read dependencies, without semantic inference.

Callers own transactions. This module never connects to the ontology database.
"""
from __future__ import annotations

import json
from sqlalchemy import text
from ..kernel.ids import Ulid
from ..ports.ontology import validate_manifest
from . import d3_search_facts as facts


def _lock(session):
    lab=session.execute(text('SELECT current_lab_id()')).scalar_one()
    if lab is None:
        raise ValueError('lab scope required')
    # Serialize receipt publishing, binding and requeue within this lab. Source
    # readers remain lock-free; no source->queue / queue->source lock inversion.
    session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('ontology:'||:lab,0))"),{'lab':lab})
    return lab


def _head(session):
    return session.execute(text('''SELECT r.manifest FROM d3_search_ontology_head h
      JOIN d3_search_ontology_release r ON (r.lab_id,r.version)=(h.lab_id,h.version)
      WHERE h.lab_id=current_lab_id()''')).scalar_one_or_none()


def publish(session, manifest: dict, *, expected_previous: str | None) -> str:
    manifest=validate_manifest(manifest)
    lab=_lock(session); previous=_head(session); version=manifest['version']
    if previous and previous['version']==version:
        return version
    if (previous['version'] if previous else None)!=expected_previous:
        raise ValueError('ontology head changed; reload before publishing')
    session.execute(text('''INSERT INTO d3_search_ontology_release(lab_id,version,manifest)
      VALUES (:lab,:version,CAST(:manifest AS jsonb)) ON CONFLICT DO NOTHING'''),
      {'lab':lab,'version':version,'manifest':json.dumps(manifest,ensure_ascii=False)})
    session.execute(text('''INSERT INTO d3_search_ontology_head(lab_id,version) VALUES (:lab,:version)
      ON CONFLICT (lab_id) DO UPDATE SET version=excluded.version'''),{'lab':lab,'version':version})
    return version


def bind(session, fact_id: str, *, expected_version: str, concept_ids: list[str]) -> str:
    lab=_lock(session); manifest=_head(session)
    if not manifest or manifest['version']!=expected_version:
        raise ValueError('ontology head changed')
    if not isinstance(concept_ids,list) or any(not isinstance(c,str) for c in concept_ids):
        raise ValueError('concept IDs must be a list of strings')
    keys={'discovery',*('concept:'+c for c in concept_ids)}
    if not keys<=manifest['entries'].keys():
        raise ValueError('unknown concept dependency')
    fact=session.execute(text('SELECT dataset_id FROM d3_search_fact_snapshot WHERE id=:id'),{'id':str(Ulid(fact_id))}).scalar_one_or_none()
    if fact is None or fact_id not in {r['id'] for r in facts.read_current(session,fact)}:
        raise ValueError('current ready source required')
    wanted={key:manifest['entries'][key] for key in keys}
    existing=session.execute(text('''SELECT id FROM d3_search_ontology_binding
      WHERE lab_id=:lab AND fact_snapshot_id=:fact AND ontology_version=:version'''),
      {'lab':lab,'fact':fact_id,'version':expected_version}).scalar_one_or_none()
    if existing:
        deps=dict(session.execute(text('''SELECT dependency_key,digest FROM d3_search_ontology_dependency
          WHERE binding_id=:id'''),{'id':existing}).all())
        if deps!=wanted:
            raise ValueError('a receipt cannot overwrite its recorded read dependencies')
        return existing
    binding=str(Ulid.generate())
    with session.begin_nested():
        session.execute(text('''INSERT INTO d3_search_ontology_binding(id,lab_id,fact_snapshot_id,ontology_version,expected_dependencies)
          VALUES (:id,:lab,:fact,:version,CAST(:expected AS jsonb))'''),{'id':binding,'lab':lab,'fact':fact_id,'version':expected_version,'expected':json.dumps(wanted)})
        session.execute(text('''INSERT INTO d3_search_ontology_dependency(lab_id,binding_id,dependency_key,digest)
          VALUES (:lab,:binding,:key,:digest)'''),
          [{'lab':lab,'binding':binding,'key':key,'digest':value} for key,value in wanted.items()])
    return binding


# Always require discovery: an empty or partially-written receipt is not valid.
_VALID = """(SELECT count(*) FROM d3_search_ontology_dependency d WHERE d.binding_id=b.id)
    = (SELECT count(*) FROM jsonb_object_keys(b.expected_dependencies))
  AND EXISTS (SELECT 1 FROM d3_search_ontology_dependency d
  WHERE d.binding_id=b.id AND d.dependency_key='discovery')
  AND NOT EXISTS (SELECT 1 FROM d3_search_ontology_dependency d
    WHERE d.binding_id=b.id AND (d.digest IS DISTINCT FROM (CAST(:entries AS jsonb) ->> d.dependency_key)
      OR d.digest IS DISTINCT FROM (b.expected_dependencies ->> d.dependency_key)))"""


def current_bindings(session, dataset_id: str) -> list[dict]:
    _lock(session)
    manifest=_head(session)
    if not manifest:
        return []
    rows=session.execute(text('''SELECT b.* FROM d3_search_ontology_binding b
      JOIN d3_search_fact_snapshot f ON f.id=b.fact_snapshot_id
      WHERE f.dataset_id=:dataset AND '''+_VALID+' ORDER BY b.id'),
      {'dataset':str(Ulid(dataset_id)),'entries':json.dumps(manifest['entries'])}).mappings()
    current={r['id'] for r in facts.read_current(session,dataset_id)}
    return [dict(r) for r in rows if r['fact_snapshot_id'] in current]


def requeue(session, *, limit: int = 100) -> list[str]:
    if type(limit) is not int or not 1<=limit<=1000:
        raise ValueError('limit must be 1..1000')
    _lock(session); manifest=_head(session)
    if not manifest:
        raise ValueError('ontology head required')
    # Old bindings remain in history; any compatible binding makes requeue unnecessary.
    return list(session.execute(text('''WITH pending AS (
      SELECT q.lab_id,q.source_kind,q.source_id FROM d3_search_change q
      WHERE q.requested_version=q.processed_version AND q.lease_until IS NULL AND NOT q.deleted
        AND EXISTS (SELECT 1 FROM d3_search_fact_snapshot f JOIN d3_search_ontology_binding b
          ON b.fact_snapshot_id=f.id WHERE f.lab_id=q.lab_id AND f.source_kind=q.source_kind
          AND f.source_id=q.source_id AND f.source_version=q.requested_version)
        AND NOT EXISTS (SELECT 1 FROM d3_search_fact_snapshot f JOIN d3_search_ontology_binding b
          ON b.fact_snapshot_id=f.id WHERE f.lab_id=q.lab_id AND f.source_kind=q.source_kind
          AND f.source_id=q.source_id AND f.source_version=q.requested_version AND '''+_VALID+''')
      ORDER BY q.source_kind,q.source_id LIMIT :limit FOR UPDATE OF q SKIP LOCKED
    ) UPDATE d3_search_change q SET requested_version=q.requested_version+1,
      retry_after=clock_timestamp(),updated_at=clock_timestamp()
      FROM pending p WHERE (q.lab_id,q.source_kind,q.source_id)=(p.lab_id,p.source_kind,p.source_id)
      RETURNING q.source_id'''),{'limit':limit,'entries':json.dumps(manifest['entries'])}).scalars())


def current_manifest(session) -> dict | None:
    """Capture the lab's current receipt while serializing with publication."""
    _lock(session)
    return _head(session)
