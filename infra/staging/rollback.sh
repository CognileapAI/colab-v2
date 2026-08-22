#!/usr/bin/env bash
# WU-I2 롤백 — 직전 서빙 상태(자리표시 오리진, compose.yml)로 되돌린다.
#
# 되돌리는 것은 **서빙 상태**지 데이터가 아니다. pgdata 볼륨은 남는다 —
# 롤백이 데이터를 지우면 그건 롤백이 아니라 재해다.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${COLAB_STAGING_ENV:-$HOME/.colab-v2-staging.env}"
docker compose -f "$HERE/compose.yml" --env-file "$ENV_FILE" up -d --remove-orphans
docker compose -f "$HERE/compose.yml" --env-file "$ENV_FILE" ps
