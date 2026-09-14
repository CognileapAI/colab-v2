import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "harness_config", ROOT / "scripts/harness/config.py"
)


class HarnessConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(cls.module)

    def write(self, value):
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name) / "harness.yaml"
        path.write_text(value, encoding="utf-8")
        self.addCleanup(temp.cleanup)
        return path

    def test_rejects_malformed_json_and_missing_required_keys(self):
        with self.assertRaises(self.module.ContractError):
            self.module.load_contract(self.write("not: strict-json"))
        with self.assertRaises(self.module.ContractError):
            self.module.load_contract(self.write(json.dumps({"schema": "colab-harness/1"})))

    def test_rejects_empty_required_gate(self):
        value = self.module.load_contract(ROOT / ".agents/harness.yaml")
        value["gates"]["required"] = []
        with self.assertRaises(self.module.ContractError):
            self.module.validate_contract(value)

    def test_repository_contract_and_declared_paths_are_valid(self):
        value = self.module.load_contract(ROOT / ".agents/harness.yaml")
        self.assertEqual(self.module.check_contract(ROOT, value), [])

    def test_missing_adapter_is_a_semantic_failure(self):
        value = self.module.load_contract(ROOT / ".agents/harness.yaml")
        value["adapters"]["required_files"].append(".codex/missing.toml")
        self.assertEqual(
            self.module.check_contract(ROOT, value),
            ["missing required adapter: .codex/missing.toml"],
        )

    def run_check(self, contract):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/harness/check.py"),
             "--root", str(ROOT), "--contract", str(contract)],
            text=True, capture_output=True, check=False,
        )

    def test_cli_preserves_readiness_and_judgment_exit_codes(self):
        malformed = self.run_check(self.write("not json"))
        self.assertEqual(malformed.returncode, 78)
        self.assertIn("::gate-readiness-failure::", malformed.stderr)

        value = self.module.load_contract(ROOT / ".agents/harness.yaml")
        value["adapters"]["required_files"].append(".codex/missing.toml")
        semantic = self.run_check(self.write(json.dumps(value)))
        self.assertEqual(semantic.returncode, 1)
        self.assertIn("red(판정)", semantic.stderr)

        green = self.run_check(ROOT / ".agents/harness.yaml")
        self.assertEqual(green.returncode, 0)
        self.assertIn("green: shared harness contract", green.stdout)


if __name__ == "__main__":
    unittest.main()
