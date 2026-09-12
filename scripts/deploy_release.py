#!/usr/bin/env python3
"""Execute a pinned release, verify every target, then notify Slack without a Stop hook."""
import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
sys_path_root = str(Path(__file__).resolve().parents[1])
import re
import subprocess
import sys
if sys_path_root not in sys.path: sys.path.insert(0,sys_path_root)
import uuid

try:
    from scripts import slack_completion as slack
except ModuleNotFoundError:
    import slack_completion as slack


class ReleaseError(ValueError):
    pass


class ReleaseBusy(ReleaseError):
    pass


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def state_directory(root):
    common = subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', '--path-format=absolute', '--git-common-dir'], text=True
    ).strip()
    return Path(common) / 'deploy-releases'


def save(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


@contextlib.contextmanager
def release_lock(directory):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(directory / 'deployment.lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ReleaseBusy('다른 배포가 실행 중입니다.') from None
        yield fd
    finally:
        os.close(fd)


def validate(plan, root):
    if not isinstance(plan, dict) or plan.get('schema') != 'colab-deploy/1':
        raise ReleaseError('배포 계획 schema가 필요합니다.')
    if not isinstance(plan.get('id'), str) or plan['id'] in ('.', '..', 'deployment.lock') or not re.fullmatch(r'[A-Za-z0-9._-]{1,120}', plan['id']):
        raise ReleaseError('고정된 배포 id가 필요합니다.')
    targets = plan.get('targets')
    if not isinstance(targets, list) or not targets or len(targets) > 2:
        raise ReleaseError('배포 대상 dv/st를 선언하세요.')
    names = set()
    for target in targets:
        if not isinstance(target, dict) or target.get('name') not in ('dv', 'st') or target['name'] in names:
            raise ReleaseError('알 수 없거나 중복된 배포 대상입니다.')
        names.add(target['name'])
        if not isinstance(target.get('version'), str) or not target['version'].strip():
            raise ReleaseError('각 대상의 배포 버전이 필요합니다.')
        for phase in ('deploy', 'verify'):
            commands = target.get(phase)
            if not isinstance(commands, list) or not commands:
                raise ReleaseError('각 대상에 배포 명령과 실제 검증 명령이 모두 필요합니다.')
            for argv in commands:
                if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or not a or '\0' in a for a in argv):
                    raise ReleaseError('명령은 비어 있지 않은 argv 배열이어야 합니다.')
    for item in plan.get('inputs', []):
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not re.fullmatch(r'[0-9a-f]{64}', str(item.get('sha256', ''))):
            raise ReleaseError('입력 파일 path/sha256이 필요합니다.')
        path = root / item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ReleaseError('고정한 배포 입력이 없거나 변경됐습니다.')
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def execute_command(argv, cwd, env, log):
    # No shell interpolation. Credentials belong in protected files/environment, never in the plan.
    inherited = {int(env['COLAB_DEPLOY_LOCK_FD'])}
    if env.get('COLAB_PIPELINE_LOCK_HELD') == '1':
        try:
            os.fstat(9)
        except OSError:
            pass
        else:
            inherited.add(9)
    with subprocess.Popen(argv, cwd=cwd, env=env, pass_fds=tuple(inherited), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as child:
        for line in child.stdout:
            log.write(line)
            log.flush()
            print(line, end='', flush=True)
        return child.wait()


def flush_operator_outbox(plan, state, path):
    from infra.notifications.spool import append
    for event in state['operator_outbox']:
        append(Path(plan['operator_notifications']['spool_directory']), event)
    state['notification'] = 'queued'
    save(path, state)
    return 0 if state['deployment'] == 'verified' else 1


def persist_operator_outbox(plan, state, path, events):
    state['operator_outbox'] = events
    state['notification_event_ids'] = [event['event_id'] for event in events]
    state['notification'] = 'pending'
    # Save terminal result and immutable records together BEFORE touching the spool.
    save(path, state)
    return flush_operator_outbox(plan, state, path)


def run_plan(root, plan, *, state_dir=None, secret_path=slack.DEFAULT_SECRET,
             execute=execute_command, sender=slack.send_webhook, retry_notification=False):
    root = Path(root).resolve()
    fingerprint = validate(plan, root)
    directory = Path(state_dir) if state_dir is not None else state_directory(root)
    with release_lock(directory) as lock_fd:
        record_dir = directory / plan['id']
        record_dir.mkdir(mode=0o700, exist_ok=True)
        path = record_dir / 'state.json'
        previous = path.exists()
        if previous:
            state = json.loads(path.read_text())
            if state.get('plan_hash') != fingerprint or state.get('root') != str(root):
                raise ReleaseError('같은 배포 id의 계획/버전/작업 사본이 변경됐습니다.')
            if plan.get('operator_notifications') and state.get('operator_outbox') and state['notification'] == 'pending':
                return flush_operator_outbox(plan, state, path)
            if state['notification'] == 'sent':
                return 0
            if state['notification'] == 'queued':
                if state['deployment'] != 'verified': return 1
                return 20 if retry_notification else 0
            if state['notification'] in ('sending', 'uncertain'):
                state['notification'] = 'uncertain'
                save(path, state)
                return 20
            if not retry_notification or state['deployment'] != 'verified' or state['notification'] != 'failed':
                raise ReleaseError('기존 실행 상태를 먼저 확인하세요. 배포는 자동 재실행하지 않습니다.')
        else:
            if retry_notification:
                raise ReleaseError('알림을 재시도할 완료 배포가 없습니다.')
            state = {'schema': 'colab-release-state/1', 'id': plan['id'], 'plan_hash': fingerprint,
                     'root': str(root), 'started_at': now(), 'deployment': 'pending',
                     'notification': 'pending', 'targets': {t['name']: {'version': t['version'], 'deploy': 'pending', 'verify': 'pending'} for t in plan['targets']}, 'steps': []}
            save(record_dir / 'plan.json', plan)
            save(path, state)
        env = dict(os.environ, COLAB_DEPLOY_MANAGED='1', COLAB_DEPLOY_RELEASE_ID=plan['id'], COLAB_DEPLOY_LOCK_FD=str(lock_fd))
        phases = () if previous else ('deploy', 'verify')
        for phase in phases:
            for target in plan['targets']:
                # Recheck pinned artifacts before *each* phase, including after deployment.
                validate(plan, root)
                name = target['name']
                state['deployment'] = 'deploying' if phase == 'deploy' else 'verifying'
                state['targets'][name][phase] = 'running'
                save(path, state)
                for index, argv in enumerate(target[phase]):
                    log_path = record_dir / f"{name}.{phase}.{len(state['steps'])}.log"
                    fd = os.open(log_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
                    with os.fdopen(fd, 'w') as log:
                        try:
                            code = execute(argv, root, env, log)
                        except Exception:
                            code = 78
                    state['steps'].append({'target': name, 'phase': phase, 'index': index, 'exit': code, 'log': str(log_path), 'at': now()})
                    if code != 0:
                        state['targets'][name][phase] = 'failed'
                        state['deployment'] = 'failed' if phase == 'deploy' else 'verification_failed'
                        operator = plan.get('operator_notifications')
                        if operator:
                            from infra.notifications.producers import release_result
                            environment = {'dv': 'dev', 'st': 'staging'}[name]
                            event = release_result(plan['id'], environment, phase, code,
                                                   target['version'], datetime.datetime.now(datetime.timezone.utc))
                            return persist_operator_outbox(plan, state, path, [event])
                        save(path, state)
                        return 1
                state['targets'][name][phase] = 'passed'
                save(path, state)
        if not all(t['deploy'] == 'passed' and t['verify'] == 'passed' for t in state['targets'].values()):
            raise ReleaseError('모든 배포와 검증이 끝나지 않았습니다.')
        state['deployment'] = 'verified'
        state['verified_at'] = now()
        state['notification'] = 'pending'
        operator = plan.get('operator_notifications')
        if operator:
            from infra.notifications.producers import release_result
            events = []
            for target in plan['targets']:
                environment = {'dv': 'dev', 'st': 'staging'}[target['name']]
                event = release_result(plan['id'], environment, 'verify', 0, target['version'],
                                       datetime.datetime.now(datetime.timezone.utc))
                events.append(event)
            return persist_operator_outbox(plan, state, path, events)
        save(path, state)
        try:
            secret = slack.validate_url(Path(secret_path).read_text())
        except Exception:
            state['notification'] = 'failed'
            state['notification_reason'] = 'webhook_configuration'
            save(path, state)
            return 20
        text = '배포와 검증이 완료됐습니다.\n' + str(plan.get('summary', '서비스 변경 사항을 반영했습니다.')) + '\n' + '\n'.join(
            f"• {t['name'].upper()}: {t['version']} — 배포·검증 통과" for t in plan['targets'])
        text += '\n완료 알림은 배포 실행기에서 자동 전송했습니다.\n배포 기록: ' + plan['id']
        state['notification'] = 'sending'
        save(path, state)  # Persist BEFORE network I/O: a crash must not cause duplicate delivery.
        try:
            sender(secret, text)
        except slack.CompletionError:
            state['notification'] = 'failed'
            state['notification_reason'] = 'slack_rejected'
        except Exception:
            state['notification'] = 'uncertain'
            state['notification_reason'] = 'delivery_unknown'
        else:
            state['notification'] = 'sent'
            state.pop('notification_reason', None)
            state['notified_at'] = now()
        save(path, state)
        return 0 if state['notification'] == 'sent' else 20


def staging_plan(root, args):
    # Preserve legacy argument validation: no default staging/prod fallback.
    if '--target' not in args or args[args.index('--target') + 1:args.index('--target') + 2] != ['staging']:
        raise ReleaseError('--target staging을 명시하세요.')
    sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    return {'schema': 'colab-deploy/1', 'id': 'st-' + uuid.uuid4().hex, 'summary': 'ST 서비스를 새 버전으로 배포했습니다.',
            'operator_notifications': {'spool_directory': os.environ.get('COLAB_OPERATOR_SPOOL_DIRECTORY','/var/lib/colab/operator-spool')},
            'targets': [{'name': 'st', 'version': sha[:12] + '-tree-' + slack.snapshot(root)[:12],
                         'deploy': [['bash', 'infra/staging/deploy.sh', *args]],
                         'verify': [['bash', 'infra/staging/verify/verify-deploy.sh'], ['bash', 'infra/staging/verify/verify-chains.sh']]}]}


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('run')
    run.add_argument('--plan', required=True)
    run.add_argument('--check', action='store_true', help='validate without deploying or notifying')
    run.add_argument('--retry-notification', action='store_true')
    staging = sub.add_parser('staging')
    staging.add_argument('args', nargs=argparse.REMAINDER)
    status = sub.add_parser('status')
    status.add_argument('id')
    args = parser.parse_args(argv)
    try:
        root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()).resolve()
        if args.command == 'status':
            if args.id in ('.', '..', 'deployment.lock') or not re.fullmatch(r'[A-Za-z0-9._-]{1,120}', args.id):
                raise ReleaseError('잘못된 배포 id입니다.')
            print((state_directory(root) / args.id / 'state.json').read_text())
            return 0
        plan = staging_plan(root, [a for a in args.args if a != '--']) if args.command == 'staging' else json.loads(Path(args.plan).read_text())
        plan.setdefault('operator_notifications', {'spool_directory': os.environ.get('COLAB_OPERATOR_SPOOL_DIRECTORY','/var/lib/colab/operator-spool')})
        if args.command == 'run' and args.check:
            validate(plan, root)
            print('배포 계획 확인 완료 — 실행·전송 없음')
            return 0
        code = run_plan(root, plan, retry_notification=getattr(args, 'retry_notification', False))
        print('배포 기록: ' + str(state_directory(root) / plan['id'] / 'state.json'))
        print({0: '배포·검증 완료 (알림 상태는 배포 기록에서 확인)' , 1: '배포 또는 검증 실패 — 완료 알림 없음', 20: '알림 전달 대기·실패 또는 전송 결과 불명확 — 전달 작업 상태를 확인하고 배포를 다시 실행하지 마세요.'}[code])
        return code
    except ReleaseBusy as error:
        print(str(error), file=sys.stderr)
        return 75
    except (ReleaseError, OSError, ValueError, subprocess.SubprocessError):
        print('배포 준비 실패 — 계획·입력·기존 실행 기록을 확인하세요.', file=sys.stderr)
        return 78


if __name__ == '__main__':
    raise SystemExit(cli())
