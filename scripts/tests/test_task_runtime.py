import importlib.util
import json
import os
from pathlib import Path
import re
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

    def measurement_report(self, evidence, gates):
        return {'schema': 'colab-gate-summary/1', 'commit': evidence['commit'], 'tree': evidence['tree'],
                'counts': {'green': len(gates), 'red_판정': 0, 'red_준비': 0},
                'gates': [{'name': g, 'status': 'green', 'exit': 0} for g in gates],
                'task_evidence': {'before': evidence, 'after': evidence}}

    def test_measurement_lane_binds_a_report_and_completes_on_its_declared_set(self):
        """The whole point of the role: a measuring lane can open AND close a task.

        Without the report binding in task_state.bind_paths this role would get
        report=None and verify_task_report would fail on every handoff.
        """
        gates = ['first', 'second', 'third']
        task = contract.begin(self.root, 'measurement-lane', gates=gates)
        self.assertEqual(task['schema'], 'colab-task/2')
        self.assertIsNotNone(task['report'], 'measurement-lane must get a bound report')
        self.assertIn('/colab-harness/', task['report'])
        # gate_evidence and gate_start must not reject the role.
        contract.gate_evidence(self.root, task['task_id'])
        evidence = contract.gate_start(self.root, task['task_id'])
        current = contract.load_task(self.root, task['task_id'])
        path = contract.resolve_task_path(self.root, current, current['report'])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.measurement_report(evidence, gates)))
        contract.verify_task_report(self.root, current)
        # stop() has no branch of its own for this role; it falls into the lane branch,
        # which demands --mode complete plus current gate evidence. Assert that on purpose
        # rather than leaving it true by accident.
        handoff = {'task_id': current['task_id'], 'run_id': current['run_id'], 'mode': 'complete',
                   'summary': 'full declared set measured on an exclusive host', 'artifacts': {}}
        payload = {'cwd': str(self.root), 'agent_type': 'measurement-lane',
                   'last_assistant_message': 'done\nCOLAB_HANDOFF ' + json.dumps(handoff)}
        self.assertEqual(contract.stop(payload, 'measurement-lane'), 'H7')
        for mode in ('read-only', 'draft-return', 'artifacts'):
            bad = dict(payload)
            bad['last_assistant_message'] = 'done\nCOLAB_HANDOFF ' + json.dumps(dict(handoff, mode=mode))
            with self.assertRaises(ValueError):
                contract.stop(bad, 'measurement-lane')
        # Recording red IS this role's output, so a coherent report that carries red rows
        # closes the task. The approved intent constraint wins over the earlier assertion
        # that red blocks here: a lane that may only close all-green rounds cannot measure.
        red = self.measurement_report(evidence, gates)
        red['gates'][1].update(status='red_판정', exit=1)
        red['gates'][2].update(status='red_준비', exit=78)
        red['counts'] = {'green': 1, 'red_판정': 1, 'red_준비': 1}
        path.write_text(json.dumps(red))
        self.assertEqual(contract.stop(payload, 'measurement-lane'), 'H7')
        # Only red is allowed through; edited counts are still a broken report.
        tampered = json.loads(json.dumps(red))
        tampered['counts'] = {'green': 3, 'red_판정': 0, 'red_준비': 0}
        path.write_text(json.dumps(tampered))
        with self.assertRaises(ValueError):
            contract.stop(payload, 'measurement-lane')
        # Measuring less than the declared set is still not completion.
        path.write_text(json.dumps(self.measurement_report(evidence, gates[:2])))
        with self.assertRaises(ValueError):
            contract.stop(payload, 'measurement-lane')

    def test_lane_worker_red_still_blocks_completion(self):
        """The measurement-lane allowance must not leak into the implementing lane."""
        task = contract.begin(self.root, 'lane-worker', gates=['check'])
        evidence = contract.gate_start(self.root, task['task_id'])
        current = contract.load_task(self.root, task['task_id'])
        path = contract.resolve_task_path(self.root, current, current['report'])
        path.parent.mkdir(parents=True, exist_ok=True)
        report = self.measurement_report(evidence, ['check'])
        path.write_text(json.dumps(report))
        contract.verify_task_report(self.root, current)
        for status, code in (('red_판정', 1), ('red_준비', 78)):
            report['gates'][0].update(status=status, exit=code)
            report['counts'] = {'green': 0, 'red_판정': 0, 'red_준비': 0, status: 1}
            path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, 'gate failures remain'):
                contract.verify_task_report(self.root, current)

    def test_measurement_lane_still_cannot_use_group_selectors_or_legacy(self):
        """`--gate all` was rejected on purpose (ADR-0005). Keep it rejected."""
        for selector in ('all', 'task'):
            task = contract.begin(self.root, 'measurement-lane', gates=[selector])
            with self.assertRaises(ValueError) as caught:
                contract.run_gates(self.root, task['task_id'])
            self.assertIn('nested group selectors', str(caught.exception))
        with self.assertRaises(ValueError):
            contract.begin(self.root, 'measurement-lane', gates=[])
        with self.assertRaises(ValueError):
            contract.begin(self.root, 'measurement-lane', legacy=True, gates=['check'],
                           report='dev-package/reports/m/lane/gate-summary.json')

    def test_researcher_still_gets_no_report_and_no_gates(self):
        """The new role widened two role checks; prove it did not widen them too far."""
        task = contract.begin(self.root, 'researcher')
        self.assertIsNone(task['report'])
        with self.assertRaises(ValueError):
            contract.gate_evidence(self.root, task['task_id'])
        with self.assertRaises(ValueError):
            contract.gate_start(self.root, task['task_id'])
        with self.assertRaises(ValueError):
            contract.begin(self.root, 'researcher', gates=['check'])
        with self.assertRaises(ValueError):
            contract.begin(self.root, 'auditor', gates=['check'])


    # ── L1 lane scope (spec S-EXTERNAL-HARNESS-GAP-20260925 · intent 2026-09-25 원한 결과 6) ──
    def complete_lane(self, task_id):
        """Bind a fresh run, write a coherent green report and hand off through stop()."""
        evidence = contract.gate_start(self.root, task_id)
        current = contract.load_task(self.root, task_id)
        path = contract.resolve_task_path(self.root, current, current['report'])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.measurement_report(evidence, current['gates'])))
        handoff = {'task_id': task_id, 'run_id': current['run_id'], 'mode': 'complete',
                   'summary': 'lane result', 'artifacts': {}}
        payload = {'cwd': str(self.root), 'agent_type': 'lane-worker',
                   'last_assistant_message': 'done\nCOLAB_HANDOFF ' + json.dumps(handoff)}
        return contract.stop(payload, 'lane-worker')

    def write(self, relative, text='x'):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def test_lane_scope_blocks_out_of_scope_change_and_names_both_exits(self):
        self.write('keep.txt', 'baseline')
        task = contract.begin(self.root, 'lane-worker', gates=['check'], scope=['src/**', 'docs/a.md'])
        self.assertEqual(task['scope'], ['src/**', 'docs/a.md'])
        self.write('src/deep/module.py')
        self.write('docs/a.md')
        self.write('docs/other.md')
        with self.assertRaises(ValueError) as caught:
            self.complete_lane(task['task_id'])
        message = str(caught.exception)
        self.assertIn('docs/other.md', message)
        self.assertNotIn('src/deep/module.py', message)
        self.assertIn('(1)', message); self.assertIn('--scope', message)
        self.assertIn('(2)', message); self.assertIn('revert', message)
        # A deletion outside the scope is a change outside the scope too.
        (self.root / 'docs/other.md').unlink(); (self.root / 'keep.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'keep.txt'):
            self.complete_lane(task['task_id'])
        self.write('keep.txt', 'baseline')
        self.assertEqual(self.complete_lane(task['task_id']), 'H7')

    def test_lane_scope_counts_committed_changes_after_the_working_copy_is_restored(self):
        task = contract.begin(self.root, 'lane-worker', gates=['check'], scope=['src/**'])
        self.write('docs/other.md', 'out of scope')
        git = ['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid']
        subprocess.run(git + ['add', 'docs/other.md'], check=True)
        subprocess.run(git + ['commit', '-qm', 'out of scope'], check=True)
        (self.root / 'docs/other.md').unlink()  # working copy back to the baseline, commit remains
        with self.assertRaisesRegex(ValueError, 'docs/other.md'):
            self.complete_lane(task['task_id'])

    def test_lane_scope_rejects_forms_that_match_no_file(self):
        self.write('src/a.py')
        for bad in (['src/'], ['src']):
            with self.subTest(scope=bad), self.assertRaisesRegex(ValueError, r'src/\*\*'):
                contract.begin(self.root, 'lane-worker', gates=['check'], scope=bad)

    def test_lane_scope_is_rejected_on_the_legacy_schema(self):
        with self.assertRaisesRegex(ValueError, 'colab-task/2'):
            contract.begin(self.root, 'lane-worker', gates=['check'], report='dev-package/reports/r/l/gate-summary.json',
                           legacy=True, scope=['src/**'])

    def test_lane_scope_sees_leading_space_paths_and_staged_only_changes(self):
        git = ['git', '-C', str(self.root), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid']
        task = contract.begin(self.root, 'lane-worker', gates=['check'], scope=['docs/**'])
        self.write(' docs/x.md', 'out of scope (leading space)')
        subprocess.run(git + ['add', '--', ' docs/x.md'], check=True)
        subprocess.run(git + ['commit', '-qm', 'leading space'], check=True)
        (self.root / ' docs/x.md').unlink()
        with self.assertRaisesRegex(ValueError, ' docs/x.md'):
            self.complete_lane(task['task_id'])
        task = contract.begin(self.root, 'lane-worker', gates=['check'], scope=['src/**'])
        self.write('notes/staged.md', 'staged only')
        subprocess.run(git + ['add', 'notes/staged.md'], check=True)
        (self.root / 'notes/staged.md').unlink()          # index keeps it, working copy restored
        with self.assertRaisesRegex(ValueError, 'notes/staged.md'):
            self.complete_lane(task['task_id'])

    def test_lane_scope_default_allowed_paths_need_no_declaration(self):
        task = contract.begin(self.root, 'lane-worker', gates=['check'], scope=['src/*.py'])
        self.write('src/a.py')
        self.write('dev-package/reports/round/lane/notes.md')
        self.write('docs/development/lifecycle-evidence.md')
        self.assertEqual(self.complete_lane(task['task_id']), 'H7')
        # `*` does not cross a directory; `**` would.
        self.write('src/nested/b.py')
        with self.assertRaisesRegex(ValueError, 'src/nested/b.py'):
            self.complete_lane(task['task_id'])

    def test_lane_without_scope_keeps_current_behavior(self):
        task = contract.begin(self.root, 'lane-worker', gates=['check'])
        self.assertNotIn('scope', task)
        self.write('anywhere/at/all.txt')
        self.assertEqual(self.complete_lane(task['task_id']), 'H7')

    def test_lane_scope_declarations_are_validated(self):
        for bad in ([''], ['/abs/**'], ['../up/**'], ['a/../b'], ['src\\x'], ['./src/**'], ['src/**', 'src/**']):
            with self.subTest(scope=bad), self.assertRaises(ValueError):
                contract.begin(self.root, 'lane-worker', gates=['check'], scope=bad)
        with self.assertRaises(ValueError):
            contract.begin(self.root, 'researcher', scope=['src/**'])

    def test_lane_scope_cli_handoff_is_refused_with_exits(self):
        (self.root / '.gitignore').write_text('__pycache__/\n')
        self.write('gates/run.sh', '#!/usr/bin/env bash\necho verified\n')
        script = str(ROOT / 'scripts/harness/hooks/lifecycle_contract.py')
        def cli(*args):
            return subprocess.run([sys.executable, script, *args], cwd=self.root, text=True, capture_output=True)
        begun = cli('begin', '--role', 'lane-worker', '--gate', 'check', '--scope', 'src/**')
        self.assertEqual(begun.returncode, 0, begun.stderr)
        task_id = json.loads(begun.stdout)['task_id']
        self.write('src/in.py'); self.write('outside.txt')
        self.assertEqual(cli('run-gates', '--task', task_id).returncode, 0)
        refused = cli('handoff', '--task', task_id, '--mode', 'complete', '--summary', 'lane result')
        self.assertEqual(refused.returncode, 78)
        self.assertNotIn('COLAB_HANDOFF', refused.stdout)
        self.assertIn('outside.txt', refused.stderr)
        self.assertIn('--scope', refused.stderr); self.assertIn('revert', refused.stderr)
        (self.root / 'outside.txt').unlink()
        self.assertEqual(cli('run-gates', '--task', task_id).returncode, 0)
        accepted = cli('handoff', '--task', task_id, '--mode', 'complete', '--summary', 'lane result')
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertIn('COLAB_HANDOFF', accepted.stdout)

class ResearcherTaskHookTests(unittest.TestCase):
    """R1 — `SubagentStart` (researcher) opens the H6 task so the first Stop is not bounced.

    The failure this replaces: A3 (2026-09-24) — researchers spawned without
    `lifecycle begin` were bounced by H6 on every Stop until the turn limit.
    The auto task carries no `--agent-id`: `stop()` compares ids only when the task has one,
    and SubagentStart/SubagentStop id equality is not yet proven.
    """
    HOOK = ROOT / 'scripts/harness/hooks/researcher-task.sh'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # A small real checkout: the hook begins with the cwd checkout's own bridge.
        self.root = Path(self.tmp.name) / 'repo'
        ignore = shutil.ignore_patterns('__pycache__')
        (self.root / 'scripts').mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts/agent-bridge.py', self.root / 'scripts/agent-bridge.py')
        shutil.copytree(ROOT / 'scripts/harness', self.root / 'scripts/harness', ignore=ignore)
        shutil.copytree(ROOT / '.claude/hooks', self.root / '.claude/hooks', ignore=ignore)
        shutil.copy2(ROOT / '.claude/settings.json', self.root / '.claude/settings.json')
        (self.root / '.gitignore').write_text('__pycache__/\n')
        git = ['git', '-C', str(self.root)]
        subprocess.run(git + ['init', '-q'], check=True)
        subprocess.run(git + ['add', '-A'], check=True)
        subprocess.run(git + ['-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                              'commit', '-qm', 'initial'], check=True)

    def run_hook(self, payload, **env):
        environment = dict(os.environ, **env)
        if 'COLAB_HOOKS' not in env:
            environment.pop('COLAB_HOOKS', None)
        return subprocess.run(['bash', str(self.HOOK)], input=json.dumps(payload), text=True,
                              capture_output=True, env=environment, timeout=120)

    def start(self, agent_id='spawn-aid'):
        payload = {'cwd': str(self.root), 'hook_event_name': 'SubagentStart',
                   'agent_type': 'researcher', 'agent_id': agent_id}
        result = self.run_hook(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def printed(self, output, key):
        match = re.search(r'^\s*' + key + r'\s*:\s*([a-f0-9]{32})\s*$', output, re.MULTILINE)
        self.assertIsNotNone(match, output)
        return match.group(1)

    def bridge(self, *args, stdin=None):
        return subprocess.run([sys.executable, 'scripts/agent-bridge.py', 'lifecycle', *args], cwd=self.root,
                              input=stdin, text=True, capture_output=True, timeout=120)

    def handoff(self, task_id, mode='read-only'):
        result = self.bridge('handoff', '--task', task_id, '--mode', mode, '--summary', 'actual findings')
        self.assertEqual(result.returncode, 0, result.stderr)
        markers = [line for line in result.stdout.splitlines() if line.startswith('COLAB_HANDOFF ')]
        self.assertEqual(len(markers), 1, result.stdout)
        return markers[0]

    def stop_payload(self, marker, agent_id):
        return {'cwd': str(self.root), 'hook_event_name': 'SubagentStop', 'agent_type': 'researcher',
                'agent_id': agent_id, 'last_assistant_message': 'findings\n' + marker}

    def runtime_tasks(self):
        common = self.root / '.git' / 'colab-harness'
        return sorted(common.rglob('task.json')) if common.exists() else []

    def test_a_researcher_start_begins_task_and_prints_ids_and_handoff_command(self):
        output = self.start()
        task_id, run_id = self.printed(output, 'task_id'), self.printed(output, 'run_id')
        task = contract.load_task(self.root.resolve(), task_id)
        self.assertEqual((task['role'], task['run_id'], task['agent_id']), ('researcher', run_id, None))
        self.assertIn('spawn-aid', output)
        self.assertIn(f"python3 scripts/agent-bridge.py lifecycle handoff --task {task_id} --mode read-only", output)
        self.assertIn('COLAB_HANDOFF', output)
        self.assertIn('--agent-id spawn-aid --artifact runtime:artifacts/', output)
        self.assertIn('커밋', output)
        self.assertLessEqual(len(output.splitlines()), 15)

    def test_b_printed_task_hands_off_and_passes_h6_for_a_different_stop_agent_id(self):
        task_id = self.printed(self.start(), 'task_id')
        marker = self.handoff(task_id)
        # ⓑ′ — the Stop payload's agent_id differs from the one SubagentStart saw.
        self.assertEqual(contract.stop(self.stop_payload(marker, 'stop-aid-other'), 'researcher'), 'H6')
        hook = subprocess.run(['bash', str(ROOT / 'scripts/harness/hooks/uncommitted-artifacts.sh')],
                              input=json.dumps(self.stop_payload(marker, 'stop-aid-other')),
                              text=True, capture_output=True, timeout=120)
        self.assertEqual(hook.returncode, 0, hook.stderr)

    def test_b_control_task_begun_with_agent_id_rejects_a_different_stop_agent_id(self):
        begun = self.bridge('begin', '--role', 'researcher', '--agent-id', 'spawn-aid',
                            '--artifact', 'runtime:artifacts/notes.md')
        self.assertEqual(begun.returncode, 0, begun.stderr)
        task = json.loads(begun.stdout)
        wrote = self.bridge('write-artifact', '--task', task['task_id'], '--run-id', task['run_id'],
                            '--agent-id', 'spawn-aid', '--artifact', 'runtime:artifacts/notes.md', stdin='notes')
        self.assertEqual(wrote.returncode, 0, wrote.stderr)
        marker = self.handoff(task['task_id'], 'artifacts')
        self.assertEqual(contract.stop(self.stop_payload(marker, 'spawn-aid'), 'researcher'), 'H6')
        with self.assertRaisesRegex(ValueError, 'agent identity'):
            contract.stop(self.stop_payload(marker, 'stop-aid-other'), 'researcher')

    def test_c_second_artifact_task_with_same_agent_id_keeps_first_handoff_valid(self):
        output = self.start()
        first = self.printed(output, 'task_id')
        command = re.search(r'python3 scripts/agent-bridge\.py lifecycle (begin --role researcher --agent-id \S+ '
                            r'--artifact runtime:artifacts/)<[^>]+>', output)
        self.assertIsNotNone(command, output)
        args = command.group(1).split()
        args[-1] += 'notes.md'
        second = self.bridge(*args)
        self.assertEqual(second.returncode, 0, second.stderr)
        task = json.loads(second.stdout)
        self.assertEqual(task['agent_id'], 'spawn-aid')
        wrote = self.bridge('write-artifact', '--task', task['task_id'], '--run-id', task['run_id'],
                            '--agent-id', 'spawn-aid', '--artifact', 'runtime:artifacts/notes.md', stdin='notes')
        self.assertEqual(wrote.returncode, 0, wrote.stderr)
        self.assertEqual(contract.stop(self.stop_payload(self.handoff(first), 'x'), 'researcher'), 'H6')
        marker = self.handoff(task['task_id'], 'artifacts')
        self.assertEqual(contract.stop(self.stop_payload(marker, 'spawn-aid'), 'researcher'), 'H6')

    def test_d_non_git_cwd_reports_begin_failure_and_exits_zero(self):
        outside = Path(self.tmp.name) / 'plain'
        outside.mkdir()
        result = self.run_hook({'cwd': str(outside), 'agent_type': 'researcher', 'agent_id': 'a1'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('researcher-task: begin 실패', result.stdout)
        self.assertIn('사유', result.stdout)
        self.assertIn('lifecycle begin --role researcher', result.stdout)
        self.assertNotIn('--agent-id', result.stdout)

    def test_e_disabled_hooks_print_nothing(self):
        result = self.run_hook({'cwd': str(self.root), 'agent_type': 'researcher', 'agent_id': 'a1'}, COLAB_HOOKS='0')
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        self.assertFalse(self.runtime_tasks())

    def test_f_other_roles_print_nothing_and_begin_nothing(self):
        for agent_type in ('lane-worker', 'Explore', 'advisor'):
            with self.subTest(agent_type=agent_type):
                result = self.run_hook({'cwd': str(self.root), 'agent_type': agent_type, 'agent_id': 'a1'})
                self.assertEqual((result.returncode, result.stdout), (0, ''))
        self.assertFalse(self.runtime_tasks())

    def test_f2_missing_agent_type_is_announced_not_silently_skipped(self):
        for payload in ({'cwd': str(self.root), 'agent_type': '', 'agent_id': 'a1'},
                        {'cwd': str(self.root), 'agent_id': 'a1'}):
            with self.subTest(payload=sorted(payload)):
                result = self.run_hook(payload)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('researcher-task: agent_type 없음', result.stdout)
                self.assertIn('lifecycle begin --role researcher', result.stdout)
        self.assertFalse(self.runtime_tasks())

    def load_bridge(self):
        spec = importlib.util.spec_from_file_location('fixture_bridge', self.root / 'scripts/agent-bridge.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_codex_subagent_start_carries_output_to_additional_context(self):
        event = {'cwd': str(self.root), 'hook_event_name': 'SubagentStart', 'agent_type': 'researcher',
                 'agent_id': 'codex-aid'}
        context = self.load_bridge().dispatch_event(event)['hookSpecificOutput']['additionalContext']
        task_id = self.printed(context, 'task_id')
        self.assertIn('codex-aid', context)
        self.assertIn(f'lifecycle handoff --task {task_id} --mode read-only', context)
        self.assertNotIn('prepares dependencies', context)
        self.assertIsNone(contract.load_task(self.root.resolve(), task_id)['agent_id'])

    def test_codex_payload_without_agent_id_still_begins_without_agent_id(self):
        event = {'cwd': str(self.root), 'hook_event_name': 'SubagentStart', 'agent_type': 'researcher'}
        context = self.load_bridge().dispatch_event(event)['hookSpecificOutput']['additionalContext']
        task_id = self.printed(context, 'task_id')
        self.assertIsNone(contract.load_task(self.root.resolve(), task_id)['agent_id'])
        self.assertNotIn('--agent-id <', context)
        self.assertIn('--artifact runtime:artifacts/', context)
        marker = self.handoff(task_id)
        self.assertEqual(contract.stop(self.stop_payload(marker, 'any'), 'researcher'), 'H6')


if __name__ == '__main__': unittest.main()
