"""Bounded SSH relay from Stage spools to the Dev AWS notification store."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from .events import canonical, validate


MAX_INPUT_BYTES = 350_000
MAX_RECEIPT_BYTES = 4_096
TARGETS = {'service-health', 'backup-freshness', 'deploy-verification'}
DEV_RELEASE_KINDS = {'deploy.succeeded', 'deploy.failed', 'deploy.verification_failed'}


def receipt_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _checked_envelope(envelope):
    if not isinstance(envelope, dict):
        raise ValueError('relay envelope required')
    if envelope.get('kind') == 'event':
        record = validate(envelope.get('record'))
        dev_release = (record['environment'] == 'dev' and record['source'] == 'release' and
                       record['channel'] == 'development' and
                       record['payload']['kind'] in DEV_RELEASE_KINDS)
        if record['environment'] != 'staging' and not dev_release:
            raise ValueError('relay accepts staging events or dev release terminal events only')
        return {'kind': 'event', 'record': record}
    if envelope.get('kind') == 'heartbeat':
        if envelope.get('environment') != 'staging' or envelope.get('target') not in TARGETS:
            raise ValueError('relay accepts staging heartbeats only')
        observed = dt.datetime.fromisoformat(envelope.get('observed_at', ''))
        if observed.tzinfo is None:
            raise ValueError('aware heartbeat timestamp required')
        return {'kind': 'heartbeat', 'environment': 'staging', 'target': envelope['target'],
                'observed_at': observed.astimezone(dt.timezone.utc).isoformat()}
    raise ValueError('unknown relay envelope')


def receive(envelope, store):
    envelope = _checked_envelope(envelope)
    if envelope['kind'] == 'event':
        record = envelope['record']
        store.put(record)
        saved = store.get(record['event_id'])['record']
        if canonical(saved) != canonical(record):
            raise ValueError('durable receipt mismatch')
        return {'event_id': record['event_id'], 'receipt_hash': receipt_hash(saved)}
    from .handlers import record_heartbeat
    observed = dt.datetime.fromisoformat(envelope['observed_at'])
    record_heartbeat(store, 'staging', envelope['target'], observed)
    saved, _ = store._read('heartbeat#staging:' + envelope['target'])
    if not saved or dt.datetime.fromisoformat(saved['observed_at']) < observed:
        raise ValueError('heartbeat was not durably accepted')
    return {'event_id': None, 'receipt_hash': receipt_hash(envelope)}


def _send(envelope, ssh_target, ssh_key, receiver_command, *, ssh_executable='ssh', timeout=30):
    envelope = _checked_envelope(envelope)
    if (not isinstance(ssh_target, str) or not ssh_target or ssh_target.startswith('-') or
            any(c.isspace() or c == '\x00' for c in ssh_target)):
        raise ValueError('bounded SSH target required')
    if (not receiver_command or len(receiver_command) > 32 or
            any(not isinstance(v, str) or not v or '\x00' in v for v in receiver_command)):
        raise ValueError('bounded receiver command required')
    remote = shlex.join(receiver_command)
    if len(remote) > 4096:
        raise ValueError('receiver command too long')
    body = canonical(envelope)
    if len(body) > MAX_INPUT_BYTES:
        raise ValueError('relay input too large')
    completed = subprocess.run(
        [str(ssh_executable), '-i', str(ssh_key), '-o', 'BatchMode=yes', ssh_target, remote],
        input=body, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout, check=False,
    )
    if completed.returncode or len(completed.stdout) > MAX_RECEIPT_BYTES:
        raise OSError('relay transport failed')
    receipt = json.loads(completed.stdout)
    subject = envelope['record'] if envelope['kind'] == 'event' else envelope
    if (not isinstance(receipt, dict) or receipt.get('receipt_hash') != receipt_hash(subject) or
            receipt.get('event_id') != subject.get('event_id')):
        raise ValueError('relay receipt mismatch')
    return receipt


def send_spool(directory, ssh_target, ssh_key, receiver_command, *, ssh_executable='ssh', timeout=30):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError('spool directory is not prepared')
    accepted = 0
    for path in sorted(directory.glob('*.json')):
        try:
            raw = path.read_bytes()
            if len(raw) > MAX_INPUT_BYTES:
                raise ValueError('relay input too large')
            record = validate(json.loads(raw))
            _send({'kind': 'event', 'record': record}, ssh_target, ssh_key, receiver_command,
                  ssh_executable=ssh_executable, timeout=timeout)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError,
                subprocess.SubprocessError):
            continue
        path.unlink()
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        accepted += 1
    return {'accepted': accepted, 'pending': len(list(directory.glob('*.json')))}


def send_heartbeat(environment, target, observed_at, ssh_target, ssh_key, receiver_command,
                   *, ssh_executable='ssh', timeout=30):
    envelope = {'kind': 'heartbeat', 'environment': environment, 'target': target,
                'observed_at': observed_at.isoformat() if isinstance(observed_at, dt.datetime) else observed_at}
    return _send(envelope, ssh_target, ssh_key, receiver_command,
                 ssh_executable=ssh_executable, timeout=timeout)


def _connected_store():
    from .aws_store import DynamoStore
    from .handlers import _client, runtime_config
    config = runtime_config()
    return DynamoStore(_client('dynamodb', None), config['table'])


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('send', 'heartbeat'):
        command = commands.add_parser(name)
        command.add_argument('--ssh-target', required=True)
        command.add_argument('--ssh-key', required=True)
        command.add_argument('--timeout', type=float, default=30)
        if name == 'send':
            command.add_argument('--spool', required=True)
        else:
            command.add_argument('--environment', choices=('staging',), required=True)
            command.add_argument('--target', choices=tuple(sorted(TARGETS)), required=True)
            command.add_argument('--observed-at', required=True)
        command.add_argument('--receiver-command', nargs=argparse.REMAINDER, required=True)
    commands.add_parser('receive')
    args = parser.parse_args(argv)
    try:
        if args.command == 'receive':
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
            if len(raw) > MAX_INPUT_BYTES:
                raise ValueError('relay input too large')
            print(json.dumps(receive(json.loads(raw), _connected_store()), separators=(',', ':')))
            return 0
        common = (args.ssh_target, Path(args.ssh_key), args.receiver_command)
        if args.command == 'send':
            result = send_spool(Path(args.spool), *common, timeout=args.timeout)
            print(json.dumps(result, separators=(',', ':')))
            return 20 if result['pending'] else 0
        receipt = send_heartbeat(args.environment, args.target, args.observed_at, *common,
                                 timeout=args.timeout)
        print(json.dumps(receipt, separators=(',', ':')))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError,
            subprocess.SubprocessError):
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
