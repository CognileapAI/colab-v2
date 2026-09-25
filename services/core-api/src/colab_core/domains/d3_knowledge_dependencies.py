"""D3-owned dependency progress and requeue share one caller-owned transaction."""
from sqlalchemy import text
from ..kernel.knowledge_wire import SourceKey
from . import d3_knowledge_source as source


def page(session, *, after_source, limit):
    params={'limit':limit,'kind':after_source.source_kind if after_source else '',
            'id':after_source.source_id if after_source else ''}
    rows=session.execute(text('''SELECT q.lab_id,q.dataset_id,q.source_kind,q.source_id
      FROM d3_search_change q
      JOIN d3_file f ON f.id=q.source_id AND f.dataset_id=q.dataset_id AND f.lab_id=q.lab_id
      JOIN d3_dataset d ON d.id=f.dataset_id AND d.lab_id=f.lab_id
      WHERE q.source_kind IN ('evidence','file') AND NOT q.deleted AND d.deleted_at IS NULL
        AND (q.source_kind,q.source_id)>(:kind,:id)
      ORDER BY q.source_kind,q.source_id LIMIT :limit'''),params).mappings()
    return [SourceKey.model_validate(dict(row)) for row in rows]


def lock_batch(session, keys, principal):
    """Fix the batch and acquire all knowledge locks before touching any queue.

    Match source._lock's identity/order, including across concurrent sweeps.
    Caller must reread current source authority and D4 revisions after waiting.
    """
    unique={(key.lab_id,key.source_kind,key.source_id):key for key in keys}
    batch=tuple(unique[identity] for identity in sorted(unique))
    for key in batch:source._scope(session,key,principal)
    for key in batch:source._lock(session,key)
    return batch


def requeue_if_lineage_changed(session, key, principal, current):
    """Caller holds lock_batch for this fixed key set until the batch commits."""
    source._scope(session,key,principal)
    # A retained D4 marker is not source existence or body authority.
    visible=session.execute(text('''SELECT 1 FROM d3_file f JOIN d3_dataset d ON d.id=f.dataset_id
      WHERE f.id=:source_id AND f.dataset_id=:dataset_id AND f.lab_id=:lab_id
        AND d.deleted_at IS NULL'''),key.model_dump()).first()
    if visible is None:raise ValueError('forbidden')
    if current is None or current.dataset_id!=key.dataset_id or current.deleted:
        raise ValueError('stale_source')
    old=session.execute(text('''SELECT lineage_revision FROM d3_knowledge_dependency
      WHERE lab_id=:lab_id AND source_kind=:source_kind AND source_id=:source_id'''),key.model_dump()).scalar_one_or_none()
    if old==current.revision:return False
    if old is not None and old>current.revision:raise ValueError('stale_source')
    # Reopen the same source revision; dependency changes do not invent new bytes.
    changed=session.execute(text('''UPDATE d3_search_change SET processed_version=0,
      claimed_version=NULL,lease_until=NULL,lease_generation=lease_generation+1,
      attempts=0,retry_after=clock_timestamp(),last_error_code=NULL
      WHERE lab_id=:lab_id AND dataset_id=:dataset_id AND source_kind=:source_kind
        AND source_id=:source_id AND NOT deleted RETURNING source_id'''),key.model_dump()).first()
    if changed is None:raise ValueError('stale_source')
    session.execute(text('''UPDATE d3_knowledge_fence SET generation=generation+1
      WHERE lab_id=:lab_id AND dataset_id=:dataset_id AND source_kind=:source_kind
        AND source_id=:source_id AND NOT deleted'''),key.model_dump())
    session.execute(text('''INSERT INTO d3_knowledge_dependency
      (lab_id,dataset_id,source_kind,source_id,lineage_revision)
      VALUES (:lab_id,:dataset_id,:source_kind,:source_id,:revision)
      ON CONFLICT (lab_id,source_kind,source_id) DO UPDATE
        SET lineage_revision=excluded.lineage_revision'''),{**key.model_dump(),'revision':current.revision})
    return True
