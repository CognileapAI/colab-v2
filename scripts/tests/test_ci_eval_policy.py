"""CI의 모델 미실행 선언을 누락/키 의존/실패 무시 변이로 검증한다."""
import contextlib
import copy
import importlib.util
import io
from pathlib import Path
import tempfile
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
