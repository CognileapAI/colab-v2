#!/usr/bin/env bash
# CI 전용: 외부 DB 입력 대신 두 개의 빈 일회용 DB를 준비한다.
# 실제 upgrade/비교는 기존 schema-diff가 한다. 운영 URL을 읽지 않는다.
set -euo pipefail
# 이 진입점은 사용자 홈의 시험 환경을 source하지 않는다.
export COLAB_TEST_ENV_SOURCED=1
slots="${COLAB_PG_MAX_CONCURRENT:-4}"
if [[ ! "$slots" =~ ^[1-9][0-9]*$ ]] || (( slots < 2 )); then
  echo '::error::ci-schema-diff red(준비) — 적용 DB와 비교 DB를 위한 동시 슬롯 2개가 필요하다.'
  exit 78
fi
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# selftest용 입력 교체나 사용자 환경이 검사 대상/준비 도구를 바꾸지 못하게 한다.
unset COLAB_GATE_VENV COLAB_GATE_REQUIREMENTS COLAB_DB_DIR
unset COLAB_PLATFORM_DB_URL_FILE COLAB_AI_DB_URL_FILE COLAB_PG_NETWORK
export COLAB_PG_IMAGE=postgres:16-alpine
source "$REPO_ROOT/gates/tools/_venv.sh"
ensure_gate_venv ci-schema-diff
export COLAB_ALEMBIC="$(dirname "$GATE_PY")/alembic"
source "$REPO_ROOT/gates/tools/_pg.sh"
pg_start ci-schema-diff
# pg_start가 설치한 cleanup trap을 유지한다. 포트·볼륨은 공개하지 않는다.
for chain in platform ai; do
  docker exec "$PGC" createdb -U postgres "applied_$chain"
done
address="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$PGC")"
if [[ ! "$address" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo '::error::ci-schema-diff red(준비) — 일회용 DB 주소를 확인하지 못했다.'
  exit 78
fi
# schema-diff의 자식 postgres도 같은 기본 bridge에서 이 DB에 닿는다.
# 호스트의 Alembic은 Linux CI/WSL에서 bridge IP로 붙는다.
export COLAB_APPLIED_DB_URL_PLATFORM="postgresql://postgres:gate@$address/applied_platform"
export COLAB_APPLIED_DB_URL_AI="postgresql://postgres:gate@$address/applied_ai"
unset COLAB_APPLIED_DB_URL COLAB_SCHEMA_DIFF_SKIP_UPGRADE
bash "$REPO_ROOT/gates/run.sh" schema-diff
