#!/usr/bin/env bash
# dev EC2의 현재 SHA를 대상으로 기존 15항 deploy_doctor를 그대로 실행한다.
set -uo pipefail
REPO="${COLAB_DEV_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
STATE="${COLAB_DEV_STATE:-/opt/colab-v2}"
SECRETS="${COLAB_DEV_SECRETS_DIR:-/etc/colab}"
ARTIFACTS="${COLAB_RELEASE_ARTIFACT_DIR:-}"
EXTRA_MOUNTS=()
DOCTOR=(ops/deploy_doctor.py)
if [ "${COLAB_RELEASE_COLLECT:-0}" = 1 ]; then
  [ -n "$ARTIFACTS" ] && [ -d "$ARTIFACTS" ] && [ ! -L "$ARTIFACTS" ] || { echo 'dedicated release artifact directory required' >&2; exit 78; }
  EXTRA_MOUNTS=(-v "$ARTIFACTS:/artifacts:rw")
  DOCTOR=(ops/deploy_doctor_evidence.py --pre /state/RELEASE_PRE.json --output /artifacts/post.json --source /repo --)
fi
SHA="$(tr -d '\r\n' < "$STATE/CURRENT_SHA" 2>/dev/null)"
[[ "$SHA" =~ ^[0-9a-f]{12,40}$ ]] || { echo "deploy probe red — CURRENT_SHA 형식" >&2; exit 1; }
IMAGE="colab-v2/core-api:dev-$SHA"
docker image inspect "$IMAGE" >/dev/null 2>&1 || { echo "deploy probe red — 현재 SHA 이미지 부재" >&2; exit 1; }
NAME="${COLAB_OPS_CONTAINER_NAME:-colab-ops-deploy-verification-$$}"
exec "$(dirname "${BASH_SOURCE[0]}")/docker-run.sh" "$NAME" "${COLAB_OPS_DOCKER_TIMEOUT:-110}" -- \
  --rm --user 0 --network host -e AWS_DEFAULT_REGION=ap-northeast-2 -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$REPO:/repo:ro" -v "$STATE:/state:ro" -v "$SECRETS:/etc/colab:ro" "${EXTRA_MOUNTS[@]}" \
  -w /repo/services/core-api --entrypoint python "$IMAGE" "${DOCTOR[@]}" --env dev \
  --endpoint https://d31zgpff2091oh.cloudfront.net \
  --db-url-file /etc/colab/platform-owner-db.url --ai-db-url-file /etc/colab/ai-owner-db.url \
  --app-base http://127.0.0.1:8000 --worker-base http://127.0.0.1:8001 \
  --viz-base http://127.0.0.1:8100 --ai-base http://127.0.0.1:8200 \
  --bucket colab-platform-data-dev --web-bucket colab-platform-web-dev --state-dir /state
