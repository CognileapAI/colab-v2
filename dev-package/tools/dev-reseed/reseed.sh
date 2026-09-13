#!/usr/bin/env bash
# dev 재생성 진입점 — 「데이터 전체 초기화하고 다시 셋팅해줘」 한 마디가 끝까지 가는 자리.
#
# 고정 순서 10단계 —
#   preflight → deploy → reset → bootstrap → up → s3 → prelude → seed → verify → report
#
# 절차의 원본 = `dev-package/sessions/DR-2-runbook.md`(2026-09-13 사람이 밟은 순서).
# 승인 = **dev 한정 상시 승인**(`.claude/rules/deploy.md` 11번 증보 문단 · 2026-09-14 개정).
#        게이트 넷 충족 시 회차별 GO 불요. staging·prod 는 무변(매회 GO)이고 이 도구가 돌지 않는다.
# 경계 = dev 하나. `_ops/` 무접촉. DB 직접 쓰기는 prelude 의 SQL 선행 4단계뿐이다.
#
# 사용:
#   bash dev-package/tools/dev-reseed/reseed.sh --dry-run
#   bash dev-package/tools/dev-reseed/reseed.sh --from reset
#
# 값은 환경변수로 받는다(레포에 절대경로·주소·비밀을 적지 않는다) —
#   COLAB_DEV_SSH · COLAB_DEV_KEY_FILE · COLAB_DEV_SECRETS_DIR · COLAB_REF_ROOT · COLAB_DEV_URL
#   RESEED_ACCOUNT_ID · RESEED_ACCOUNT_EMAIL · RESEED_ACCOUNT_NAME · RESEED_ACCOUNT_ROLE
set -euo pipefail

RESEED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$RESEED_DIR/../../.." && pwd)"

# ── 고정 값 ──────────────────────────────────────────────────────────────
STAGES_ALL=(preflight deploy reset bootstrap up s3 prelude seed verify report)

# 근거: R-DEV-RESET §11-1 ⑶ — 버킷·리전은 `dev.env` 가 아니라 compose 의 리터럴이다.
#       미지정 상태의 `s3-plan` 은 exit 2 로 아무것도 하지 않는다.
S3_BUCKET="${COLAB_CORE_S3_BUCKET:-colab-platform-data-dev}"
S3_REGION="${COLAB_CORE_S3_REGION:-ap-northeast-2}"
WEB_BUCKET="${COLAB_WEB_S3_BUCKET:-colab-platform-web-dev}"

SECRETS_DIR="${COLAB_DEV_SECRETS_DIR:-/etc/colab}"
LAB_ID="${RESEED_LAB_ID:-00000000000000000000HYMETS}"
RESEED_ACCOUNT_ROLE="${RESEED_ACCOUNT_ROLE:-연구원}"

EXPECT_DATASETS="${COLAB_RESEED_EXPECT_DATASETS:-28}"
EXPECT_EDGES="${COLAB_RESEED_EXPECT_EDGES:-18}"
EXPECT_PROJECTS="${COLAB_RESEED_EXPECT_PROJECTS:-4}"

MIN_MEM_MIB="${COLAB_RESEED_MIN_MEM_MIB:-4096}"
MIN_DISK_GIB="${COLAB_RESEED_MIN_DISK_GIB:-20}"

# 정본 md 4건의 자리(참조자료 뿌리 기준 · R-DATA-CANON §2 ㈎ ⓐ).
REF_MD_RELS=(
  "01.level-data/01.precipitation/DATASETS.md"
  "01.level-data/02.vegetation/DATASETS.md"
  "01.level-data/03.drought/DATASETS.md"
  "02.File-format/DATASETS.md"
)

# 시크릿 파일 이름만 본다 — 값은 읽지 않는다(`infra/dev/README.md` 표 ＋ 런북 §3·§5 마운트).
SECRET_FILE_NAMES=(
  master.url platform-owner-db.url ai-owner-db.url
  core-database.url pipeline-db.url ai-db.url account-admin-database.url
  subjects.json credentials.json
)

