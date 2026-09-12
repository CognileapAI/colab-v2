import unittest
from heldout_eval import files_match


class HeldoutVerdictTest(unittest.TestCase):
    def test_extra_dataset_cannot_pass_an_only_request(self):
        case = dict(required=['prediction'], files=['prediction.npy'])
        result = dict(ids=['p','raw'], file_evidence={'p':[{'file':'prediction.npy'}]})
        self.assertFalse(files_match(case, result, {'p':'prediction', 'raw':'raw'}))
