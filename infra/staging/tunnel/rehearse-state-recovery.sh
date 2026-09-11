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
TARGET="cloudflare_zero_trust_tunnel_cloudflared_config.staging"
MODE=ephemeral
BUNDLE=""
APPROVED_SHA=""

ready_red() { echo "::gate-readiness-failure::gate=is4-recovery|detail=$1" >&2; exit "$READINESS_EXIT"; }
case "${1:-}" in
  "") ;;
  --prepare)
    [ "$#" -eq 2 ] || ready_red "--prepare에는 새 bundle 경로 하나가 필요하다"
    MODE=prepare; BUNDLE="$2"
    ;;
  --apply-approved)
    [ "$#" -eq 4 ] && [ "${3:-}" = "--plan-sha256" ] || ready_red "승인 bundle과 --plan-sha256가 필요하다"
    MODE=apply; BUNDLE="$2"; APPROVED_SHA="$4"
    [[ "$APPROVED_SHA" =~ ^[0-9a-f]{64}$ ]] || ready_red "승인 plan sha256 형식이 틀렸다"
    ;;
  *) ready_red "알 수 없는 실행 모드다" ;;
esac

[ -r "$JUDGE" ] || ready_red "recovery plan 판정부가 없다"
command -v docker >/dev/null 2>&1 || ready_red "docker가 없다 — 새 Terraform 컨테이너를 세울 수 없다"

if [ "$MODE" = apply ]; then
  SCRATCH="$BUNDLE"
else
  if [ "$MODE" = prepare ]; then
    [ ! -e "$BUNDLE" ] && [ ! -L "$BUNDLE" ] || ready_red "prepare bundle 경로가 이미 존재한다"
    mkdir -m 0700 -- "$BUNDLE"
    SCRATCH="$BUNDLE"
  else
    SCRATCH="$(mktemp -d -p "${TMPDIR:-/tmp}" is4-recovery-XXXXXX)"
    chmod 0700 "$SCRATCH"
    trap 'rm -rf "$SCRATCH"' EXIT INT TERM
  fi
fi

[ -f "$ENV_FILE" ] && [ ! -L "$ENV_FILE" ] || ready_red "Cloudflare 자격증명 env 파일이 없다"
[ "$(stat -c '%a:%u' "$ENV_FILE" 2>/dev/null)" = "600:$HOST_UID" ] \
  || ready_red "Cloudflare 자격증명 env 파일은 현재 사용자 소유 0600이어야 한다"
# 값은 출력하지 않고 필요한 셋만 Terraform process env로 옮긴다.
# shellcheck source=/dev/null
set -a; . "$ENV_FILE"; set +a
: "${CF_API_TOKEN:?CF_API_TOKEN이 없다}"
: "${CF_ACCOUNT_ID:?CF_ACCOUNT_ID가 없다}"
: "${CF_TUNNEL_ID:?CF_TUNNEL_ID가 없다}"
export TF_VAR_cloudflare_api_token="$CF_API_TOKEN"
export TF_VAR_cloudflare_account_id="$CF_ACCOUNT_ID"
export TF_VAR_tunnel_id="$CF_TUNNEL_ID"

RESOLVED_IMAGE="$(docker image inspect --format '{{index .RepoDigests 0}}' "$IMAGE" 2>/dev/null || true)"
[[ "$RESOLVED_IMAGE" == *@sha256:* ]] || ready_red "Terraform image digest를 고정할 수 없다"
TF_VERSION="$(docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
  --user "$HOST_UID:$HOST_GID" --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --entrypoint /bin/sh "$RESOLVED_IMAGE" -c 'terraform version -json | sed -n '\''s/.*"terraform_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'\''' 2>/dev/null || true)"
[ "$TF_VERSION" = "1.9.8" ] || ready_red "Terraform 실행 버전이 1.9.8이 아니다"

if [ "$MODE" = apply ]; then
  python3 "$JUDGE" --verify-bundle "$BUNDLE" "$APPROVED_SHA" "$SOURCE" "$RESOLVED_IMAGE" "$TF_VERSION" \
    || { echo "is4-recovery red — 승인 bundle 검증 실패" >&2; exit 1; }
fi

tf() {
  docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
    --user "$HOST_UID:$HOST_GID" --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    -e TF_IN_AUTOMATION=1 -e TF_INPUT=0 \
    -e TF_VAR_cloudflare_api_token -e TF_VAR_cloudflare_account_id -e TF_VAR_tunnel_id \
    -v "$SCRATCH:/work" -w /work "$RESOLVED_IMAGE" "$@"
}

