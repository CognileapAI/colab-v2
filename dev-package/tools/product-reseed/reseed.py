#!/usr/bin/env python3
"""Durable, fail-closed orchestration; infrastructure commands come from a reviewed plan.

Run on the designated persistent execution host, never in an ephemeral runner.
This command does not infer deployment credentials or implement reset operations.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


STAGES = ('preflight', 'deploy', 'reset', 'bootstrap', 'up', 's3', 'prelude', 'seed', 'verify', 'report')


class Rejected(ValueError):
    pass


class NotReady(OSError):
    pass


def argv_valid(value):
    return (isinstance(value, list) and bool(value)
            and all(isinstance(x, str) and x and '\0' not in x for x in value))


def validate(plan, *, provision=False):
    if not isinstance(plan, dict) or plan.get('schema') != 'colab-product-reseed/1':
        raise Rejected('지원하지 않는 최초 실행 계획입니다.')
    if plan.get('environment') != 'prod':
        raise Rejected('운영 전용 계획이어야 합니다.')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', str(plan.get('id', ''))):
        raise Rejected('실행 식별자가 올바르지 않습니다.')
    for key, size in [('candidate_sha', 40), ('manifest_sha', 64)]:
        if key == 'candidate_sha' and provision and plan.get(key) is None:
            continue
        if not re.fullmatch('[0-9a-f]{' + str(size) + '}', str(plan.get(key, ''))):
            raise Rejected('고정된 후보와 입력 식별자가 필요합니다.')
    stages = plan.get('stages')
    if not isinstance(stages, list) or any(not isinstance(x, dict) for x in stages):
        raise Rejected('단계 계획이 필요합니다.')
    if tuple(x.get('name') for x in stages) != STAGES:
        raise Rejected('10개 단계가 지정된 순서로 모두 필요합니다.')
    if not all(argv_valid(x.get('argv')) for x in stages):
        raise Rejected('실행 명령은 비어 있지 않은 argv 목록이어야 합니다.')
    maintenance = plan.get('maintenance')
    if not isinstance(maintenance, dict) or not all(argv_valid(maintenance.get(x)) for x in ('enter', 'status', 'leave')):
        raise Rejected('점검 진입·확인·해제 명령이 필요합니다.')
    binding = {key: value for key, value in plan.items() if key != 'candidate_sha'}
    return hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def save(path, record):
    fd, name = tempfile.mkstemp(prefix='.record-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(record, stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(name).unlink(missing_ok=True)


@contextlib.contextmanager
def locked(directory, provision):
    if directory.is_symlink():
        raise Rejected('상태 디렉터리 심볼릭 링크를 거부합니다.')
    if provision:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not directory.is_dir():
        raise NotReady('사전에 등록한 운영 실행 기록이 없습니다.')
    if directory.stat().st_mode & 0o077:
        raise Rejected('상태 디렉터리는 소유자만 접근할 수 있어야 합니다.')
    flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
    descriptor = os.open(directory / '.execution.lock', flags, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Rejected('다른 운영 실행이 진행 중입니다.') from exc
        yield descriptor
    finally:
        os.close(descriptor)


def decide_initialization(record, manifest_sha, resume):
    if record.get('manifest_sha') != manifest_sha:
        raise Rejected('최초 실행 입력이 변경됐습니다.')
    state = record.get('state')
    if state == 'succeeded':
        return 'skip'
    if state == 'ready' and not resume:
        return 'start'
    if state in ('failed', 'running') and resume:
        return 'resume'
    raise Rejected('중단된 실행은 사람이 기록 확인 후 재개해야 합니다.')


def validate_record(record, plan):
    completed = record.get('completed')
    if not isinstance(completed, list) or completed != list(STAGES[:len(completed)]):
        raise Rejected('완료 단계 기록의 순서가 올바르지 않습니다.')
    candidate_matches = record.get('candidate_sha') == plan['candidate_sha']
    unbound_ready = record.get('candidate_sha') is None and record.get('state') == 'ready'
    if (record.get('id') != plan['id'] or not (candidate_matches or unbound_ready)
            or not isinstance(record.get('results'), list)):
        raise Rejected('실행 기록과 고정된 계획이 다릅니다.')
    current = record.get('current')
    if current not in (*STAGES, 'enter', 'status', 'leave', None):
        raise Rejected('진행 단계 기록이 올바르지 않습니다.')
    if record.get('state') == 'ready' and (completed or current or record['results']):
        raise Rejected('실행 준비 기록에 이미 변경 이력이 있습니다.')
    if record.get('state') == 'succeeded' and (completed != list(STAGES) or current is not None):
        raise Rejected('필수 단계가 완료되지 않은 성공 기록입니다.')


def execute(argv, lock_fd, candidate_sha):
    # Never print subprocess output: arbitrary operational tools may echo secrets.
    try:
        descriptors = {lock_fd}
        for key in ('COLAB_DEPLOY_LOCK_FD', 'COLAB_PRODUCT_RELEASE_LOCK_FD'):
            if key in os.environ:
                descriptor = int(os.environ[key])
                os.fstat(descriptor)
                descriptors.add(descriptor)
        return subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, check=False,
                              pass_fds=tuple(descriptors), env=dict(os.environ,
                              COLAB_PRODUCT_RESEED_LOCK_FD=str(lock_fd),
                              COLAB_PRODUCT_CANDIDATE_SHA=candidate_sha)).returncode
    except OSError as exc:
        raise NotReady('단계 실행기를 시작하지 못했습니다.') from exc


def run(plan, directory, *, provision=False, resume=False, verified_stage=None, verify_completed=False):
    fingerprint = validate(plan, provision=provision)
    with locked(directory, provision) as lock_fd:
        path = directory / 'initialization.json'
        if path.is_symlink():
            raise Rejected('실행 기록 심볼릭 링크를 거부합니다.')
        if provision:
            if path.exists():
                raise Rejected('최초 실행 기록은 다시 등록할 수 없습니다.')
            save(path, dict(state='ready', id=plan['id'], plan_sha=fingerprint,
                            manifest_sha=plan['manifest_sha'], candidate_sha=plan['candidate_sha'],
                            completed=[], current=None, results=[]))
            return 0
        if not path.exists():
            raise NotReady('최초 실행 기록이 없습니다. 자동 초기화를 거부합니다.')
        if path.stat().st_mode & 0o077:
            raise Rejected('실행 기록은 소유자만 접근할 수 있어야 합니다.')
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise NotReady('실행 기록을 읽을 수 없습니다.') from exc
        if not isinstance(record, dict) or record.get('plan_sha') != fingerprint:
            raise Rejected('실행 계획이 등록된 내용과 다릅니다.')
        validate_record(record, plan)
        if verify_completed:
            if record['state'] != 'succeeded':
                raise Rejected('최초 실행이 성공으로 완료되지 않았습니다.')
            return 0
        action = decide_initialization(record, plan['manifest_sha'], resume)
        if action == 'skip':
            return 0
        if record['candidate_sha'] is None:
            record['candidate_sha'] = plan['candidate_sha']
            save(path, record)
        current = record.get('current')
        if action == 'resume' and current not in (None, 'preflight', 'verify', 'report', 'enter', 'status', 'leave'):
            checks = plan.get('resume_checks', {})
            check = checks.get(current) if isinstance(checks, dict) else None
            if verified_stage != current or not argv_valid(check):
                raise Rejected('부분 변경 단계는 명시적 재개와 실물 정합성 검사가 필요합니다.')
            # A supplied check must verify that the interrupted stage completed.
            # The runner never repeats an uncertain reset or other mutating stage.
            if execute(check, lock_fd, plan['candidate_sha']) != 0:
                raise Rejected('부분 변경 단계의 실물 정합성을 확인하지 못했습니다.')
            if current not in record['completed']:
                record['completed'].append(current)
            record['current'] = None
            save(path, record)

        def step(name, argv):
            record['state'] = 'running'
            record['current'] = name
            save(path, record)
            try:
                code = execute(argv, lock_fd, plan['candidate_sha'])
            except NotReady:
                record['state'] = 'failed'
                record['results'].append({'stage': name, 'exit_code': 78})
                save(path, record)
                raise
            record['results'].append({'stage': name, 'exit_code': code})
            if code:
                record['state'] = 'failed'
                save(path, record)
                return 78 if code == 78 else 1
            record['current'] = None
            if name in STAGES and name not in record['completed']:
                record['completed'].append(name)
            save(path, record)
            return 0

        # Recheck preflight and maintenance even on a manually resumed run.
        code = step('preflight', plan['stages'][0]['argv'])
        if code:
            return code
        for name in ('enter', 'status'):
            code = step(name, plan['maintenance'][name])
            if code:
                return code
        for stage in plan['stages'][1:]:
            if stage['name'] in record['completed'] and stage['name'] not in ('verify', 'report'):
                continue
            code = step(stage['name'], stage['argv'])
            if code:
                return code
        code = step('leave', plan['maintenance']['leave'])
        if code:
            return code
        record['state'] = 'succeeded'
        save(path, record)
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--state-dir', required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--provision', action='store_true')
    mode.add_argument('--resume', action='store_true')
    mode.add_argument('--verify-completed', action='store_true')
    parser.add_argument('--verified-stage', choices=STAGES)
    args = parser.parse_args()
    try:
        try:
            plan = json.loads(Path(args.plan).read_text())
        except OSError as exc:
            raise NotReady('최초 실행 계획 파일을 읽을 수 없습니다.') from exc
        except ValueError as exc:
            raise Rejected('최초 실행 계획 JSON이 올바르지 않습니다.') from exc
        validate(plan, provision=args.provision)
        if args.verified_stage and not args.resume:
            raise Rejected('단계 확인은 수동 재개에만 사용할 수 있습니다.')
        if args.check:
            return 0
        return run(plan, Path(args.state_dir), provision=args.provision, resume=args.resume,
                   verified_stage=args.verified_stage, verify_completed=args.verify_completed)
    except NotReady as exc:
        print(str(exc), file=sys.stderr)
        return 78
    except (Rejected, OSError) as exc:
        print(str(exc) if isinstance(exc, Rejected) else '운영 상태 저장소 접근 실패.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
