#!/usr/bin/env bash
# Isolated PostgreSQL; no operational DB/S3 access. Invoke with bash.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$REPO_ROOT/gates/tools/_pg.sh"
pg_start storage-tests || exit 78
trap pg_cleanup EXIT
docker exec "$PGC" createdb -U postgres colab_platform >/dev/null
storage_test_url="$(CONTAINER="$PGC" DB=colab_platform bash "$REPO_ROOT/services/core-api/tests/fixtures/setup-db.sh" 2>/dev/null)"
export COLAB_CORE_TEST_DATABASE_URL="$storage_test_url" COLAB_PIPELINE_DB_URL="$storage_test_url"
storage_core_rc=0
storage_pipeline_rc=0
(cd "$REPO_ROOT/services/core-api" && .venv/bin/python -m pytest -q tests/test_storage_maintenance.py -p no:cacheprovider) || storage_core_rc=$?
(cd "$REPO_ROOT/services/pipeline-worker" && .venv/bin/python -m pytest -q tests/test_storage_reaper_dbint.py -m dbint -p no:cacheprovider) || storage_pipeline_rc=$?
if (( storage_core_rc != 0 || storage_pipeline_rc != 0 )); then exit 1; fi
