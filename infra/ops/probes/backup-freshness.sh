#!/usr/bin/env bash
# core-api 이미지 안에서 기존 deploy_doctor.check_backups만 실행한다.
set -uo pipefail
REPO="${COLAB_DEV_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
STATE="${COLAB_DEV_STATE:-/opt/colab-v2}"
SHA="$(tr -d '\r\n' < "$STATE/CURRENT_SHA" 2>/dev/null)"
[[ "$SHA" =~ ^[0-9a-f]{12,40}$ ]] || { echo "backup probe red — CURRENT_SHA 형식" >&2; exit 1; }
IMAGE="colab-v2/core-api:dev-$SHA"
docker image inspect "$IMAGE" >/dev/null 2>&1 || { echo "backup probe red — 현재 SHA 이미지 부재" >&2; exit 1; }
NAME="${COLAB_OPS_CONTAINER_NAME:-colab-ops-backup-freshness-$$}"
exec "$(dirname "${BASH_SOURCE[0]}")/docker-run.sh" "$NAME" "${COLAB_OPS_DOCKER_TIMEOUT:-110}" -- \
  --rm --user 0 --network host -e AWS_DEFAULT_REGION=ap-northeast-2 \
  -v "$REPO:/repo:ro" -w /repo --entrypoint python "$IMAGE" \
  infra/ops/probes/backup-freshness.py --repo /repo
