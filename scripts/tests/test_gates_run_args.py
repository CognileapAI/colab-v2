"""A4 — `gates/run.sh` 인자 검사: 버린·알 수 없는 토큰은 78 로 드러나고 host mutex·gate-start 앞에서 끝난다.

spec `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-20260925.md` §4.4 (V10–V12).
⚠ 안전망: 모든 실행에 `COLAB_GATE_INNER_JOBS=bogus` 를 준다 — 인자 검사가 없던 실행기에서도 `all` 은
  게이트를 하나도 돌리지 않고 exit 1 로 끝난다(RED 가 전수를 돌리거나 이 시험을 재귀로 부르지 않게).
  같은 이유로 단독 게이트 추가 인자 케이스는 `agent-bridge`(이 시험을 담은 게이트) 대신 가벼운 게이트를 쓴다.
"""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'gates/run.sh'
FAKE_TASK = '0' * 32


@unittest.skipIf(os.name == 'nt', 'gates/run.sh requires bash (WSL)')
class RunArgsTests(unittest.TestCase):
    def run_gate(self, *args, task_id=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        env = dict(os.environ, TMPDIR=tmp.name, COLAB_GATE_INNER_JOBS='bogus')
        for key in ('COLAB_TASK_ID', 'COLAB_GATE_REPORT_DIR', 'COLAB_GATE_SUMMARY_CHILD', 'COLAB_GATE_OUTDIR',
                    'COLAB_GATE_MUTEX_HELD', 'COLAB_GATE_TASK_BEFORE'):
            env.pop(key, None)
        if task_id:
            env['COLAB_TASK_ID'] = task_id
        result = subprocess.run(['bash', str(RUN), *args], env=env, text=True, capture_output=True, timeout=120)
        return result, Path(tmp.name)

    def assert_rejected(self, args, dropped, task_id=None):
        result, tmp = self.run_gate(*args, task_id=task_id)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 78, output)
        self.assertIn('::gate-readiness-failure::', result.stderr)
        for token in dropped:
            self.assertIn(token, result.stderr)
        self.assertIn('usage: gates/run.sh', result.stderr)
        self.assertNotIn('::gate-waiting::', output)
        self.assertFalse((tmp / 'colab-v2-gate-host-mutex').exists(), 'host mutex was touched')
        self.assertNotIn('task evidence preparation failed', output)
        return result

    def test_extra_or_malformed_arguments_are_78(self):
        for args, dropped in (
            (('harness-contract', 'extra'), ['extra']),
            (('exec-bit', 'a', 'b'), ['a', 'b']),
            (('all', '-j4'), ['-j4', '-j 4']),
            (('all', '-j'), ['-j']),
            (('all', '-j', '4', 'x'), ['x']),
            (('all', '-j', 'abc'), ['abc']),
            (('all', '-j', '0'), ['0']),
            (('all', 'x'), ['x']),
            (('task', 'x'), ['x']),
        ):
            with self.subTest(args=args):
                self.assert_rejected(args, dropped)

    def test_unknown_gate_and_missing_argument_are_78_before_mutex(self):
        for args, dropped in ((('no-such-gate',), ['no-such-gate']), ((), []), (('',), [])):
            with self.subTest(args=args):
                self.assert_rejected(args, dropped)

    def test_task_id_does_not_start_evidence_for_rejected_arguments(self):
        for args in (('task', 'x'), ('no-such-gate',), ('harness-contract', 'extra')):
            with self.subTest(args=args):
                self.assert_rejected(args, [], task_id=FAKE_TASK)

    def test_task_without_id_keeps_existing_message(self):
        result, _ = self.run_gate('task')
        self.assertEqual(result.returncode, 78, result.stderr)
        self.assertIn('COLAB_TASK_ID required', result.stderr)

    def test_every_case_label_is_a_known_gate(self):
        text = RUN.read_text(encoding='utf-8')

        def array(name):
            match = re.search(r'^' + name + r'=\((.*?)^\)', text, re.MULTILINE | re.DOTALL)
            self.assertIsNotNone(match, f'{name} array missing in gates/run.sh')
            body = match.group(1).replace(f'"${{ALL_GATES[@]}}"', '')
            return set(body.split())

        known = array('ALL_GATES') | array('KNOWN_GATES') | {'all', 'task'}
        start = text.index('case "$GATE" in')
        labels = set()
        for line in text[start:].splitlines():
            match = re.match(r'^  ([a-z0-9-]+(?:\|[a-z0-9-]+)*)\)', line)
            if match:
                labels.update(match.group(1).split('|'))
        self.assertGreater(len(labels), 50)
        self.assertEqual(sorted(labels - known), [])


if __name__ == '__main__':
    unittest.main()
