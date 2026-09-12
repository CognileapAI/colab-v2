#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0026-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM
export COLAB_PLATFORM_DB_URL=postgresql+psycopg://offline/offline
(cd "$CHAIN" && "$ALEMBIC" upgrade 0026_login_sessions --sql) >"$TMP/head.sql" ||
  { echo "::error::0026-drift red — render 실패"; exit 1; }
for token in login_session revoke_digest credential_kind purpose credential_version; do
  grep -q "$token" "$TMP/head.sql" ||
    { echo "::error::0026-drift red — head에 $token 없음"; exit 1; }
done
echo "0026-drift green — head SQL에 세션 원장 불변식이 있다."
