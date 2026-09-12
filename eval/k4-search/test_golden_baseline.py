import unittest

from golden_baseline import assess, expanded_cases


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
