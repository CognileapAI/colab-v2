"""Record gates: `adr-records` (ADR structure) and `intent-ref` (commit → intent link).

Every repository here is a throwaway `git init` under a temporary directory. Nothing is
written to this checkout.
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "gates/fixtures"
INTENT = "dev-package/intent/2026-01-01-approved.md"
TRAILER = "Intent-Ref: " + INTENT
APPROVED = ("# Intent: fixture approved\n"
            "메타 — 발의자: Ted · 작성 2026-01-01 · 승인: **Ted 2026-01-01**\n"
            "\n## 문제\n- first line\n- second line\n")
DRAFT = ("# Intent: fixture draft\n"
         "메타 — 발의자: agent · 작성 2026-01-02 · 승인 **미승인**\n"
         "\n## 문제\n- draft line\n")
TEMPLATE = "# Intent: <제목>\n메타 — 발의자: <누구> · 작성 2026-MM-DD · 승인 <날짜 | 미승인>\n"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, text=True).stdout.strip()


class AdrRecordsGateTests(unittest.TestCase):
    def run_gate(self, fixture):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init", "-q")
            (root / ".agents").mkdir()
            shutil.copy2(ROOT / ".agents/harness.yaml", root / ".agents/harness.yaml")
            shutil.copytree(FIXTURES / "adr-records" / fixture, root / "docs/decisions")
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "fixture")
            return subprocess.run([sys.executable, str(ROOT / "scripts/harness/adr_gate.py"), "--all",
                                   "--repo-root", str(root)], capture_output=True, text=True)

    def test_record_missing_a_required_section_is_red(self):
        result = self.run_gate("missing-section")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("one 재검토 조건 section is required", result.stderr)
        green = self.run_gate("valid")
        self.assertEqual(green.returncode, 0, green.stdout + green.stderr)

    def test_runner_dispatches_adr_records_over_all_records(self):
        runner = (ROOT / "gates/run.sh").read_text(encoding="utf-8")
        case = re.search(r"^  adr-records\)\n(.*?)\n    ;;", runner, re.M | re.S)
        self.assertIsNotNone(case, "gates/run.sh has no adr-records case")
        self.assertIn("scripts/harness/adr_gate.py", case.group(1))
        self.assertIn("--all", case.group(1))
        listed = re.search(r"^ALL_GATES=\(\n(.*?)^\)", runner, re.M | re.S).group(1).split()
        self.assertIn("adr-records", listed)
        self.assertIn("intent-ref", listed)

    def test_ci_filter_check_requires_decisions_in_the_dev_package_filter(self):
        yaml = __import__("yaml")
        checker = load("ci_filter_record_gates", ROOT / "gates/tools/ci-filter-check.py")
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))

        def check(data):
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "ci.yml"
                path.write_text(yaml.safe_dump(data), encoding="utf-8")
                original = checker.CI_PATH
                try:
                    checker.CI_PATH = str(path)
                    with contextlib.redirect_stdout(io.StringIO()) as out:
                        return checker.main(), out.getvalue()
                finally:
                    checker.CI_PATH = original

        self.assertEqual(check(workflow)[0], 0)
        broken = copy.deepcopy(workflow)
        step = next(s for s in broken["jobs"]["changes"]["steps"] if s.get("id") == "filter")
        step["with"]["filters"] = re.sub(r"\n[ \t]*- 'docs/decisions/\*\*'", "", step["with"]["filters"])
        code, output = check(broken)
        self.assertEqual(code, 1)
        self.assertIn("docs/decisions/", output)


class IntentRefGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load("intent_ref", ROOT / "scripts/harness/intent_ref.py")

    def repo(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        git(root, "init", "-q")
        self.write(root, {INTENT: APPROVED, "dev-package/intent/2026-01-02-draft.md": DRAFT,
                          "dev-package/intent/TEMPLATE.md": TEMPLATE, "README.md": "fixture\n"})
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "base")
        return root, git(root, "rev-parse", "HEAD")

    def write(self, root, files):
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def commit(self, root, message, files=None, delete=()):
        self.write(root, files or {})
        for name in delete:
            git(root, "rm", "-q", name)
        git(root, "add", "-A")
        git(root, "commit", "-q", "--allow-empty", "-m", message)

    def run_gate(self, root, base=None, head=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("COLAB_INTENT_REF_")}
        if base is not None:
            env["COLAB_INTENT_REF_BASE"] = base
        if head is not None:
            env["COLAB_INTENT_REF_HEAD"] = head
        return subprocess.run([sys.executable, str(ROOT / "scripts/harness/intent_ref.py"),
                               "--repo-root", str(root)], capture_output=True, text=True, env=env)

    def assertExit(self, result, code):
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def test_subject_change_without_trailer_is_red(self):
        root, base = self.repo()
        self.commit(root, "change code", {"scripts/tool.py": "print(1)\n"})
        result = self.run_gate(root, base)
        self.assertExit(result, 1)
        self.assertIn("Intent-Ref", result.stdout)

    def test_trailer_naming_a_missing_intent_is_red(self):
        root, base = self.repo()
        self.commit(root, "change code\n\nIntent-Ref: dev-package/intent/2026-01-09-missing.md",
                    {"services/core-api/x.py": "x = 1\n"})
        result = self.run_gate(root, base)
        self.assertExit(result, 1)
        self.assertIn("2026-01-09-missing.md", result.stdout)

    def test_valid_trailer_is_green_even_on_an_empty_commit(self):
        root, base = self.repo()
        self.commit(root, "change code", {"gates/tool.sh": "true\n"})
        self.commit(root, "link intent\n\n" + TRAILER)  # retroactive path: --allow-empty
        result = self.run_gate(root, base)
        self.assertExit(result, 0)
        self.assertIn("Intent-Ref 1", result.stdout)

    def test_approved_intent_line_deletion_or_edit_is_red(self):
        for label, text in (("delete", APPROVED.replace("- first line\n", "")),
                            ("edit", APPROVED.replace("- first line", "- first line (typo fixed)"))):
            with self.subTest(change=label):
                root, base = self.repo()
                self.commit(root, "touch intent\n\n" + TRAILER, {INTENT: text})
                result = self.run_gate(root, base)
                self.assertExit(result, 1)
                self.assertIn(INTENT, result.stdout)

    def test_approved_intent_deleted_is_red(self):
        root, base = self.repo()
        self.commit(root, "drop intent", delete=[INTENT])
        self.assertExit(self.run_gate(root, base), 1)

    def test_approved_intent_line_addition_and_draft_edits_are_green(self):
        root, base = self.repo()
        self.commit(root, "append\n\n" + TRAILER,
                    {INTENT: APPROVED + "- appended line\n",
                     "dev-package/intent/2026-01-02-draft.md": DRAFT.replace("draft line", "rewritten")})
        self.assertExit(self.run_gate(root, base), 0)

    def test_docs_only_range_is_out_of_scope_and_green(self):
        root, base = self.repo()
        self.commit(root, "docs", {"docs/guide.md": "text\n", "dev-package/sessions/x.md": "x\n"})
        result = self.run_gate(root, base)
        self.assertExit(result, 0)
        self.assertIn("대상 밖", result.stdout)
        self.assertIn("변경 파일 2", result.stdout)

    def test_undeclared_base_uses_origin_develop_merge_base_or_is_readiness(self):
        root, base = self.repo()
        self.commit(root, "change code", {"scripts/tool.py": "print(1)\n"})
        result = self.run_gate(root)
        self.assertExit(result, 78)
        self.assertIn("::gate-readiness-failure::", result.stderr)
        git(root, "update-ref", "refs/remotes/origin/develop", base)
        result = self.run_gate(root)
        self.assertExit(result, 1)
        self.assertIn("merge-base", result.stdout)
        self.assertIn(base[:12], result.stdout)

    def test_unresolvable_declared_base_is_readiness(self):
        root, _ = self.repo()
        result = self.run_gate(root, "no-such-ref")
        self.assertExit(result, 78)
        self.assertIn("::gate-readiness-failure::", result.stderr)

    def test_explicit_head_limits_the_range(self):
        root, base = self.repo()
        self.commit(root, "linked\n\n" + TRAILER, {"scripts/a.py": "a\n"})
        linked = git(root, "rev-parse", "HEAD")
        self.commit(root, "unlinked", {"scripts/b.py": "b\n"})
        self.assertExit(self.run_gate(root, base, linked), 0)
        self.assertExit(self.run_gate(root, linked, "HEAD"), 1)

    def test_classification_matches_the_frozen_62_intent_answer_table(self):
        table = json.loads((FIXTURES / "intent-ref/intent-meta-classification.json").read_text(encoding="utf-8"))
        self.assertEqual(table["total"], 62)
        self.assertEqual(len(table["files"]), 62)
        self.assertEqual(table["counts"], {"approved": 44, "unapproved": 13, "no-meta": 5})
        for row in table["files"]:
            text = "# Intent\n" + (row["meta"] + "\n" if row["meta"] is not None else "") + "\n## 문제\n"
            with self.subTest(name=row["name"]):
                self.assertEqual(self.module.classify(text), row["class"])
                self.assertEqual(self.module.is_protected(row["name"], text), row["class"] == "approved"
                                 and row["name"] not in table["excluded_by_name"])
        protected = [row for row in table["files"]
                     if self.module.is_protected(row["name"], "# I\n" + (row["meta"] or "") + "\n")]
        self.assertEqual(len(protected), 44)
        # Known misjudgment kept on purpose: really approved, but the meta line still says 미승인.
        evals = next(row for row in table["files"] if row["name"] == "2026-09-08-harness-evals.md")
        self.assertEqual(evals["class"], "unapproved")
        self.assertIn(evals["name"], table["intended_unprotected"])
        self.assertFalse(self.module.is_protected("TEMPLATE.md", "# T\n메타 — 승인: Ted 2026-01-01\n"))


if __name__ == "__main__":
    unittest.main()
