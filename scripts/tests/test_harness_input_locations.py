from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class HarnessInputLocationTests(unittest.TestCase):
    def test_seed_gate_default_is_a_gate_fixture_not_a_report(self):
        source = (ROOT / "gates/tools/seed-plan-drift.sh").read_text(encoding="utf-8")
        self.assertNotIn("dev-package/reports/reference-data/datasets-md", source)
        self.assertIn("gates/fixtures/seed-plan-drift/green/md", source)


if __name__ == "__main__":
    unittest.main()
