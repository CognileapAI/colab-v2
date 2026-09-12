import unittest
from condition_assessment import assess_conditions


class ConditionAssessmentTest(unittest.TestCase):
    def test_native_resolution_is_contradiction_not_quality_unknown(self):
        result = assess_conditions('100m 직접 관측 결측률 0%', {'direct_observation': False})
        self.assertEqual(result['direct_observation']['status'], 'contradicted')
        self.assertEqual(result['quality']['status'], 'unknown')

    def test_period_does_not_extend_to_document_end(self):
        result = assess_conditions('2025년 12월 31일', {'coverage': ['2000-01-01', '2025-12-20']})
        self.assertEqual(result['period']['status'], 'contradicted')

    def test_unknown_region_stays_unknown(self):
        self.assertEqual(assess_conditions('제주 자료', {})['region']['status'], 'unknown')

    def test_explicit_matching_region_is_supported(self):
        result = assess_conditions('경기 남부와 충청권', {'region': '경기남부충청'})
        self.assertEqual(result['region']['status'], 'supported')

    def test_day_inside_sparse_extent_is_not_proven(self):
        result = assess_conditions('2023년 5월 2일', {'coverage': None})
        self.assertEqual(result['period']['status'], 'unknown')

    def test_no_interpolation_request_conflicts_with_applied_interpolation(self):
        result = assess_conditions('결측 보간을 하지 않은 자료', {'interpolated': True})
        self.assertEqual(result.get('interpolation', {}).get('status'), 'contradicted')

    def test_interpolation_evidence_is_not_resolution_evidence(self):
        result = assess_conditions('보간을 하지 않은 자료', dict(
            interpolated=True, note='uniform division', interpolation_evidence='linear interpolation'))
        self.assertEqual(result['interpolation']['evidence'], 'linear interpolation')
