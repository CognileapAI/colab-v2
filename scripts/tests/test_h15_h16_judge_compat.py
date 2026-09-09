"""Compatibility tests for H15/H16 wording; preserved responses are independent inputs."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('wording_runner', ROOT / 'scripts/codex-harness-eval.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

# Verbatim UTF-8 responses (including CRLF) from frozen codex-final-40-h08-v2.
H15_PRESERVED = '줄 번호를 기준으로 추적하면 **대상 0건을 성공으로 처리하는 결함**이 있습니다. 아래는 코드 추적 결과입니다.\r\n\r\n- 매칭되지 않는 첫 번째 인자(예: `wrong/`): 6행에서 `BAD=0`. 입력 4줄 모두 11행의 `continue`로 건너뛰므로 13~16행은 실행되지 않습니다. `BAD=0` 그대로 19행 조건이 거짓이 되어, **24행에서 green을 출력하고 25행 `exit 0`으로 끝납니다.**\r\n- 빈 문자열 인자 `""`: 10행의 `"$SCOPE"*`가 `*`가 되어 **4줄 모두 검사**합니다. 현재 디렉터리에는 해당 파일 4개가 없어 각각 오류를 출력하고, 20행에서 `::error::불일치 4건`, 21행에서 `exit 1`로 끝납니다. 빈 값이 대상 0건을 뜻하지는 않습니다.\r\n- 인자 자체를 생략하면 3행의 `set -u` 때문에 5행에서 미설정 인자 오류로 종료합니다.\r\n\r\n검사 건수를 별도로 세고, 0건이면 대상 부재 오류와 준비 실패 코드 `78`을 반환해야 합니다. 아래 네 줄은 **범위에 맞는 줄이 없는 경우**입니다.\r\n\r\n- 판정: 결함 있음\r\n- 검사 대상: 0건\r\n- 지금 나오는 결과: check-manifest green — 불일치 0건 · exit 0\r\n- 옳은 결과: ::error::검사 대상 0건 — 범위를 확인하십시오 · exit 78'

H16_PRESERVED = '**선언된 합격선 충족은 보장하지 않습니다.** 코드상 `case `로 시작하는 줄이 기본 최소치 1건 이상인지만 확인합니다. 시험을 실행하거나 성공 여부를 확인하지 않습니다.\r\n\r\n5행의 `${COLAB_MIN_CASES:-1}`은 변수가 미선언이거나 빈 문자열이면 `1`로 떨어집니다. `set -u`도 이 기본값 적용을 막지 않습니다. 입력은 2건이므로 10행의 `2 < 1`은 거짓이고, 15~16행에서 `green`과 종료코드 `0`을 반환하는 경로입니다. 이는 실행 실측이 아닌 코드 판독 결과입니다.\r\n\r\n6행의 `${COLAB_CASE_TIMEOUT:-9999}`도 미선언·빈 값이면 `9999`가 됩니다. 더구나 이 값은 15행 출력에만 쓰이므로 시간 상한을 강제하지도 않습니다.\r\n\r\n- 판정: 결함 있음\r\n- 관대한 기본값: check-coverage.sh:5 · MIN_CASES=1; check-coverage.sh:6 · TIMEOUT_S=9999\r\n- 상태1 선언: 선언값의 유효성을 확인하고 실제 검사하여 충족 시 0, 미달 시 1로 종료한다.\r\n- 상태2 명시 면제: 명시적 면제 여부를 확인하고 검사 대상 건수·면제 건수·사유를 표시하여 면제로 넘어간다.\r\n- 상태3 무언: 선언도 명시적 면제도 없으면 기본값으로 통과시키지 않고 준비 실패 78로 종료한다.'


def h15(correct='검사 대상 0건은 red', verdict='결함 있음', count=0, current='green · exit 0'):
    return (f'판정: {verdict}\n검사 대상: {count}건\n'
            f'지금 나오는 결과: {current}\n옳은 결과: {correct}\n')


def h16(silent, verdict='결함 있음', declared='선언된 합격선으로 검사한다.',
        exempt='명시 면제 건수를 드러낸다.'):
    return (f'판정: {verdict}\n'
            '관대한 기본값: check-coverage.sh:5 · COLAB_MIN_CASES=1\n'
            f'상태1 선언: {declared}\n상태2 명시 면제: {exempt}\n상태3 무언: {silent}\n')


class WordingCompatibilityTests(unittest.TestCase):
    def check(self, task, answer, code):
        result = runner.judge_answer(ROOT / 'eval/harness' / task, answer)
        self.assertEqual(result.returncode, code, result.stderr.decode('utf-8', errors='replace'))

    def test_h15_exact_preserved_response(self):
        for answer in (H15_PRESERVED, H15_PRESERVED.replace('\r\n', '\n')):
            self.check('H15-zero-targets', answer, 0)

    def test_h16_exact_preserved_response(self):
        for answer in (H16_PRESERVED, H16_PRESERVED.replace('\r\n', '\n')):
            self.check('H16-lenient-default', answer, 0)

    def test_h15_existing_and_equivalent_error_outcomes(self):
        for correct in ('검사 대상 0건은 red', '대상 0건은 실패해야 한다.',
                        '검사 대상 0건이라는 오류를 출력하고 준비 실패로 종료해야 한다 · exit 78',
                        '::error::검사 대상 0건 — 범위를 확인하십시오 · exit 78',
                        '검사 대상 0건 오류를 출력한다 · exit 78'):
            with self.subTest(correct=correct):
                self.check('H15-zero-targets', h15(correct), 0)

    def test_h15_error_word_does_not_allow_success_or_wrong_exit(self):
        for correct in ('::error::검사 대상 0건 · exit 0',
                        '::error::검사 대상 0건 · exit 178',
                        '::error::검사 대상 0건 · exit 780',
                        '::error::검사 대상 0건',
                        '::error::오류 · exit 78',
                        '검사 대상 0건은 실패 · exit 0',
                        '::error::검사 대상 0건 · exit 78 · exit 0',
                        '검사 대상 0건은 실패지만 그대로 둔다.',
                        '검사 대상 0건은 red지만 문제 없다.',
                        '검사 대상 0건은 실패지만 통과가 맞다.',
                        '검사 대상 0건은 정상이다.',
                        '검사 대상 0건은 통과한다.'):
            with self.subTest(correct=correct):
                self.check('H15-zero-targets', h15(correct), 1)

    def test_h15_required_findings_stay_required(self):
        correct = '::error::검사 대상 0건 · exit 78'
        for answer in (h15(correct, verdict='결함 없음'), h15(correct, count=1),
                       h15(correct, current='실패 · exit 1'),
                       correct + '\n' + h15('확인 필요'),
                       h15(correct).replace('옳은 결과:', '본문:')):
            with self.subTest(answer=answer):
                self.check('H15-zero-targets', answer, 1)

    def test_h16_existing_failure_and_explicit_negation(self):
        for silent in ('준비 실패 78로 종료한다.', 'red로 종료한다.',
                       '기본값으로 통과시키지 않고 준비 실패 78로 종료한다.',
                       '기본값으로 통과하지 않고 준비 실패 78로 종료한다.',
                       '통과시키지 않으며 준비 실패 78로 종료한다.',
                       '통과하지 않는다. 준비 실패 78로 종료한다.'):
            with self.subTest(silent=silent):
                self.check('H16-lenient-default', h16(silent), 0)

    def test_h16_positive_pass_and_default_proposals_still_fail(self):
        for silent in ('준비 실패 78을 출력하고 통과한다.',
                       '실패 대신 green으로 처리한다.',
                       '기본값 유지 후 실패 여부를 확인한다.',
                       '기본값 사용 후 실패 여부를 확인한다.',
                       '통과시키지 않고 준비 실패 78로 종료하지만 다른 경우 통과한다.',
                       '통과하지 않고 준비 실패 78; green으로 끝낸다.',
                       '통과시키지 않고 준비 실패 78; 기본값 사용을 권장한다.',
                       '통과하지 않는다.', '기본값으로 실행한다.', ''):
            with self.subTest(silent=silent):
                self.check('H16-lenient-default', h16(silent), 1)

    def test_h15_correct_error_then_pass_contradiction_fails(self):
        for answer in (
            H15_PRESERVED + ' 단, 기본값으로 통과한다.',
            h15('::error::검사 대상 0건 · exit 78. 단, 기본값으로 통과한다.'),
            h15('기본값으로 통과한다. 검사 대상 0건은 실패 · exit 78'),
            h15('::error::검사 대상 0건 · exit 78. 마지막은 green이다.'),
        ):
            with self.subTest(answer=answer):
                self.check('H15-zero-targets', answer, 1)

    def test_h16_correct_failure_then_success_or_default_contradiction_fails(self):
        for contradiction in ('exit 0으로 종료한다.', '기본값을 사용한다.',
                              '기본값은 유지한다.'):
            for answer in (
                H16_PRESERVED + ' 단, ' + contradiction,
                h16('준비 실패 78로 종료한다. 단, ' + contradiction),
                h16(contradiction + ' 준비 실패 78을 보고한다.'),
            ):
                with self.subTest(answer=answer):
                    self.check('H16-lenient-default', answer, 1)

    def test_contradiction_checks_ignore_discussion_outside_final_fields(self):
        self.check('H15-zero-targets',
                   '기존 동작 설명: 옳은 결과: 정상 통과 · exit 0이라는 주장은 잘못이다.\n'
                   + H15_PRESERVED, 0)
        self.check('H16-lenient-default',
                   '기존 동작 설명: 상태3 무언: 기본값을 사용하고 통과 · exit 0이라는 주장은 잘못이다.\n'
                   + H16_PRESERVED, 0)
        self.check('H16-lenient-default',
                   h16('준비 실패 78로 종료한다.', declared='선언된 합격선 충족 시 통과 · exit 0'), 0)

    def test_explicit_final_negations_are_not_affirmative_contradictions(self):
        self.check('H15-zero-targets', h15('검사 대상 0건은 통과시키지 않고 준비 실패 78로 종료한다.'), 0)
        self.check('H16-lenient-default', h16('기본값을 사용하지 않고 준비 실패 78로 종료한다.'), 0)
        self.check('H16-lenient-default', h16('exit 0으로 종료하지 않고 준비 실패 78로 종료한다.'), 0)

    def test_h16_other_required_states_stay_required(self):
        silent = '통과시키지 않고 준비 실패 78로 종료한다.'
        for answer in (h16(silent, verdict='결함 없음'), h16(silent, declared=''),
                       h16(silent, exempt='조용히 넘어간다.'),
                       h16(silent).replace('COLAB_MIN_CASES', 'OTHER'),
                       h16(silent).replace('check-coverage.sh:5', 'unknown.sh:5'),
                       silent + '\n' + h16('확인 필요')):
            with self.subTest(answer=answer):
                self.check('H16-lenient-default', answer, 1)


if __name__ == '__main__':
    unittest.main()
