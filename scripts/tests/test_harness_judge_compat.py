import pathlib
import importlib.util
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('codex_judge', ROOT/'scripts/codex-harness-eval.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class JudgeCompatibilityTests(unittest.TestCase):
    def test_runner_preserves_line_end_anchors_across_wsl(self):
        task = ROOT/'eval/harness/H07-graph-font-size'
        self.assertEqual(runner.judge_answer(task, '판정: 있음\n건수: 13\n최소: 10px\n').returncode, 0)
        self.assertNotEqual(runner.judge_answer(task, '판정: 있음\n건수: 12\n최소: 10px\n').returncode, 0)

    def judge(self, answer):
        task = ROOT / 'eval/harness/H03-md-table-blank-line'
        command = (['wsl.exe', '--cd', str(task), '-e', 'bash', 'expect.sh']
                   if sys.platform == 'win32' else ['bash', str(task / 'expect.sh')])
        return subprocess.run(command, input=answer.encode('utf-8'), capture_output=True).returncode

    def answer(self, command, line=13, count=2):
        return f'판정: 있음\n빈 줄: {line}\n표 밖으로 떨어진 행: {count}건\n확인 명령: {command}\n'

    def test_numbered_posix_and_powershell_inspection(self):
        for command in ("cat -n input.md", "rg -n -A 6 '^\\| 출처' input.md",
                        "$n=0; Get-Content input.md | ForEach-Object { $n++; '{0}: {1}' -f $n, $_ }"):
            with self.subTest(command=command):
                self.assertEqual(self.judge(self.answer(command)), 0)

    def test_no_numbering_and_wrong_findings_still_fail(self):
        for answer in (self.answer('Get-Content input.md'), self.answer('cat -n input.md', line=12),
                       self.answer('cat -n input.md', count=1)):
            with self.subTest(answer=answer):
                self.assertNotEqual(self.judge(answer), 0)


class MissingLevelJudgeTests(unittest.TestCase):
    def judge(self, answer):
        return runner.judge_answer(ROOT / 'eval/harness/H12-lvl3-missing', answer)

    def answer(self, symptom, selector='.lvl-3', verdict='있음'):
        return f'판정: {verdict}\n빠진 규칙: {selector}\n증상: {symptom}\n'

    def test_transparent_background_and_inherited_text_are_missing_level_colors(self):
        # Verbatim symptom from the independently checked H12 response.
        answer = self.answer(
            'Lv3 칩만 단계별 배경·글자색이 적용되지 않아 '
            '투명 배경과 상속된 글자색으로 보인다.')
        for text in (answer, answer.replace('\n', '\r\n')):
            with self.subTest(text=text):
                result = self.judge(text)
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))

    def test_existing_missing_color_vocabulary_still_passes(self):
        for symptom in ('Lv3 칩이 무색이다.', 'Lv3 칩은 색이 없다.',
                        'Lv3 칩은 색이 안 나온다.', 'Lv3 칩은 배경색이 없다.',
                        'Lv3 칩이 비어 보인다.', 'Lv3 칩은 기본 색으로 보인다.',
                        'Lv3 칩은 스타일이 없다.', 'Lv3 칩은 스타일이 안 나온다.'):
            with self.subTest(symptom=symptom):
                result = self.judge(self.answer(symptom))
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))

    def test_wrong_or_existing_missing_selectors_still_fail(self):
        for selector in ('.lvl-0', '.lvl-1', '.lvl-2', '.lvl-4', '',
                         '.lvl-3, .lvl-0', '.lvl-3, .lvl-1', '.lvl-3, .lvl-2'):
            for symptom in ('Lv3 칩은 무색이다.',
                            'Lv3 칩은 투명 배경과 상속된 글자색으로 보인다.'):
                with self.subTest(selector=selector, symptom=symptom):
                    self.assertEqual(self.judge(self.answer(symptom, selector)).returncode, 1)

    def test_normal_colors_and_absent_symptoms_still_fail(self):
        for symptom in ('네 단계 모두 배경·글자색이 정상적으로 적용된다.',
                        'Lv3 칩은 투명 배경과 상속된 글자색이 아니라 정상 색상이다.',
                        'Lv3 칩은 투명 배경으로 보인다.',
                        'Lv3 칩은 상속된 글자색으로 보인다.',
                        'Lv3 칩이 보인다.', ''):
            with self.subTest(symptom=symptom):
                self.assertEqual(self.judge(self.answer(symptom)).returncode, 1)
        self.assertEqual(self.judge('판정: 있음\n빠진 규칙: .lvl-3\n').returncode, 1)
        self.assertEqual(self.judge(
            '투명 배경과 상속된 글자색으로 보인다.\n'
            '판정: 있음\n빠진 규칙: .lvl-3\n증상: 확인 필요\n').returncode, 1)

    def test_missing_or_negative_verdict_still_fails_with_valid_symptom(self):
        symptom = 'Lv3 칩은 투명 배경과 상속된 글자색으로 보인다.'
        for verdict in ('없음', ''):
            with self.subTest(verdict=verdict):
                self.assertEqual(self.judge(self.answer(symptom, verdict=verdict)).returncode, 1)
        self.assertEqual(self.judge(f'빠진 규칙: .lvl-3\n증상: {symptom}\n').returncode, 1)


if __name__ == '__main__':
    unittest.main()
