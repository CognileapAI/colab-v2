"""Internal, lab-scoped incremental search work. Callers own short transactions.

Commit claims before reading/processing sources. A pointer grants no body access.
Ack fences ledger state only: future result writers must fence their writes too.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid


@dataclass(frozen=True)
class Claim:
    lab_id: str
    source_kind: str
    source_id: str
    dataset_id: str
    claimed_version: int
    lease_generation: int
    deleted: bool
    attempts: int


def _bounded(value: int, maximum: int, name: str) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f'{name} must be an integer between 1 and {maximum}')


def claim(session: Session, *, limit: int = 100, lease_seconds: int = 300, authorized_only: bool = False) -> list[Claim]:
    """Lease disjoint pending pointers; commit promptly, then load authorized sources."""
    _bounded(limit, 1000, 'limit')
    _bounded(lease_seconds, 3600, 'lease_seconds')
    rows = session.execute(text("""
        WITH pending AS (
          SELECT lab_id, source_kind, source_id FROM d3_search_change q
          WHERE requested_version > processed_version
            AND (NOT :authorized_only OR (q.deleted OR EXISTS (
              SELECT 1 FROM d3_dataset d WHERE d.id=q.dataset_id AND d.lab_id=q.lab_id
                AND (d.deleted_at IS NOT NULL OR q.source_kind='metadata' OR EXISTS (
                  SELECT 1 FROM d3_file f WHERE f.id=q.source_id AND f.dataset_id=q.dataset_id
                    AND f.lab_id=q.lab_id)))))
            AND retry_after <= clock_timestamp()
            AND (lease_until IS NULL OR lease_until <= clock_timestamp())
          ORDER BY retry_after, updated_at, source_kind, source_id
          LIMIT :limit FOR UPDATE SKIP LOCKED
        )
        UPDATE d3_search_change q
        SET claimed_version=q.requested_version, lease_generation=q.lease_generation+1,
            lease_until=clock_timestamp()+make_interval(secs => :seconds), attempts=q.attempts+1
        FROM pending p WHERE (q.lab_id,q.source_kind,q.source_id)=(p.lab_id,p.source_kind,p.source_id)
        RETURNING q.lab_id,q.source_kind,q.source_id,q.dataset_id,q.claimed_version,
                  q.lease_generation,q.deleted,q.attempts
    """), {'limit': limit, 'seconds': lease_seconds, 'authorized_only': authorized_only}).mappings()
    return [Claim(**row) for row in rows]


_FENCE = """ WHERE lab_id=:lab_id AND source_kind=:source_kind AND source_id=:source_id
    AND lease_generation=:lease_generation AND claimed_version=:claimed_version
    AND lease_until > clock_timestamp()"""


def _lock(session: Session, item: Claim) -> bool:
    # Evaluate expiry in the NEXT statement, after any row-lock wait. PostgreSQL
    # can otherwise evaluate UPDATE's clock predicate before waiting on a lock.
    return session.execute(text("""SELECT 1 FROM d3_search_change
        WHERE lab_id=:lab_id AND source_kind=:source_kind AND source_id=:source_id
        FOR UPDATE"""), asdict(item)).scalar_one_or_none() is not None


def ack(session: Session, item: Claim) -> bool:
    """Complete only the captured version; concurrent edits stay pending."""
    if not _lock(session, item):
        return False
    return session.execute(text("""UPDATE d3_search_change SET
        processed_version=:claimed_version, claimed_version=NULL, lease_until=NULL,
        attempts=0, retry_after=clock_timestamp(), last_error_code=NULL
        """ + _FENCE), asdict(item)).rowcount == 1


def fail(session: Session, item: Claim, *, error_code: str, retry_seconds: int = 60) -> bool:
    """Record a bounded code, never arbitrary source text or exception messages."""
    if error_code not in {'source_unavailable', 'processing_failed', 'transient'}:
        raise ValueError('unsupported error code')
    _bounded(retry_seconds, 86400, 'retry_seconds')
    if not _lock(session, item):
        return False
    return session.execute(text("""UPDATE d3_search_change SET
        claimed_version=NULL, lease_until=NULL, last_error_code=:error,
        retry_after=clock_timestamp()+make_interval(secs => :seconds)
        """ + _FENCE), {**asdict(item), 'error': error_code, 'seconds': retry_seconds}).rowcount == 1


def renew(session: Session, item: Claim, *, lease_seconds: int = 300) -> bool:
    _bounded(lease_seconds, 3600, 'lease_seconds')
    if not _lock(session, item):
        return False
    return session.execute(text("""UPDATE d3_search_change
        SET lease_until=clock_timestamp()+make_interval(secs => :seconds)
        """ + _FENCE), {**asdict(item), 'seconds': lease_seconds}).rowcount == 1


# Closed SQL fragments: no caller-provided table/column names are interpolated.
_SOURCES = {
    'metadata': ('d3_dataset', 'id', 'id', 'deleted_at IS NOT NULL'),
    'file': ('d3_file', 'id', 'dataset_id', 'false'),
    'evidence': ('d3_search_evidence', 'file_id', 'dataset_id', 'false'),
}


def bootstrap(session: Session, *, source_kind: str, after: Ulid | None = None,
              limit: int = 100) -> list[str]:
    """Return one page of visible IDs, enqueue missing ones without resetting progress.

    Repeat per kind and authorized scope using the last returned ID as cursor until
    empty. This is explicit initialization, not a daily timestamp cursor. Source RLS
    remains active; a lab-only account does not automatically see private files.
    """
    _bounded(limit, 1000, 'limit')
    if source_kind not in _SOURCES:
        raise ValueError('unsupported source kind')
    if after is not None:
        after = Ulid(after)
    table, key, dataset, deleted = _SOURCES[source_kind]
    return list(session.execute(text(f"""
        WITH page AS MATERIALIZED (
          SELECT lab_id, {key} AS source_id, {dataset} AS dataset_id, {deleted} AS deleted
          FROM {table} WHERE (CAST(:after AS text) IS NULL OR {key} > CAST(:after AS text))
          ORDER BY {key} LIMIT :limit
        ), inserted AS (
          INSERT INTO d3_search_change (lab_id,source_kind,source_id,dataset_id,deleted)
          SELECT lab_id,:kind,source_id,dataset_id,deleted FROM page
          ON CONFLICT (lab_id,source_kind,source_id) DO NOTHING
        ) SELECT source_id FROM page ORDER BY source_id
    """), {'kind': source_kind, 'after': after, 'limit': limit}).scalars())


def is_current(session: Session, item: Claim) -> bool:
    """A lease permits source tools only while its captured request is current."""
    return session.execute(text('SELECT 1 FROM d3_search_change'+_FENCE+
        ' AND requested_version=:claimed_version AND dataset_id=:dataset_id'), asdict(item)).first() is not None
