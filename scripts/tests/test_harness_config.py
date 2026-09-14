import importlib.util
import json
import shutil
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

    def test_rejects_missing_judge_wrong_adapter_and_duplicated_body(self):
        value = self.module.load_contract(ROOT / ".agents/harness.yaml")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (".claude/hooks", "scripts/harness/hooks"):
                shutil.copytree(ROOT / relative, root / relative)
            value["adapters"]["required_files"] = []
            value["paths"]["required"] = []
            self.assertEqual(self.module.check_contract(root, value), [])
            adapter = root / ".claude/hooks/git-guard.sh"
            original = adapter.read_text()
            adapter.write_text(original.replace("hooks/git-guard.sh", "hooks/migration-guard.sh"))
            self.assertTrue(self.module.check_contract(root, value), "wrong judge must fail")
            adapter.write_text((root / "scripts/harness/hooks/git-guard.sh").read_text())
            self.assertTrue(self.module.check_contract(root, value), "duplicated body must fail")
            adapter.write_text(original)
            (root / "scripts/harness/hooks/git-guard.sh").unlink()
            self.assertTrue(self.module.check_contract(root, value), "missing judge must fail")

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
