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
# preflight 는 **언제나 돈다** — 읽기 전용이고, 배포 대상 sha 를 해석하는 자리가 거기 하나뿐이다.
# `--from` 은 **바꾸는 단계 여덟** 중 시작 지점만 고른다.
#
# 사용:
#   bash dev-package/tools/dev-reseed/reseed.sh --dry-run
#   bash dev-package/tools/dev-reseed/reseed.sh --preflight-only
#   bash dev-package/tools/dev-reseed/reseed.sh --rehearse
#   bash dev-package/tools/dev-reseed/reseed.sh --from reset
#
# 값은 환경변수로 받는다(레포에 절대경로·주소·비밀을 적지 않는다) —
#   COLAB_DEV_SSH · COLAB_DEV_KEY_FILE · COLAB_REF_ROOT · COLAB_DEV_URL
#   COLAB_RESEED_EC2_SECRETS_DIR(기본 /etc/colab) — **EC2 위 경로**다
#   RESEED_ACCOUNT_ID · RESEED_ACCOUNT_EMAIL · RESEED_ACCOUNT_NAME · RESEED_ACCOUNT_ROLE
#
# ⚠ **`COLAB_DEV_SECRETS_DIR` 를 읽지 않는다.** 그 이름은 운영자 기계의 `dev-operator.env` 에서
#   **개발 기계의 로컬 폴더**를 가리키고, `infra/dev/README.md` 의 같은 이름은 EC2 의 `dev.env`
#   안에서 **EC2 경로**를 가리킨다 — 한 이름이 두 뜻이다. 이 도구가 그 값을 원격 경로로 읽으면
#   EC2 에 없는 호스트 경로를 `docker -v` 로 마운트한다(DR-4 회차 §5 ⑴ 실측).
#   그래서 원격 경로의 출처를 `COLAB_RESEED_EC2_SECRETS_DIR` 하나로 분리했다.
set -euo pipefail

RESEED_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$RESEED_DIR/../../.." && pwd)"

# ── 고정 값 ──────────────────────────────────────────────────────────────
STAGES_ALL=(preflight deploy reset bootstrap up s3 prelude seed verify report)
# 바꾸는 단계 여덟. `--from` 은 **이 중에서** 어디부터 시작할지만 고른다.
# preflight 와 report 는 그 바깥이다 — preflight 는 읽기 전용이라 언제나 돌고,
# report 는 결과를 적는 자리라 실패해도 돈다.
STAGES_MUTATING=(deploy reset bootstrap up s3 prelude seed verify)

# 근거: R-DEV-RESET §11-1 ⑶ — 버킷·리전은 `dev.env` 가 아니라 compose 의 리터럴이다.
#       미지정 상태의 `s3-plan` 은 exit 2 로 아무것도 하지 않는다.
S3_BUCKET="${COLAB_CORE_S3_BUCKET:-colab-platform-data-dev}"
S3_REGION="${COLAB_CORE_S3_REGION:-ap-northeast-2}"
WEB_BUCKET="${COLAB_WEB_S3_BUCKET:-colab-platform-web-dev}"

# EC2 위 시크릿 폴더. `preflight` ⑻ 이 `stat` 하는 자리이자 `reset`·`prelude` 가 `docker -v` 로
# 마운트하는 자리다 — **이름 하나가 원격 경로만 가리킨다**(머리말 ⚠ 참조).
EC2_SECRETS_DIR="${COLAB_RESEED_EC2_SECRETS_DIR:-/etc/colab}"
LAB_ID="${RESEED_LAB_ID:-00000000000000000000HYMETS}"

