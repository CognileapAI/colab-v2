import importlib.util
import contextlib
import io
import json
from pathlib import Path
import unittest
import tempfile
import subprocess
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('codex_eval', Path(__file__).parents[1]/'codex-harness-eval.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ResponseTests(unittest.TestCase):
    def raw(self, *rows):
        return '\n'.join(json.dumps(r) for r in rows)

    def message(self, text):
        return {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': text}}

    def test_uses_final_message_and_real_completion_usage(self):
        raw = self.raw(self.message('progress'), self.message('result'),
                       {'type': 'turn.completed', 'usage': {'input_tokens': 12}})
        self.assertEqual(runner.response(raw), ('result', {'input_tokens': 12}))

    def test_json_string_unicode_separators_do_not_split_records(self):
        for separator in ('\u0085', '\u2028', '\u2029'):
            text = 'before' + separator + 'after'
            raw = '\n'.join(json.dumps(r, ensure_ascii=False) for r in [
                self.message(text), {'type': 'turn.completed', 'usage': {'input_tokens': 3}}])
            with self.subTest(separator=repr(separator)):
                self.assertEqual(runner.response(raw), (text, {'input_tokens': 3}))

    def test_error_matching_expected_words_cannot_pass(self):
        for event in ('error', 'turn.failed'):
            raw = self.raw(self.message('green expected words'), {'type': event}, {'type': 'turn.completed'})
            with self.assertRaises(ValueError):
                runner.response(raw)


class EvidenceTests(ResponseTests):
    def test_runtime_events_preserve_unicode_string_separators(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'rollout-id.jsonl'
            path.write_text('{"type":"session_meta","payload":{"id":"id"}}\n'
                            '{"type":"turn_context","payload":{"model":"gpt-6-astra"}}\n', encoding='utf-8')
            for separator in ('\u0085', '\u2028', '\u2029'):
                raw = '\n'.join(json.dumps(r, ensure_ascii=False) for r in [
                    {'type':'thread.started','thread_id':'id'}, self.message('a' + separator + 'b')])
                with self.subTest(separator=repr(separator)):
                    self.assertEqual(runner.runtime_model(raw, Path(tmp))['models'], ['gpt-6-astra'])

    def test_persisted_context_preserves_unicode_string_separators(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'rollout-id.jsonl'
            for separator in ('\u0085', '\u2028', '\u2029'):
                path.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in [
                    {'type':'session_meta','payload':{'id':'id'}},
                    {'type':'turn_context','payload':{'model':'gpt-6-astra','cwd':'a' + separator + 'b'}}]), encoding='utf-8')
                with self.subTest(separator=repr(separator)):
                    evidence = runner.runtime_model('{"type":"thread.started","thread_id":"id"}', Path(tmp))
                    self.assertEqual(evidence['models'], ['gpt-6-astra'])
                    self.assertEqual(evidence['contexts'][0]['payload']['cwd'], 'a' + separator + 'b')

    def test_missing_executable_records_readiness_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'eval/harness/H01-example').mkdir(parents=True)
            output = root/'output'
            with patch.object(runner, 'ROOT', root), patch.object(runner.sys, 'argv', ['eval', '--codex', str(root/'absent-executable'), '--timeout', '1', '--only', 'H01', '--output', str(output)]):
                self.assertEqual(runner.main(), 78)
            self.assertEqual(json.loads((output/'summary.json').read_text(encoding='utf-8'))['status'], 'readiness-failure')

    def test_timeout_preserves_partial_logs_and_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp)/'H01-example'
            (task/'fixture').mkdir(parents=True)
            (task/'task.md').write_text('inspect', encoding='utf-8')
            (task/'expect.sh').write_text('exit 0', encoding='utf-8')
            with patch.object(runner.subprocess, 'run', side_effect=subprocess.TimeoutExpired('codex', 1, output=b'partial event', stderr=b'partial error')):
                self.assertTrue(hasattr(runner, 'run_task'), 'runner must preserve each attempt independently')
                row = runner.run_task(task, 1, 'codex', 1, Path(tmp))
            self.assertEqual(row['status'], 'readiness-failure')
            self.assertEqual((Path(tmp)/'H01-example.1.jsonl').read_bytes(), b'partial event')
            self.assertEqual((Path(tmp)/'H01-example.1.stderr').read_bytes(), b'partial error')
            self.assertEqual(json.loads((Path(tmp)/'H01-example.1.result.json').read_text())['status'], 'readiness-failure')

    def test_model_self_claim_is_not_runtime_evidence(self):
        self.assertTrue(hasattr(runner, 'runtime_model'), 'runtime model evidence is mandatory')
        with self.assertRaises(ValueError):
            runner.runtime_model('{"type":"item.completed","item":{"type":"agent_message","text":"model gpt-6-astra"}}', Path('.'))

    def test_session_id_must_match_and_turn_context_supplies_model(self):
        self.assertTrue(hasattr(runner, 'runtime_model'), 'runtime model evidence is mandatory')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'rollout-id.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in [
                {'type':'session_meta','payload':{'id':'id'}},
                {'type':'turn_context','payload':{'model':'gpt-6-astra'}}]), encoding='utf-8')
            evidence = runner.runtime_model('{"type":"thread.started","thread_id":"id"}', Path(tmp))
            self.assertEqual(evidence['models'], ['gpt-6-astra'])
            with self.assertRaises(ValueError):
                runner.runtime_model('{"type":"thread.started","thread_id":"other"}', Path(tmp))

    def test_snapshot_detects_dirty_fixture_and_judge_changes(self):
        self.assertTrue(hasattr(runner, 'snapshot'), 'snapshot hashes are mandatory')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git','init',str(root)], capture_output=True, check=True)
            fixture = root/'fixture.txt'
            fixture.write_text('first')
            before = runner.snapshot(root)
            fixture.write_text('second')
            self.assertNotEqual(before['sha256'], runner.snapshot(root)['sha256'])
            output = root/'new-results'
            output.mkdir()
            fixed = runner.snapshot(root, output)
            (output/'run.json').write_text('new evidence')
            self.assertEqual(fixed['sha256'], runner.snapshot(root, output)['sha256'])
            fixture.write_text('third')
            self.assertNotEqual(fixed['sha256'], runner.snapshot(root, output)['sha256'])

    def test_judge_readiness_exit_is_not_judgment_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp)/'H01-example'
            (task/'fixture').mkdir(parents=True)
            (task/'task.md').write_text('inspect')
            (task/'expect.sh').write_text('exit 78')
            raw = self.raw(self.message('answer'), {'type':'turn.completed'}).encode()
            for code, want in [(0, 'green'), (1, 'judgment-failure'), (78, 'readiness-failure')]:
                with patch.object(runner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, raw, b'')), patch.object(runner, 'runtime_model', return_value={'models':['test-model']}), patch.object(runner, 'judge_answer', return_value=subprocess.CompletedProcess([], code, b'', b'')):
                    self.assertEqual(runner.run_task(task, 1, 'codex', 1, Path(tmp))['status'], want)

    def test_missing_completion_empty_or_invalid_output_is_readiness_failure(self):
        for raw in ('', '{}', '[]', 'null', '{"type":"item.completed","item":null}', 'not JSON', self.raw(self.message('result')),
                    self.raw(self.message(''), {'type': 'turn.completed'})):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                runner.response(raw)


