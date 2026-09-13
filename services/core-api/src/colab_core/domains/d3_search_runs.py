"""Per-authenticated-account refresh leases and durable bootstrap checkpoints."""
from __future__ import annotations
import json
from sqlalchemy import text
from . import d3_search_changes as changes

_WHERE=' WHERE lab_id=current_lab_id() AND account_id=current_account_id()'


def status(session):
    row=session.execute(text("SELECT *, (manifest_checked_at IS NULL OR manifest_checked_at < clock_timestamp()-interval '1 day') AS manifest_due FROM d3_search_refresh_run"+_WHERE)).mappings().first()
    return dict(row) if row else None


def claim_run(session):
    session.execute(text("""INSERT INTO d3_search_refresh_run(lab_id,account_id)
      VALUES (current_lab_id(),current_account_id()) ON CONFLICT DO NOTHING"""))
    session.execute(text('SELECT 1 FROM d3_search_refresh_run'+_WHERE+' FOR UPDATE'))
    return session.execute(text("""UPDATE d3_search_refresh_run SET generation=generation+1,
      lease_until=clock_timestamp()+interval '10 minutes',status='running',updated_at=clock_timestamp()
      """+_WHERE+""" AND next_run<=clock_timestamp() AND (lease_until IS NULL OR lease_until<=clock_timestamp())
      RETURNING generation""")).scalar_one_or_none()


def _current(session,generation):
    session.execute(text('SELECT 1 FROM d3_search_refresh_run'+_WHERE+' FOR UPDATE'))
    return session.execute(text('SELECT 1 FROM d3_search_refresh_run'+_WHERE+
      ' AND generation=:generation AND lease_until>clock_timestamp()'),{'generation':generation}).first() is not None


def checkpoint(session,generation, *, bootstrap=None, manifest_checked=False):
    if not _current(session,generation):raise ValueError('refresh run lease expired')
    if bootstrap is not None:
        session.execute(text('UPDATE d3_search_refresh_run SET bootstrap=CAST(:value AS jsonb),updated_at=clock_timestamp()'+_WHERE),
                        {'value':json.dumps(bootstrap)})
    if manifest_checked:
        session.execute(text('UPDATE d3_search_refresh_run SET manifest_checked_at=clock_timestamp()'+_WHERE))


def bootstrap_page(session,generation, *, limit=100):
    if not _current(session,generation):raise ValueError('refresh run lease expired')
    cursors=status(session)['bootstrap']
    for kind in ('metadata','file','evidence'):
        state=cursors.get(kind,{})
        if state.get('done'):continue
        page=changes.bootstrap(session,source_kind=kind,after=state.get('after'),limit=limit)
        cursors[kind]={'after':page[-1] if page else state.get('after'),'done':len(page)<limit}
        break
    checkpoint(session,generation,bootstrap=cursors)
    return all(cursors.get(kind,{}).get('done') for kind in ('metadata','file','evidence'))


def pending(session):
    return session.execute(text("""SELECT count(*) FROM d3_search_change q
      WHERE q.requested_version>q.processed_version AND (q.deleted OR EXISTS (
        SELECT 1 FROM d3_dataset d WHERE d.id=q.dataset_id AND d.lab_id=q.lab_id
          AND (d.deleted_at IS NOT NULL OR q.source_kind='metadata' OR EXISTS (
            SELECT 1 FROM d3_file f WHERE f.id=q.source_id AND f.dataset_id=q.dataset_id AND f.lab_id=q.lab_id))))""")).scalar_one()


def finish(session,generation, *, summary, pending, failed=False):
    if not _current(session,generation):return False
    if any(k not in {'processed','ready','candidate','deleted','failed'} or type(v) is not int or v<0 for k,v in summary.items()):
        raise ValueError('invalid run summary')
    session.execute(text("""UPDATE d3_search_refresh_run SET lease_until=NULL, status=:status,
      next_run=clock_timestamp()+make_interval(secs => :seconds),summary=CAST(:summary AS jsonb),updated_at=clock_timestamp()
      """+_WHERE),{'status':'failed' if failed else 'pending' if pending else 'complete',
      'seconds':60 if (pending or failed) else 86400,'summary':json.dumps(summary)})
    return True
