#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export COLAB_PLATFORM_DB_URL="postgresql+psycopg://offline/offline"
(cd "$ROOT/db/platform" && "$ALEMBIC" upgrade 0026_login_sessions:0027_operator_audit --sql) >"$TMP/up.sql" || exit 1
for token in d2_operator_audit d3_operator_audit d6_operator_audit d2_operator_export d3_operator_export d5_operator_export d6_operator_export d8_operator_export 'ENABLE ROW LEVEL SECURITY' 'receipt_hash IS NULL'; do
  grep -q "$token" "$TMP/up.sql" || { echo "::error::0025 drift red — $token 없음"; exit 1; }
done
echo "[0025-drift] 감사 3표·내보내기 5표·RLS·pending index 확인 → OK"
