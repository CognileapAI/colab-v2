import unittest

from scripts.tests.operator_notifications_support import run_case


class DeliveryTests(unittest.TestCase):
    def test_restart_keeps_important_uncertain_and_channel(self):
        result = run_case("important_timeout_then_restart")
        self.assertEqual(result["activity_posts"], [])
        self.assertEqual(result["development_posts"][1]["event_id"], result["development_posts"][0]["event_id"])
        self.assertIn("중복 가능", result["development_posts"][1]["text"])
        self.assertEqual(result["deployment_runs"], 0)

    def test_success_is_idempotent_across_restart(self):
        result = run_case("success_then_restart")
        self.assertEqual(result["posts"], 1)
        self.assertEqual(result["state"], "sent")

    def test_retry_after_and_server_error_are_persisted(self):
        result = run_case("retry_responses")
        self.assertEqual(result["retry_after_seconds"], [120, 300])
        self.assertEqual(result["states"], ["retry_wait", "retry_wait"])

    def test_rejection_is_held(self):
        result = run_case("permanent_rejection")
        self.assertEqual(result["state"], "held")

    def test_general_uncertain_requires_operator_resolution(self):
        result = run_case("general_timeout")
        self.assertEqual(result["before"], "uncertain")
        self.assertEqual(result["after"], "retry_wait")
        self.assertEqual(result["actor"], "operator-1")

    def test_channel_and_body_contract_are_enforced(self):
        result = run_case("invalid_records")
        self.assertEqual(result, {"wrong_channel": True, "secret": True, "bad_body": "retry_wait"})

    def test_competing_workers_claim_once(self):
        result = run_case("competing_workers")
        self.assertEqual(result["posts"], 1)


if __name__ == "__main__":
    unittest.main()
