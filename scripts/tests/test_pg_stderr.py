"""DB 슬롯 확보 뒤에도 준비 실패 진단이 stderr로 전달되어야 한다."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import os

ROOT = Path(__file__).resolve().parents[2]


class PgStderrTests(unittest.TestCase):
    def test_acquiring_slot_preserves_stderr(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(["bash", "-c",
                'source gates/tools/_pg.sh; pg_slot_acquire fixture || exit $?; '
                'printf "diagnostic-after-slot\\n" >&2; pg_slot_release'],
                cwd=ROOT, env={**os.environ, "COLAB_PG_SLOT_DIR": temp},
                text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0)
            self.assertIn("diagnostic-after-slot", result.stderr)
