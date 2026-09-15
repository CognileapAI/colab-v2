import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('runtime_lifecycle', ROOT / 'scripts/harness/hooks/lifecycle_contract.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class TaskRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                        'commit', '--allow-empty', '-qm', 'initial'], check=True)

    def test_default_lane_report_is_runtime_and_bound_to_current_run(self):
        task = contract.begin(self.root, 'lane-worker', gates=['check'])
        self.assertEqual(task['schema'], 'colab-task/2')
        self.assertIn('/colab-harness/', task['report'])
        old_report = task['report']
        evidence = contract.gate_start(self.root, task['task_id'])
        current = contract.load_task(self.root, task['task_id'])
        self.assertNotEqual(current['report'], old_report)
        report = {'schema': 'colab-gate-summary/1', 'commit': evidence['commit'], 'tree': evidence['tree'],
                  'counts': {'green': 1, 'red_판정': 0, 'red_준비': 0},
                  'gates': [{'name': 'check', 'status': 'green', 'exit': 0}],
                  'task_evidence': {'before': evidence, 'after': evidence}}
        path = contract.resolve_task_path(self.root, current, current['report'])
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(report))
        contract.verify_task_report(self.root, current)
        with self.assertRaises(ValueError): contract.resolve_task_path(self.root, current, old_report)
        report['commit'] = 'a' * 40; path.write_text(json.dumps(report))
        with self.assertRaises(ValueError): contract.verify_task_report(self.root, current)

    def test_artifact_handoff_rejects_tamper_undeclared_and_cross_task(self):
        task = contract.begin(self.root, 'researcher', artifacts=['runtime:artifacts/findings.md'], agent_id='owner')
        name = task['artifacts'][0]
        path = contract.resolve_task_path(self.root, task, name)
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text('findings')
        handoff = {'task_id': task['task_id'], 'run_id': task['run_id'], 'mode': 'artifacts',
                   'summary': 'current findings', 'artifacts': {name: contract.digest(path)}}
        payload = {'cwd': str(self.root), 'agent_type': 'researcher', 'agent_id': 'owner',
                   'last_assistant_message': 'COLAB_HANDOFF ' + json.dumps(handoff)}
        self.assertEqual(contract.stop(payload, 'researcher'), 'H6')
        path.write_text('changed')
        with self.assertRaises(ValueError): contract.stop(payload, 'researcher')
        path.write_text('findings'); extra = path.parent / 'undeclared.md'; extra.write_text('extra')
        with self.assertRaises(ValueError): contract.stop(payload, 'researcher')
        extra.unlink()
        other = contract.begin(self.root, 'researcher', artifacts=['runtime:artifacts/findings.md'])
        with self.assertRaises(ValueError): contract.resolve_task_path(self.root, other, name)
        path.unlink(); path.symlink_to(self.root / 'outside')
        with self.assertRaises(ValueError): contract.resolve_task_path(self.root, task, name)

    def test_external_edit_requires_task_run_and_agent_identity(self):
        task = contract.begin(self.root, 'researcher', artifacts=['runtime:artifacts/findings.md'], agent_id='owner')
        payload = {'cwd': str(self.root), 'tool_name': 'Write', 'agent_id': 'owner',
                   'task_id': task['task_id'], 'run_id': task['run_id'],
                   'tool_input': {'file_path': task['artifacts'][0], 'content': 'draft'}}
        self.assertEqual(contract.validate_input(payload, 'file_path')['tool_input']['file_path'], task['artifacts'][0])
        for key in ('task_id', 'run_id', 'agent_id'):
            bad = dict(payload); bad[key] = 'other'
            with self.subTest(key=key), self.assertRaises(ValueError): contract.validate_input(bad, 'file_path')

    def test_other_checkout_cannot_load_runtime_task(self):
        task = contract.begin(self.root, 'researcher')
        other = self.root.parent / 'other'
        subprocess.run(['git', '-C', str(self.root), 'worktree', 'add', '--detach', str(other)], check=True, capture_output=True)
        with self.assertRaises((ValueError, OSError)): contract.load_task(other, task['task_id'])

    def test_real_gate_run_and_slack_prepare_use_current_runtime_hashes(self):
        (self.root / '.gitignore').write_text('__pycache__/\n')
        runner = self.root / 'gates/run.sh'
        runner.parent.mkdir(); runner.write_text('#!/usr/bin/env bash\necho verified\n')
        for relative in ('scripts/harness/hooks/lifecycle_contract.py', 'scripts/harness/task_state.py'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / relative, target)
        task = contract.begin(self.root, 'lane-worker', gates=['check'], artifacts=['runtime:artifacts/completion.md', 'runtime:artifacts/findings.md'])
        self.assertEqual(contract.run_gates(self.root, task['task_id']), 0)
        task = contract.load_task(self.root, task['task_id'])
        note = Path(task['artifacts'][0]); note.parent.mkdir(parents=True); note.write_text('검증 완료')
        with self.assertRaises(ValueError): contract.verify_task_report(self.root, task)
        findings = Path(task['artifacts'][1]); findings.write_text('required findings')
        contract.verify_task_report(self.root, task)
        spec = importlib.util.spec_from_file_location('runtime_slack', ROOT / 'scripts/slack_completion.py')
        slack = importlib.util.module_from_spec(spec); spec.loader.exec_module(slack)
        pending = slack.prepare(self.root, 'runtime-test', note, [(task['task_id'], task['report'])], True, [])
        self.assertEqual(slack._load_notice(pending,self.root,'runtime-test',slack.verify_evidence)[0], '검증 완료')
        findings.write_text('changed findings')
        with self.assertRaises(ValueError): slack._load_notice(pending,self.root,'runtime-test',slack.verify_evidence)
        findings.write_text('required findings')
        note.write_text('changed')
        with self.assertRaises(ValueError): slack._load_notice(pending,self.root,'runtime-test',slack.verify_evidence)
        # Changing only the commit is stale even when working-file hashes match.
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                        'commit', '--allow-empty', '-qm', 'next'], check=True)
        with self.assertRaises(ValueError): contract.verify_task_report(self.root, task)

    def test_cli_writes_only_declared_artifact_for_current_owner_and_run(self):
        task = contract.begin(self.root, 'researcher', artifacts=['runtime:artifacts/findings.md'], agent_id='owner')
        command = [sys.executable, str(ROOT / 'scripts/harness/hooks/lifecycle_contract.py'), 'write-artifact',
                   '--task', task['task_id'], '--run-id', task['run_id'], '--agent-id', 'owner',
                   '--artifact', 'runtime:artifacts/findings.md']
        result = subprocess.run(command, cwd=self.root, input='findings', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(task['artifacts'][0]).read_text(), 'findings')
        command[command.index('--run-id') + 1] = 'a' * 32
        result = subprocess.run(command, cwd=self.root, input='bad overwrite', text=True, capture_output=True)
        self.assertEqual(result.returncode, 78)
        self.assertEqual(Path(task['artifacts'][0]).read_text(), 'findings')


if __name__ == '__main__': unittest.main()
