from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]


class HarnessSourceLayoutTests(unittest.TestCase):
    def test_bridge_loads_by_file_without_repository_on_python_path(self):
        # Hook hosts import by absolute filename, unlike `python scripts/agent-bridge.py`.
        code = (
            "import importlib.util,sys; "
            "s=importlib.util.spec_from_file_location('bridge',sys.argv[1]); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.check()"
        )
        result = subprocess.run(
            [sys.executable, "-I", "-c", code, str(ROOT / "scripts/agent-bridge.py")],
            cwd="/tmp", text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_skill_bodies_and_claude_adapters_are_not_duplicated(self):
        shared_names = sorted(
            path.parent.name for path in (ROOT / ".agents/skills").glob("*/SKILL.md")
        )
        self.assertEqual(len(shared_names), 16)
        for name in shared_names:
            if name == "slack-completion":
                continue
            with self.subTest(name=name):
                shared = (ROOT / f".agents/skills/{name}/SKILL.md").read_text(encoding="utf-8")
                adapter = (ROOT / f".claude/skills/{name}/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("# Claude adapter", adapter)
                self.assertIn(f".agents/skills/{name}/SKILL.md", adapter)
                self.assertLess(len(adapter), len(shared))
                self.assertNotIn(".claude/skills/", shared)

    def test_shared_resources_moved_with_their_skills(self):
        expected = [
            "VENDORED.md",
            "agent-browser/references/authentication.md",
            "agent-browser/templates/authenticated-session.sh",
            "apple-design/LICENSE.txt",
            "design-review/scripts/css_audit.py",
            "design-review/scripts/live_audit.sh",
            "design-review/scripts/live_probe.js",
            "test-driven-development/writing-good-tests.md",
            "writing-plans/plan-document-reviewer-prompt.md",
        ]
        for relative in expected:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / ".agents/skills" / relative).is_file())
                self.assertFalse((ROOT / ".claude/skills" / relative).exists())

    def test_hook_judges_are_shared_and_claude_files_are_adapters(self):
        names = [
            "bootstrap-diet.sh", "css-edit-audit.sh", "decision-number-guard.sh",
            "git-guard.sh", "lane-gate-summary.sh", "migration-guard.sh",
            "test-file-guard.sh", "uncommitted-artifacts.sh", "worktree-setup.sh",
        ]
        for name in names:
            with self.subTest(name=name):
                shared = ROOT / "scripts/harness/hooks" / name
                adapter = ROOT / ".claude/hooks" / name
                self.assertTrue(shared.is_file())
                adapter_body = adapter.read_text(encoding="utf-8")
                self.assertIn(f"scripts/harness/hooks/{name}", adapter_body)
                self.assertLess(len(adapter_body), len(shared.read_text(encoding="utf-8")))
        self.assertTrue((ROOT / "scripts/harness/hooks/lifecycle_contract.py").is_file())


if __name__ == "__main__":
    unittest.main()
