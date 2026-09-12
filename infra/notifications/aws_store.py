"""DynamoDB persistence. Conditional writes fence stale workers; no TTL deletes events."""
from __future__ import annotations

import contextlib
import copy
import datetime as dt
import hashlib
import json
import uuid
from zoneinfo import ZoneInfo

from .delivery import EventConflict
from .events import canonical, validate


def conditional(error):
    response = getattr(error, 'response', {})
    code = response.get('Error', {}).get('Code')
    return code == 'ConditionalCheckFailedException' or (
        code == 'TransactionCanceledException' and any(
            r.get('Code') == 'ConditionalCheckFailed' for r in response.get('CancellationReasons', [])))


class ConcurrentWrite(RuntimeError):
    pass


class DynamoStore:
    def __init__(self, client, table_name: str):
        self.client, self.table_name = client, table_name
        self._claims = {}

    def _read(self, key):
        item = self.client.get_item(TableName=self.table_name, Key={'pk': {'S': key}}, ConsistentRead=True).get('Item')
        if not item:
            return None, None
        return json.loads(item['body']['S']), int(item['version']['N'])

    def _operation(self, key, body, version):
        encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        if len(encoded.encode()) > 350000:
            raise ValueError('operator record exceeds durable item limit; source must remain pending')
        args = {'TableName': self.table_name, 'Item': {'pk': {'S': key}, 'body': {'S': encoded},
                'version': {'N': str((version or 0) + 1)}}}
        if version is None:
            args['ConditionExpression'] = 'attribute_not_exists(pk)'
        else:
            args.update(ConditionExpression='#v=:v', ExpressionAttributeNames={'#v': 'version'},
                        ExpressionAttributeValues={':v': {'N': str(version)}})
        return {'Put': args}

    def _save(self, key, body, version):
        try:
            self.client.put_item(**self._operation(key, body, version)['Put'])
        except Exception as error:
            if conditional(error):
                raise ConcurrentWrite('operator state changed concurrently') from None
            raise

    def _all(self, prefix):
        args = {'TableName': self.table_name, 'ConsistentRead': True}
        result = {}
        while True:
            page = self.client.scan(**args)
            for item in page.get('Items', []):
                key = item['pk']['S']
                if key.startswith(prefix):
                    result[key] = (json.loads(item['body']['S']), int(item['version']['N']))
            if not page.get('LastEvaluatedKey'):
                return result
            args['ExclusiveStartKey'] = page['LastEvaluatedKey']

    def put(self, record):
        record = validate(record)
        digest = hashlib.sha256(canonical({k: v for k, v in record.items() if k != 'received_at'})).hexdigest()
        key = 'event#' + record['event_id']
        old, version = self._read(key)
        if old:
            if old['record_hash'] != digest:
                raise EventConflict('same event ID has different content')
            return False
        try:
            self._save(key, {'record': record, 'record_hash': digest, 'state': 'pending',
                             'attempt': 0, 'resolutions': []}, version)
        except ConcurrentWrite:
            return self.put(record)
        return True

    def get(self, event_id):
        item, _ = self._read('event#' + event_id)
        if item is None:
            raise KeyError(event_id)
        return item

    def claim(self, event_id, now):
        key = 'event#' + event_id
        item, version = self._read(key)
        if not item or item['state'] in {'sent', 'held', 'uncertain'}:
            return None
        if item['state'] == 'sending':
            if dt.datetime.fromisoformat(item['lease_until']) > now:
                return None
            item['duplicate_warning'] = True
            if item['record']['severity'] not in {'critical', 'error'}:
                item.update(state='uncertain', reason='worker_lease_expired', unresolved_since=now.isoformat())
                self._save(key, item, version)
                return None
        if item.get('next_at') and dt.datetime.fromisoformat(item['next_at']) > now:
            return None
        payload = item['record']['payload']
        if payload.get('report_id') and payload.get('part', 1) > 1:
            for other, _ in self._all('event#').values():
                p = other['record']['payload']
                if (p.get('report_id'), p.get('revision')) == (payload['report_id'], payload.get('revision')):
                    if p.get('part', 1) < payload['part'] and other['state'] != 'sent':
                        return None
        channel_key = 'channel#' + item['record']['channel']
        channel, channel_version = self._read(channel_key)
        if channel and dt.datetime.fromisoformat(channel['available_at']) > now:
            return None
        token = uuid.uuid4().hex
        item.update(state='sending', attempt=item['attempt'] + 1, claimed_at=now.isoformat(),
                    lease_until=(now + dt.timedelta(seconds=30)).isoformat(), claim_token=token)
        channel = {'token': token, 'available_at': item['lease_until'],
                   'next_send_at': (now + dt.timedelta(seconds=1)).isoformat()}
        try:
            self.client.transact_write_items(TransactItems=[self._operation(key, item, version),
                self._operation(channel_key, channel, channel_version)])
        except Exception as error:
            if conditional(error):
                return None
            raise
        self._claims[event_id] = token
        return copy.deepcopy(item)

    def mark_uncertain(self, event_id, *, duplicate_warning=True, claim_token=None):
        item, version = self._read('event#' + event_id)
        token = claim_token or self._claims.get(event_id)
        if item.get('claim_token') != token:
            return
        item['duplicate_warning'] = duplicate_warning
        self._save('event#' + event_id, item, version)

    def finish(self, event_id, state, next_at, reason, *, rendered=None, claim_token=None):
        key = 'event#' + event_id
        item, version = self._read(key)
        token = claim_token or self._claims.get(event_id)
        if item['state'] != 'sending' or item.get('claim_token') != token:
            return
        item.update(state=state, reason=reason, next_at=next_at.isoformat() if next_at else None)
        if state in {'uncertain', 'held'}:
            item.setdefault('unresolved_since', item['claimed_at'])
        if rendered is not None:
            item.update(rendered=rendered, body_hash=hashlib.sha256(rendered.encode()).hexdigest())
        item.pop('claim_token', None)
        item.pop('lease_until', None)
        operations = [self._operation(key, item, version)]
        channel_key = 'channel#' + item['record']['channel']
        channel, cv = self._read(channel_key)
        if channel and channel.get('token') == token:
            channel['available_at'] = channel['next_send_at']
            channel.pop('token', None)
            operations.append(self._operation(channel_key, channel, cv))
        try:
            self.client.transact_write_items(TransactItems=operations)
        except Exception as error:
            if conditional(error):
                return
            raise

    def due(self, now):
        rows = []
        for key, (item, _) in self._all('event#').items():
            due = item['state'] in {'pending', 'retry_wait'} and (not item.get('next_at') or dt.datetime.fromisoformat(item['next_at']) <= now)
            expired = item['state'] == 'sending' and dt.datetime.fromisoformat(item['lease_until']) <= now
            if due or expired:
                p = item['record']['payload']
                rows.append(((p.get('report_date', ''), p.get('revision', 0), p.get('part', 0), key), key[6:]))
        return [event_id for _, event_id in sorted(rows)]

    def resolve(self, event_id, action, actor, now):
        if action not in {'confirmed-sent', 'retry'} or not actor:
            raise ValueError('explicit resolution and actor required')
        item, version = self._read('event#' + event_id)
        if not item or item['state'] not in {'uncertain', 'held'}:
            raise ValueError('event does not require resolution')
        item.update(state='sent' if action == 'confirmed-sent' else 'retry_wait', next_at=None)
        if action == 'retry':
            item['duplicate_warning'] = True
        item['resolutions'].append({'action': action, 'actor': actor, 'at': now.isoformat()})
        self._save('event#' + event_id, item, version)

    def unresolved(self, now):
        return [v for v, _ in self._all('event#').values() if v['state'] in {'uncertain', 'held'}]

    def record_collection(self, collection):
        DynamoArchive(self).record_collection(collection)

    def accept_archive(self, record, day=None):
        required = {'source_id', 'lab_id', 'actor_id', 'target_id', 'action', 'occurred_at'}
        if required - record.keys():
            raise ValueError('audit source fields missing')
        occurred = dt.datetime.fromisoformat(record['occurred_at'])
        if occurred.tzinfo is None:
            raise ValueError('aware audit timestamp required')
        actual_day = occurred.astimezone(ZoneInfo('Asia/Seoul')).date().isoformat()
        if day is not None and day != actual_day:
            raise ValueError('audit day mismatch')
        digest = hashlib.sha256(canonical(record)).hexdigest()
        receipt = {'source_id': record['source_id'], 'content_hash': digest,
                   'receipt_hash': hashlib.sha256((record['source_id'] + digest).encode()).hexdigest()}
        key = 'audit#' + record['source_id']
        old, version = self._read(key)
        if old:
            if old['hash'] != digest:
                raise EventConflict('audit source ID collision')
            return receipt
        _, dirty_version = self._read('dirty#' + actual_day)
        try:
            self.client.transact_write_items(TransactItems=[self._operation(key, {'record': record, 'hash': digest}, version),
                self._operation('dirty#' + actual_day, {'dirty': True}, dirty_version)])
        except Exception as error:
            if conditional(error):
                raise ConcurrentWrite('retry audit export after concurrent archive update') from None
            raise
        return receipt

    def archive_snapshot(self):
        return {'events': {k[6:]: v for k, (v, _) in self._all('audit#').items()},
                'dirty': {k[6:]: v['dirty'] for k, (v, _) in self._all('dirty#').items()},
                'reports': {k[7:]: v for k, (v, _) in self._all('report#').items()}}


