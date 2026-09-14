#!/usr/bin/env python3
"""Approved first-production reset inputs; dev reset permissions are independent."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from urllib.parse import urlsplit


HOST = 'colab-platform-prod-db.crc0aiws4t52.ap-northeast-2.rds.amazonaws.com'
DATABASES = {'platform': 'colab_platform', 'ai': 'colab_ai'}
SCHEMAS = {'platform': {'public', 'account_admin'}, 'ai': {'public'}}


def private_bytes(path):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
        raise ValueError('운영 입력은 실행자 소유의 비공개 일반 파일이어야 합니다.')
    return path.read_bytes()


def checked_json(path, digest):
    raw = private_bytes(path)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('승인된 입력 또는 백업 내용이 변경됐습니다.')
    return json.loads(raw)


def key_allowed(value):
    return isinstance(value, str) and value.startswith(('uploads/', 'previews/'))


def prepare(manifest_path, digest, backup_path, url_files):
    manifest = checked_json(manifest_path, digest)
    reset = manifest.get('reset') if isinstance(manifest, dict) else None
    if not isinstance(reset, dict):
        raise ValueError('정확한 운영 삭제 범위가 필요합니다.')
    if (reset.get('environment') != 'prod' or reset.get('bucket') != 'colab-platform-data-prod'
            or reset.get('region') != 'ap-northeast-2'):
        raise ValueError('승인된 운영 저장소와 다릅니다.')
    databases = reset.get('databases')
    if not isinstance(databases, dict) or set(databases) != set(DATABASES):
        raise ValueError('두 운영 DB의 명시적 범위가 필요합니다.')
    urls = {}
    for chain, name in DATABASES.items():
        target = databases[chain]
        if (not isinstance(target, dict) or target.get('host') != HOST or target.get('name') != name
                or not isinstance(target.get('schemas'), list)
                or len(target['schemas']) != len(SCHEMAS[chain]) or set(target['schemas']) != SCHEMAS[chain]):
            raise ValueError('승인된 운영 DB 또는 스키마와 다릅니다.')
        url = private_bytes(url_files[chain]).decode().strip().replace('postgresql+psycopg://', 'postgresql://')
        parsed = urlsplit(url)
        if (parsed.scheme != 'postgresql' or parsed.hostname != HOST or parsed.path != '/' + name
                or parsed.username != 'colab_owner' or parsed.query or parsed.fragment
                or parsed.port not in (None, 5432)):
            raise ValueError('운영 소유자 연결의 대상이 다릅니다.')
        urls[chain] = url
    keys, uploads = reset.get('keys'), reset.get('multipartUploads')
    if not isinstance(keys, list) or not all(key_allowed(key) for key in keys) or len(set(keys)) != len(keys):
        raise ValueError('중복 없는 허용 접두사의 exact-key 목록이 필요합니다.')
    if (not isinstance(uploads, list) or any(not isinstance(pair, list) or len(pair) != 2
            or not key_allowed(pair[0]) or not isinstance(pair[1], str) or not pair[1] for pair in uploads)
            or len({tuple(pair) for pair in uploads}) != len(uploads)):
        raise ValueError('명시적 멀티파트 목록이 필요합니다.')
    backup = checked_json(backup_path, reset.get('backup_manifest_sha256'))
    if not isinstance(backup, dict) or backup.get('schema') != 'colab-product-backup/1' or not isinstance(backup.get('files'), list):
        raise ValueError('복구 자료 목록이 필요합니다.')
    records = backup['files']
    sources = [record.get('source') for record in records if isinstance(record, dict)]
    if len(sources) != len(records) or len(set(sources)) != len(sources) or set(sources) != {'platform', 'ai', *keys}:
        raise ValueError('두 DB와 모든 삭제 파일의 보존 사본이 필요합니다.')
    for record in records:
        path = Path(record['path'])
        if not path.is_absolute(): path = Path(backup_path).resolve().parent / path
        if hashlib.sha256(private_bytes(path)).hexdigest() != record.get('sha256'):
            raise ValueError('복구 자료가 변경됐습니다.')
    return {'reset': reset, 'urls': urls, 'manifest_sha': digest,
            'object_hashes': {record['source']: record['sha256'] for record in records if record['source'] in keys}}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(storage):
    keys = sorted(key for prefix in ('uploads/', 'previews/') for key, _ in storage.list_objects(prefix))
    uploads = sorted([key, upload] for prefix in ('uploads/', 'previews/')
                     for key, upload in storage.list_multipart_uploads(prefix))
    return keys, uploads


def execute(prepared, phase, controller_path, state_dir, candidate_sha, *, maintenance,
            quiescent, connect=None, s3_factory=None):
    """Run below the persistent reseed controller; uncertain writes cannot be retried here."""
    if phase not in ('schema', 's3'):
        raise ValueError('지원하지 않는 초기화 단계입니다.')
    controller = json.loads(private_bytes(controller_path))
    if (not isinstance(controller, dict) or controller.get('state') != 'running'
            or controller.get('current') != ('reset' if phase == 'schema' else 's3')
            or controller.get('candidate_sha') != candidate_sha
            or controller.get('manifest_sha') != prepared['manifest_sha']):
        raise ValueError('승인된 최초 실행의 현재 단계가 아닙니다.')
    if not maintenance() or not quiescent():
        raise ValueError('점검 상태와 쓰기 중지가 확인되지 않았습니다.')
    root = Path(__file__).resolve().parents[3]
    durable = load_module('product_reseed_state', root / 'dev-package/tools/product-reseed/reseed.py')
    # Read-only helpers/DDL are shared. The dev CLI and its environment guards are never called or changed.
    dev = load_module('dev_reset_helpers', Path(__file__).with_name('reset_dev_environment.py'))
    connect = connect or dev._default_connect
    s3_factory = s3_factory or dev._default_s3
    directory = Path(state_dir)
    with durable.locked(directory, provision=False):
        record_path = directory / (phase + '.json')
        if not record_path.is_file():
            raise OSError('초기화 단계 기록을 먼저 등록해야 합니다.')
        record = json.loads(private_bytes(record_path))
        if record.get('manifest_sha') != prepared['manifest_sha']:
            raise ValueError('초기화 단계의 승인 입력이 다릅니다.')
        if record.get('state') == 'succeeded':
            if record.get('candidate_sha') != candidate_sha:
                raise ValueError('초기화 단계의 실행 후보가 다릅니다.')
            return 0
        if record.get('state') != 'ready' or record.get('candidate_sha') is not None:
            raise ValueError('부분 실행은 실물 확인 후 상위 실행에서 수동 재개해야 합니다.')
        storage = s3_factory(bucket=prepared['reset']['bucket'], region=prepared['reset']['region'])
        if snapshot(storage) != (sorted(prepared['reset']['keys']), sorted(prepared['reset']['multipartUploads'])):
            raise ValueError('현재 저장 파일이 승인된 삭제 목록과 다릅니다.')
        for key, expected in prepared['object_hashes'].items():
            _, etag = storage.head_object(key)
            if not etag:
                raise ValueError('삭제할 원본의 버전 표지를 확인하지 못했습니다.')
            checksum = hashlib.sha256()
            for chunk in storage.get_object_stream(key, expected_etag=etag):
                checksum.update(chunk)
            if checksum.hexdigest() != expected:
                raise ValueError('삭제할 원본 내용과 승인된 보존 사본이 다릅니다.')
        if phase == 'schema':
            for chain, url in prepared['urls'].items():
                with connect(url) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT current_database(), current_user')
                        if tuple(cursor.fetchone()) != (DATABASES[chain], 'colab_owner'):
                            raise ValueError('연결된 DB 또는 실행 역할이 다릅니다.')
                        if dev._namespaces(cursor) != SCHEMAS[chain]:
                            raise ValueError('현재 스키마가 승인된 삭제 목록과 다릅니다.')
                    connection.rollback()
        record.update(state='running', candidate_sha=candidate_sha)
        durable.save(record_path, record)
        try:
            if phase == 'schema':
                for chain, url in prepared['urls'].items():
                    with connect(url) as connection:
                        with connection.cursor() as cursor:
                            for sql in dev.RECREATE_DDL[chain]:
                                cursor.execute(sql)
                        connection.commit()
            else:
                for key, upload in prepared['reset']['multipartUploads']:
                    storage.abort_multipart_upload(key, upload)
                if prepared['reset']['keys']:
                    storage.delete_objects(prepared['reset']['keys'])
                if snapshot(storage) != ([], []):
                    raise ValueError('초기화 뒤 남은 파일 또는 멀티파트가 있습니다.')
            record['state'] = 'succeeded'
            durable.save(record_path, record)
        except Exception:
            record['state'] = 'failed'
            durable.save(record_path, record)
            raise
    return 0


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--config', required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--provision', action='store_true')
    action.add_argument('--phase', choices=('schema', 's3'))
    args = parser.parse_args(argv)
    try:
        manifest = checked_json(args.manifest, args.manifest_sha256)
        config = checked_json(args.config, manifest['reset']['operator_input_sha256'])
        if config.get('schema') != 'colab-product-reset-input/1':
            raise ValueError('운영 초기화 설정 형식이 다릅니다.')
        prepared = prepare(args.manifest, args.manifest_sha256, config['backup_path'], config['url_files'])
        if args.check:
            print('초기화 입력 검증 통과 — 원격 상태 검증과 삭제는 실행하지 않았습니다.')
            return 0
        root = Path(__file__).resolve().parents[3]
        durable = load_module('product_reseed_state', root / 'dev-package/tools/product-reseed/reseed.py')
        directory = Path(config['state_directory'])
        if not directory.is_absolute():
            raise ValueError('영속 상태 디렉터리는 절대 경로여야 합니다.')
        if args.provision:
            with durable.locked(directory, provision=True):
                paths = [directory / (phase + '.json') for phase in ('schema', 's3')]
                if any(path.exists() for path in paths):
                    raise ValueError('이미 등록된 초기화 기록을 덮어쓸 수 없습니다.')
                for path in paths:
                    durable.save(path, {'state': 'ready', 'manifest_sha': args.manifest_sha256, 'candidate_sha': None})
            print('초기화 단계 기록 등록 완료 — 삭제는 실행하지 않았습니다.')
            return 0
        maintenance_path = Path(config['maintenance_config_path'])
        checked_json(maintenance_path, config['maintenance_config_sha256'])
        quiescence = config['quiescence']
        command, files = quiescence['argv'], quiescence['files']
        if (not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command)
                or not isinstance(files, dict) or not files):
            raise ValueError('승인된 쓰기 중지 검사 명령과 파일 hash가 필요합니다.')
        for path, digest in files.items():
            if hashlib.sha256(private_bytes(path)).hexdigest() != digest:
                raise ValueError('쓰기 중지 검사 파일이 변경됐습니다.')
        candidate = os.environ.get('COLAB_PRODUCT_CANDIDATE_SHA', '')
        if len(candidate) != 40 or any(char not in '0123456789abcdef' for char in candidate):
            raise ValueError('상위 배포에서 고정한 후보 SHA가 필요합니다.')
        descriptors = set()
        for name in ('COLAB_PRODUCT_RESEED_LOCK_FD', 'COLAB_DEPLOY_LOCK_FD', 'COLAB_PRODUCT_RELEASE_LOCK_FD'):
            if name in os.environ:
                descriptor = int(os.environ[name])
                os.fstat(descriptor)
                descriptors.add(descriptor)
        def maintenance():
            result = subprocess.run([sys.executable, str(root / 'infra/prod/maintenance.py'),
                                     '--action', 'status', '--config', str(maintenance_path)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    pass_fds=tuple(descriptors))
            return result.returncode == 0
        def quiescent():
            result = subprocess.run(command, capture_output=True, pass_fds=tuple(descriptors))
            if result.returncode != 0: return False
            observed = json.loads(result.stdout)
            return (isinstance(observed, dict) and observed.get('writers_stopped') is True
                    and observed.get('origin_isolated') is True
                    and observed.get('candidate_sha') == candidate)
        return execute(prepared, args.phase, config['controller_path'], directory, candidate,
                       maintenance=maintenance, quiescent=quiescent)
    except OSError:
        print('초기화에 필요한 파일 또는 실행 환경이 준비되지 않았습니다.', file=sys.stderr)
        return 78
    except Exception:
        # Drivers can put connection strings in exception text. Never forward them.
        print('운영 초기화 검증 또는 실행 실패 — 점검을 유지하고 실행 기록을 확인하세요.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(cli())
