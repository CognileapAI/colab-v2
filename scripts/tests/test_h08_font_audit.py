"""H08 contract tests: literal, independently checked fixture oracle, no judge helpers."""
import importlib.util
import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / 'eval/harness/H08-caption-seven'
spec = importlib.util.spec_from_file_location('h08_runner', ROOT / 'scripts/codex-harness-eval.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
# Checked directly against the committed CSS declarations (including decimal px).
ORACLE = {
    'detail.css': (47, 50, 65, 89, 97, 101, 136),
    'upload.css': (82, 92, 106, 107, 123, 124, 128, 167, 168, 175, 176, 179, 182, 187),
    'lineageGraph.css': (10, 14, 31, 44, 45, 58, 72, 76, 81, 82, 83, 85, 95),
}
COORDS = [f'{name}:{line}' for name, lines in ORACLE.items() for line in lines]


def answer(coords=COORDS, count=None, untouched='.vizerr, .warn 13px'):
    return (f'지목: {len(coords) if count is None else count}곳\n'
            f'목록: {" · ".join(coords)}\n'
            f'무접촉(이미 13px): {untouched}\n')


class H08FontAuditTests(unittest.TestCase):
    def judge(self, text, task=TASK):
        return runner.judge_answer(task, text)

    def check(self, text, expected, task=TASK):
        result = self.judge(text, task)
        self.assertEqual(result.returncode, expected, result.stderr.decode('utf-8', errors='replace'))

    def test_complete_literal_inventory_passes(self):
        self.check(answer(), 0)

    def test_order_bullets_and_crlf(self):
        self.check('설명입니다.\n' + answer(list(reversed(COORDS))).replace('\n', '\r\n'), 0)
        self.check('\n'.join('- ' + line for line in answer().splitlines()), 0)

    def test_every_single_omission_fails_even_with_correct_body(self):
        for coord in COORDS:
            with self.subTest(coord=coord):
                self.check('본문 근거: ' + coord + '\n' + answer([c for c in COORDS if c != coord]), 1)

    def test_extra_duplicate_wrongcount_and_old_subset(self):
        old = ['detail.css:101', 'upload.css:106', 'upload.css:168',
               'lineageGraph.css:95', 'lineageGraph.css:81', 'lineageGraph.css:76', 'upload.css:92']
        for text in (answer(COORDS + ['upload.css:144']), answer(COORDS + [COORDS[0]]),
                     answer(count=7), answer(count=33), answer(count=35), answer(old),
                     answer(COORDS[:-1] + [COORDS[0]]), answer([]),
                     answer().replace('detail.css:47', 'detail.css:47junk')):
            with self.subTest(text=text):
                self.check(text, 1)

    def test_wrong_untouched_selector_or_value(self):
        for untouched in ('.vizerr 13px', '.warn 13px', '.other 13px', '.vizerr, .warn 12px',
                          '.vizerr, .warn 113px', '.vizerr, .warn 13px 아니다',
                          '.vizerr, .warn 13pxjunk', '.vizerr, .warn, .other 13px'):
            with self.subTest(untouched=untouched):
                self.check(answer(untouched=untouched), 1)
        self.check(answer(untouched='.warn, .vizerr 13.0px'), 0)

    def test_duplicate_fields_conflicting_or_identical_fail(self):
        for field in answer().splitlines() + ['지목: 7곳', '목록: detail.css:101',
                                            '무접촉(이미 13px): .other 12px']:
            with self.subTest(field=field):
                self.check(field + '\n' + answer(), 1)
                self.check(answer() + field + '\n', 1)

    def test_final_fields_required_not_body_matches(self):
        for index in range(3):
            lines = answer().splitlines()
            lines.pop(index)
            self.check('본문: ' + ' '.join(COORDS) + '\n' + '\n'.join(lines), 1)
        self.check(answer() + '뒤에 덧붙인 본문', 1)

    def sandbox(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        task = pathlib.Path(tmp.name)
        (task / 'fixture').mkdir()
        for name in ('expect.sh', 'judge.py'):
            if (TASK / name).exists():
                shutil.copyfile(TASK / name, task / name)
        for name in ORACLE:
            (task / 'fixture' / name).write_text('.base { font-size: 13px; }\n', encoding='utf-8')
        (task / 'fixture/upload.css').write_text('.vizerr, .warn { font-size: 13px; }\n', encoding='utf-8')
        return task

    def test_comments_functions_malformed_values_and_property_start_lines(self):
        task = self.sandbox()
        css = ('/* font-size: 1px;\n font-size: 2px; */\n'
               '.shared, .also {\n font-size\n : 12.5px; }\n'
               '.calc { font-size: calc(10px + 2px); }\n'
               '.var { font-size: var(--size, 11px); }\n'
               '.rem { font-size: .5rem; }\n'
               '.bad { font-size: 12pxjunk; }\n'
               '.bad { font-size: 12px 14px; }\n'
               '.quoted { content: "font-size: 1px;"; }\n'
               '.okay { font-size: 13px; }\n'
               '.small { font-size: .5px; }\n'
               '.big { font-size: 13.1px; }\n'
               '.bad { font-size: 12/**/px; }\n'
               '.bad { font-size: 12px "text"; }\n'
               '.okay { font-size: /* comment */ +12.75px; }\n'
               '.bad { --font-size: 1px; x-font-size: 2px; }\n'
               '.media {} @media (min-width: 1px) { .tiny { font-size: 1e1px; } }\n')
        (task / 'fixture/detail.css').write_text(css, encoding='utf-8')
        expected = ['detail.css:4', 'detail.css:13', 'detail.css:17', 'detail.css:19']
        self.check(answer(expected), 0, task)
        for line in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 18):
            with self.subTest(line=line):
                self.check(answer(expected + [f'detail.css:{line}']), 1, task)

    def test_dynamic_inventory_and_zero_findings(self):
        task = self.sandbox()
        self.check(answer([]), 0, task)
        (task / 'fixture/detail.css').write_text('\n.a {font-size:12px}\n', encoding='utf-8')
        self.check(answer(['detail.css:2']), 0, task)
        self.check(answer([]), 1, task)

    def test_preparation_failures_are_78(self):
        for problem in ('missing', 'empty', 'same-line', 'comment', 'brace', 'missing-anchor', 'anchor-value'):
            with self.subTest(problem=problem):
                task = self.sandbox()
                path = task / 'fixture/detail.css'
                if problem == 'missing':
                    path.unlink()
                elif problem == 'empty':
                    path.write_text('')
                elif problem == 'same-line':
                    path.write_text('.a {font-size:12px; font-size:11px;}')
                elif problem == 'comment':
                    path.write_text('/* unclosed')
                elif problem == 'brace':
                    path.write_text('.a {font-size:12px;')
                elif problem == 'missing-anchor':
                    (task / 'fixture/upload.css').write_text('.other {font-size:13px;}')
                else:
                    (task / 'fixture/upload.css').write_text('.vizerr, .warn {font-size:12px;}')
                self.check(answer([]), 78, task)


if __name__ == '__main__':
    unittest.main()