# 첫 계정 신원. 기본값의 원본은 **prelude ① 이 실행하는 SQL** 이다 — 사본을 두지 않고 실행 때 읽는다.
# 왜 = ① `provision-lab.sql` 이 고정 id 로 `d1_account` 를 이미 심고 `d1_account` 에는
#   `UNIQUE (lab_id, email)` 이 있다(`db/platform/schema.sql`). ② `provision-account.sql` 에
#   **새 ULID** 를 주면 id 충돌이 안 나 삽입이 진행되고 그 유일성에 걸려 prelude 가 죽는다
#   (DR-4 회차 §4 실측 · 그래서 그 회차는 새 ULID 를 버리고 ① 의 값을 썼다).
#   같은 id 를 주면 ② 의 `ON CONFLICT (id) DO NOTHING` 이 먼저 걸려 **멱등**이다.
# 값을 여기에 다시 적지 않는다 — 두 벌이 되면 SQL 이 바뀔 때 갈린다.
PROVISION_LAB_SQL="${COLAB_RESEED_PROVISION_LAB_SQL:-$REPO_ROOT/infra/staging/provision-lab.sql}"
# 못 읽으면 **빈 값으로 둔다**(지어내지 않는다). 빈 값은 prelude 의 값 점검에서 이름을 대고 멈춘다.
_lab_account_row="$(python3 - "$PROVISION_LAB_SQL" <<'PY' 2>/dev/null || true
import re, sys
try:
    src = open(sys.argv[1], encoding="utf-8").read()
except OSError:
    raise SystemExit(1)
m = re.search(
    r"INSERT\s+INTO\s+d1_account\s*\(\s*id\s*,\s*lab_id\s*,\s*name\s*,\s*email\s*\)\s*VALUES\s*"
    r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)", src)
if not m:
    raise SystemExit(1)
# 역할도 같은 파일에서 읽는다 — ② 를 건너뛰면 ① 이 심은 역할이 실물이므로, 다른 값을 찍으면
# `--preflight-only` 가 사실과 다른 신원을 보고하게 된다.
r = re.search(
    r"INSERT\s+INTO\s+d2_member_role\s*\(\s*account_id\s*,\s*lab_id\s*,\s*role\s*\)\s*VALUES\s*"
    r"\(\s*'%s'\s*,\s*'[^']*'\s*,\s*'([^']*)'\s*\)" % re.escape(m.group(1)), src)
print("\t".join(m.groups()) + "\t" + (r.group(1) if r else ""))
PY
)"
IFS=$'\t' read -r PROVISION_LAB_ACCOUNT_ID _sql_lab_id _sql_account_name _sql_account_email _sql_account_role \
  <<<"${_lab_account_row:-$'\t\t\t\t'}"
RESEED_ACCOUNT_ID="${RESEED_ACCOUNT_ID:-$PROVISION_LAB_ACCOUNT_ID}"
RESEED_ACCOUNT_NAME="${RESEED_ACCOUNT_NAME:-$_sql_account_name}"
RESEED_ACCOUNT_EMAIL="${RESEED_ACCOUNT_EMAIL:-$_sql_account_email}"
RESEED_ACCOUNT_ROLE="${RESEED_ACCOUNT_ROLE:-${_sql_account_role:-연구원}}"

EXPECT_DATASETS="${COLAB_RESEED_EXPECT_DATASETS:-28}"
EXPECT_EDGES="${COLAB_RESEED_EXPECT_EDGES:-18}"
EXPECT_PROJECTS="${COLAB_RESEED_EXPECT_PROJECTS:-4}"

MIN_MEM_MIB="${COLAB_RESEED_MIN_MEM_MIB:-4096}"
MIN_DISK_GIB="${COLAB_RESEED_MIN_DISK_GIB:-20}"

# 계획 생성기 자리. preflight ⑽ 과 seed ① 이 **같은 값**을 쓴다 — 둘이 갈리면 preflight 가
# 판정한 생성기와 실제로 도는 생성기가 달라진다. 픽스처가 대역을 끼우는 자리이기도 하다.
BUILD_PLAN_PY="${COLAB_RESEED_BUILD_PLAN:-$REPO_ROOT/dev-package/tools/dev-seed/build_plan.py}"

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
PREFLIGHT_ONLY=0
REHEARSE=0
RUN_DIR=""
TARGET_REF="${COLAB_RESEED_TARGET_REF:-origin/develop}"
TARGET_SHA=""
ACCOUNTS_FILE=""
OPERATOR_PASSWORD_FILE="${COLAB_RESEED_OPERATOR_PASSWORD_FILE:-}"
DEV_URL="${COLAB_DEV_URL:-}"
MD_ROOT=""
SEED_WORK_DIR=""

