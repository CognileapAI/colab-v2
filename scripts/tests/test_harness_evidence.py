import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "harness_evidence", ROOT / "scripts/harness/verify_evidence.py"
)


class HarnessEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(cls.module)

    def test_pull_request_and_push_shas_are_distinct(self):
        pr = self.module.event_shas("pull_request", {
            "pull_request": {"base": {"sha": "base"}, "head": {"sha": "head"}}
        }, "merge")
        self.assertEqual(pr, {"base_sha": "base", "head_sha": "head", "merge_sha": "merge"})
        push = self.module.event_shas("push", {"before": "before", "after": "after"}, "after")
        self.assertEqual(push, {"before_sha": "before", "after_sha": "after"})

    def test_missing_sha_is_readiness_failure(self):
        with self.assertRaises(self.module.EvidenceReadinessError):
            self.module.event_shas("pull_request", {"pull_request": {}}, "merge")

    def test_applicable_skip_is_readiness_red_and_failure_is_judgment_red(self):
        jobs = [
            {"name": "green", "applicable": True, "result": "success"},
            {"name": "failed", "applicable": True, "result": "failure"},
            {"name": "skipped", "applicable": True, "result": "skipped"},
            {"name": "na", "applicable": False, "result": "skipped", "reason": "path filter"},
        ]
        evidence = self.module.build_ci_evidence("run", 2, "sha", "tree", {"head_sha": "sha"}, jobs)
        self.assertEqual(evidence["counts"], {
            "green": 1, "red_judgment": 1, "red_readiness": 1, "not_applicable": 1,
        })
        self.assertEqual(self.module.verdict(evidence), 1)

    def test_all_non_applicable_is_not_green(self):
        jobs = [{"name": "na", "applicable": False, "result": "skipped", "reason": "path filter"}]
        evidence = self.module.build_ci_evidence("run", 1, "sha", "tree", {"head_sha": "sha"}, jobs)
        self.assertEqual(self.module.verdict(evidence), 78)

    def test_gate_summary_rejects_wrong_sha_and_readiness(self):
        summary = {"schema": "colab-gate-summary/1", "commit": "sha",
                   "counts": {"green": 1, "red_판정": 0, "red_준비": 0},
                   "gates": [{"name": "x", "status": "green", "exit": 0}]}
        self.module.verify_gate_summary(summary, "sha", ["x"])
        with self.assertRaises(self.module.EvidenceError):
            self.module.verify_gate_summary(summary, "other", ["x"])
        summary["counts"]["red_준비"] = 1
        with self.assertRaises(self.module.EvidenceError):
            self.module.verify_gate_summary(summary, "sha", ["x"])


if __name__ == "__main__":
    unittest.main()
