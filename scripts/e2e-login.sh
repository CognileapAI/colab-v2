#!/usr/bin/env bash
# 새 일회용 Postgres만 사용한다. 앱/DB/브라우저는 종료 시 회수한다.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${E2E_PYTHON:?core-api 의존성이 설치된 Python 경로 필요}"
: "${E2E_FRONTEND_ROOT:?같은 HEAD의 의존성이 설치된 frontend 경로 필요}"
export COLAB_TEST_ENV_SOURCED=1
unset COLAB_PG_NETWORK
export COLAB_PG_IMAGE=postgres:16-alpine
source "$REPO_ROOT/gates/tools/_pg.sh"
pg_start e2e-login
docker exec "$PGC" createdb -U postgres colab_e2e_login
E2E_DATABASE_URL="$(CONTAINER="$PGC" DB=colab_e2e_login OWNER=colab_owner APP=colab_app APP_PASSWORD=e2e_app bash "$REPO_ROOT/services/core-api/tests/fixtures/setup-db.sh")"
export E2E_DATABASE_URL
e2e_child=""
e2e_cleanup() {
  if [ -n "$e2e_child" ]; then
    kill -TERM "$e2e_child" 2>/dev/null || true
    wait "$e2e_child" 2>/dev/null || true
    e2e_child=""
  fi
  pg_cleanup
}
trap e2e_cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
"$E2E_PYTHON" "$REPO_ROOT/scripts/e2e-login.py" --frontend-root "$E2E_FRONTEND_ROOT" "$@" &
e2e_child=$!
e2e_status=0
wait "$e2e_child" || e2e_status=$?
e2e_child=""
exit "$e2e_status"
