import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('alayer_runner', Path(__file__).with_name('run.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class TargetScopeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manifest = Path(self.temp.name) / 'manifest.json'
        self.manifest.write_text(json.dumps({'datasets':[{'name':'Known', 'key':'D-01'}]}))

    def load(self, rows, **kwargs):
        with patch.object(runner, 'MANIFEST', self.manifest), patch.object(runner, 'psql', return_value=rows):
            return runner.load_targets('fixture', 'fixture', 'fixture', **kwargs)

    def test_default_still_rejects_additional_corpus(self):
        with self.assertRaises(runner.Unmeasurable):
            self.load([('a','Known'),('b','New')])

    def test_explicit_current_corpus_keeps_unknown_hits_visible(self):
        ids = self.load([('a','Known'),('b','New')], allow_extra=True)
        self.assertEqual(ids, {'a':'D-01', 'b':'EXTRA:b'})

    def test_current_corpus_does_not_excuse_missing_baseline_targets(self):
        with self.assertRaises(runner.Unmeasurable):
            self.load([('b','New')], allow_extra=True)
