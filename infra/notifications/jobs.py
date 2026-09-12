"""Daily scheduling and an outbox that survives generation/publication interruptions."""
from __future__ import annotations
import datetime as dt
from zoneinfo import ZoneInfo
from .digest import build, event_id
from .events import make_event


def run(now: dt.datetime, manifest: dict, archive) -> list[dict]:
    if now.tzinfo is None:
        raise ValueError('aware job clock required')
    local = now.astimezone(ZoneInfo('Asia/Seoul'))
    if local.hour < 8 or manifest.get('usage') != 'live':
        return []
    yesterday = local.date() - dt.timedelta(days=1)
    coverage = dt.datetime.fromisoformat(manifest['coverage_started_at']).astimezone(ZoneInfo('Asia/Seoul')).date()
    result = []
    current = coverage
    while current <= yesterday:
        # Revisit even empty dates: a generated but unpublished report has no audit
        # dirty flag, and a collection failure can recover without a new audit row.
        result.extend(build(current.isoformat(), dict(manifest, run_at=now.isoformat()), archive))
        current += dt.timedelta(days=1)
    return result


def publish(parts: list[dict], manifest: dict, archive, delivery_store) -> int:
    count = 0
    groups = {}
    for part in parts:
        groups.setdefault((part['report_date'], part['revision']), []).append(part)
    for (date, revision), group in sorted(groups.items()):
        snapshot = archive.snapshot()['reports'][date]
        group.sort(key=lambda p: p['part'])
        if snapshot['revision'] != revision or snapshot['parts'] != group:
            raise ValueError('publisher must use the complete immutable outbox revision')
        occurred = dt.datetime.combine(dt.date.fromisoformat(date) + dt.timedelta(days=1),
                                      dt.time(), ZoneInfo('Asia/Seoul'))
        for part in group:
            record = make_event(source='operator-digest', environment=manifest['environment'], severity='info',
                channel='activity', occurred_at=occurred, event_id=event_id(part),
                payload={'kind': 'activity.digest', **part})
            count += int(delivery_store.put(record))
        # If interrupted above, generated parts remain replayable. Repeated event
        # insertion is idempotent and does not change already accepted text.
        with archive.transaction() as data:
            report = data['reports'][date]
            if report['revision'] != revision:
                raise ValueError('outbox revision changed during publication')
            if report['status'] == 'generated':
                report['status'] = 'published'
    return count


def reconcile(archive, delivery_store) -> int:
    snapshot = archive.snapshot()
    completed = 0
    for date, report in snapshot['reports'].items():
        if report.get('status') != 'published':
            continue
        try:
            sent = all(delivery_store.get(identity)['state'] == 'sent' for identity in report['event_ids'])
        except KeyError:
            sent = False
        if sent:
            with archive.transaction() as data:
                current = data['reports'][date]
                if current['revision'] == report['revision'] and current['status'] == 'published':
                    current['status'] = 'sent'
                    current['complete'] = current['collection_complete']
                    completed += 1
    return completed
