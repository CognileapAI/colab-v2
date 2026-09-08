"""원본을 복사하지 않고 기획 검사기의 실패 판정을 검증한다."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("freshness", ROOT / "dev-package/tools/check-package-freshness.py")
freshness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freshness)


class PlanningGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        epic = self.root / "에픽/E-00_fixture"
        (epic / "documents").mkdir(parents=True)
        (epic / "package").mkdir()
        self.source = epic / "documents/Policy_fixture.md"
        self.html = epic / "package/index.html"
        self.source.write_text("version: 1\n정책 원본\n", encoding="utf-8")
        self.html.write_text('<script type="text/markdown" id="md-policy">\nversion: 1\n정책 원본\n</script>', encoding="utf-8")

    def test_matching_source(self):
        rows, errors = freshness.check(str(self.root))
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][3], "MATCH")

    def test_tampered_embedded_text(self):
        self.html.write_text(self.html.read_text(encoding="utf-8").replace("정책 원본", "변조"), encoding="utf-8")
        rows, errors = freshness.check(str(self.root))
        self.assertTrue(errors)
        self.assertEqual(rows[0][3], "DIFFER")

    def test_missing_source_and_empty_root(self):
        self.source.unlink()
        self.assertTrue(freshness.check(str(self.root))[1])
        self.assertTrue(freshness.check(str(self.root / "missing"))[1])

    def test_read_failure_is_diagnosed(self):
        with patch.object(freshness, "read", side_effect=freshness.Unreadable("fixture")):
            self.assertIn("읽기 실패", " ".join(freshness.check(str(self.root))[1]))

    def test_applied_manifest_negative_cases(self):
        with contextlib.redirect_stdout(io.StringIO()):
            failures = freshness._selftest_applied(str(self.root))
        self.assertEqual(failures, [])