class DynamoArchive:
    """Report state adapter with a version fence against concurrent late arrivals."""
    def __init__(self, store):
        self.store = store
        self._baseline = None

    def accept(self, record):
        receipt = self.store.accept_archive(record)
        self._baseline = None
        return receipt

    def record_collection(self, collection):
        if collection.get('status') not in {'complete', 'partial', 'failed'}:
            raise ValueError('explicit collection status required')
        observed = dt.datetime.fromisoformat(collection['collected_at'])
        if observed.tzinfo is None:
            raise ValueError('aware collection timestamp required')
        old, version = self.store._read('collection#latest')
        if old and dt.datetime.fromisoformat(old['collected_at']) > observed:
            raise ValueError('older collection snapshot cannot replace newer facts')
        self.store._save('collection#latest', collection, version)
        self._baseline = None

    def _pack_report(self, report):
        packed = copy.deepcopy(report)
        if 'parts' in packed:
            refs = []
            for part in packed.pop('parts'):
                key = 'report-part#' + hashlib.sha256(canonical(part)).hexdigest()
                old, version = self.store._read(key)
                if old is None:
                    try:
                        self.store._save(key, part, version)
                    except ConcurrentWrite:
                        existing, _ = self.store._read(key)
                        if existing != part:
                            raise EventConflict('immutable report part collision')
                elif old != part:
                    raise EventConflict('immutable report part collision')
                refs.append(key)
            packed['part_refs'] = refs
        packed['history'] = [self._pack_report(h) for h in packed.get('history', [])]
        return packed

    def _unpack_report(self, packed):
        report = copy.deepcopy(packed)
        if 'part_refs' in report:
            report['parts'] = []
            for key in report.pop('part_refs'):
                part, _ = self.store._read(key)
                if part is None:
                    raise ValueError('durable report part missing')
                report['parts'].append(part)
        report['history'] = [self._unpack_report(h) for h in report.get('history', [])]
        return report

    def snapshot(self):
        metadata = self.store._read('collection#latest')
        dirties = self.store._all('dirty#')
        audits = self.store._all('audit#')
        reports = self.store._all('report#')
        data = {'events': {k[6:]: v for k, (v, _) in audits.items()},
                'dirty': {k[6:]: v['dirty'] for k, (v, _) in dirties.items()},
                'reports': {k[7:]: self._unpack_report(v) for k, (v, _) in reports.items()}}
        if metadata[0] is not None:
            data['collection'] = metadata[0]
        self._baseline = (copy.deepcopy(data), dirties, reports, metadata)
        return data

    @contextlib.contextmanager
    def transaction(self):
        if self._baseline is None:
            self.snapshot()
        before, dirties, reports, metadata = self._baseline
        self._baseline = None
        after = copy.deepcopy(before)
        yield after
        operations = []
        changed_reports = {k for k, v in after['reports'].items() if v != before['reports'].get(k)}
        for group, prefix, existing in [('dirty', 'dirty#', dirties), ('reports', 'report#', reports)]:
            for key, value in after[group].items():
                if value != before[group].get(key) or (group == 'dirty' and key in changed_reports):
                    version = existing.get(prefix + key, (None, None))[1]
                    body = {'dirty': value} if group == 'dirty' else self._pack_report(value)
                    operations.append(self.store._operation(prefix + key, body, version))
        if changed_reports and metadata[0] is not None:
            operations.append(self.store._operation('collection#latest', metadata[0], metadata[1]))
        if len(operations) > 100:
            raise ValueError('report transaction exceeds atomic write limit')
        if operations:
            try:
                self.store.client.transact_write_items(TransactItems=operations)
            except Exception as error:
                if conditional(error):
                    raise ConcurrentWrite('report snapshot changed; regenerate before publishing') from None
                raise
        self._baseline = None
