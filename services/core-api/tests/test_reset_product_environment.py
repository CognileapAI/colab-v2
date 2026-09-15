"""Production reset refuses changed targets before opening destructive connections."""
import hashlib
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import pytest


SCRIPT = Path(__file__).parents[1] / 'ops/reset_product_environment.py'


def module():
    assert SCRIPT.exists(), 'production reset boundary is not implemented'
    spec = importlib.util.spec_from_file_location('product_reset', SCRIPT)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def private(path, value):
    path.write_text(json.dumps(value))
    path.chmod(0o600)
    return path


@pytest.fixture
def bundle(tmp_path):
    backups = []
    for name in ('platform', 'ai', 'uploads/a'):
        path = tmp_path / name.replace('/', '-')
        path.write_bytes(b'backup bytes for ' + name.encode())
        path.chmod(0o600)
        backups.append({'source': name, 'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    backup = private(tmp_path / 'backup.json', {'schema': 'colab-product-backup/1', 'files': backups})
    manifest = {'reset': {
        'environment': 'prod', 'bucket': 'colab-platform-data-prod', 'region': 'ap-northeast-2',
        'databases': {
            'platform': {'host': 'colab-platform-prod-db.crc0aiws4t52.ap-northeast-2.rds.amazonaws.com', 'name': 'colab_platform', 'schemas': ['public', 'account_admin']},
            'ai': {'host': 'colab-platform-prod-db.crc0aiws4t52.ap-northeast-2.rds.amazonaws.com', 'name': 'colab_ai', 'schemas': ['public']},
        },
        'keys': ['uploads/a'], 'multipartUploads': [],
        'backup_manifest_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(),
    }}
    manifest_path = private(tmp_path / 'manifest.json', manifest)
    urls = {}
    for chain, name in [('platform', 'colab_platform'), ('ai', 'colab_ai')]:
        path = tmp_path / (chain + '.url')
        path.write_text('postgresql://colab_owner:private@colab-platform-prod-db.crc0aiws4t52.ap-northeast-2.rds.amazonaws.com/' + name)
        path.chmod(0o600)
        urls[chain] = str(path)
    return manifest, manifest_path, backup, urls


def prepare(bundle):
    manifest, path, backup, urls = bundle
    private(path, manifest)
    return module().prepare(path, hashlib.sha256(path.read_bytes()).hexdigest(), backup, urls)


def test_valid_reset_input_retains_only_exact_keys(bundle):
    prepared = prepare(bundle)
    assert prepared['reset']['keys'] == ['uploads/a']


@pytest.mark.parametrize('mutation', ['dev_bucket', 'dev_host', 'other_host', 'protected_key', 'extra_schema', 'duplicate_key', 'wrong_database'])
def test_unapproved_reset_target_is_rejected(bundle, mutation):
    reset = bundle[0]['reset']
    if mutation == 'dev_bucket': reset['bucket'] = 'colab-platform-data-dev'
    if mutation == 'dev_host': reset['databases']['ai']['host'] = 'db-dev.example'
    if mutation == 'other_host': reset['databases']['ai']['host'] = 'another-prod.example'
    if mutation == 'protected_key': reset['keys'].append('_ops/backup.sql')
    if mutation == 'extra_schema': reset['databases']['platform']['schemas'].append('unapproved')
    if mutation == 'duplicate_key': reset['keys'].append('uploads/a')
    if mutation == 'wrong_database': reset['databases']['ai']['name'] = 'colab_platform'
    with pytest.raises(ValueError): prepare(bundle)


def test_changed_manifest_is_rejected_before_backup_read(bundle):
    _, path, backup, urls = bundle
    with pytest.raises(ValueError): module().prepare(path, '0' * 64, backup, urls)


def test_missing_or_changed_backup_blocks_reset(bundle):
    (bundle[1].parent / 'uploads-a').write_bytes(b'changed')
    with pytest.raises(ValueError): prepare(bundle)


def test_missing_file_backup_blocks_reset(bundle):
    backup = json.loads(bundle[2].read_text())
    backup['files'] = backup['files'][:2]
    private(bundle[2], backup)
    bundle[0]['reset']['backup_manifest_sha256'] = hashlib.sha256(bundle[2].read_bytes()).hexdigest()
    with pytest.raises(ValueError): prepare(bundle)


def test_url_secret_is_not_exposed_on_target_mismatch(bundle):
    path = Path(bundle[3]['ai'])
    path.write_text('postgresql://colab_owner:DO_NOT_PRINT@wrong-prod.example/colab_ai')
    with pytest.raises(ValueError) as error: prepare(bundle)
    assert 'DO_NOT_PRINT' not in str(error.value)


class Database:
    """Only PostgreSQL wire calls are replaced; SQL and commit effects are observable."""
    def __init__(self):
        self.schemas = {'platform': {'public', 'account_admin'}, 'ai': {'public'}}
        self.ddl = []
        self.commits = []

    def connect(self, url):
        chain = 'ai' if url.endswith('/colab_ai') else 'platform'
        database = self
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def cursor(self): return self
            def execute(self, sql):
                self.query = sql
                if sql.startswith(('DROP ', 'CREATE ', 'REVOKE ', 'COMMENT ')): database.ddl.append((chain, sql))
            def fetchall(self): return [(name,) for name in database.schemas[chain]]
            def fetchone(self): return ('colab_ai' if chain == 'ai' else 'colab_platform', 'colab_owner')
            def commit(self): database.commits.append(chain)
            def rollback(self): pass
        return Connection()


class Storage:
    def __init__(self):
        self.objects = {'uploads/a': 12}
        self.contents = {'uploads/a': b'backup bytes for uploads/a'}
        self.deleted = []
    def list_objects(self, prefix): return [(key, size) for key, size in self.objects.items() if key.startswith(prefix)]
    def list_multipart_uploads(self, prefix): return []
    def head_object(self, key): return len(self.contents[key]), '"fixture-etag"'
    def get_object_stream(self, key, *, expected_etag): return iter([self.contents[key]])
    def delete_objects(self, keys):
        self.deleted.extend(keys)
        for key in keys: self.objects.pop(key)


def execute(bundle, tmp_path, *, phase='schema', maintenance=True, state='running', database=None, storage=None):
    prepared = prepare(bundle)
    database, storage = database or Database(), storage or Storage()
    controller = {'state': state, 'current': 'reset' if phase == 'schema' else 's3',
                  'manifest_sha': prepared['manifest_sha'], 'candidate_sha': 'a' * 40}
    record = private(tmp_path / 'initialization.json', controller)
    directory = tmp_path / 'reset-state'
    directory.mkdir(mode=0o700, exist_ok=True)
    journal = directory / (phase + '.json')
    if not journal.exists():
        private(journal, {'state': 'ready', 'candidate_sha': None, 'manifest_sha': prepared['manifest_sha']})
    return module().execute(prepared, phase, record, directory, 'a' * 40,
                            maintenance=lambda: maintenance, quiescent=lambda: True,
                            connect=database.connect, s3_factory=lambda **kwargs: storage)


def test_maintenance_not_confirmed_causes_zero_deletes(bundle, tmp_path):
    database, storage = Database(), Storage()
    with pytest.raises(ValueError): execute(bundle, tmp_path, maintenance=False, database=database, storage=storage)
    assert database.ddl == [] and storage.deleted == []


@pytest.mark.parametrize('state', ['ready', 'failed', 'succeeded'])
def test_reset_requires_running_controller_stage(bundle, tmp_path, state):
    database = Database()
    with pytest.raises(ValueError): execute(bundle, tmp_path, state=state, database=database)
    assert database.ddl == []


def test_both_database_schemas_checked_before_first_drop(bundle, tmp_path):
    database = Database()
    database.schemas['ai'].add('unexpected')
    with pytest.raises(ValueError): execute(bundle, tmp_path, database=database)
    assert database.ddl == []


def test_changed_s3_inventory_blocks_database_drop(bundle, tmp_path):
    database, storage = Database(), Storage()
    storage.objects['uploads/new'] = 5
    with pytest.raises(ValueError): execute(bundle, tmp_path, database=database, storage=storage)
    assert database.ddl == []


@pytest.mark.parametrize('phase', ['schema', 's3'])
def test_same_key_changed_source_blocks_all_deletes(bundle, tmp_path, phase):
    database, storage = Database(), Storage()
    storage.contents['uploads/a'] = b'overwritten after backup'
    with pytest.raises(ValueError): execute(bundle, tmp_path, phase=phase, database=database, storage=storage)
    assert database.ddl == []
    assert storage.deleted == []


def test_schema_reset_is_committed_once_and_repetition_does_not_drop(bundle, tmp_path):
    database = Database()
    assert execute(bundle, tmp_path, database=database) == 0
    assert database.commits == ['platform', 'ai']
    assert [sql for _, sql in database.ddl if sql.startswith('DROP')] == [
        'DROP SCHEMA public, account_admin CASCADE', 'DROP SCHEMA public CASCADE']
    assert execute(bundle, tmp_path, database=database) == 0
    assert database.commits == ['platform', 'ai']


def test_s3_reset_deletes_exact_approved_keys_once(bundle, tmp_path):
    storage = Storage()
    assert execute(bundle, tmp_path, phase='s3', storage=storage) == 0
    assert storage.deleted == ['uploads/a']
    assert execute(bundle, tmp_path, phase='s3', storage=storage) == 0
    assert storage.deleted == ['uploads/a']


def test_partial_database_reset_cannot_be_automatically_repeated(bundle, tmp_path):
    database = Database()
    original = database.connect
    def failing_connect(url):
        connection = original(url)
        if url.endswith('/colab_ai'):
            def fail(): raise RuntimeError('simulated commit interruption')
            connection.commit = fail
        return connection
    database.connect = failing_connect
    with pytest.raises(RuntimeError): execute(bundle, tmp_path, database=database)
    writes = list(database.ddl)
    with pytest.raises(ValueError): execute(bundle, tmp_path, database=database)
    assert database.ddl == writes
    assert json.loads((tmp_path / 'reset-state/schema.json').read_text())['state'] == 'failed'


def cli_bundle(bundle, tmp_path):
    config = private(tmp_path / 'config.json', {
        'schema': 'colab-product-reset-input/1', 'url_files': bundle[3],
        'backup_path': str(bundle[2]), 'controller_path': str(tmp_path / 'initialization.json'),
        'state_directory': str(tmp_path / 'reset-state'),
        'maintenance_config_path': str(tmp_path / 'maintenance.json'),
        'maintenance_config_sha256': '0' * 64,
        'quiescence': {'argv': [sys.executable, str(tmp_path / 'quiescence.py')],
                       'files': {str(tmp_path / 'quiescence.py'): '0' * 64}},
    })
    bundle[0]['reset']['operator_input_sha256'] = hashlib.sha256(config.read_bytes()).hexdigest()
    private(bundle[1], bundle[0])
    return [sys.executable, str(SCRIPT), '--manifest', str(bundle[1]), '--manifest-sha256',
            hashlib.sha256(bundle[1].read_bytes()).hexdigest(), '--config', str(config)]


def test_cli_check_never_provisions_or_connects(bundle, tmp_path):
    command = cli_bundle(bundle, tmp_path)
    result = subprocess.run(command + ['--check'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / 'reset-state').exists()
    assert '입력 검증' in result.stdout


def test_cli_provision_is_explicit_and_cannot_replace_existing_state(bundle, tmp_path):
    command = cli_bundle(bundle, tmp_path)
    result = subprocess.run(command + ['--provision'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    path = tmp_path / 'reset-state/schema.json'
    record = json.loads(path.read_text())
    assert record['state'] == 'ready'
    assert record['candidate_sha'] is None
    result = subprocess.run(command + ['--provision'], capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(path.read_text()) == record


def test_cli_missing_backup_is_preparation_failure_without_state(bundle, tmp_path):
    command = cli_bundle(bundle, tmp_path)
    bundle[2].unlink()
    result = subprocess.run(command + ['--provision'], capture_output=True, text=True)
    assert result.returncode == 78
    assert not (tmp_path / 'reset-state').exists()


def test_controller_reset_maintenance_chain_preserves_lock_after_parent_death(bundle, tmp_path):
    root = SCRIPT.parents[3]
    copied = tmp_path / 'repo/services/core-api/ops/reset_product_environment.py'
    copied.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT, copied)
    shutil.copy2(SCRIPT.with_name('reset_dev_environment.py'), copied.with_name('reset_dev_environment.py'))
    copied_runner = tmp_path / 'repo/dev-package/tools/product-reseed/reseed.py'
    copied_runner.parent.mkdir(parents=True)
    shutil.copy2(root / 'dev-package/tools/product-reseed/reseed.py', copied_runner)
    maintenance = tmp_path / 'repo/infra/prod/maintenance.py'
    maintenance.parent.mkdir(parents=True)
    marker, finish, attempted = tmp_path / 'maintenance-ready', tmp_path / 'finish', tmp_path / 'maintenance-attempt'
    maintenance.write_text('import os,json,pathlib,time\n'
        f'pathlib.Path({str(attempted)!r}).touch()\n'
        'for name in ("COLAB_PRODUCT_RELEASE_LOCK_FD","COLAB_DEPLOY_LOCK_FD","COLAB_PRODUCT_RESEED_LOCK_FD"):\n'
        '    os.fstat(int(os.environ[name]))\n'
        f'pathlib.Path({str(marker)!r}).write_text(json.dumps([os.getppid(),os.getpid()]))\n'
        'deadline=time.monotonic()+8\n'
        f'while not pathlib.Path({str(finish)!r}).exists() and time.monotonic()<deadline:time.sleep(.02)\n')
    command = cli_bundle(bundle, tmp_path)
    command[1] = str(copied)
    config_path = tmp_path / 'config.json'
    config = json.loads(config_path.read_text())
    state_dir = tmp_path / 'controller-state'
    config['controller_path'] = str(state_dir / 'initialization.json')
    private(tmp_path / 'maintenance.json', {})
    config['maintenance_config_sha256'] = hashlib.sha256((tmp_path / 'maintenance.json').read_bytes()).hexdigest()
    probe = tmp_path / 'quiescence.py'
    probe.write_text('print("{}")\n'); probe.chmod(0o600)
    config['quiescence']['files'][str(probe)] = hashlib.sha256(probe.read_bytes()).hexdigest()
    private(config_path, config)
    bundle[0]['reset']['operator_input_sha256'] = hashlib.sha256(config_path.read_bytes()).hexdigest()
    private(bundle[1], bundle[0])
    digest = hashlib.sha256(bundle[1].read_bytes()).hexdigest()
    command[command.index('--manifest-sha256') + 1] = digest
    stages = ['preflight','deploy','reset','bootstrap','up','s3','prelude','seed','verify','report']
    plan = private(tmp_path / 'reseed.json', {
        'schema':'colab-product-reseed/1','id':'lock-chain','environment':'prod',
        'candidate_sha':'a'*40,'manifest_sha':digest,
        'maintenance':{name:[sys.executable,'-c','pass'] for name in ('enter','status','leave')},
        'stages':[{'name':name,'argv':command+['--phase','schema'] if name=='reset' else [sys.executable,'-c','pass']} for name in stages],
    })
    runner = [sys.executable,str(root / 'dev-package/tools/product-reseed/reseed.py'),
              '--plan',str(plan),'--state-dir',str(state_dir)]
    assert subprocess.run(runner + ['--provision'],capture_output=True).returncode == 0
    outer = tmp_path / 'release.lock'
    with outer.open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        process = subprocess.Popen(runner,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            pass_fds=(lock.fileno(),),env=dict(os.environ,COLAB_PRODUCT_RELEASE_LOCK_FD=str(lock.fileno()),
                                            COLAB_DEPLOY_LOCK_FD=str(lock.fileno())))
    try:
        deadline=time.monotonic()+3
        while not marker.exists() and process.poll() is None and time.monotonic()<deadline:time.sleep(.02)
        assert attempted.exists(), 'fixture did not reach the maintenance subprocess'
        assert marker.exists(), 'reset → maintenance subprocess lost controller lock descriptors'
        reset_pid, _ = json.loads(marker.read_text())
        process.kill();process.wait(timeout=3)
        os.kill(reset_pid,signal.SIGKILL)
        with outer.open() as probe_lock:
            with pytest.raises(BlockingIOError):fcntl.flock(probe_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    finally:
        finish.touch()
        if process.poll() is None:process.kill()
        process.wait(timeout=3)
