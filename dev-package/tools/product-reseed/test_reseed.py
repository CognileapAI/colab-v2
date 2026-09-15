"""Exercise the durable runner through its CLI; no infrastructure is contacted."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


RUNNER = Path(__file__).with_name('reseed.py')
STAGES = ['preflight', 'deploy', 'reset', 'bootstrap', 'up', 's3', 'prelude', 'seed', 'verify', 'report']


class ProductReseedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.calls = self.root / 'calls'
        self.state = self.root / 'state'
        self.plan_file = self.root / 'plan.json'
        self.failure = self.root / 'fail'
        child = self.root / 'child.py'
        child.write_text(
            'import pathlib,sys\n'
            'calls,fail,name=map(pathlib.Path,sys.argv[1:])\n'
            'with calls.open("a") as f:f.write(str(name)+"\\n")\n'
            'sys.exit(1 if fail.exists() and fail.read_text()==str(name) else 0)\n'
        )
        self.argv = lambda name: [sys.executable, str(child), str(self.calls), str(self.failure), name]
        self.plan = {
            'schema': 'colab-product-reseed/1', 'id': 'first-production',
            'environment': 'prod', 'candidate_sha': 'a' * 40,
            'manifest_sha': 'b' * 64,
            'maintenance': {key: self.argv(key) for key in ['enter', 'status', 'leave']},
            'stages': [{'name': name, 'argv': self.argv(name)} for name in STAGES],
        }
        self.save_plan()

    def save_plan(self):
        self.plan_file.write_text(json.dumps(self.plan))

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(RUNNER), '--plan', str(self.plan_file),
             '--state-dir', str(self.state), *args], capture_output=True, text=True,
        )

    def recorded_calls(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def provision(self):
        result = self.run_cli('--provision')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_plan_is_readiness_failure_without_changes(self):
        self.plan_file.unlink()
        result = self.run_cli('--check')
        self.assertEqual(result.returncode, 78, result.stderr)
        self.assertFalse(self.state.exists())

    def test_check_does_not_create_state_or_call_commands(self):
        result = self.run_cli('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.state.exists())
        self.assertEqual(self.recorded_calls(), [])

    def test_verify_completed_never_starts_ready_or_failed_execution(self):
        self.assertEqual(self.run_cli('--verify-completed').returncode, 78)
        self.provision()
        before = (self.state / 'initialization.json').read_bytes()
        self.assertEqual(self.run_cli('--verify-completed').returncode, 1)
        self.assertEqual((self.state / 'initialization.json').read_bytes(), before)
        self.assertEqual(self.recorded_calls(), [])
        self.failure.write_text('reset')
        self.assertEqual(self.run_cli().returncode, 1)
        calls = self.recorded_calls()
        self.assertEqual(self.run_cli('--verify-completed').returncode, 1)
        self.assertEqual(self.recorded_calls(), calls)

    def test_verify_completed_accepts_only_matching_success_without_commands(self):
        self.provision()
        self.assertEqual(self.run_cli().returncode, 0)
        calls = self.recorded_calls()
        before = (self.state / 'initialization.json').read_bytes()
        self.assertEqual(self.run_cli('--verify-completed').returncode, 0)
        self.assertEqual((self.state / 'initialization.json').read_bytes(), before)
        self.assertEqual(self.recorded_calls(), calls)
        self.plan['candidate_sha'] = 'c' * 40
        self.save_plan()
        self.assertEqual(self.run_cli('--verify-completed').returncode, 1)
        self.assertEqual(self.recorded_calls(), calls)

    def test_stage_inherits_outer_release_lock_and_reseed_lock(self):
        probe = self.root / 'probe-lock.py'
        probe.write_text('import os\n'
                         'fd=int(os.environ["COLAB_PRODUCT_RELEASE_LOCK_FD"])\n'
                         'assert os.pread(fd, 6, 0)==b"marker"\n'
                         'os.fstat(int(os.environ["COLAB_PRODUCT_RESEED_LOCK_FD"]))\n')
        self.plan['stages'][0]['argv'] = [sys.executable, str(probe)]
        self.save_plan()
        self.provision()
        outer = self.root / 'outer.lock'
        outer.write_bytes(b'marker')
        with outer.open('rb') as stream:
            result = subprocess.run([sys.executable, str(RUNNER), '--plan', str(self.plan_file),
                                     '--state-dir', str(self.state)], capture_output=True, text=True,
                                    pass_fds=(stream.fileno(),),
                                    env=dict(os.environ, COLAB_PRODUCT_RELEASE_LOCK_FD=str(stream.fileno())))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_provision_before_merge_binds_real_candidate_only_when_run(self):
        self.plan['candidate_sha'] = None
        self.save_plan()
        self.provision()
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual(self.recorded_calls(), [])
        self.plan['candidate_sha'] = 'a' * 40
        self.save_plan()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads((self.state / 'initialization.json').read_text())
        self.assertEqual(record['candidate_sha'], 'a' * 40)
        self.plan['candidate_sha'] = 'c' * 40
        self.save_plan()
        calls = self.recorded_calls()
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual(self.recorded_calls(), calls)

    def test_ordinary_run_cannot_initialize_absent_record(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 78, result.stderr)
        self.assertEqual(self.recorded_calls(), [])

    def test_first_run_succeeds_and_duplicate_never_resets(self):
        self.provision()
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        calls = self.recorded_calls()
        self.assertEqual(calls.count('reset'), 1)
        self.assertLess(calls.index('status'), calls.index('reset'))
        self.assertGreater(calls.index('leave'), calls.index('verify'))
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(self.recorded_calls(), calls)

    def test_reset_failure_keeps_maintenance_and_refuses_automatic_retry(self):
        self.provision()
        self.failure.write_text('reset')
        self.assertEqual(self.run_cli().returncode, 1)
        calls = self.recorded_calls()
        self.assertNotIn('leave', calls)
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual(self.recorded_calls(), calls)

    def test_failed_mutating_stage_cannot_be_blindly_resumed(self):
        self.provision()
        self.failure.write_text('reset')
        self.run_cli()
        calls = self.recorded_calls()
        self.failure.unlink()
        self.assertEqual(self.run_cli('--resume').returncode, 1)
        self.assertEqual(self.recorded_calls(), calls)

    def test_changed_manifest_rejected_before_commands(self):
        self.provision()
        self.plan['manifest_sha'] = 'c' * 64
        self.save_plan()
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual(self.recorded_calls(), [])

    def test_reprovision_cannot_erase_existing_state(self):
        self.provision()
        self.assertEqual(self.run_cli('--provision').returncode, 1)
        self.assertEqual(self.recorded_calls(), [])

    def test_missing_required_stage_rejected_without_state(self):
        self.plan['stages'] = [x for x in self.plan['stages'] if x['name'] != 'verify']
        self.save_plan()
        self.assertEqual(self.run_cli('--provision').returncode, 1)
        self.assertFalse(self.state.exists())

    def test_dev_target_rejected_without_state(self):
        self.plan['environment'] = 'dev'
        self.save_plan()
        self.assertEqual(self.run_cli('--provision').returncode, 1)
        self.assertFalse(self.state.exists())

    def test_maintenance_failure_prevents_reset(self):
        self.provision()
        self.failure.write_text('status')
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertNotIn('reset', self.recorded_calls())
        self.assertNotIn('leave', self.recorded_calls())

    def test_state_is_private(self):
        self.provision()
        state_files = list(self.state.glob('*.json'))
        self.assertEqual(len(state_files), 1)
        self.assertEqual(state_files[0].stat().st_mode & 0o777, 0o600)

    def test_manual_resume_checks_partial_stage_and_never_repeats_reset(self):
        self.plan['resume_checks'] = {'reset': self.argv('check-reset')}
        self.save_plan()
        self.provision()
        self.failure.write_text('reset')
        self.assertEqual(self.run_cli().returncode, 1)
        self.failure.unlink()
        result = self.run_cli('--resume', '--verified-stage', 'reset')
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.recorded_calls()
        self.assertEqual(calls.count('reset'), 1)
        self.assertLess(calls.index('check-reset'), calls.index('bootstrap'))
        self.assertEqual(calls.count('leave'), 1)

    def test_partial_stage_check_failure_keeps_service_closed(self):
        self.plan['resume_checks'] = {'reset': self.argv('check-reset')}
        self.save_plan()
        self.provision()
        self.failure.write_text('reset')
        self.run_cli()
        self.failure.write_text('check-reset')
        result = self.run_cli('--resume', '--verified-stage', 'reset')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn('bootstrap', self.recorded_calls())
        self.assertNotIn('leave', self.recorded_calls())

    def test_corrupt_record_is_not_treated_as_ready(self):
        self.provision()
        (self.state / 'initialization.json').write_text('{broken')
        self.assertEqual(self.run_cli().returncode, 78)
        self.assertEqual(self.recorded_calls(), [])

    def test_unknown_completed_stage_is_rejected_before_commands(self):
        self.provision()
        path = self.state / 'initialization.json'
        record = json.loads(path.read_text())
        record['completed'] = ['unrecognized']
        path.write_text(json.dumps(record))
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual(self.recorded_calls(), [])

    def test_ready_record_cannot_skip_mutating_stages(self):
        self.provision()
        path = self.state / 'initialization.json'
        record = json.loads(path.read_text())
        record['completed'] = list(STAGES)
        path.write_text(json.dumps(record))
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual(self.recorded_calls(), [])

    def test_child_keeps_lock_if_parent_is_killed(self):
        sleeper = self.root / 'sleeper.py'
        pid_file = self.root / 'child.pid'
        sleeper.write_text('import os,pathlib,sys,time\npathlib.Path(sys.argv[1]).write_text(str(os.getpid()))\ntime.sleep(20)\n')
        self.plan['stages'][2]['argv'] = [sys.executable, str(sleeper), str(pid_file)]
        self.save_plan()
        self.provision()
        parent = subprocess.Popen([sys.executable, str(RUNNER), '--plan', str(self.plan_file),
                                   '--state-dir', str(self.state)], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: parent.poll() is None and parent.kill())
        deadline = time.monotonic() + 5
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(pid_file.exists())
        import os
        import signal
        child_pid = int(pid_file.read_text())
        self.addCleanup(lambda: os.kill(child_pid, signal.SIGKILL))
        parent.kill()
        parent.wait()
        import fcntl
        with (self.state / '.execution.lock').open('r+') as lock:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


if __name__ == '__main__':
    unittest.main()
