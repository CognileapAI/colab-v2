import json,tempfile,unittest
from pathlib import Path
from infra.notifications.install_jobs import render

class ScheduleTests(unittest.TestCase):
    def test_schedule_has_probe_export_retry_and_daily_kst(self):
        value=render({"environment":"dev","usage":"live","probes":[{"target":"service-health","command":["/bin/true"],"timeout":2}]})
        self.assertEqual(value["daily"]["timezone"],"Asia/Seoul")
        self.assertEqual(value["daily"]["expression"],"cron(0 8 * * ? *)")
        self.assertEqual(value["probe"]["minutes"],5)
        self.assertEqual(value["retry"]["minutes"],1)