class OverallExitTests(unittest.TestCase):
    def run_statuses(self, statuses, change_snapshot=False):
        # Run the real main/report/snapshot path. Only the model-calling boundary is stubbed.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init', str(root)], capture_output=True, check=True)
            selected = []
            for index in range(len(statuses) // 2):
                key = f'H{index + 1:02d}'
                (root / 'eval/harness' / f'{key}-stub').mkdir(parents=True)
                selected.extend(['--only', key])
            sentinel = root / 'fixture.txt'
            sentinel.write_text('before', encoding='utf-8')
            output = root / 'output'
            pending = iter(statuses)

            def model_result(task, repeat, codex, timeout, destination):
                if change_snapshot:
                    sentinel.write_text('after', encoding='utf-8')
                return {'task': task.name, 'repeat': repeat, 'status': next(pending)}

            argv = ['eval', '--codex', runner.sys.executable, '--timeout', '1',
                    '--output', str(output), *selected]
            with patch.object(runner, 'ROOT', root), patch.object(runner.sys, 'argv', argv), \
                    patch.object(runner, 'run_task', side_effect=model_result), \
                    contextlib.redirect_stdout(io.StringIO()):
                code = runner.main()
            report = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
            self.assertEqual([row['status'] for row in report['runs']], list(statuses))
            self.assertEqual(report['snapshot_matches'], not change_snapshot)
            return code

    def test_mixed_judgment_and_readiness_prioritizes_judgment(self):
        for statuses in (
            ('judgment-failure', 'readiness-failure'),
            ('readiness-failure', 'judgment-failure'),
            ('judgment-failure', 'judgment-failure', 'readiness-failure', 'readiness-failure'),
            ('readiness-failure', 'readiness-failure', 'judgment-failure', 'judgment-failure'),
        ):
            with self.subTest(statuses=statuses):
                self.assertEqual(self.run_statuses(statuses), 1)

    def test_pure_readiness_and_green_keep_existing_exit_codes(self):
        for statuses, want in (
            (('green', 'green'), 0),
            (('green', 'readiness-failure'), 78),
            (('readiness-failure', 'readiness-failure'), 78),
            (('green', 'judgment-failure'), 1),
        ):
            with self.subTest(statuses=statuses):
                self.assertEqual(self.run_statuses(statuses), want)

    def test_snapshot_mismatch_remains_readiness_even_with_judgment(self):
        for statuses in (('green', 'green'), ('judgment-failure', 'readiness-failure'),
                         ('judgment-failure', 'judgment-failure')):
            with self.subTest(statuses=statuses):
                self.assertEqual(self.run_statuses(statuses, change_snapshot=True), 78)


if __name__ == '__main__':
    unittest.main()