# ── 인자 ─────────────────────────────────────────────────────────────────
DRY_RUN=0
FROM_STAGE=preflight
RUN_DIR=""
TARGET_REF="${COLAB_RESEED_TARGET_REF:-origin/main}"
TARGET_SHA=""
ACCOUNTS_FILE=""
OPERATOR_PASSWORD_FILE="${COLAB_RESEED_OPERATOR_PASSWORD_FILE:-}"
DEV_URL="${COLAB_DEV_URL:-}"
MD_ROOT=""
SEED_WORK_DIR=""

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  cat <<'USAGE'

인자:
  --from <단계>                 그 단계부터 재개(기본 preflight). 단계 이름은 위 10개.
  --dry-run                     실행할 명령을 전부 찍고 dev·AWS·docker 를 건드리지 않는다.
  --run-dir <자리>              실행 자리. 기본 = $COLAB_JOB_DIR/tmp/dev-reseed/<시각>
                                또는 dev-package/reports/dev-reseed-runs/<시각>(무시 대상).
  --target-ref <ref>            배포 대상(기본 origin/main).
  --accounts-file <파일>        러너에 넘길 계정 파일(러너가 그 인자를 받을 때만 넘긴다).
  --operator-password-file <파일>  prelude ③ 의 초기 비밀번호(0600 · 10자 이상).
  --base-url <주소>             dev 주소(기본 $COLAB_DEV_URL).
  --md-root <자리>              정본 md 뿌리(기본 = 참조자료 뿌리).
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --from) FROM_STAGE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --run-dir) RUN_DIR="$2"; shift 2 ;;
    --target-ref) TARGET_REF="$2"; shift 2 ;;
    --accounts-file) ACCOUNTS_FILE="$2"; shift 2 ;;
    --operator-password-file) OPERATOR_PASSWORD_FILE="$2"; shift 2 ;;
    --base-url) DEV_URL="$2"; shift 2 ;;
    --md-root) MD_ROOT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "모르는 인자: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# `--from` 부터 끝까지가 이번 실행의 단계 집합이다.
STAGES=()
seen=0
for s in "${STAGES_ALL[@]}"; do
  [ "$s" = "$FROM_STAGE" ] && seen=1
  [ "$seen" = 1 ] && STAGES+=("$s")
done
if [ "${#STAGES[@]}" -eq 0 ]; then
  echo "모르는 단계: $FROM_STAGE (${STAGES_ALL[*]})" >&2; exit 2
fi

stage_enabled() {
  local want="$1" s
  for s in "${STAGES[@]}"; do [ "$s" = "$want" ] && return 0; done
  return 1
}

# ── 실행 자리 ────────────────────────────────────────────────────────────
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
if [ -z "$RUN_DIR" ]; then
  if [ -n "${COLAB_JOB_DIR:-}" ]; then
    RUN_DIR="$COLAB_JOB_DIR/tmp/dev-reseed/$RUN_ID"
  else
    RUN_DIR="$REPO_ROOT/dev-package/reports/dev-reseed-runs/$RUN_ID"
  fi
fi
mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"

# 레포 안이면 뿌리 기준 상대경로, 밖이면 있는 그대로 — `../../..` 사슬을 찍지 않는다.
relpath() {
  python3 -c 'import os,sys
p, root = sys.argv[1], sys.argv[2]
r = os.path.relpath(p, root)
print(p if r.startswith("..") else r)' "$1" "$REPO_ROOT"
}

# 참조자료·작업 자리 기본값.
MD_ROOT="${MD_ROOT:-${COLAB_REF_ROOT:-}}"
SEED_WORK_DIR="${COLAB_SEED_WORK_DIR:-$REPO_ROOT/dev-package/tools/dev-seed/.work}"

