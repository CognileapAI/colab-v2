#!/usr/bin/env bash
set -uo pipefail
ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
PYTHON="${COLAB_GATE_PYTHON:-python3}"
source "$ROOT/gates/tools/_pg.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"; pg_cleanup' EXIT INT TERM
[ -f "$ROOT/gates/config/operator-notifications.toml" ] || exit 78
[ -x "$ROOT/services/core-api/.venv/bin/python" ] || exit 78
pg_start operator-notifications || exit 78
docker exec "$PGC" createdb -U postgres colab_platform >"$TMP/setup.log" 2>&1 || exit 78
DB_URLS="$(CONTAINER="$PGC" DB=colab_platform bash "$ROOT/services/core-api/tests/fixtures/setup-db.sh" 2>"$TMP/setup.log")" || exit 78
IFS=$'\t' read -r DB_URL ADMIN_DB_URL <<< "$DB_URLS"
[ -n "$DB_URL" ] && [ -n "$ADMIN_DB_URL" ] || exit 78
export COLAB_CORE_TEST_ADMIN_DATABASE_URL="$ADMIN_DB_URL"
export COLAB_CORE_TEST_DATABASE_URL="$DB_URL"
export COLAB_CORE_TEST_SUBJECTS_FILE="$ROOT/services/core-api/tests/fixtures/subjects.json"
cd "$ROOT"
"$PYTHON" "$ROOT/gates/tools/operator_notifications.py"
