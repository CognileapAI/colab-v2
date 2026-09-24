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
    def test_startup_does_not_require_legacy_round_for_new_task(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(['bash', str(ROOT/'scripts/harness/hooks/bootstrap-diet.sh')],
                input=json.dumps({'cwd': directory}), capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(result.returncode, 0)
            self.assertIn('task', result.stdout)
            self.assertNotIn('읽을 것은 **라운드 파일 하나다**', result.stdout)

    def test_product_adapter_cannot_fork_or_lose_shared_body(self):
        value = self.module.load_contract(ROOT / '.agents/harness.yaml')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ('.claude', '.agents', '.codex/agents', 'scripts/harness/hooks'):
                shutil.copytree(ROOT / relative, root / relative)
            shutil.copy2(ROOT / 'CLAUDE.md', root / 'CLAUDE.md')
            value['adapters']['required_files'] = []
            value['paths']['required'] = []
            self.assertEqual(self.module.check_contract(root, value), [])
            adapter = root / 'CLAUDE.md'
            original = adapter.read_text()
            adapter.write_text(original + '\nForked product policy.\n')
            self.assertTrue(self.module.check_contract(root, value))
            adapter.write_text(original)
            source = root / '.agents/rules/product.md'
            source.unlink()
            self.assertTrue(self.module.check_contract(root, value))

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

    def test_current_branch_policy_rejects_obsolete_main(self):
        value = self.module.load_contract(ROOT / '.agents/harness.yaml')
        value['project'].update(default_branch='develop', deployment_branch='product')
        self.module.validate_contract(value)
        for field in ('default_branch', 'deployment_branch'):
            bad = json.loads(json.dumps(value))
            bad['project'][field] = 'main'
            with self.subTest(field=field), self.assertRaises(self.module.ContractError):
                self.module.validate_contract(bad)

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

    def test_rejects_missing_or_forked_rule_and_role_sources(self):
        value = self.module.load_contract(ROOT / ".agents/harness.yaml")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (".claude", ".agents", ".codex/agents", "scripts/harness/hooks"):
                shutil.copytree(ROOT / relative, root / relative)
            value["adapters"]["required_files"] = []
            value["paths"]["required"] = []
            shutil.copy2(ROOT / 'CLAUDE.md', root / 'CLAUDE.md')
            self.assertEqual(self.module.check_contract(root, value), [])
            for relative in (".claude/rules/deploy.md", ".claude/agents/advisor.md"):
                adapter = root / relative
                original = adapter.read_text()
                adapter.write_text(original + "\nIndependent policy body.\n")
                self.assertTrue(self.module.check_contract(root, value), "forked body must fail")
                adapter.write_text(original)
            for relative in (".agents/rules/deploy.md", ".agents/roles/advisor.md"):
                source = root / relative
                original = source.read_text()
                source.unlink()
                self.assertTrue(self.module.check_contract(root, value), "missing source must fail")
                source.write_text(original)
            adapter = root / ".codex/agents/advisor.toml"
            adapter.write_text(adapter.read_text().replace(".agents/roles/advisor.md", ".agents/roles/researcher.md"))
            self.assertTrue(self.module.check_contract(root, value), "wrong Codex source must fail")

    def test_rejects_missing_judge_wrong_adapter_and_duplicated_body(self):
        value = self.module.load_contract(ROOT / ".agents/harness.yaml")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (".claude", ".agents", ".codex/agents", "scripts/harness/hooks"):
                shutil.copytree(ROOT / relative, root / relative)
            value["adapters"]["required_files"] = []
            value["paths"]["required"] = []
            shutil.copy2(ROOT / 'CLAUDE.md', root / 'CLAUDE.md')
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

    def surface(self, directory):
        """Copy the adapter surface the contract judges into a scratch root."""
        root = Path(directory)
        for relative in ('.claude', '.agents', '.codex/agents', 'scripts/harness/hooks'):
            shutil.copytree(ROOT / relative, root / relative)
        shutil.copy2(ROOT / 'CLAUDE.md', root / 'CLAUDE.md')
        return root

    # K1 — a hook can be declared and shimmed and still be silently unwired.
    def test_declared_hook_must_be_registered_under_its_event_and_matcher(self):
        value = self.module.load_contract(ROOT / '.agents/harness.yaml')
        value['adapters']['required_files'] = []
        value['paths']['required'] = []
        with tempfile.TemporaryDirectory() as directory:
            root = self.surface(directory)
            self.assertEqual(self.module.check_contract(root, value), [])
            path = root / '.claude/settings.json'
            original = path.read_text()
            settings = json.loads(original)
            # Keep the matcher; drop exactly one command line (bridge symmetry cannot see this).
            entry = next(e for e in settings['hooks']['PreToolUse'] if e['matcher'] == 'Edit|Write')
            entry['hooks'] = [h for h in entry['hooks'] if 'test-file-guard.sh' not in h['command']]
            path.write_text(json.dumps(settings))
            self.assertEqual(self.module.check_contract(root, value), [
                'hook not registered in .claude/settings.json: test-file-guard.sh '
                '(event PreToolUse, matcher Edit|Write)'])
            path.write_text(original)
            moved = json.loads(json.dumps(value))
            moved['sources']['hook_registrations']['git-guard.sh']['matcher'] = 'Edit|Write'
            self.assertEqual(self.module.check_contract(root, moved), [
                'hook not registered in .claude/settings.json: git-guard.sh '
                '(event PreToolUse, matcher Edit|Write)'])
            undeclared = json.loads(json.dumps(value))
            del undeclared['sources']['hook_registrations']['worktree-setup.sh']
            self.assertEqual(self.module.check_contract(root, undeclared), [
                'hook has no event/matcher registration: worktree-setup.sh'])
        missing = json.loads(json.dumps(value))
        del missing['sources']['hook_registrations']
        with self.assertRaises(self.module.ContractError):
            self.module.validate_contract(missing)

    # K4 — always-on documents carry a declared line budget.
    def test_always_on_documents_over_the_line_budget_are_red(self):
        value = self.module.load_contract(ROOT / '.agents/harness.yaml')
        self.assertEqual(value['hygiene']['always_on_max_lines'], 120)
        self.assertEqual(self.module.check_always_on_lines(ROOT, value), [])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.claude/rules').mkdir(parents=True)
            (root / 'AGENTS.md').write_text('line\n' * 120)
            (root / 'CLAUDE.md').write_text('line\n')
            (root / '.claude/rules/fixture.md').write_text('line\n' * 121)
            self.assertEqual(self.module.check_always_on_lines(root, value), [
                'always-on document exceeds 120 lines: .claude/rules/fixture.md (121)'])
            (root / '.claude/rules/fixture.md').unlink()
            (root / 'CLAUDE.md').unlink()
            self.assertEqual(self.module.check_always_on_lines(root, value), [
                'always-on document is missing: CLAUDE.md',
                'always-on pattern matches no file: .claude/rules/*.md'])
        for broken in (None, 0, '120', True):
            bad = json.loads(json.dumps(value))
            bad['hygiene']['always_on_max_lines'] = broken
            with self.subTest(limit=broken), self.assertRaises(self.module.ContractError):
                self.module.validate_contract(bad)

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
