import unittest
from structured_probe import search


def dataset(id, topic, summary, files=(), parents=()):
    return dict(id=id, topic=topic, name=id, summary=summary,
                files=[{'file_name': f} for f in files], parents=list(parents))


class StructuredProbeTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            dataset('raw', '식생·NDVI', '원자료', ['raw.nc']),
            dataset('mean', '식생·NDVI', '일→월 평균', ['average_202305.tif'],
                    [{'parent_dataset_id': 'raw', 'parent_role': '주입력'}]),
            dataset('pred', '식생·NDVI', 'U-Net 예측', ['Prediction_20230501.npy']),
            dataset('dry', '가뭄', '주간 SPI'),
        ]

    def test_particle_model_and_topic_are_conjoined(self):
        self.assertEqual(search('U-Net으로 예측한 가뭄', self.rows)['ids'], [])
        self.assertEqual(search('U-Net으로 예측한 식생', self.rows)['ids'], ['pred'])

    def test_filename_source_uses_direct_parent(self):
        self.assertEqual(search('average_202305.tif의 원자료', self.rows)['ids'], ['raw'])

    def test_month_mismatch(self):
        self.assertEqual(search('2023년 4월 월평균 식생', self.rows)['ids'], [])

    def test_quality_is_unknown_not_verified(self):
        result = search('결측률 0% 식생', self.rows)
        self.assertIn('quality', result['unverified'])

    def test_unknown_query_does_not_return_everything(self):
        self.assertEqual(search('아무 관련 없는 요청', self.rows)['ids'], [])

    def test_file_lookup_does_not_cross_available_scope(self):
        self.assertEqual(search('average_202305.tif 원자료', self.rows[1:])['ids'], [])

    def test_requested_day_is_not_replaced_by_same_month(self):
        self.assertEqual(search('2023년 5월 2일 U-Net 식생 예측', self.rows)['ids'], [])

    def test_korean_month_is_not_ignored(self):
        self.assertEqual(search('2023년 사월 월평균 식생', self.rows)['ids'], [])

    def test_model_parent_is_not_automatically_validation(self):
        rows = self.rows + [dataset('output', '식생·NDVI',
            'U-Net 주입력과 별도 검증자료로 학습', ['Prediction_20230502.npy'],
            [{'parent_dataset_id': 'mean', 'parent_role': '주입력'}])]
        self.assertNotIn('mean', search('식생 검증자료', rows)['ids'])

    def test_multiple_topics_are_explicitly_unsupported(self):
        self.assertIn('multiple_topics', search('식생과 가뭄 자료', self.rows)['unverified'])

    def test_file_role_requires_present_file(self):
        rows = [dict(self.rows[1], manifest_key='MONTHLY')]
        evidence = [dict(dataset_key='MONTHLY', file='absent.npy', role='validation',
                         source_document='processing.docx', scope='validation')]
        self.assertEqual(search('식생 검증자료', rows, evidence=evidence)['ids'], [])

    def test_verified_file_role_restores_validation(self):
        rows = [dict(self.rows[1], manifest_key='MONTHLY')]
        evidence = [dict(dataset_key='MONTHLY', file='average_202305.tif', role='validation',
                         source_document='processing.docx', scope='validation')]
        result = search('식생 검증자료', rows, evidence=evidence)
        self.assertEqual(result['ids'], ['mean'])
        self.assertEqual(result['file_evidence']['mean'][0]['role'], 'validation')

    def test_spi_exclusion_selects_file_not_entire_bundle(self):
        rows = [dataset('indices', '가뭄', 'SPI SPEI', ['SPI.gpkg', 'SPEI.gpkg'])]
        rows[0]['manifest_key'] = 'INDICES'
        evidence = [dict(dataset_key='INDICES', file=v+'.gpkg', role='index', variable=v,
                         source_document='info.docx', scope='index') for v in ['SPI','SPEI']]
        result = search('SPEI 말고 SPI 자료', rows, evidence=evidence)
        self.assertEqual([e['file'] for e in result['file_evidence']['indices']], ['SPI.gpkg'])

    def test_requested_prediction_day_selects_one_file(self):
        result = search('2023년 5월 1일 U-Net 식생 예측 파일', self.rows)
        self.assertEqual([e['file'] for e in result.get('file_evidence', {}).get('pred', [])],
                         ['Prediction_20230501.npy'])

    def test_unknown_exclusion_remains_unverified_despite_file_evidence(self):
        result = search('첫 번째 말고 U-Net 식생 예측 파일', self.rows)
        self.assertTrue(result['file_evidence'])
        self.assertIn('file_exclusion', result['unverified'])

    def test_excluded_auxiliaries_are_not_positive_requirements(self):
        rows = [dict(self.rows[1], manifest_key='MONTHLY', summary='검증자료와 보조입력')]
        rows[0]['files'] = rows[0]['files'] + [{'file_name': 'terrain.tif'}]
        roles = [dict(dataset_key='MONTHLY', file='average_202305.tif', role='validation',
                      source_document='info.docx', scope='validation'),
                 dict(dataset_key='MONTHLY', file='terrain.tif', role='auxiliary_input',
                      source_document='info.docx', scope='terrain')]
        result = search('식생 검증용 자료만. 지형·토지피복은 빼줘.', rows, evidence=roles)
        self.assertEqual(result['ids'], ['mean'])
        self.assertEqual([e['file'] for e in result['file_evidence']['mean']], ['average_202305.tif'])
