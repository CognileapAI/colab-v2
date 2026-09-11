import copy
import errno
import importlib.util
import io
import sys
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
contract = module('lifecycle_contract', ROOT/'.claude/hooks/lifecycle_contract.py')
bridge = module('bridge_lifecycle_test', ROOT/'scripts/agent-bridge.py')
producer = module('gate_summary_producer_test', ROOT/'gates/tools/gate_summary_json.py')


@unittest.skipIf(os.name == 'nt', 'Bash hook integration requires WSL')
class LifecycleRedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git','init','-q',str(self.root)], check=True)
        self.env = dict(os.environ, COLAB_HOOKS='1')
        self.env.pop('COLAB_GATE_REPORT_DIR', None)

    def hook(self, name, role, message='', route='claude'):
        payload = dict(cwd=str(self.root), agent_type=role, hook_event_name='SubagentStop',
                       last_assistant_message=message)
        if route == 'codex':
            with patch.object(bridge, 'ROOT', self.root), patch.object(bridge, 'registered_hooks', return_value=[ROOT/'.claude/hooks'/name]):
                try:
                    output = bridge.dispatch_event(payload)
                    return subprocess.CompletedProcess([], 0, json.dumps(output), '')
                except ValueError as exc:
                    return subprocess.CompletedProcess([], 2, '', str(exc))
        return subprocess.run(['bash',str(ROOT/'.claude/hooks'/name)], input=json.dumps(payload),
                              text=True, capture_output=True, cwd=self.root, env=self.env)

    def test_broken_report_must_block(self):
        report = self.root/'dev-package/reports/old/gate-summary.json'
        report.parent.mkdir(parents=True)
        report.write_text('{broken')
        result = self.hook('lane-gate-summary.sh', 'lane-worker')
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_missing_task_and_handoff_must_block_researcher(self):
        result = self.hook('uncommitted-artifacts.sh', 'researcher')
        self.assertEqual(result.returncode, 2, result.stdout)

    def put(self, name, content):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def marker(self, task, mode, artifacts=None):
        return 'Actual findings returned to parent.\nCOLAB_HANDOFF ' + json.dumps(dict(
            task_id=task['task_id'], mode=mode, summary='Observed current input and result', artifacts=artifacts or {}))

    def assert_routes(self, role, message, expected):
        hook = 'uncommitted-artifacts.sh' if role == 'researcher' else 'lane-gate-summary.sh'
        for route in ('claude', 'codex'):
            with self.subTest(route=route):
                result = self.hook(hook, role, message, route)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_unrelated_preexisting_output_allows_read_only_and_draft_return(self):
        self.put('dev-package/sessions/other-task.md', 'untracked before this task')
        task = contract.begin(self.root, 'researcher')
        for mode in ('read-only', 'draft-return'):
            self.assert_routes('researcher', self.marker(task, mode), 0)
        self.assertEqual(self.put('dev-package/sessions/other-task.md', 'untracked before this task').read_text(), 'untracked before this task')

    def test_this_task_output_without_handoff_blocks(self):
        task = contract.begin(self.root, 'researcher')
        self.put('dev-package/intent/new.md', 'unapproved draft')
        self.assert_routes('researcher', self.marker(task, 'read-only'), 2)
        self.assert_routes('researcher', '', 2)

    def test_declared_untracked_artifact_can_be_handed_off_without_commit(self):
        name = 'dev-package/intent/new.md'
        task = contract.begin(self.root, 'researcher', artifacts=[name])
        path = self.put(name, 'approval: pending')
        msg = self.marker(task, 'artifacts', {name: contract.digest(path)})
        self.assert_routes('researcher', msg, 0)
        self.assertIn('??', contract.git(self.root, 'status', '--porcelain'))
        self.put(name, 'changed after handoff')
        self.assert_routes('researcher', msg, 2)
        path.unlink()
        self.assert_routes('researcher', msg, 2)

    def test_research_product_edit_is_rejected(self):
        task = contract.begin(self.root, 'researcher', artifacts=['dev-package/sessions/new.md'])
        path = self.put('dev-package/sessions/new.md', 'findings')
        self.put('product.py', 'unauthorized edit')
        self.assert_routes('researcher', self.marker(task, 'artifacts', {'dev-package/sessions/new.md': contract.digest(path)}), 2)

    def lane(self):
        self.put('product.py', 'dirty working content')
        task = contract.begin(self.root, 'lane-worker', gates=['contract-lint'],
                              report='dev-package/reports/current/lane/gate-summary.json')
        evidence = contract.gate_start(self.root, task['task_id'])
        task = contract.load_task(self.root, task['task_id'])
        report = dict(schema='colab-gate-summary/1', tree='head-does-not-prove-working-content',
                      counts={'green': 1, 'red_판정': 0, 'red_준비': 0},
                      gates=[dict(name='contract-lint', status='green', exit=0)],
                      task_evidence={'before': evidence, 'after': evidence})
        self.put(task['report'], json.dumps(report))
        return task, report

    def test_dirty_working_content_gate_is_accepted_then_stale_change_rejected(self):
        task, report = self.lane()
        msg = self.marker(task, 'complete')
        self.assert_routes('lane-worker', msg, 0)
        self.put('product.py', 'later content')
        self.assert_routes('lane-worker', msg, 2)

    def test_no_fallback_to_other_report_when_declared_one_missing(self):
        task, report = self.lane()
        (self.root/task['report']).unlink()
        self.put('dev-package/reports/other/gate-summary.json', json.dumps(report))
        self.assert_routes('lane-worker', self.marker(task, 'complete'), 2)

    def test_invalid_gate_evidence_never_passes_either_harness(self):
        task, original = self.lane()
        for mutate in (lambda d: d.clear(), lambda d: d.update(gates=[]),
                       lambda d: d['gates'][0].update(name='other-gate'),
                       lambda d: d['counts'].update(green=0, red_준비=1),
                       lambda d: d['task_evidence']['before'].update(files='changed-during-run'),
                       lambda d: d['task_evidence']['after'].update(task_id='other-task'),
                       lambda d: d['task_evidence']['after'].update(checkout='other-checkout')):
            report = copy.deepcopy(original)
            mutate(report)
            self.put(task['report'], json.dumps(report))
            self.assert_routes('lane-worker', self.marker(task, 'complete'), 2)
        self.put(task['report'], '{broken')
        self.assert_routes('lane-worker', self.marker(task, 'complete'), 2)

    def test_actual_summary_producer_binds_task_and_rejects_changed_during_gate(self):
        self.put('product.py', 'before execution')
        task = contract.begin(self.root, 'lane-worker', gates=['contract-lint'],
                              report='dev-package/reports/producer/lane/gate-summary.json')
        before = contract.gate_start(self.root, task['task_id'])
        task = contract.load_task(self.root, task['task_id'])
        tsv = 'meta\tcontract-lint\ttree\tcommit\tstart\tfinish\t1\ncounts\t1\t0\t0\t0\ngate\tcontract-lint\tgreen\t0\t\ntarget\tcontract-lint\n'
        for changed in (False, True):
            if changed:
                self.put('product.py', 'changed while gate ran')
            with patch.object(producer, '__file__', str(self.root/'gates/tools/gate_summary_json.py')), patch.object(sys, 'argv', ['producer',str(self.root/task['report'])]), patch.object(sys, 'stdin', io.StringIO(tsv)), patch.dict(os.environ, {'COLAB_TASK_ID':task['task_id'], 'COLAB_GATE_TASK_BEFORE':json.dumps(before)}):
                self.assertEqual(producer.main(),0)
            self.assert_routes('lane-worker', self.marker(task, 'complete'), 2 if changed else 0)

    def test_new_gate_run_invalidates_old_success_even_if_producer_fails(self):
        task, report = self.lane()
        self.assert_routes('lane-worker', self.marker(task, 'complete'), 0)
        contract.gate_start(self.root, task['task_id'])
        self.assertFalse((self.root/task['report']).exists())
        self.assert_routes('lane-worker', self.marker(task, 'complete'), 2)
        # Even restoring the old JSON cannot satisfy the new run identity.
        self.put(task['report'], json.dumps(report))
        self.assert_routes('lane-worker', self.marker(task, 'complete'), 2)

    def test_gate_start_archives_report_across_filesystems(self):
        task, report = self.lane()
        report_path = self.root/task['report']
        original = report_path.read_bytes()
        real_replace = os.replace
        calls = []

        def cross_device_once(source, destination):
            calls.append((Path(source), Path(destination)))
            if len(calls) == 1:
                raise OSError(errno.EXDEV, 'cross-device link')
            return real_replace(source, destination)

        with patch.object(contract.os, 'replace', side_effect=cross_device_once):
            contract.gate_start(self.root, task['task_id'])
        archive = contract.task_path(self.root, task['task_id']).parent/'history'/task['task_id']/(task['run_id']+'.json')
        self.assertEqual(archive.read_bytes(), original)
        self.assertFalse(report_path.exists())
        self.assertGreaterEqual(len(calls), 2)

    def test_cross_filesystem_archive_copy_failure_preserves_source(self):
        source = self.put('dev-package/reports/current/lane/gate-summary.json', 'current evidence')
        destination = self.root/'private/history/evidence.json'
        with patch.object(contract.os, 'replace', side_effect=OSError(errno.EXDEV, 'cross-device link')), \
             patch.object(contract.shutil, 'copy2', side_effect=OSError('copy failed')):
            with self.assertRaisesRegex(OSError, 'copy failed'):
                contract.archive_report(source, destination)
        self.assertEqual(source.read_text(), 'current evidence')
        self.assertFalse(destination.exists())
        self.assertEqual(list(destination.parent.glob('.evidence.json.*.tmp')), [])

    def test_gate_start_archive_failure_invalidates_retained_old_report(self):
        task, report = self.lane()
        report_path = self.root/task['report']
        old_run_id = task['run_id']
        with patch.object(contract.os, 'replace', side_effect=OSError(errno.EXDEV, 'cross-device link')), \
             patch.object(contract.shutil, 'copy2', side_effect=OSError('copy failed')):
            with self.assertRaisesRegex(OSError, 'copy failed'):
                contract.gate_start(self.root, task['task_id'])
        current = contract.load_task(self.root, task['task_id'])
        self.assertNotEqual(current['run_id'], old_run_id)
        self.assertTrue(report_path.exists())
        with self.assertRaisesRegex(ValueError, 'stale'):
            contract.verify_task_report(self.root, current)

    def test_archive_propagates_non_cross_filesystem_replace_error(self):
        source = self.put('dev-package/reports/current/lane/gate-summary.json', 'current evidence')
        destination = self.root/'private/history/evidence.json'
        with patch.object(contract.os, 'replace', side_effect=OSError(errno.EACCES, 'denied')):
            with self.assertRaisesRegex(OSError, 'denied'):
                contract.archive_report(source, destination)
        self.assertTrue(source.exists())
        self.assertFalse(destination.exists())

    def test_raw_guard_malformed_input_blocks_but_irrelevant_tool_is_allowed(self):
        for name in ('git-guard.sh', 'migration-guard.sh', 'decision-number-guard.sh', 'test-file-guard.sh'):
            for payload, expected in (('{broken',2), ('{}',2),
                                      (json.dumps(dict(tool_name='Read', tool_input={})),0)):
                with self.subTest(hook=name, payload=payload):
                    result = subprocess.run(['bash',str(ROOT/'.claude/hooks'/name)],input=payload,text=True,
                                            capture_output=True,cwd=self.root,env=dict(self.env,COLAB_FIX_LANE='1'))
                    self.assertEqual(result.returncode,expected,result.stdout+result.stderr)

    def test_declared_multiple_gates_complete_in_one_run_and_failure_is_not_hidden(self):
        runner = self.put('gates/run.sh', '#!/usr/bin/env bash\nprintf "ran %s\\n" "$1"\nif [ "$1" = "second" ]; then exit "${FIXTURE_GATE_EXIT:-0}"; fi\n')
        task = contract.begin(self.root, 'lane-worker', gates=['first', 'second'],
                              report='dev-package/reports/group/lane/gate-summary.json')
        for code in (0, 1, 78):
            with patch.dict(os.environ, {'FIXTURE_GATE_EXIT':str(code)}):
                self.assertEqual(contract.run_gates(self.root, task['task_id']),code)
            task = contract.load_task(self.root,task['task_id'])
            report = json.loads((self.root/task['report']).read_text())
            self.assertEqual([row['name'] for row in report['gates']], ['first','second'])
            self.assertEqual(report['task_evidence']['before']['run_id'], task['run_id'])
            self.assert_routes('lane-worker', self.marker(task, 'complete'), 0 if code == 0 else 2)

    def test_codex_decision_content_hits_shared_judge_without_editing_file(self):
        ledger = self.put('dev-package/PLAN-SoT.md','| 〈5〉 | existing |')
        maximum = self.put('dev-package/prd/tools/max-decision.sh','#!/usr/bin/env bash\necho 5\n')
        maximum.chmod(0o755)
        for number, allowed in ((6, True), (99999, False)):
            event = dict(cwd=str(self.root),hook_event_name='PreToolUse',tool_name='apply_patch',
                         tool_input=dict(command='*** Begin Patch\n*** Update File: dev-package/PLAN-SoT.md\n@@\n+| 〈%d〉 | decision |\n*** End Patch' % number))
            with patch.object(bridge,'ROOT',self.root), patch.object(bridge,'registered_hooks',return_value=[ROOT/'.claude/hooks/decision-number-guard.sh']):
                if allowed:
                    bridge.dispatch_event(event)
                else:
                    with self.assertRaises(ValueError):
                        bridge.dispatch_event(event)
            self.assertEqual(ledger.read_text(),'| 〈5〉 | existing |')

    def test_raw_ledger_requires_content_and_normalizes_relative_paths(self):
        ledger = self.put('dev-package/PLAN-SoT.md','| 〈5〉 | existing |')
        maximum = self.put('dev-package/prd/tools/max-decision.sh','#!/usr/bin/env bash\necho 5\n')
        maximum.chmod(0o755)
        for tool, field in (('Edit','new_string'),('Write','content')):
            for value in (None, 3, [], {}):
                payload = dict(cwd=str(self.root),tool_name=tool,tool_input=dict(file_path='dev-package/../dev-package/PLAN-SoT.md'))
                if value is not None:
                    payload['tool_input'][field]=value
                result=subprocess.run(['bash',str(ROOT/'.claude/hooks/decision-number-guard.sh')],input=json.dumps(payload),text=True,capture_output=True,cwd=self.root,env=self.env)
                self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        for path in ('frontend/test/../test/example.ts','../outside.py'):
            payload=dict(cwd=str(self.root),tool_name='Edit',tool_input=dict(file_path=path))
            result=subprocess.run(['bash',str(ROOT/'.claude/hooks/test-file-guard.sh')],input=json.dumps(payload),text=True,capture_output=True,cwd=self.root,env=dict(self.env,COLAB_FIX_LANE='1'))
            self.assertEqual(result.returncode,2,result.stdout+result.stderr)

    def test_agent_identity_mismatch_blocks(self):
        task = contract.begin(self.root, 'researcher', agent_id='assigned-agent')
        self.assert_routes('researcher', self.marker(task, 'read-only'), 2)

    def test_bootstrap_explicit_round_and_unselected_candidate(self):
        self.put('dev-package/prd/rounds/R-A.md', 'selected')
        self.put('dev-package/prd/rounds/R-Z.md', 'newer but unrelated')
        payload = dict(cwd=str(self.root), hook_event_name='SessionStart', round='dev-package/prd/rounds/R-A.md')
        result = subprocess.run(['bash', str(ROOT/'.claude/hooks/bootstrap-diet.sh')], input=json.dumps(payload), text=True, capture_output=True, cwd=self.root)
        self.assertIn('지정 라운드', result.stdout)
        self.assertIn('R-A.md', result.stdout)
        self.assertNotIn('R-Z.md', result.stdout)
        payload.pop('round')
        result = subprocess.run(['bash', str(ROOT/'.claude/hooks/bootstrap-diet.sh')], input=json.dumps(payload), text=True, capture_output=True, cwd=self.root)
        self.assertIn('추천', result.stdout)
        self.assertIn('Git', result.stdout)

    def test_lifecycle_payload_preserves_assigned_subdirectory(self):
        child = self.root/'child'
        child.mkdir()
        with patch.object(bridge, 'ROOT', self.root), patch.object(bridge, 'registered_hooks', return_value=[Path('hook')]), patch.object(bridge.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([],0,'','')
            bridge.dispatch_event(dict(cwd=str(child), hook_event_name='SubagentStart', agent_type='lane-worker'))
            self.assertEqual(json.loads(run.call_args.kwargs['input'])['cwd'], str(child))

if __name__ == '__main__':
    unittest.main()
