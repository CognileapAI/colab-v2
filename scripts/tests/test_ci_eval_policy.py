"""CI의 모델 미실행 선언을 누락/키 의존/실패 무시 변이로 검증한다."""
import contextlib
import copy
import importlib.util
import io
import os
from pathlib import Path
import tempfile
from unittest import mock
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ci_filter", ROOT / "gates/tools/ci-filter-check.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class EvalPolicyTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))

    def check(self, workflow):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ci.yml"
            path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
            original = checker.CI_PATH
            try:
                checker.CI_PATH = str(path)
                with contextlib.redirect_stdout(io.StringIO()):
                    return checker.main()
            finally:
                checker.CI_PATH = original

    def test_current_workflow(self):
        self.assertEqual(self.check(self.workflow), 0)

    def test_both_breaking_gates_use_the_fixed_base_ref(self):
        steps = self.workflow["jobs"]["contract-gates"]["steps"]
        breaking = [step for step in steps if "breaking" in step.get("run", "")]
        self.assertEqual(len(breaking), 2)
        self.assertTrue(all(step.get("env", {}).get("COLAB_BREAKING_BASE_REF")
                            == "${{ github.event.pull_request.base.sha || github.event.before }}"
                            for step in breaking))

    def test_common_and_tool_adapter_paths_trigger_harness_checks(self):
        filters = next(
            step["with"]["filters"] for step in self.workflow["jobs"]["changes"]["steps"]
            if step.get("id") == "filter"
        )
        # + E0: the whole config-hash set (`.claude/**` covers settings.json · rules) · judge · eval runner.
        for path in ("AGENTS.md", ".agents/**", ".codex/**", "scripts/harness/**",
                     ".claude/**", "gates/**", "eval/harness/**", "scripts/harness/hooks/**"):
            self.assertIn("- '" + path + "'", filters)

    def filters_of(self, workflow):
        step = next(s for s in workflow["jobs"]["changes"]["steps"] if s.get("id") == "filter")
        return step, yaml.safe_load(step["with"]["filters"])

    def test_filter_must_cover_the_config_hash_set(self):
        # filter-drop-settings: without the pattern covering `.claude/settings.json` a settings-only
        # change alters the eval config hash but never wakes the harness-eval job.
        data = copy.deepcopy(self.workflow)
        step, filters = self.filters_of(data)
        filters["harness"] = [p for p in filters["harness"] if p != ".claude/**"]
        step["with"]["filters"] = yaml.safe_dump(filters)
        self.assertEqual(self.check(data), 1)

    def test_new_config_path_without_filter_update_is_red(self):
        # paths-file-extra: the canonical list grows, the CI filter does not.
        canonical = (ROOT / "eval/harness/config-paths.txt").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            extra = Path(temp) / "config-paths.txt"
            extra.write_text(canonical + "docs/extra/**\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"COLAB_EVAL_CONFIG_PATHS": str(extra)}):
                self.assertEqual(self.check(self.workflow), 1)
            missing = Path(temp) / "absent.txt"
            with mock.patch.dict(os.environ, {"COLAB_EVAL_CONFIG_PATHS": str(missing)}):
                with self.assertRaises(SystemExit) as raised:
                    self.check(self.workflow)
                self.assertEqual(raised.exception.code, 78)

    def test_required_gates_aggregator_is_not_skippable(self):
        job = self.workflow["jobs"]["required-gates"]
        self.assertEqual(job["if"], "${{ always() }}")
        self.assertIn("changes", job["needs"])
        self.assertFalse(job.get("continue-on-error", False))
        runs = "\n".join(step.get("run", "") for step in job["steps"])
        self.assertIn("verify_evidence.py ci", runs)
        self.assertTrue(any(step.get("uses", "").startswith("actions/upload-artifact@")
                            for step in job["steps"]))

    def test_missing_exemption_secret_dependency_and_failure_masking(self):
        for mutation in ("exemption", "secret", "masking", "runner", "gate"):
            with self.subTest(mutation=mutation):
                data = copy.deepcopy(self.workflow)
                job = data["jobs"]["harness-eval"]
                if mutation == "secret":
                    job["env"] = {"ANTHROPIC_API_KEY": "${{ secrets.ANTHROPIC_API_KEY }}"}
                elif mutation == "masking":
                    job["continue-on-error"] = True
                else:
                    for step in job["steps"]:
                        if mutation == "exemption":
                            step.pop("env", None)
                        elif "run" in step:
                            target = ("eval/harness/tests/run-selftest.sh" if mutation == "runner"
                                      else "gates/tools/harness-eval-selftest.sh")
                            step["run"] = step["run"].replace(target, "removed-check.sh")
                self.assertEqual(self.check(data), 1)


if __name__ == "__main__":
    unittest.main()
