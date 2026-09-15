"""Product promotion must not ignore a failed or missing CI result."""
import json
import os
from pathlib import Path
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]


class RequiredCITests(unittest.TestCase):
    def setUp(self):
        self.jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
        self.required = self.jobs['ci-required']

    def run_result(self, overrides=None, missing=None):
        results = {name: {'result': 'success'} for name in self.required['needs']}
        for name, result in (overrides or {}).items():
            results[name]['result'] = result
        if missing:
            del results[missing]
        return subprocess.run(['bash', '-e', '-c', self.required['steps'][0]['run']],
                              env=dict(os.environ, CI_RESULTS=json.dumps(results)),
                              capture_output=True, text=True)

    def test_covers_every_job_and_runs_after_failure(self):
        self.assertEqual(set(self.required['needs']), set(self.jobs) - {'ci-required'})
        self.assertEqual(self.required['if'], '${{ always() }}')
        self.assertEqual(self.run_result().returncode, 0)

    def test_failure_cancellation_and_missing_result_block_promotion(self):
        for result in ('failure', 'cancelled', 'unknown'):
            with self.subTest(result=result):
                self.assertNotEqual(self.run_result({'frontend-gates': result}).returncode, 0)
        self.assertNotEqual(self.run_result(missing='service-tests').returncode, 0)

    def test_only_path_filtered_jobs_may_be_skipped(self):
        self.assertEqual(self.run_result({'dormant-tests': 'skipped'}).returncode, 0)
        for name in ('changes', 'product-safety', 'repo-hygiene'):
            self.assertNotEqual(self.run_result({name: 'skipped'}).returncode, 0)


if __name__ == '__main__':
    unittest.main()