usage() {
  sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  cat <<'USAGE'

계정 신원 기본값:
  RESEED_ACCOUNT_ID · _EMAIL · _NAME · _ROLE 을 주지 않으면 prelude ① 이 실행하는
  infra/staging/provision-lab.sql 의 `INSERT INTO d1_account`(＋ d2_member_role 의 역할)
  값을 **실행 때 읽어** 쓴다
  (자리는 COLAB_RESEED_PROVISION_LAB_SQL 로 바꾼다). 사본을 두지 않는 이유 =
  d1_account 에 UNIQUE (lab_id, email) 이 있어 새 ULID 를 주면 prelude ② 가 유일성 위반으로
  죽는다. id 가 ① 의 값과 같으면 prelude ② 는 **건너뛴다**(2026-09-13 회차와 같은 순서 ·
  d2_permission_switch 0행 유지). 다른 id 를 주면 ② 를 돌린다.

인자:
  --from <단계>                 **바꾸는 단계** 중 어디부터 시작할지 고른다
                                (deploy·reset·bootstrap·up·s3·prelude·seed·verify · 기본 deploy).
                                ⚠ preflight 는 이 인자와 무관하게 **언제나 먼저 돈다** — 읽기 전용이고,
                                배포 대상 sha 를 해석하는 자리가 거기 하나뿐이라 건너뛰면
                                이미지 태그·승인 기록이 빈 sha 로 선다.
  --preflight-only              preflight 만 돌고 **바꾸는 단계는 하나도 돌지 않는다**.
                                dev 를 읽기만 한다(ssh 조회·aws sts·docker ps·파일·계획 생성 dry-run).
  --rehearse                    preflight ＋ **리허설**만 돌고 바꾸는 단계는 하나도 돌지 않는다.
                                리허설 = 원격 원시동작 10 을 실모드로 한 번씩 내 보고 응답을 판정한다 —
                                psql:master(작은따옴표 든 SQL) · ssh_script(따옴표·$·백틱 되받기) ·
                                compose ps · 마이그레이터 `alembic current` 두 체인 ·
                                초기화 도구 `--phase s3-plan`(임시 폴더 · **적용 없음**) ·
                                postgres:16-alpine 로 소유자 URL `select 1` · deploy_doctor 1회 ·
                                러너 `--phase report` · agent-browser 제목 읽기.
                                ⚠ 쓰기·정지·삭제·적용은 0건이다. 어긋난 원시동작이 있으면
                                **그 이름을 대고** 비영 종료한다. 파괴 단계 **앞에** 둔다 —
                                실모드 정지가 매번 「한 번도 실행된 적 없는 원격 줄」에서 났다.
  --dry-run                     실행할 명령을 전부 찍고 dev·AWS·docker 를 건드리지 않는다.
  --run-dir <자리>              실행 자리. 기본 = $COLAB_JOB_DIR/tmp/dev-reseed/<시각>
                                또는 dev-package/reports/dev-reseed-runs/<시각>(무시 대상).
  --target-ref <ref>            배포 대상(기본 origin/develop).
  --accounts-file <파일>        러너에 넘길 계정 파일(러너가 그 인자를 받을 때만 넘긴다).
  --operator-password-file <파일>  prelude ③ 의 초기 비밀번호(0600 · 10자 이상).
  --base-url <주소>             dev 주소(기본 $COLAB_DEV_URL).
  --md-root <자리>              정본 md 뿌리(기본 = 참조자료 뿌리).
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --from) FROM_STAGE="$2"; shift 2 ;;
    --preflight-only) PREFLIGHT_ONLY=1; shift ;;
    --rehearse) REHEARSE=1; shift ;;
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

# ── 단계 집합 ────────────────────────────────────────────────────────────
# **preflight 는 언제나 돈다.** 읽기 전용이고, 배포 대상 sha 를 해석하는 자리가 거기 하나뿐이다.
# 건너뛰면 `TARGET_SHA` 가 빈 채로 이미지 태그(`…:dev-`)·승인 기록·`--from deploy` 로 들어간다.
# `--from` 이 고르는 것은 **바꾸는 단계 중 시작 지점** 하나다.
STAGES=(preflight)
# 리허설은 **바꾸는 단계가 아니다** — preflight 와 함께 읽기 전용으로 돌고 거기서 끝난다.
if [ "$REHEARSE" = 1 ]; then
  STAGES+=(rehearse)
