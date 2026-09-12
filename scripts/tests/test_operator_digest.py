import unittest
from scripts.tests.operator_notifications_support import run_case

class DigestTests(unittest.TestCase):
    def test_late_commit_corrects_the_original_day(self):
        result=run_case("report_then_old_timestamp_commit")
        self.assertEqual(result["report_dates"],["2026-09-11","2026-09-11"])
        self.assertEqual(result["revisions"],[1,2])
        self.assertIn("정정 보고",result["messages"][-1]["text"])

    def test_zero_partial_and_exclusions_remain_distinct(self):
        result=run_case("digest_completeness")
        self.assertIn("활동 없음",result["complete_zero"])
        self.assertIn("집계 불완전",result["partial"])
        self.assertNotIn(result["test_actor"],result["complete"])

    def test_long_digest_is_split_without_mentions(self):
        result=run_case("long_digest")
        self.assertGreater(result["parts"],1)
        self.assertTrue(all(n<=3000 for n in result["lengths"]))
        self.assertEqual(result["raw_mentions"],0)