# shellcheck source=lib.sh
. "$RESEED_DIR/lib.sh"
# shellcheck source=preflight.sh
. "$RESEED_DIR/preflight.sh"
# shellcheck source=stages.sh
. "$RESEED_DIR/stages.sh"

# 실행 전 한 줄 — 무엇을 어디에 쓰는지 먼저 밝힌다.
CURRENT_STAGE=start
STAGE_LOG="$RUN_DIR/logs/start.log"
log "dev 재생성 — 단계 ${STAGES[*]}"
log "실행 자리 = $(relpath "$RUN_DIR") · dry-run = $DRY_RUN · 대상 ref = $TARGET_REF"
if [ "$DRY_RUN" != 1 ]; then
  : "${COLAB_DEV_SSH:?COLAB_DEV_SSH 가 필요하다 (예: ec2-user@<IP>)}"
  : "${COLAB_DEV_KEY_FILE:?COLAB_DEV_KEY_FILE 이 필요하다 (0600 개인키)}"
  : "${DEV_URL:?--base-url 또는 COLAB_DEV_URL 이 필요하다}"
else
  # dry-run 은 값이 하나도 없어도 끝까지 간다 — 빈 자리는 **이름 그대로** 찍어 무엇을 줘야 하는지 보인다.
  COLAB_DEV_SSH="${COLAB_DEV_SSH:-<COLAB_DEV_SSH>}"
  COLAB_DEV_KEY_FILE="${COLAB_DEV_KEY_FILE:-<COLAB_DEV_KEY_FILE>}"
  DEV_URL="${DEV_URL:-<COLAB_DEV_URL>}"
  COLAB_REF_ROOT="${COLAB_REF_ROOT:-<COLAB_REF_ROOT>}"
  MD_ROOT="${MD_ROOT:-<COLAB_REF_ROOT>}"
  TARGET_SHA="${TARGET_SHA:-<대상 sha · preflight 가 해석>}"
fi
export COLAB_DEV_SSH COLAB_DEV_KEY_FILE

# ── 순차 실행 ────────────────────────────────────────────────────────────
# 단계 하나가 비영 종료하면 **그 자리에서 멈춘다** — 단계 이름과 로그 경로를 낸다.
FAILED_STAGE=""
for s in "${STAGES[@]}"; do
  [ "$s" = report ] && continue     # report 는 마지막에 한 번만 돈다
  stage_begin "$s"
  rc=0
  case "$s" in
    preflight) stage_preflight || rc=$? ;;
    deploy)    stage_deploy    || rc=$? ;;
    reset)     stage_reset     || rc=$? ;;
    bootstrap) stage_bootstrap || rc=$? ;;
    up)        stage_up        || rc=$? ;;
    s3)        stage_s3        || rc=$? ;;
    prelude)   stage_prelude   || rc=$? ;;
    seed)      stage_seed      || rc=$? ;;
    verify)    stage_verify    || rc=$? ;;
  esac
  stage_end "$rc"
  if [ "$rc" -ne 0 ]; then
    FAILED_STAGE="$s"
    break
  fi
done

# report 는 실패했을 때도 돈다 — 어디서 멈췄는지가 결과다.
if stage_enabled report; then
  stage_begin report
  rrc=0
  stage_report || rrc=$?
  stage_end "$rrc"
  [ "$rrc" -eq 0 ] || { FAILED_STAGE="${FAILED_STAGE:-report}"; }
fi

if [ -n "$FAILED_STAGE" ]; then
  printf '⛔ 단계 %s 에서 멈췄다 — 로그 %s\n' \
    "$FAILED_STAGE" "$(relpath "$RUN_DIR/logs/$FAILED_STAGE.log")" >&2
  exit 1
fi
printf '재생성 %s — 결과 %s\n' \
  "$([ "$DRY_RUN" = 1 ] && echo 'dry-run 완료' || echo '완료')" "$(relpath "$RUN_DIR/result.json")"
