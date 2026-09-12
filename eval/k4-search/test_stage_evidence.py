import unittest
from stage_evidence import facts_for_file, resolve_targets, validate_base


class StageEvidenceTest(unittest.TestCase):
    def test_document_and_code_do_not_inherit_data_conditions(self):
        condition={'coverage':['2023-05-01','2023-05-31'],'cadence':'daily','region':'한반도'}
        self.assertEqual(facts_for_file('LD-VEG-LV0','info.docx',condition,None),{'roles':['documentation']})
        self.assertEqual(facts_for_file('LD-DRGH-LV1','reader.ipynb',condition,None),{'roles':['analysis_code']})
    def test_daily_file_does_not_inherit_a_whole_month(self):
        facts=facts_for_file('LD-VEG-LV2','Prediction_20230517.npy',
                             {'coverage':['2023-05-01','2023-05-31'],'cadence':'daily'},None)
        self.assertEqual(facts['period'],{'start':'2023-05-17','end':'2023-05-17'})

    def test_timeless_auxiliary_does_not_inherit_observation_period(self):
        facts=facts_for_file('LD-VEG-LV1-MODELIN','DEM.tif',{}, {'role':'auxiliary_input'})
        self.assertNotIn('period',facts)

    def test_duplicate_dataset_names_fail_before_writes(self):
        with self.assertRaises(ValueError):
            resolve_targets([{'dataset_name':'same','file_name':'f'}],
                            [{'datasetId':'a','name':'same'},{'datasetId':'b','name':'same'}],lambda _:[])

    def test_target_ids_come_from_stage_not_dev(self):
        resolved=resolve_targets([{'dataset_name':'same','file_name':'f','facts':{},'source':{}}],
            [{'datasetId':'stage-id','name':'same'}],
            lambda _: [{'fileId':'stage-file','fileName':'f','fileRevision':3,'evidence':None}])
        self.assertEqual(resolved[0]['dataset_id'],'stage-id')
        self.assertEqual(resolved[0]['payload']['expectedFileRevision'],3)

    def test_remote_or_credentialed_url_is_rejected(self):
        for url in ['https://dev.example.com','http://user:secret@localhost:8000','http://localhost:8000/api']:
            with self.assertRaises(ValueError): validate_base(url)
        self.assertEqual(validate_base('http://127.0.0.1:8080'),'http://127.0.0.1:8080')