if [ "$MODE" = apply ]; then
  tf init -input=false -no-color -lockfile=readonly >"$SCRATCH/preapply-init.log" 2>&1 \
    || { echo "is4-recovery red — provider lock 재검증 실패" >&2; exit 1; }
  chmod 0600 "$SCRATCH/preapply-init.log"
  set +e
  tf plan -refresh-only -detailed-exitcode -input=false -no-color -out=approval-drift.tfplan >"$SCRATCH/approval-drift.log" 2>&1
  DRIFT_RC=$?
  set -e
  chmod 0600 "$SCRATCH"/approval-drift.* 2>/dev/null || true
  [ "$DRIFT_RC" -eq 0 ] || { echo "is4-recovery red — 승인 뒤 remote/state drift가 있어 새 bundle 승인이 필요하다" >&2; exit 1; }
  tf show -json final.tfplan >"$SCRATCH/preapply-plan.json" 2>"$SCRATCH/preapply-show.log" \
    || { echo "is4-recovery red — saved plan 재판독 실패" >&2; exit 1; }
  chmod 0600 "$SCRATCH"/preapply-*.json "$SCRATCH"/preapply-*.log 2>/dev/null || true
  python3 "$JUDGE" "$SCRATCH/preapply-plan.json" \
    || { echo "is4-recovery red — saved plan 재판정 실패" >&2; exit 1; }
  install -m 0600 /dev/null "$SCRATCH/apply-attempted"
  printf '%s\n' "$APPROVED_SHA" >"$SCRATCH/apply-attempted"
  if ! tf apply -input=false -no-color final.tfplan >"$SCRATCH/apply.log" 2>&1; then
    echo "is4-recovery red — 승인 plan 적용 시도 실패(같은 plan 재사용 금지)" >&2
    exit 1
  fi
  set +e
  tf plan -detailed-exitcode -input=false -no-color -out=post-apply.tfplan >"$SCRATCH/post-apply.log" 2>&1
  POST_RC=$?
  set -e
  chmod 0600 "$SCRATCH"/apply-attempted "$SCRATCH"/apply.log "$SCRATCH"/post-apply.log "$SCRATCH"/post-apply.tfplan 2>/dev/null || true
  [ "$POST_RC" -eq 0 ] || { echo "is4-recovery red — 적용 후 plan이 literal No changes가 아니다" >&2; exit 1; }
  echo "is4-recovery green — 승인된 exact plan 1회 소비 · 후속 detailed-exitcode 0"
  exit 0
fi

# 선언 다섯 파일만 복사한다. 기존 terraform.tfstate/.backup/.terraform은 이 경계를 건너지 않는다.
for name in versions.tf variables.tf tunnel.tf terraform.tfvars.example .terraform.lock.hcl; do
  [ -r "$SOURCE/$name" ] || ready_red "선언 파일이 없다: $name"
  install -m 0600 "$SOURCE/$name" "$SCRATCH/$name"
done
if find "$SCRATCH" -maxdepth 1 \( -name 'terraform.tfstate*' -o -name '.terraform' \) | grep -q .; then
  echo "is4-recovery red — 빈 scratch에 기존 state/plugin이 들어왔다" >&2
  exit 1
fi
if ! tf init -input=false -no-color >"$SCRATCH/init.log" 2>&1; then
  echo "is4-recovery red — terraform init 실패(세부 로그는 비밀 보호를 위해 출력하지 않음)" >&2
  exit 1
fi
if ! docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
  --user "$HOST_UID:$HOST_GID" --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e TF_IN_AUTOMATION=1 -e TF_INPUT=0 \
  -e TF_VAR_cloudflare_api_token -e TF_VAR_cloudflare_account_id -e TF_VAR_tunnel_id \
  -v "$SCRATCH:/work" -w /work --entrypoint /bin/sh "$RESOLVED_IMAGE" -c \
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
tf show -json first.tfplan >"$SCRATCH/first-plan.json" 2>"$SCRATCH/show.log" \
  || { echo "is4-recovery red — terraform show 실패" >&2; exit 1; }
chmod 0600 "$SCRATCH"/* 2>/dev/null || true
python3 "$JUDGE" "$SCRATCH/first-plan.json"
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
[ "$FINAL_RC" -eq 2 ] || { echo "is4-recovery red — 최종 plan 실패(exit $FINAL_RC)" >&2; exit 1; }
tf show -json final.tfplan >"$SCRATCH/final-plan.json" 2>"$SCRATCH/final-show.log" \
  || { echo "is4-recovery red — 최종 plan 판독 실패" >&2; exit 1; }
chmod 0600 "$SCRATCH"/* 2>/dev/null || true
python3 "$JUDGE" "$SCRATCH/final-plan.json"

if [ "$MODE" = prepare ]; then
  [ -f "$SCRATCH/terraform.tfstate" ] || { echo "is4-recovery red — 보존할 state가 없다" >&2; exit 1; }
  PLAN_SHA="$(sha256sum "$SCRATCH/final.tfplan" | cut -d' ' -f1)"
  STATE_SHA="$(sha256sum "$SCRATCH/terraform.tfstate" | cut -d' ' -f1)"
  python3 - "$SCRATCH" "$TARGET" "$PLAN_SHA" "$STATE_SHA" "$RESOLVED_IMAGE" "$TF_VERSION" <<'PY'
import hashlib, json, pathlib, sys
b = pathlib.Path(sys.argv[1])
names = ("versions.tf", "variables.tf", "tunnel.tf", "terraform.tfvars.example", ".terraform.lock.hcl")
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {"schema":"colab-is4-recovery/1", "address":sys.argv[2],
            "plan_sha256":sys.argv[3], "state_sha256":sys.argv[4],
            "terraform_image":sys.argv[5], "terraform_version":sys.argv[6],
            "declarations":{name:digest(b / name) for name in names}}
(b / "manifest.json").write_text(json.dumps(manifest, sort_keys=True)+"\n", encoding="utf-8")
PY
  chmod 0600 "$SCRATCH/manifest.json"
  echo "::gate-readiness-failure::gate=is4-recovery|detail=승인 검토용 bundle 보존 완료 · plan_sha256=$PLAN_SHA · 원격 resource apply 0" >&2
  exit "$READINESS_EXIT"
fi
echo "::gate-readiness-failure::gate=is4-recovery|detail=값 동일 sensitivity metadata 1건을 원격 apply해야 literal No changes가 된다. 승인 전이라 apply 0회로 중단한다." >&2
exit "$READINESS_EXIT"