elif [ "$PREFLIGHT_ONLY" != 1 ]; then
  if [ "$FROM_STAGE" = preflight ]; then
    STAGES+=("${STAGES_MUTATING[@]}")
  else
    seen=0
    for s in "${STAGES_MUTATING[@]}"; do
      [ "$s" = "$FROM_STAGE" ] && seen=1
      [ "$seen" = 1 ] && STAGES+=("$s")
    done
    if [ "$seen" != 1 ]; then
      echo "모르는 단계: $FROM_STAGE (preflight ${STAGES_MUTATING[*]})" >&2; exit 2
    fi
  fi
fi
STAGES+=(report)

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
  # ⚠ 접속 값 부재로 **셸을 끝내지 않는다**(`${VAR:?}` 를 쓰지 않는다) — 그러면 단계가 하나도
  #   기록되지 않아 `result.json` 이 서지 않고, 무엇이 없어서 멈췄는지가 표준오류 한 줄에만 남는다.
  #   부재는 **preflight 미달 항목**이다. 이름을 대고 그 안에서 떨어진다(`DEV_SSH_MISSING`).
  DEV_SSH_MISSING=()
  [ -n "${COLAB_DEV_SSH:-}" ]      || DEV_SSH_MISSING+=(COLAB_DEV_SSH)
  [ -n "${COLAB_DEV_KEY_FILE:-}" ] || DEV_SSH_MISSING+=(COLAB_DEV_KEY_FILE)
  # dev 주소는 **화면을 여는 단계**(seed·verify)만 쓴다. preflight 는 쓰지 않으므로
  # `--preflight-only` 는 이 값 없이도 끝까지 검사한다.
  if stage_enabled seed || stage_enabled verify || stage_enabled rehearse; then
    : "${DEV_URL:?--base-url 또는 COLAB_DEV_URL 이 필요하다 (seed·verify 가 화면을 연다)}"
  fi
else
  # dry-run 은 값이 하나도 없어도 끝까지 간다 — 빈 자리는 **이름 그대로** 찍어 무엇을 줘야 하는지 보인다.
  COLAB_DEV_SSH="${COLAB_DEV_SSH:-<COLAB_DEV_SSH>}"
  COLAB_DEV_KEY_FILE="${COLAB_DEV_KEY_FILE:-<COLAB_DEV_KEY_FILE>}"
  DEV_URL="${DEV_URL:-<COLAB_DEV_URL>}"
  COLAB_REF_ROOT="${COLAB_REF_ROOT:-<COLAB_REF_ROOT>}"
  MD_ROOT="${MD_ROOT:-<COLAB_REF_ROOT>}"
  TARGET_SHA="${TARGET_SHA:-<대상 sha · preflight 가 해석>}"
  DEV_SSH_MISSING=()
fi
export COLAB_DEV_SSH="${COLAB_DEV_SSH:-}" COLAB_DEV_KEY_FILE="${COLAB_DEV_KEY_FILE:-}"

# ── 순차 실행 ────────────────────────────────────────────────────────────
# 단계 하나가 비영 종료하면 **그 자리에서 멈춘다** — 단계 이름과 로그 경로를 낸다.
FAILED_STAGE=""
# 바꾸는 단계가 **실제로 하나라도 돌았는가.** 회차 기록을 레포(`dev-package/sessions/`)에 남길지
# 실행 자리에만 남길지를 이 값이 가른다 — preflight 에서 멈춘 회차는 dev 를 읽기만 했으므로
# 레포에 기록을 만들지 않는다(픽스처가 레포를 더럽히던 자리이기도 하다).
MUTATED=0
for s in "${STAGES[@]}"; do
  [ "$s" = report ] && continue     # report 는 마지막에 한 번만 돈다
  # preflight 와 rehearse 는 **읽기 전용**이다 — 레포에 회차 기록을 남기지 않는다.
  case "$s" in preflight|rehearse) : ;; *) MUTATED=1 ;; esac
  stage_begin "$s"
  rc=0
  case "$s" in
    preflight) stage_preflight || rc=$? ;;
    rehearse)  stage_rehearse  || rc=$? ;;
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
