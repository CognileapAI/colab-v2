import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_regression.py"


def _runner():
    if not RUNNER.is_file():
        raise AssertionError("검색 골든 회귀 러너가 없다")
    spec = importlib.util.spec_from_file_location("k4_search_regression", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_zero_helper_tests_are_rejected():
    runner = _runner()
    assert runner.run_suite(unittest.TestSuite()) != 0


def test_helper_failure_is_propagated():
    runner = _runner()
    class FailingCase(unittest.TestCase):
        def runTest(self):
            self.fail("의도한 실패")
    suite = unittest.TestSuite([FailingCase()])
    assert runner.run_suite(suite) != 0


def test_expected_helper_suite_can_pass():
    runner = _runner()
    class PassingCase(unittest.TestCase):
        def runTest(self):
            self.assertTrue(True)
    suite = unittest.TestSuite([PassingCase()])
    assert runner.run_suite(suite) == 0
