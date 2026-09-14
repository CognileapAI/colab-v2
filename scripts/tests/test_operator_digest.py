import unittest
from infra.notifications.digest import DETAIL_ACTIONS, LABELS
from scripts.tests.operator_notifications_support import run_case

class DigestActionVocabularyTests(unittest.TestCase):
    """일일 보고는 `LABELS[action]` 을 **직접 첨자**로 읽는다(`infra/notifications/digest.py:195`·`:200`).

    이름이 빠져 있으면 그 줄만 비는 것이 아니라 `KeyError` 로 **그날 보고 전체가 죽는다.**
    그래서 감사에 쓰는 행위 문자열이 늘 때마다 여기 이름이 함께 서야 한다.
    """

    def test_tombstoning_a_dataset_has_a_report_name(self):
        # `DL-1` 묘비 전환이 `d3_operator_audit` 에 적는 값
        # (`services/core-api/src/colab_core/app/routes/deletion.py` `AUDIT_ACTION_TOMBSTONED`).
        # 물리 삭제(`ops/purge_datasets.py`)의 `dataset.deleted` 와 **다른 값**이다 —
        # 같은 대상에 둘이 쌓일 수 있고, 둘은 되돌릴 수 있는 정도가 다르다.
        self.assertIn('dataset.tombstoned', LABELS)
        self.assertIn('dataset.tombstoned', DETAIL_ACTIONS)

    def test_every_detailed_action_has_a_name(self):
        self.assertEqual(DETAIL_ACTIONS - set(LABELS), set())

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
