"""일회용 DB wrapper가 외부 환경 대신 자기 입력을 쓰는지 검사한다."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SchemaSetupTests(unittest.TestCase):
    def test_invalid_or_single_slot_fails_before_preparation(self):
        for value in ("0", "1", "bad"):
            with self.subTest(value=value):
                result = subprocess.run(
                    ["bash", str(ROOT / "gates/tools/ci-schema-diff.sh")],
                    env={**os.environ, "COLAB_PG_MAX_CONCURRENT": value},
                    capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 78, result.stdout + result.stderr)

    def test_external_inputs_cannot_replace_disposable_database(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tools = root / "gates/tools"
            tools.mkdir(parents=True)
            shutil.copy2(ROOT / "gates/tools/ci-schema-diff.sh", tools)
            (tools / "_venv.sh").write_text(
                'ensure_gate_venv() { GATE_PY="$REPO_ROOT/gates/.venv/bin/python"; }\n')
            (tools / "_pg.sh").write_text(
                'pg_start() { PGC=disposable; }\n'
                'docker() { if [ "$1" = inspect ]; then echo 172.17.0.2; fi; }\n'
                'export -f docker\n')
            (root / "gates/run.sh").write_text('''set -eu
test "$COLAB_TEST_ENV_SOURCED" = 1
test "$COLAB_APPLIED_DB_URL_PLATFORM" = postgresql://postgres:gate@172.17.0.2/applied_platform
test "$COLAB_APPLIED_DB_URL_AI" = postgresql://postgres:gate@172.17.0.2/applied_ai
test "$COLAB_PG_IMAGE" = postgres:16-alpine
test "$COLAB_ALEMBIC" = "$REPO_ROOT/gates/.venv/bin/alembic"
for name in COLAB_GATE_VENV COLAB_GATE_REQUIREMENTS COLAB_DB_DIR COLAB_PLATFORM_DB_URL_FILE COLAB_AI_DB_URL_FILE COLAB_PG_NETWORK COLAB_APPLIED_DB_URL COLAB_SCHEMA_DIFF_SKIP_UPGRADE; do
  test -z "${!name-}"
done
''')
            poison = {name: "external-input" for name in (
                "COLAB_GATE_VENV", "COLAB_GATE_REQUIREMENTS", "COLAB_DB_DIR",
                "COLAB_PLATFORM_DB_URL_FILE", "COLAB_AI_DB_URL_FILE", "COLAB_PG_NETWORK",
                "COLAB_APPLIED_DB_URL", "COLAB_SCHEMA_DIFF_SKIP_UPGRADE",
                "COLAB_APPLIED_DB_URL_PLATFORM", "COLAB_APPLIED_DB_URL_AI", "COLAB_PG_IMAGE")}
            result = subprocess.run(["bash", str(tools / "ci-schema-diff.sh")],
                env={**os.environ, **poison, "REPO_ROOT": str(root), "COLAB_PG_MAX_CONCURRENT": "4"},
                capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
