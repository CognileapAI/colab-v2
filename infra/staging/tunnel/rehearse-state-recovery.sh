#!/usr/bin/env bash
# IS4 맨몸 리허설 — 기존 state/plugin/terraform을 재사용하지 않고 원격 변경 0으로 복구한다.
set -euo pipefail

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
SOURCE="$ROOT/infra/staging/tunnel"
JUDGE="$SOURCE/validate-recovery-plan.py"
ENV_FILE="${COLAB_IS4_ENV_FILE:-${HOME:-}/.colab-v2-staging.env}"
IMAGE="${COLAB_IS4_TERRAFORM_IMAGE:-hashicorp/terraform:1.9.8}"
READINESS_EXIT=78
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"

ready_red() { echo "::gate-readiness-failure::gate=is4-recovery|detail=$1" >&2; exit "$READINESS_EXIT"; }
[ -r "$ENV_FILE" ] || ready_red "Cloudflare 자격증명 env 파일이 없다"
[ -x "$JUDGE" ] || ready_red "recovery plan 판정부가 없다"
command -v docker >/dev/null 2>&1 || ready_red "docker가 없다 — 새 Terraform 컨테이너를 세울 수 없다"

# 레포 밖 0600 파일의 기존 관례. 값은 출력하지 않고 필요한 셋만 Terraform process env로 옮긴다.
# shellcheck source=/dev/null
set -a; . "$ENV_FILE"; set +a
: "${CF_API_TOKEN:?CF_API_TOKEN이 없다}"
: "${CF_ACCOUNT_ID:?CF_ACCOUNT_ID가 없다}"
: "${CF_TUNNEL_ID:?CF_TUNNEL_ID가 없다}"
export TF_VAR_cloudflare_api_token="$CF_API_TOKEN"
export TF_VAR_cloudflare_account_id="$CF_ACCOUNT_ID"
export TF_VAR_tunnel_id="$CF_TUNNEL_ID"

SCRATCH="$(mktemp -d -p "${TMPDIR:-/tmp}" is4-recovery-XXXXXX)"
chmod 0700 "$SCRATCH"
trap 'rm -rf "$SCRATCH"' EXIT INT TERM

# 선언 네 파일만 복사한다. 기존 terraform.tfstate/.backup/.terraform은 이 경계를 건너지 않는다.
for name in versions.tf variables.tf tunnel.tf terraform.tfvars.example; do
  [ -r "$SOURCE/$name" ] || ready_red "선언 파일이 없다: $name"
  install -m 0644 "$SOURCE/$name" "$SCRATCH/$name"
done
if find "$SCRATCH" -maxdepth 1 \( -name 'terraform.tfstate*' -o -name '.terraform' \) | grep -q .; then
  echo "is4-recovery red — 빈 scratch에 기존 state/plugin이 들어왔다" >&2
  exit 1
fi

tf() {
  docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
    --user "$HOST_UID:$HOST_GID" \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    -e TF_IN_AUTOMATION=1 -e TF_INPUT=0 \
    -e TF_VAR_cloudflare_api_token -e TF_VAR_cloudflare_account_id -e TF_VAR_tunnel_id \
    -v "$SCRATCH:/work" -w /work "$IMAGE" "$@"
}

if ! tf init -input=false -no-color >"$SCRATCH/init.log" 2>&1; then
  echo "is4-recovery red — terraform init 실패(세부 로그는 비밀 보호를 위해 출력하지 않음)" >&2
  # init은 원격 자격증명을 쓰지 않는다. 오류 종류만 허용 목록으로 뽑아 진단 가능하게 한다.
  grep -Ei 'error:|permission denied|read-only|failed|could not|cannot|not found' \
    "$SCRATCH/init.log" | head -n 8 | sed -E 's/[[:alnum:]_=-]{24,}/[redacted]/g' >&2 || true
  exit 1
fi
# resource ID를 호스트 process argv에 값으로 싣지 않는다. 컨테이너 안의 env에서 조립한다.
if ! docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
  --user "$HOST_UID:$HOST_GID" \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e TF_IN_AUTOMATION=1 -e TF_INPUT=0 \
  -e TF_VAR_cloudflare_api_token -e TF_VAR_cloudflare_account_id -e TF_VAR_tunnel_id \
  -v "$SCRATCH:/work" -w /work --entrypoint /bin/sh "$IMAGE" -c \
  'terraform import -input=false -no-color cloudflare_zero_trust_tunnel_cloudflared_config.staging "$TF_VAR_cloudflare_account_id/$TF_VAR_tunnel_id"' \
  >"$SCRATCH/import.log" 2>&1; then
  echo "is4-recovery red — terraform import 실패(세부 로그는 비밀 보호를 위해 출력하지 않음)" >&2
  exit 1
fi

set +e
tf plan -input=false -no-color -out=first.tfplan >"$SCRATCH/first-plan.log" 2>&1
PLAN_RC=$?
set -e
[ "$PLAN_RC" -eq 0 ] || [ "$PLAN_RC" -eq 2 ] || { echo "is4-recovery red — 첫 plan 실패" >&2; exit 1; }
if ! tf show -json first.tfplan >"$SCRATCH/first-plan.json" 2>"$SCRATCH/show.log"; then
  echo "is4-recovery red — terraform show 실패(세부 로그는 비밀 보호를 위해 출력하지 않음)" >&2
  exit 1
fi
chmod 0600 "$SCRATCH/first-plan.json"
"$JUDGE" "$SCRATCH/first-plan.json"

# refresh-only는 scratch state만 갱신하며 Cloudflare resource 변경을 계획/적용하지 않는다.
if ! tf apply -refresh-only -auto-approve -input=false -no-color >"$SCRATCH/refresh-only.log" 2>&1; then
  echo "is4-recovery red — scratch state refresh-only 실패(원격 resource apply는 실행하지 않음)" >&2
  exit 1
fi
set +e
tf plan -detailed-exitcode -input=false -no-color -out=final.tfplan >"$SCRATCH/final-plan.log" 2>&1
FINAL_RC=$?
set -e
if [ "$FINAL_RC" -eq 0 ]; then
  echo "is4-recovery green — 새 Terraform 1.9.8 컨테이너 · 빈 state에서 import · 원격 resource apply 0 · 최종 No changes"
  exit 0
fi
if [ "$FINAL_RC" -eq 2 ]; then
  if ! tf show -json final.tfplan >"$SCRATCH/final-plan.json" 2>"$SCRATCH/final-show.log"; then
    echo "is4-recovery red — 최종 plan 판독 실패" >&2
    exit 1
  fi
  chmod 0600 "$SCRATCH/final-plan.json"
  "$JUDGE" "$SCRATCH/final-plan.json"
  echo "::gate-readiness-failure::gate=is4-recovery|detail=값 동일 sensitivity metadata 1건을 원격 apply해야 literal No changes가 된다. 승인 전이라 apply 0회로 중단한다." >&2
  exit "$READINESS_EXIT"
fi
echo "is4-recovery red — 최종 plan 실패(exit $FINAL_RC)" >&2
exit 1
