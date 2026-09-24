import json
import unittest
from pathlib import Path

from golden_baseline import ROOT, assess, expanded_cases, validate_suite


HERE = Path(__file__).resolve().parent


class CommittedSuiteTests(unittest.TestCase):
    """커밋된 골든 12문항이 **자기가 가리키는 스냅샷**과 맞는지를 dev 접속 없이 본다.

    종전에는 이 검사가 `main()` 안(dev 환경변수 뒤)에만 있어 낡은 ID 가 실측 직전의
    준비 실패로 처음 드러났다. 건수는 스냅샷의 `counts.datasets` 에서 읽는다(다시 박지 않는다).
    """

    def load(self):
        suite = json.loads((HERE / 'golden-cases.json').read_text())
        return suite, json.loads((ROOT / suite['snapshot']).read_text())

    def test_committed_suite_points_at_v2_snapshot_and_validates(self):
        suite, snapshot = self.load()
        self.assertEqual(suite['snapshot'], 'eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json')
        expected = validate_suite(suite, snapshot)
        self.assertEqual(len(expected), snapshot['counts']['datasets'])

    def test_snapshot_count_mismatch_is_preparation_failure(self):
        suite, snapshot = self.load()
        broken = dict(snapshot, datasets=snapshot['datasets'][:-1])
        with self.assertRaises(ValueError):
            validate_suite(suite, broken)


class RemoteSubjectCheckTests(unittest.TestCase):
    """주체 확인은 dev DB 의 계정·연구실 행으로 한다 — 토큰 표(`subjects.json`)가 아니다.

    2026-09-25 WU5: 재시드 뒤 dev 의 토큰 표가 `{}` 여서 `subject absent` 로 78 이 났다.
    토큰 표는 인증 수단이고 계정 존재의 증거가 아니다. 같은 읽기 전용 스코프 안에서
    `d1_account(id, lab_id)` 가 정확히 1행 보여야 진행한다.
    """

    def test_remote_does_not_read_token_table(self):
        from golden_baseline import REMOTE
        self.assertNotIn('COLAB_CORE_SUBJECTS_FILE', REMOTE)

    def test_remote_checks_account_row_in_lab_under_scope(self):
        from golden_baseline import REMOTE
        self.assertIn('FROM d1_account WHERE id=:a AND lab_id=:l', REMOTE)
        self.assertLess(REMOTE.index('read_only_scope(factory'), REMOTE.index('FROM d1_account'))


class AssessmentTests(unittest.TestCase):
    def test_dictionary_failure_cannot_silently_become_literal_comparison(self):
        with self.assertRaises(ValueError):
            expanded_cases([{'id':'Q'}], [{'id':'Q','degraded':True,'interpretation':{'terms':['a'],'topic':None}}])

    def test_expanded_topic_is_preserved(self):
        result = expanded_cases([{'id':'Q'}], [{'id':'Q','degraded':False,'interpretation':{'terms':['SPI'],'topic':'가뭄'}}])
        self.assertEqual(result[0]['topic'], '가뭄')
        self.assertEqual(result[0]['terms'], ['SPI'])

    def test_expansion_case_mismatch_is_preparation_failure(self):
        with self.assertRaises(ValueError):
            expanded_cases([{'id':'Q'}], [{'id':'OTHER','degraded':False,'interpretation':{'terms':[],'topic':None}}])

    def case(self, **changes):
        return dict(id='Q', scope=['A', 'B'], required=['A'], mode='retrieval', **changes)

    def test_truncation_cannot_be_reported_as_no_answer(self):
        with self.assertRaises(ValueError):
            assess(self.case(), [{'dataset_id': 'X'}], total=2)

    def test_scoped_negative_ignores_outside_candidates(self):
        c = dict(id='Q', scope=['A'], required=[], mode='empty')
        self.assertEqual(assess(c, [{'dataset_id': 'X'}], 1)['retrieval'], 'pass')

    def test_partial_multi_answer_is_a_failure(self):
        c = dict(id='Q', scope=['A', 'B'], required=['A', 'B'], mode='retrieval')
        self.assertEqual(assess(c, [{'dataset_id': 'A'}], 1)['retrieval'], 'fail')

    def test_quality_claim_requires_human_judgment_even_when_empty(self):
        c = dict(id='Q', scope=['A'], required=[], mode='manual')
        self.assertEqual(assess(c, [], 0)['retrieval'], 'not_applicable')

    def test_duplicate_results_are_not_complete_evidence(self):
        with self.assertRaises(ValueError):
            assess(self.case(), [{'dataset_id': 'A'}, {'dataset_id': 'A'}], 2)


if __name__ == '__main__':
    unittest.main()
