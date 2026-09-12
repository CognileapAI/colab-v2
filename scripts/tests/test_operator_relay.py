import datetime as dt
import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from infra.notifications.events import canonical, make_event
from infra.notifications import handlers, spool
from scripts.tests.test_operator_aws_runtime import CONFIG, DynamoSDK


NOW = dt.datetime(2026, 9, 12, tzinfo=dt.timezone.utc)


def event():
    return make_event(
        source='stage-probe', environment='staging', severity='error', channel='development',
        occurred_at=NOW, event_id='stage-relay-event',
        payload={'kind': 'probe.failed', 'target': 'service-health'},
    )


def dev_release(kind='deploy.succeeded', source='release', channel='development'):
    return make_event(
        source=source, environment='dev', severity='info', channel=channel,
        occurred_at=NOW, event_id='dev-release-event-' + kind.replace('.', '-'),
        payload={'kind': kind, 'release_id': 'release-20260912'},
    )


class RelayTests(unittest.TestCase):
    def stub(self, root):
        path = Path(root) / 'ssh-stub'
        path.write_text(textwrap.dedent('''\
            #!/usr/bin/env python3
            import hashlib, json, os, sys
            raw = sys.stdin.buffer.read()
            with open(os.environ['STUB_CAPTURE'], 'ab') as stream:
                stream.write(raw + b'\\n')
            if os.environ.get('STUB_MODE') == 'fail':
                raise SystemExit(255)
            envelope = json.loads(raw)
            subject = envelope['record'] if envelope['kind'] == 'event' else envelope
            canonical = json.dumps(subject, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
            digest = hashlib.sha256(canonical).hexdigest()
            if os.environ.get('STUB_MODE') == 'wrong':
                digest = '0' * 64
            print(json.dumps({'receipt_hash': digest, 'event_id': subject.get('event_id')}))
        '''))
        path.chmod(0o700)
        return path

    def test_successful_sha_receipt_deletes_spool_item(self):
        from infra.notifications import relay
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); directory = root / 'spool'; capture = root / 'capture'
            spool.append(directory, event())
            with mock.patch.dict(os.environ, {'STUB_CAPTURE': str(capture)}, clear=False):
                result = relay.send_spool(directory, 'dev-host', root / 'key', ['receiver'],
                                          ssh_executable=str(self.stub(root)))
            self.assertEqual(result, {'accepted': 1, 'pending': 0})
            self.assertEqual(list(directory.glob('*.json')), [])
            sent = json.loads(capture.read_text())
            self.assertEqual(sent['record']['event_id'], 'stage-relay-event')

    def test_wrong_receipt_and_ssh_failure_keep_stable_local_item(self):
        from infra.notifications import relay
        for mode in ('wrong', 'fail'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); directory = root / 'spool'; capture = root / 'capture'
                spool.append(directory, event()); stub = self.stub(root)
                with mock.patch.dict(os.environ, {'STUB_CAPTURE': str(capture), 'STUB_MODE': mode}, clear=False):
                    result = relay.send_spool(directory, 'dev-host', root / 'key', ['receiver'], ssh_executable=str(stub))
                self.assertEqual(result, {'accepted': 0, 'pending': 1})
                self.assertEqual(json.loads(next(directory.glob('*.json')).read_text())['event_id'], 'stage-relay-event')
                with mock.patch.dict(os.environ, {'STUB_CAPTURE': str(capture), 'STUB_MODE': ''}, clear=False):
                    self.assertEqual(relay.send_spool(directory, 'dev-host', root / 'key', ['receiver'], ssh_executable=str(stub))['accepted'], 1)
                attempts = [json.loads(line) for line in capture.read_text().splitlines()]
                self.assertEqual({row['record']['event_id'] for row in attempts}, {'stage-relay-event'})

    def test_receiver_persists_stage_event_before_returning_receipt(self):
        from infra.notifications import relay
        store = handlers.DynamoStore(DynamoSDK(), 'table')
        receipt = relay.receive({'kind': 'event', 'record': event()}, store)
        saved = store.get('stage-relay-event')['record']
        self.assertEqual(receipt['receipt_hash'], relay.receipt_hash(saved))
        invalid = event(); invalid['environment'] = 'dev'
        with self.assertRaises(ValueError):
            relay.receive({'kind': 'event', 'record': invalid}, store)

    def test_receiver_accepts_only_dev_release_terminal_events(self):
        from infra.notifications import relay
        store = handlers.DynamoStore(DynamoSDK(), 'table')
        for kind in ('deploy.succeeded', 'deploy.failed', 'deploy.verification_failed'):
            record = dev_release(kind)
            receipt = relay.receive({'kind': 'event', 'record': record}, store)
            self.assertEqual(receipt['receipt_hash'], relay.receipt_hash(record))
        rejected = [
            dev_release('deploy.succeeded', source='arbitrary'),
            make_event(source='release', environment='dev', severity='error', channel='development',
                       occurred_at=NOW, event_id='dev-release-probe',
                       payload={'kind': 'probe.failed', 'target': 'service-health'}),
            make_event(source='release', environment='dev', severity='info', channel='activity',
                       occurred_at=NOW, event_id='dev-release-activity',
                       payload={'kind': 'activity.digest', 'text': 'not allowed'}),
        ]
        for record in rejected:
            with self.assertRaises(ValueError):
                relay.receive({'kind': 'event', 'record': record}, store)
        with self.assertRaises(ValueError):
            relay.receive({'kind': 'heartbeat', 'environment': 'dev',
                           'target': 'service-health', 'observed_at': NOW.isoformat()}, store)

    def test_late_heartbeat_does_not_replace_newer_observation(self):
        from infra.notifications import relay
        store = handlers.DynamoStore(DynamoSDK(), 'table')
        newer = NOW + dt.timedelta(minutes=2)
        for observed in (newer, NOW):
            envelope = {'kind': 'heartbeat', 'environment': 'staging',
                        'target': 'service-health', 'observed_at': observed.isoformat()}
            receipt = relay.receive(envelope, store)
            self.assertEqual(receipt['receipt_hash'], relay.receipt_hash(envelope))
        saved, _ = store._read('heartbeat#staging:service-health')
        self.assertEqual(saved['observed_at'], newer.isoformat())

    def test_missing_heartbeats_cover_dev_and_staging(self):
        sdk = DynamoSDK(); store = handlers.DynamoStore(sdk, 'table')
        config = json.loads(json.dumps(CONFIG))
        config['manifest'].update(
            monitored_environments=['dev', 'staging'],
            probes=['service-health', 'backup-freshness', 'deploy-verification'],
            coverage_started_at=NOW.isoformat(),
        )
        handlers._heartbeats(store, config, NOW + dt.timedelta(minutes=16))
        records = [item['record'] for item, _ in store._all('event#').values()]
        self.assertEqual(len(records), 6)
        self.assertEqual({row['environment'] for row in records}, {'dev', 'staging'})
        self.assertEqual({row['payload']['target'] for row in records},
                         {'service-health', 'backup-freshness', 'deploy-verification'})


if __name__ == '__main__':
    unittest.main()
