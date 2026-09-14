import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location('work_state', ROOT/'scripts/harness/work_state.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class WorkStateTests(unittest.TestCase):
    def test_handoff_special_rows_cannot_be_omitted(self):
        first='| 1 | fixture | work |\n'
        for second in ('| ~~2~~ | fixture | work |\n','  | 2 | fixture | work |\n','\n| 2 | fixture | work |\n'):
            raw=('## 4. 블로커 (사람이 풀어야 할 것)\n| # | 블로커 | 막는 것 |\n|---|---|---|\n'+first+second).encode()
            manifest={'source_sha256':self.m.digest(raw),'classifications':[{'row_sha256':self.m.digest(first.encode()),'kind':'historical-resolved'}]}
            with self.subTest(row=second),self.assertRaises(self.m.StateError):self.m.verify_handoff_classification(manifest,raw,{})

    def test_handoff_cannot_reduce_actual_rows_to_one_classification(self):
        first = '| 1 | fixture one | work |\n'
        second = '| 2 | fixture two | work |\n'
        raw = ('## 4. 블로커 (사람이 풀어야 할 것)\n| # | 블로커 | 막는 것 |\n|---|---|---|\n'+first+second).encode()
        manifest = {'source_sha256': self.m.digest(raw), 'classifications': [
            {'row_sha256': self.m.digest(first.encode()), 'kind':'historical-resolved'}]}
        with self.assertRaises(self.m.StateError): self.m.verify_handoff_classification(manifest, raw, {})
        manifest['classifications'].append({'row_sha256':self.m.digest(second.encode()), 'kind':'security-excluded'})
        self.m.verify_handoff_classification(manifest, raw, {})
        manifest['classifications'][1]['kind'] = 'unclassified'
        with self.assertRaises(self.m.StateError): self.m.verify_handoff_classification(manifest, raw, {})

    def test_real_gate_dispatches_explicit_state_without_legacy_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'state.json'; path.write_text(json.dumps(self.state))
            env = dict(os.environ, COLAB_WORK_STATE_MODE='work-state', COLAB_WORK_STATE_INPUT=str(path), COLAB_WORK_ITEMS_LEDGER=str(Path(directory)/'missing.yaml'))
            command = [sys.executable, str(ROOT/'gates/tools/work_item_consistency.py')]
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            env.pop('COLAB_WORK_STATE_INPUT')
            self.assertEqual(subprocess.run(command, cwd=ROOT, env=env, capture_output=True).returncode, 78)

    def test_task_uses_real_runtime_and_rejects_stale_run_sha_and_hash(self):
        lifecycle = self.m.module('state_test_lifecycle', 'hooks/lifecycle_contract.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root/'gates').mkdir(); (root/'gates/run.sh').write_text('exit 0\n')
            (root/'plan.md').write_text('completion definition')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
            task = lifecycle.begin(root, 'lane-worker', gates=['fixture'], artifacts=['runtime:artifacts/work-binding.json'])
            lifecycle.gate_start(root, task['task_id'])
            task = lifecycle.load_task(root, task['task_id'])
            binding_path = Path(task['artifacts'][0]); binding_path.parent.mkdir(parents=True)
            binding_path.write_text(json.dumps({'schema': 'colab-work-binding/1', 'item_id': 'local-1',
                'completion_def': {'path': 'plan.md', 'sha256': self.m.digest((root/'plan.md').read_bytes())}, 'required_gates': ['fixture']}))
            self.assertEqual(lifecycle.run_gates(root, task['task_id'], before=lifecycle.gate_evidence(root, task['task_id'])), 0)
            task = lifecycle.load_task(root, task['task_id'])
            report = Path(task['report'])
            reference = {key: task[key] for key in ('task_id', 'run_id', 'checkout_id')}
            reference['report_sha256'] = self.m.digest(report.read_bytes())
            reference['binding'] = str(binding_path)
            self.m.verify_task(reference, root, self.state['issues'][0])
            for mutation in ('id', 'completion', 'gate'):
                unrelated = copy.deepcopy(self.state['issues'][0])
                if mutation == 'id': unrelated['id'] = 'unrelated'
                if mutation == 'completion': unrelated['product']['completion_def_ref'] = 'other.md'
                if mutation == 'gate': unrelated['product']['required_gates'] = ['missing-gate']
                with self.subTest(binding=mutation), self.assertRaises(self.m.StateError):
                    self.m.verify_task(reference, root, unrelated)
            # Compose real task evidence with the actual CI registry bundle; no judge mocks.
            ci = self.m.module('state_test_ci', 'verify_evidence.py')
            registry = ci.load_registry(); identity = lifecycle.head_identity(root)
            commit, tree = identity['commit'], identity['tree']
            filters = {key: 'false' for item in registry.values() for key in item['filters']}
            needs = {item['job']: {'result': 'skipped'} for item in registry.values()}
            needs.update({'changes': {'result': 'success'}, 'repo-hygiene': {'result': 'success'}})
            bundle = root/'.git/ci-fixture'; bundle.mkdir()
            for name, check in registry['repo-hygiene']['checks'].items():
                folder = bundle/name; folder.mkdir()
                record = {'schema': 'colab-ci-check/1', 'producer': 'repo-hygiene', 'check': name,
                    'run_id': '1', 'run_attempt': 1, 'commit': commit, 'tree': tree,
                    'kind': check['kind'], 'command': check['command'], 'exit': 0,
                    'counts': {'green': 1, 'red_judgment': 0, 'red_readiness': 0}}
                (folder/'evidence.json').write_text(json.dumps(record))
                (folder/'gate-summary.json').write_text(json.dumps({'schema': 'colab-gate-summary/1',
                    'commit': commit, 'tree': tree, 'counts': {'green': len(check['gates']), 'red_판정': 0, 'red_준비': 0},
                    'gates': [{'name': g, 'status': 'green', 'state': 'green', 'exit': 0} for g in check['gates']]}))
            event = {'after': commit, 'before': commit}
            jobs = ci.collect_ci('1', 1, commit, tree, registry, needs, filters, bundle)
            evidence = ci.build_ci_evidence('1', 1, commit, tree, ci.event_shas('push', event, commit), jobs)
            evidence['inputs'] = {'event_name': 'push', 'event': event, 'needs': needs, 'filters': filters}
            completed = copy.deepcopy(self.state); issue = completed['issues'][0]
            issue.update(state='closed', task=reference, pr={'head_sha': commit, 'merge_sha': commit,
                         'merged': True, 'ci': evidence, 'artifact_root': str(bundle)})
            issue['product'].update(status='done', evidence_ref='local-ci')
            with self.assertRaises(self.m.StateError):
                self.m.verify_pr(issue['pr'], root)
            record = {'schema': 'colab-github-pr-record/1',
                'source': {'repository': 'CognileapAI/colab-v2', 'number': 1, 'endpoint': 'repos/CognileapAI/colab-v2/pulls/1', 'transport': 'gh-api', 'fetched_at': '2026-09-15T01:00:00+00:00'},
                'record': {'number': 1, 'state': 'closed', 'merged': True, 'merged_at': '2026-09-15T00:00:00+00:00',
                    'head': {'sha': commit}, 'merge_commit_sha': commit, 'base': {'ref': 'main', 'repo': {'full_name': 'CognileapAI/colab-v2'}}}}
            record_path = root/'.git/pr-record.json'; record_path.write_text(json.dumps(record))
            issue['pr'].update(number=1, repository='CognileapAI/colab-v2', base_ref='main',
                record={'path': str(record_path), 'sha256': self.m.digest(record_path.read_bytes())})
            self.m.validate(completed, root)
            for key, value in [('number', 2), ('repository', 'other/repo'), ('head_sha', 'b'*40), ('merge_sha', 'b'*40)]:
                bad_pr = copy.deepcopy(issue['pr']); bad_pr[key] = value
                with self.subTest(pr=key), self.assertRaises(self.m.StateError): self.m.verify_pr(bad_pr, root)
            bad = copy.deepcopy(completed); bad['issues'][0]['pr']['ci']['run_id'] = '2'
            with self.assertRaises(self.m.StateError): self.m.validate(bad, root)
            for key in ('run_id', 'checkout_id', 'report_sha256'):
                bad = dict(reference); bad[key] = '0'*32
                with self.subTest(key=key), self.assertRaises(self.m.StateError): self.m.verify_task(bad, root)
            data = json.loads(report.read_text()); data['commit'] = 'b'*40; report.write_text(json.dumps(data))
            reference['report_sha256'] = self.m.digest(report.read_bytes())
            with self.assertRaises(self.m.StateError): self.m.verify_task(reference, root)

    def test_pr_missing_bundle_and_wrong_sha_fail_closed(self):
        with self.assertRaises(self.m.ReadinessError):
            self.m.verify_pr({'head_sha': 'a'*40, 'merge_sha': 'b'*40, 'merged': True}, ROOT)
        with self.assertRaises(self.m.StateError):
            self.m.verify_pr({'head_sha': 'short', 'merge_sha': 'b'*40, 'merged': True}, ROOT)

    def test_decision_index_retains_hash_not_content_and_rejects_duplicates(self):
        raw = '| 〈1〉 | PRIVATE-DECISION |\n'.encode()
        result = self.m.decision_index(raw, 'plan.md')
        self.assertEqual(result['decisions'][0]['number'], 1)
        self.assertNotIn('PRIVATE', json.dumps(result))
        with self.assertRaises(self.m.StateError): self.m.decision_index(raw+raw, 'plan.md')

    def setUp(self):
        self.m = load()
        self.state = {'schema': 'colab-work-state/1', 'issues': [
            {'id': 'local-1', 'number': None, 'state': 'open', 'dependencies': [],
             'product': {'title': 'Local work', 'owner': 'test', 'status': 'open', 'stage': 'stage1',
                         'entry_conditions': [], 'completion_def_ref': 'plan.md', 'evidence_ref': '', 'deadline': None, 'required_gates': ['fixture']}}]}

    def test_new_mode_preserves_product_status_stage_deadline_conflict_rules(self):
        for key, value in [('stage', 'invalid'), ('status', 'conflict'), ('status', 'partial'),
                           ('completion_def_ref', ''), ('deadline', {'condition': 'now', 'fired': True}), ('ignored', 'field')]:
            bad = copy.deepcopy(self.state); bad['issues'][0]['product'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(self.m.StateError):
                self.m.validate(bad, ROOT)

    def test_open_local_issue_needs_no_legacy_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            self.m.validate(self.state, Path(directory))

    def test_empty_duplicate_and_missing_dependencies_fail(self):
        for mutation in ('empty', 'id', 'number', 'dependency', 'closed'):
            value = copy.deepcopy(self.state)
            if mutation == 'empty': value['issues'] = []
            if mutation == 'id': value['issues'] *= 2
            if mutation == 'number':
                value['issues'][0]['number'] = 3
                value['issues'].append({'id': 'local-2', 'number': 3, 'state': 'open', 'dependencies': []})
            if mutation == 'dependency': value['issues'][0]['dependencies'] = ['missing']
            if mutation == 'closed': value['issues'][0]['state'] = 'closed'
            with self.subTest(mutation=mutation), self.assertRaises(self.m.StateError):
                self.m.validate(value, ROOT)

    def test_safe_export_does_not_publish_notes_or_completion_text(self):
        item = {'id': 'A', 'name': 'Title', 'status': 'open', 'stage': 'stage1',
                'depends_on': [], 'completion_def': 'PRIVATE-COMPLETION', 'note': 'PRIVATE-NOTE', 'evidence': 'PRIVATE-EVIDENCE'}
        exported = self.m.safe_export([item], 'ledger.yaml')
        encoded = json.dumps(exported)
        self.assertNotIn('PRIVATE', encoded)
        self.assertEqual(exported['items'][0]['completion_def_present'], True)
        self.assertEqual(exported['publication'], 'local-review-draft')

    def test_transition_cannot_close_without_measured_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(self.m.StateError):
                self.m.verify_transition_complete(self.state, Path(directory), {})

    def test_transition_detects_consumers_outside_claimed_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ('scripts', 'gates', '.agents/skills'): (root/folder).mkdir(parents=True)
            (root/'ledger.yaml').write_text('items:\n  - id: local-1\n    status: open\n')
            (root/'claimed.py').write_text('pass\n')
            (root/'scripts/hidden.py').write_text('source="dev-package/work-items.yaml"\n')
            value = copy.deepcopy(self.state); value['issues'][0]['number'] = 1
            cfg = {'mode': 'retired', 'ledger': 'ledger.yaml', 'consumer_paths': ['claimed.py'], 'handoff_review': 'complete'}
            def record(name, value):
                path = root/name; path.write_text(json.dumps(value))
                return {'path': name, 'sha256': self.m.digest(path.read_bytes())}
            (root/'dev-package').mkdir()
            handoff_row = '| 1 | fixture | work |\n'
            (root/'dev-package/03-HANDOFF.md').write_text('## 4. 블로커 (사람이 풀어야 할 것)\n| # | 블로커 | 막는 것 |\n|---|---|---|\n'+handoff_row)
            external = []
            for number in (35, 38):
                external.append(record(f'pr-{number}.json', {'schema': 'colab-github-pr-record/1',
                    'source': {'repository': 'CognileapAI/colab-v2', 'number': number, 'endpoint': f'repos/CognileapAI/colab-v2/pulls/{number}', 'transport': 'gh-api', 'fetched_at': '2026-09-15T01:00:00+00:00'},
                    'record': {'number': number, 'state': 'closed', 'merged': True, 'merged_at': '2026-09-15T00:00:00+00:00',
                        'head': {'sha': 'a'*40}, 'merge_commit_sha': 'b'*40,
                        'base': {'ref': 'main', 'repo': {'full_name': 'CognileapAI/colab-v2'}}}}))
            cfg['closure_evidence'] = {
                'mapping': record('mapping.json', {'schema': 'colab-work-mapping/1', 'ledger_sha256': self.m.digest((root/'ledger.yaml').read_bytes()),
                    'mappings': [{'id': 'local-1', 'kind': 'issue', 'issue_number': 1, 'source_sha256': self.m.digest(json.dumps({'id':'local-1','status':'open'},sort_keys=True,ensure_ascii=False).encode())}]}),
                'handoff': record('handoff.json', {'schema': 'colab-handoff-classification/1', 'source_sha256': self.m.digest((root/'dev-package/03-HANDOFF.md').read_bytes()),
                    'classifications': [{'row_sha256': self.m.digest(handoff_row.encode()), 'kind':'historical-resolved'}]}), 'external_pr_records': external}
            with self.assertRaisesRegex(self.m.StateError, 'legacy consumer remains'): self.m.verify_transition_complete(value, root, cfg)

    def test_transition_issue_number_and_complete_label_are_not_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'ledger.yaml').write_text('items:\n  - id: local-1\n')
            value = copy.deepcopy(self.state); value['issues'][0]['number'] = 1
            cfg = {'mode': 'retired', 'ledger': 'ledger.yaml', 'consumer_paths': ['claimed.py'], 'handoff_review': 'complete'}
            with self.assertRaises(self.m.ReadinessError): self.m.verify_transition_complete(value, root, cfg)


if __name__ == '__main__': unittest.main()
