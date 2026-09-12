"""Run the model-free K4 helper suite and the public API golden regression."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "eval" / "k4-search"
REPORTS = ROOT / "dev-package" / "reports" / "stage3-ai-search-plan"
HELPER_FILES = (
    "test_condition_assessment.py",
    "test_golden_baseline.py",
    "test_heldout_eval.py",
    "test_reference_evidence.py",
    "test_stage_evidence.py",
    "test_structured_probe.py",
)
def run_suite(suite: unittest.TestSuite) -> int:
    count = suite.countTestCases()
    if count == 0:
        print("검색 helper 시험이 0건 수집됐다", file=sys.stderr)
        return 1
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def helper_suite() -> unittest.TestSuite:
    sys.path.insert(0, str(HERE))
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for filename in HELPER_FILES:
        path = HERE / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        suite.addTests(loader.discover(str(HERE), pattern=filename, top_level_dir=str(HERE)))
    return suite


def validate_golden_inputs() -> int:
    cases = json.loads((HERE / "golden-cases.json").read_text(encoding="utf-8"))["cases"]
    responses = json.loads(
        (REPORTS / "expanded-normalized-02.json").read_text(encoding="utf-8")
    )["expansion"]["responses"]
    snapshot = json.loads(
        (REPORTS / "dev-data-snapshot.json").read_text(encoding="utf-8")
    )["datasets"]
    packet = json.loads(
        (REPORTS / "stage-evidence-packet-02.json").read_text(encoding="utf-8")
    )["items"]
    if not cases or not responses:
        raise ValueError("검색 골든 문항 또는 frozen 해석 응답이 비었다")
    if [case["id"] for case in cases] != [response["id"] for response in responses]:
        raise ValueError("검색 골든 문항과 frozen 해석 응답 ID/순서가 다르다")
    if not snapshot or not packet:
        raise ValueError("검색 API 회귀에 필요한 snapshot 또는 evidence packet이 비었다")
    return len(cases)


def main() -> int:
    golden_count = validate_golden_inputs()
    helpers = helper_suite()
    helper_count = helpers.countTestCases()
    rc = run_suite(helpers)
    if rc:
        return rc
    print(f"검색 helper 회귀 green — {helper_count}건")
    completed = subprocess.run(
        ["bash", str(ROOT / "gates" / "tools" / "service-tests.sh"),
         "core-api", "search_golden"],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        return completed.returncode
    print(f"검색 public API 골든 회귀 green — {golden_count}문항")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
