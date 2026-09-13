#!/usr/bin/env bash
# 단계 본문 9개 — deploy · reset · bootstrap · up · s3 · prelude · seed · verify · report.
#
# 원본 절차 = `dev-package/sessions/DR-2-runbook.md`(2026-09-13 사람이 실제로 밟은 순서).
# 런북 정정 6건은 각 자리에 「근거: R-DEV-RESET §11-1 ⑴」 형태로 주석을 달았다.
# 이 파일은 단독 실행하지 않는다. `reseed.sh` 가 source 한다.

# ── 공통 값 ──────────────────────────────────────────────────────────────
# EC2 위 운영 식별자다(레포 경로가 아니다 — 런북 머리말과 같은 취급).
DEV_STATE_DIR=/opt/colab-v2
DEV_REPO_DIR=/opt/colab-repo
DOCTOR_PROBE="$DEV_REPO_DIR/infra/ops/probes/deploy-verification.sh"
RESET_TOOL="$DEV_REPO_DIR/services/core-api/ops/reset_dev_environment.py"
REMOTE_OUT=/tmp/colab-reseed-out
# 근거: R-DEV-RESET §11-1 ⑷ — core-api 이미지에 psql 이 없다. SQL 은 이 이미지로 낸다.
PSQL_IMAGE=postgres:16-alpine
# compose 서비스 이름 넷(컨테이너 이름이 아니다 — 런북 §3 ①′).
APP_UNITS="core-api pipeline-worker viz-render ai-service"

core_image() { printf 'colab-v2/core-api:dev-%s' "$TARGET_SHA"; }

# 초기화 도구 공통 마운트 — URL 파일은 읽기 전용, 보고서 자리는 도구가 0600 으로 쓴다.
# 근거: R-DEV-RESET §11-1 ⑶ — 버킷·리전은 compose 의 리터럴이라 여기서 명시하지 않으면
#       `s3-plan` 이 exit 2 로 아무것도 하지 않는다.
reset_docker_cmd() {
  printf 'docker run --rm --network host --user 0 \\\n'
  printf '  -v %s/platform-owner-db.url:/s/platform.url:ro \\\n' "$SECRETS_DIR"
  printf '  -v %s/ai-owner-db.url:/s/ai.url:ro \\\n' "$SECRETS_DIR"
  printf '  -v %s:/tmp/reset.py:ro \\\n' "$RESET_TOOL"
  printf '  -v %s:/out \\\n' "$REMOTE_OUT"
  printf '  -e COLAB_CORE_S3_BUCKET=%s -e COLAB_CORE_S3_REGION=%s \\\n' "$S3_BUCKET" "$S3_REGION"
  printf '  %s python /tmp/reset.py --target dev --yes-reset-dev \\\n' "$(core_image)"
  printf '    --platform-url-file /s/platform.url --ai-url-file /s/ai.url'
}

# ── deploy ───────────────────────────────────────────────────────────────
# 정본 = `infra/dev/README.md` 「올리기」 ＋ 런북 §1. 사람 입력을 요구하는 자리는 없다.
# 트리 동기화는 배포 절차 밖의 별도 1회다 — `ship.sh` 가 /opt/colab-repo 를 밀지 않는다(이슈 #48 ⑴).
stage_deploy() {
  local head; head="$(run_capture git -C "$REPO_ROOT" rev-parse --short=12 HEAD || true)"
  if [ "$DRY_RUN" != 1 ] && [ "$head" != "$TARGET_SHA" ]; then
    die "작업 트리 HEAD $head ≠ 배포 대상 $TARGET_SHA — build.sh 는 HEAD 를 굽는다. 먼저 체크아웃한다."
  fi

  log "① 이미지 5벌 빌드 (linux/arm64)"
  run bash "$REPO_ROOT/infra/dev/build.sh" "$REPO_ROOT/dist" || return 1

  log "② 반입 — ship.sh 안의 조상 게이트가 판정한다(비조상 65 · origin 조회 실패 78)"
  run env COLAB_DEV_SSH="$COLAB_DEV_SSH" COLAB_DEV_KEY_FILE="$COLAB_DEV_KEY_FILE" \
      bash "$REPO_ROOT/infra/dev/ship.sh" "$REPO_ROOT/dist" || return 1

  log "③ 배포 레포 트리 동기화 — deploy_doctor ⑥⑦ 이 옛 head 를 정답으로 삼는 것을 막는다"
  local tgz="$RUN_DIR/repo-$TARGET_SHA.tgz"
  run bash -c "git -C \"$REPO_ROOT\" archive '$TARGET_SHA' -- db gates services/core-api/ops infra | gzip > \"$tgz\"" || return 1
  run scp -o BatchMode=yes -o IdentitiesOnly=yes -i "$COLAB_DEV_KEY_FILE" \
      "$tgz" "$COLAB_DEV_SSH:/tmp/repo.tgz" || return 1
  ssh_dev "sudo tar xzf /tmp/repo.tgz -C $DEV_REPO_DIR --overwrite && rm -f /tmp/repo.tgz" || return 1

  log "④ 기동 — up.sh (마이그레이션 두 체인 → 4 단위 healthy · fail-closed)"
  ssh_dev "sudo bash $DEV_STATE_DIR/up.sh" || return 1

  log "⑤ 프런트 정적 번들"
  run bash -c "cd \"$REPO_ROOT/frontend\" && npm ci && npm run build" || return 1
  # deploy_web.py 는 자작 SigV4 라 AWS_PROFILE 을 해석하지 않는다(이슈 #48 ⑵) —
  # preflight ⑶ 이 환경변수 갈래를 이미 판정했다.
  run python3 "$REPO_ROOT/services/core-api/ops/deploy_web.py" \
      --dist "$REPO_ROOT/frontend/dist" --bucket "$WEB_BUCKET" --region "$S3_REGION" || return 1

  log "⑥ deploy_doctor 기준선 1회"
  doctor_once || return 1
}

# deploy_doctor 를 **한 번** 돌리고 요약줄로 판정한다.
# 부분 실행 둘을 합쳐 15 라 하지 않는다(완료 정의 · `.claude/rules/deploy.md`).
doctor_once() {
  # 표준오류를 되받지 않는다 — `run_capture` 가 그쪽으로 DRY 줄과 실행 로그를 낸다.
  local out; out="$(ssh_dev_capture "sudo bash $DOCTOR_PROBE" || true)"
  printf '%s\n' "$out" | redact >> "$STAGE_LOG"
  if [ "$DRY_RUN" = 1 ]; then return 0; fi
  local line; line="$(printf '%s\n' "$out" | grep -E '^항목 [0-9]+ — ' | tail -1 || true)"
  log "deploy_doctor 요약줄: ${line:-<없음>}"
  if [ -z "$line" ]; then blocked_add deploy_doctor "요약줄 없음 — 판정 불가"; return 1; fi
  printf '%s\n' "$line" > "$RUN_DIR/doctor-summary.txt"
  if printf '%s' "$line" | grep -qE '^항목 15 — ✓ 15 · ✗ 0 · ─ 0$'; then
    log "deploy_doctor 15/15 — 한 번의 실행"
    return 0
  fi
  blocked_add deploy_doctor "15/15 아님 — $line"
  return 1
}

# ── reset ────────────────────────────────────────────────────────────────
# 유일한 파괴 단계다. 실행 **전에** 승인 기록을 남긴다(dev 한정 상시 승인 · `.claude/rules/deploy.md`).
stage_reset() {
  write_approval_record || return 1

  log "① 실행 전 계수 — 연구실 경계를 건 상태에서 센다"
  ssh_dev "mkdir -p $REMOTE_OUT && chmod 700 $REMOTE_OUT" || return 1
  ssh_script "reset:count" <<EOF || return 1
set -euo pipefail
$(reset_docker_cmd) --phase count --report /out/count-before.json
test -s $REMOTE_OUT/count-before.json
EOF

  log "①′ 앱 4 단위 정지 — 스키마 DROP 이 잠금에 걸리지 않게 한다"
  ssh_dev "sudo docker compose -f $DEV_STATE_DIR/compose.yml --env-file $DEV_STATE_DIR/dev.env stop $APP_UNITS" || return 1
  log "①″ 활성 트랜잭션 0 확인 — 마스터 롤로 본다(비특권 롤은 state 를 NULL 로 받는다)"
  psql_master_query "select count(*) from pg_stat_activity where datname in ('colab_platform','colab_ai') and state <> 'idle' and pid <> pg_backend_pid();" "0" \
    || { blocked_add reset "활성 트랜잭션 0 아님"; return 1; }

  log "② 두 체인 스키마 재생성"
  ssh_script "reset:schema" <<EOF || return 1
set -euo pipefail
$(reset_docker_cmd) --phase schema --report /out/schema.json
EOF
}

# 승인 기록 — 누가 · 언제 · 어느 sha · 어느 게이트를 통과했는가.
# 게이트 넷의 문면은 `.claude/rules/deploy.md` 11번 증보 문단이 정본이다.
write_approval_record() {
  local who="${COLAB_RESEED_OPERATOR:-$(id -un)}"
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY 승인 기록 기록 자리 = $RUN_DIR/approval-record.json (who=$who sha=${TARGET_SHA:-<미해석>})"
    return 0
  fi
  python3 - "$RUN_DIR/approval-record.json" "$who" "$TARGET_SHA" "$S3_BUCKET" "$RUN_ID" <<'PY'
import datetime, json, sys
path, who, sha, bucket, run_id = sys.argv[1:6]
json.dump({
    "schema": "colab-reseed-approval/1",
    "runId": run_id,
    "operator": who,
    "recordedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "targetSha": sha,
    "basis": "dev 한정 상시 승인 — .claude/rules/deploy.md 11번 증보 문단(2026-09-14 개정)",
    "gatesPassed": [
        {"id": 1, "text": "--target dev ＋ --yes-reset-dev", "evidence": "reseed.sh 가 두 인자를 고정으로 넘긴다"},
        {"id": 2, "text": "COLAB_CORE_S3_BUCKET 정확 일치", "evidence": bucket},
        {"id": 3, "text": "두 DB URL 호스트에 -dev 포함", "evidence": "reset_dev_environment.py ENV_HOST_MARK 가 판정한다"},
        {"id": 4, "text": "계획 키가 uploads/·previews/ 안", "evidence": "s3 단계의 계획 검토와 도구 NEVER_TOUCH_PREFIXES 가 판정한다"},
    ],
}, open(path, "w"), ensure_ascii=False, indent=2)
PY
  log "승인 기록 = approval-record.json (operator=$who sha=$TARGET_SHA)"
}

# 마스터 URL 로 읽기 전용 질의 한 줄. 기대값과 다르면 비영.
# 근거: R-DEV-RESET §11-1 ⑴⑵⑷ — 스킴 치환 · --user 0 · postgres:16-alpine.
psql_master_query() {
  local sql="$1" expect="$2"
  # SQL 은 원격 셸 변수로 두고 `-e SQL`(값 없이)로 넘긴다 — docker 의 argv 에 문장이 실리지 않는다.
  local out; out="$(ssh_script "psql:master" <<EOF
set -euo pipefail
export SQL='$sql'
docker run --rm --network host --user 0 \\
  -v $SECRETS_DIR/master.url:/s/master.url:ro \\
  -e SQL \\
  $PSQL_IMAGE sh -c 'psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/master.url)" -c "\$SQL"'
EOF
)"
  printf '%s\n' "$out" | redact >> "$STAGE_LOG"
  [ "$DRY_RUN" = 1 ] && return 0
  local val; val="$(printf '%s\n' "$out" | grep -E '^[0-9]+$' | tail -1 || true)"
  log "질의 결과 = ${val:-<없음>} (기대 $expect)"
  [ "$val" = "$expect" ]
}

# ── bootstrap ────────────────────────────────────────────────────────────
# 비밀번호는 **원격 셸 안에서 0600 URL 파일에서만** 꺼낸다. argv·로그·결과 JSON 에 0건이다.
# 근거: R-DEV-RESET §11-1 ⑸ — db-bootstrap.sh 는 어느 단계를 부르든 이름 넷을 전부 요구한다.
stage_bootstrap() {
  log "① extensions — pg_trgm (멱등)"
  ssh_dev "sudo COLAB_PG_MASTER_URL_FILE=$SECRETS_DIR/master.url bash $DEV_REPO_DIR/infra/dev/db-bootstrap.sh extensions" || return 1

  log "② 마이그레이션 두 체인 — up.sh ① 만 떼어 낸다(⑤ 의 GRANT 가 표를 요구한다)"
  ssh_dev "sudo docker compose -f $DEV_STATE_DIR/compose.yml --env-file $DEV_STATE_DIR/dev.env --profile migrate run --rm -T migrate-platform < /dev/null" || return 1
  ssh_dev "sudo docker compose -f $DEV_STATE_DIR/compose.yml --env-file $DEV_STATE_DIR/dev.env --profile migrate run --rm -T migrate-ai < /dev/null" || return 1

  log "②′ 체인별 버전 표 확인"
  # 근거: R-DEV-RESET §11-1 ⑹ — 표 이름은 `alembic_version_platform`·`alembic_version_ai` 다.
  #       `alembic_version` 을 보면 **적용된 것을 미적용으로 오판한다**.
  #       head 값 자체의 정오는 `up` 단계의 `deploy_doctor` ⑥⑦ 이 레포 트리와 대조해 판정한다.
  ssh_script "bootstrap:chain-heads" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $SECRETS_DIR/platform-owner-db.url:/s/platform.url:ro \\
  -v $SECRETS_DIR/ai-owner-db.url:/s/ai.url:ro \\
  $PSQL_IMAGE sh -c '
    p=\$(psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/platform.url)" \\
      -c "select version_num from alembic_version_platform")
    a=\$(psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/ai.url)" \\
      -c "select version_num from alembic_version_ai")
    echo "체인 head — platform=\$p · ai=\$a"
    [ -n "\$p" ] && [ -n "\$a" ]'
EOF

  log "③ 앱 롤 GRANT — app-grants ＋ account-admin (기본 권한은 스키마와 함께 사라진다)"
  ssh_script "bootstrap:grants" <<EOF || return 1
set -euo pipefail
# URL 파일의 비밀번호 필드만 꺼낸다 — 값은 이 셸 밖으로 나가지 않는다.
pw() { sudo sed -E 's#^[a-z+]+://[^:]+:([^@]+)@.*#\1#' "\$1"; }
COLAB_OWNER_PASSWORD="\$(pw $SECRETS_DIR/platform-owner-db.url)"
COLAB_APP_PASSWORD="\$(pw $SECRETS_DIR/core-database.url)"
COLAB_AI_APP_PASSWORD="\$(pw $SECRETS_DIR/ai-db.url)"
COLAB_ACCOUNT_ADMIN_PASSWORD="\$(pw $SECRETS_DIR/account-admin-database.url)"
export COLAB_OWNER_PASSWORD COLAB_APP_PASSWORD COLAB_AI_APP_PASSWORD COLAB_ACCOUNT_ADMIN_PASSWORD
# account-admin 단계의 문자 집합 가드(base64url) — 어긋나면 값을 찍지 않고 멈춘다.
case "\$COLAB_ACCOUNT_ADMIN_PASSWORD" in
  *[!A-Za-z0-9_-]*) echo "account-admin 비밀번호가 base64url 집합 밖이다 — 멈춘다" >&2; exit 1 ;;
esac
for n in \$(bash $DEV_REPO_DIR/infra/staging/db-bootstrap.sh required-env); do
  eval "v=\\\${\$n:-}"; [ -n "\$v" ] || { echo "필수 환경변수 미설정: \$n" >&2; exit 1; }
done
sudo -E COLAB_PG_MASTER_URL_FILE=$SECRETS_DIR/master.url bash $DEV_REPO_DIR/infra/dev/db-bootstrap.sh app-grants
sudo -E COLAB_PG_MASTER_URL_FILE=$SECRETS_DIR/master.url bash $DEV_REPO_DIR/infra/dev/db-bootstrap.sh account-admin
unset COLAB_OWNER_PASSWORD COLAB_APP_PASSWORD COLAB_AI_APP_PASSWORD COLAB_ACCOUNT_ADMIN_PASSWORD
EOF

  log "④ 사후 확인 — 세 롤이 각자 URL 파일로 붙는가"
  ssh_script "bootstrap:verify-roles" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $SECRETS_DIR/core-database.url:/s/core.url:ro \\
  -v $SECRETS_DIR/ai-db.url:/s/ai.url:ro \\
  -v $SECRETS_DIR/account-admin-database.url:/s/aa.url:ro \\
  $PSQL_IMAGE sh -c '
    for f in /s/core.url /s/ai.url /s/aa.url; do
      psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" \$f)" -c "select 1" >/dev/null || exit 1
    done
    echo "역할 접속 3/3 ok"'
EOF
}

# ── up ───────────────────────────────────────────────────────────────────
# up.sh 전체(마이그레이션 재확인 → 기동 → healthy → healthz) 뒤 deploy_doctor **1회**.
stage_up() {
  ssh_dev "sudo bash $DEV_STATE_DIR/up.sh" || return 1
  log "── ai 시드 계수(K3·K4 의 사전) — 세 표가 전부 0 보다 커야 한다"
  ssh_script "up:ai-seed" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $SECRETS_DIR/ai-owner-db.url:/s/ai.url:ro \\
  $PSQL_IMAGE sh -c '
    n=\$(psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/ai.url)" \\
      -c "select least((select count(*) from d9_method_term),(select count(*) from d9_topic_synonym),(select count(*) from d9_place_alias))")
    echo "ai 시드 최소 계수 = \$n"
    [ "\$n" -gt 0 ]'
EOF
  doctor_once
}

# ── s3 ───────────────────────────────────────────────────────────────────
# 계획 → 자동 검토 → 적용. 계획을 손으로 고치지 않는다.
stage_s3() {
  if [ "$DRY_RUN" = 1 ]; then
    # 이 단계의 명령은 출력을 되받아 판정하므로 `ssh_script` 의 DRY 줄이 변수로 들어간다.
    # dry-run 에서는 네 걸음을 여기서 그대로 찍는다.
    log "DRY ① ssh <dev> — $(reset_docker_cmd | tr -d '\\\n') --phase s3-plan --plan-out /out/plan.json --report /out/s3-plan.json"
    log "DRY ② ssh <dev> python3 — 계획 검토(_ops/ 0 건 · 접두사 uploads/·previews/ · 모드 0600 · 소유자 일치)"
    log "DRY ③ ssh <dev> — 같은 도구 --phase s3-apply --apply-plan /out/plan.json --plan-sha256 <① 출력값> --report /out/s3-apply.json"
    log "DRY ④ ssh <dev> — 같은 도구 --phase count --report /out/count-after.json"
    return 0
  fi
  log "① s3-plan — exact-key 계획 ＋ sha256"
  local out; out="$(ssh_script "s3:plan" <<EOF
set -euo pipefail
$(reset_docker_cmd) --phase s3-plan --plan-out /out/plan.json --report /out/s3-plan.json
EOF
)"
  printf '%s\n' "$out" | redact >> "$STAGE_LOG"
  local sha256; sha256="$(printf '%s\n' "$out" | grep -Eo '\b[0-9a-f]{64}\b' | tail -1 || true)"
  [ -n "$sha256" ] || { blocked_add s3-plan "계획 sha256 을 읽지 못했다"; return 1; }

  log "② 계획 검토 — _ops/ 0 건 · 접두사 uploads/·previews/ 둘뿐 · 소유자 0600"
  ssh_script "s3:review" <<EOF || { blocked_add s3-plan "계획 검토 미달"; return 1; }
set -euo pipefail
python3 - "$REMOTE_OUT/plan.json" <<'PY'
import json, os, stat, sys
p = sys.argv[1]
st = os.stat(p)
assert stat.S_IMODE(st.st_mode) == 0o600, "계획 파일 모드가 0600 이 아니다"
assert st.st_uid == os.getuid(), "계획 파일 소유자가 실행자가 아니다"
plan = json.load(open(p))
keys = plan.get("keys") or []
bad = [k for k in keys if k.startswith("_ops/")]
assert not bad, "_ops/ 키 %d 건" % len(bad)
pre = sorted({k.split("/", 1)[0] + "/" for k in keys})
assert set(pre) <= {"uploads/", "previews/"}, "허용 밖 접두사 %s" % pre
print("계획 검토 ok — 키 %d 건 · 접두사 %s" % (len(keys), pre))
PY
EOF

  log "③ s3-apply — 멀티파트를 객체보다 먼저 중단한다(도구가 그 순서를 강제한다)"
  ssh_script "s3:apply" <<EOF || return 1
set -euo pipefail
$(reset_docker_cmd) --phase s3-apply --apply-plan /out/plan.json --plan-sha256 $sha256 --report /out/s3-apply.json
EOF

  log "④ 실행 후 계수 — 표 넷 0 · uploads/·previews/ 객체 0 · 멀티파트 0"
  ssh_script "s3:count-after" <<EOF || return 1
set -euo pipefail
$(reset_docker_cmd) --phase count --report /out/count-after.json
EOF
}

# ── prelude ──────────────────────────────────────────────────────────────
# 화면 밖 SQL 은 이 넷뿐이다(런북 §5). 연구실 → 계정 → 로그인 자격 → 서비스 운영자.
stage_prelude() {
  if [ "$DRY_RUN" = 1 ]; then
    RESEED_ACCOUNT_EMAIL="${RESEED_ACCOUNT_EMAIL:-<RESEED_ACCOUNT_EMAIL>}"
    RESEED_ACCOUNT_NAME="${RESEED_ACCOUNT_NAME:-<RESEED_ACCOUNT_NAME>}"
    RESEED_ACCOUNT_ID="${RESEED_ACCOUNT_ID:-<RESEED_ACCOUNT_ID · 26자 ULID>}"
  else
    : "${RESEED_ACCOUNT_EMAIL:?RESEED_ACCOUNT_EMAIL 이 필요하다 — 첫 계정 이메일}"
    : "${RESEED_ACCOUNT_NAME:?RESEED_ACCOUNT_NAME 이 필요하다 — 첫 계정 이름}"
    : "${RESEED_ACCOUNT_ID:?RESEED_ACCOUNT_ID 이 필요하다 — 26자 ULID(② ③ ④ 가 같은 값을 쓴다)}"
    [ -n "${OPERATOR_PASSWORD_FILE:-}" ] \
      || die "--operator-password-file 이 필요하다 — 초기 비밀번호 10자 이상 0600 파일"
  fi

  log "① 연구실 — provision-lab.sql (파일이 스스로 app.current_lab 을 건다)"
  ssh_script "prelude:lab" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  -v $DEV_REPO_DIR/infra/staging/provision-lab.sql:/s/lab.sql:ro \\
  $PSQL_IMAGE sh -c 'psql -v ON_ERROR_STOP=1 "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -f /s/lab.sql'
EOF

  log "② 첫 계정 — provision-account.sql (id 는 ③ ④ 가 그대로 재사용한다)"
  ssh_script "prelude:account" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  -v $DEV_REPO_DIR/services/core-api/ops/provision-account.sql:/s/acct.sql:ro \\
  $PSQL_IMAGE sh -c 'psql -v ON_ERROR_STOP=1 \\
    -v account_id="'"'"'$RESEED_ACCOUNT_ID'"'"'" -v lab_id="'"'"'$LAB_ID'"'"'" \\
    -v name="'"'"'$RESEED_ACCOUNT_NAME'"'"'" -v email="'"'"'$RESEED_ACCOUNT_EMAIL'"'"'" \\
    -v role="'"'"'$RESEED_ACCOUNT_ROLE'"'"'" \\
    "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -f /s/acct.sql'
EOF

  log "③ 첫 로그인 자격 — account_admin.login_credential INSERT 1건 (제품과 같은 두 함수로 해싱)"
  prelude_login_credential || return 1

  log "④ 서비스 운영자 — provision-service-operator.sql (FORCE RLS 아래라 경계를 먼저 건다)"
  ssh_script "prelude:operator" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  -v $DEV_REPO_DIR/services/core-api/ops/provision-service-operator.sql:/s/op.sql:ro \\
  $PSQL_IMAGE sh -c 'psql -v ON_ERROR_STOP=1 -v account_id="'"'"'$RESEED_ACCOUNT_ID'"'"'" \\
    -c "SET app.current_lab = '"'"'$LAB_ID'"'"'" \\
    "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -f /s/op.sql'
EOF
}

# ③ 만 따로 둔다 — 비밀번호가 **표준입력 한 줄**로만 움직인다.
# 해시는 제품과 같은 두 함수를 그대로 부른다(`hash_password` · `normalize_login_name`).
prelude_login_credential() {
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY ssh <dev> docker exec -i colab_v2_dev_core_api python -  # login_credential INSERT (비밀번호 = 표준입력 1줄)"
    return 0
  fi
  local py; py="$(cat <<'PY'
import os, sys
from sqlalchemy import create_engine, text
from colab_core.kernel.password import hash_password
from colab_core.kernel.db_credentials import normalize_login_name
pw = sys.stdin.readline().rstrip("\n")
if len(pw) < 10:
    raise SystemExit("초기 비밀번호가 10자 미만이다 — 제품 하한이 10자다")
h = hash_password(pw).as_dict()
url = open(os.environ["COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE"]).read().strip()
eng = create_engine(url)
with eng.begin() as c:
    c.execute(text("SELECT pg_advisory_xact_lock(1131379081)"))
    c.execute(text(
        "INSERT INTO account_admin.login_credential"
        " (account_id, login_name, kdf, salt, password_hash, n, r, p)"
        " VALUES (:account_id, :login_name, :kdf, :salt, :password_hash, :n, :r, :p)"),
        dict(account_id=os.environ["RESEED_ACCOUNT_ID"],
             login_name=normalize_login_name(os.environ["RESEED_ACCOUNT_EMAIL"]), **h))
print("login_credential 1행 · must_change_password 는 DB 기본값 true")
PY
)"
  # 표준입력 한 줄기에 파이썬 본문 ＋ `__PW__` 구분줄 ＋ 비밀번호 한 줄을 실어 보낸다.
  # 원격에서 둘로 갈라 파이썬은 파일로, 비밀번호는 컨테이너 표준입력으로만 넣는다.
  # argv·환경변수·로그 어디에도 값이 남지 않는다(런북 §5 ③ 축자 조건).
  log "RUN ssh <dev> docker exec -i colab_v2_dev_core_api python  # login_credential INSERT"
  local remote; remote=$(cat <<REMOTE
set -euo pipefail
all=\$(mktemp); chmod 600 "\$all"; cat > "\$all"
body=\$(mktemp); chmod 600 "\$body"; sed '/^__PW__\$/,\$d' "\$all" > "\$body"
pwf=\$(mktemp); chmod 600 "\$pwf"; sed -n '/^__PW__\$/,\$p' "\$all" | tail -n +2 > "\$pwf"
rm -f "\$all"
sudo docker cp "\$body" colab_v2_dev_core_api:/tmp/reseed_cred.py
rc=0
sudo docker exec -i \\
  -e RESEED_ACCOUNT_ID='$RESEED_ACCOUNT_ID' -e RESEED_ACCOUNT_EMAIL='$RESEED_ACCOUNT_EMAIL' \\
  colab_v2_dev_core_api python /tmp/reseed_cred.py < "\$pwf" || rc=\$?
sudo docker exec colab_v2_dev_core_api rm -f /tmp/reseed_cred.py
shred -u "\$body" "\$pwf" 2>/dev/null || rm -f "\$body" "\$pwf"
exit \$rc
REMOTE
)
  local out rc=0
  out="$( { printf '%s\n__PW__\n' "$py"; cat "$OPERATOR_PASSWORD_FILE"; } \
      | ssh -o BatchMode=yes -o IdentitiesOnly=yes -i "$COLAB_DEV_KEY_FILE" \
            "$COLAB_DEV_SSH" "$remote" 2>&1 )" || rc=$?
  printf '%s\n' "$out" | redact | tee -a "$STAGE_LOG" >/dev/null
  return $rc
}

# ── seed ─────────────────────────────────────────────────────────────────
# 화면 경로로만 투입한다. DB 직접 쓰기는 prelude 넷뿐이다(라운드 §7).
stage_seed() {
  log "① 계획 생성 — 정본 md 4건 → plan-manifest.yaml ＋ upload-plan.json"
  run python3 "$REPO_ROOT/dev-package/tools/dev-seed/build_plan.py" \
      --ref-root "$COLAB_REF_ROOT" --md-root "$MD_ROOT" --work-dir "$SEED_WORK_DIR" || return 1

  log "② 러너 — 로그인 · 프로젝트 · 데이터셋 · 확인 · 보고"
  local extra=()
  # `--accounts-file` 은 러너 레인(WU-C1b)이 붙이는 인자다. 이 기준에는 아직 없으므로
  # 값이 주어졌을 때만 넘긴다 — 없는 인자를 무조건 넘겨 러너를 죽이지 않는다.
  if [ -n "$ACCOUNTS_FILE" ]; then extra+=(--accounts-file "$ACCOUNTS_FILE"); fi
  run python3 "$REPO_ROOT/dev-package/tools/dev-seed/runner.py" \
      --phase all --base-url "$DEV_URL" --work-dir "$SEED_WORK_DIR" \
      --account "$RESEED_ACCOUNT_EMAIL" "${extra[@]}" || return 1
}

# ── verify ───────────────────────────────────────────────────────────────
# 읽기 전용이다. 쓰기는 한 건도 내지 않는다.
# 한 번의 상세 화면 순회로 넷을 함께 잰다 — 가공 단계 · 「미지정」 · 프로젝트 연결 · 미리보기 판정.
# 대기 = 45,000 ms. 근거 = DR-3 실측에서 viz-render 실소요가 20,037~38,391 ms 였고
#        core-api 가 10,02x ms 에 끊어 503 을 냈다(`dev-package/sessions/DR-3-run-2026-09-13.md §6`).
#        뒷단 개선은 이 회차 범위 밖(`PV-2`)이라 여기서는 **판정만** 한다.
PREVIEW_WAIT_MS="${COLAB_RESEED_PREVIEW_WAIT_MS:-45000}"

stage_verify() {
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY 러너 verify.json 계수 대조(데이터셋 $EXPECT_DATASETS · 프로젝트 $EXPECT_PROJECTS · 간선 $EXPECT_EDGES)"
    log "DRY agent-browser open /datasets/<id> ×$EXPECT_DATASETS — 대기 ${PREVIEW_WAIT_MS}ms · 가공 단계 · 「미지정」 · usage-card · 미리보기 판정"
    log "DRY 정본 md 의 가공 단계 분포와 대조 · 미지정 0 · 프로젝트 미연결 0"
    return 0
  fi

  local state="$SEED_WORK_DIR/state.json" verify="$SEED_WORK_DIR/verify.json"
  local manifest="$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml"
  for f in "$state" "$verify" "$manifest"; do
    [ -f "$f" ] || { blocked_add verify "$(basename "$f") 부재 — seed 단계 산출물이 없다"; return 1; }
  done

  log "① 상세 화면 순회 — $EXPECT_DATASETS 건 · 한 건당 최대 ${PREVIEW_WAIT_MS}ms"
  local ids; ids="$(python3 - "$state" <<'PY'
import json, sys
st = json.load(open(sys.argv[1]))
for seq, row in sorted(st.get("datasets", {}).items(), key=lambda kv: int(kv[0])):
    print("%s\t%s\t%s" % (seq, row.get("dataset_id") or "", row.get("name") or ""))
PY
)"
  : > "$RUN_DIR/preview-judgment.tsv"
  local seq did name t0 t1 ms shown level unset_lv usage
  while IFS=$'\t' read -r seq did name; do
    [ -n "$seq" ] || continue
    if [ -z "$did" ]; then
      printf '%s\t%s\t?\t미성립\t0\t?\t?\t데이터셋 id 미확보\n' "$seq" "$name" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name" "데이터셋 id 미확보"
      continue
    fi
    t0="$(date +%s%3N)"
    run_capture agent-browser open "$DEV_URL/datasets/$did" >/dev/null || true
    run_capture agent-browser wait '[data-testid="dataset-preview"]' "$PREVIEW_WAIT_MS" >/dev/null 2>&1 || true
    t1="$(date +%s%3N)"; ms=$(( t1 - t0 ))
    shown="$(run_capture agent-browser get count '[data-testid="preview-unavailable"]' 2>/dev/null | tr -dc '0-9')"
    level="$(run_capture agent-browser get text '[data-testid="ig-가공 단계"]' 2>/dev/null | tr '\n' ' ')"
    unset_lv="$(run_capture agent-browser get count '[data-testid="ig-unset-가공 단계"]' 2>/dev/null | tr -dc '0-9')"
    usage="$(run_capture agent-browser get count '[data-testid="usage-card"]' 2>/dev/null | tr -dc '0-9')"
    local verdict=성립
    [ "${shown:-0}" -gt 0 ] && verdict=미성립
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n' \
      "$seq" "$name" "${level:-?}" "$verdict" "$ms" "${unset_lv:-0}" "${usage:-0}" >> "$RUN_DIR/preview-judgment.tsv"
  done <<< "$ids"

  log "② 계수 대조 — 러너 verify.json ＋ 순회 결과 ＋ 정본 등재표"
  python3 - "$verify" "$manifest" "$RUN_DIR/preview-judgment.tsv" "$RUN_DIR/counts.json" \
      "$EXPECT_DATASETS" "$EXPECT_PROJECTS" "$EXPECT_EDGES" <<'PY' || return 1
import json, sys
try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML 이 없다 — 등재표 대조 불가")
verify, manifest, tsv, out, nds, nproj, nedge = sys.argv[1:8]
v = json.load(open(verify))
m = yaml.safe_load(open(manifest))
rows = [l.rstrip("\n").split("\t") for l in open(tsv) if l.strip()]
want = {}
for d in m.get("datasets", []):
    want[str(d.get("seq"))] = str(d.get("processing_level") or d.get("level") or "")
got = {r[0]: r[2] for r in rows}
level_mismatch = [s for s, w in want.items() if w and w not in (got.get(s) or "")]
unset = [r[0] for r in rows if r[5] not in ("0", "")]
unlinked = [r[0] for r in rows if r[6] in ("0", "")]
res = {
    "datasets": {"expected": int(nds), "ui": v.get("dataset_count_ui"), "state": v.get("dataset_count_state")},
    "projects": {"expected": int(nproj), "byProject": len(v.get("by_project") or {})},
    "edges": {"expected": int(nedge), "ok": v.get("edges_ok"), "missing": v.get("edges_missing")},
    "processingLevel": {"mismatchSeq": level_mismatch, "unsetSeq": unset},
    "projectUnlinkedSeq": unlinked,
    "previewRows": len(rows),
    "previewEstablished": sum(1 for r in rows if r[3] == "성립"),
}
json.dump(res, open(out, "w"), ensure_ascii=False, indent=2)
bad = []
if res["datasets"]["ui"] != int(nds): bad.append("데이터셋 계수 %s" % res["datasets"]["ui"])
if res["edges"]["ok"] != int(nedge): bad.append("간선 계수 %s" % res["edges"]["ok"])
if level_mismatch: bad.append("가공 단계 불일치 seq %s" % ",".join(level_mismatch))
if unset: bad.append("「미지정」 seq %s" % ",".join(unset))
if unlinked: bad.append("프로젝트 미연결 seq %s" % ",".join(unlinked))
if len(rows) != int(nds): bad.append("판정 표 %d 행" % len(rows))
print("대조 결과 — " + ("전건 일치" if not bad else " · ".join(bad)))
raise SystemExit(1 if bad else 0)
PY
}

# ── report ───────────────────────────────────────────────────────────────
# result.json(스키마 대조) ＋ 회차 기록 뼈대. 기록은 JSON 에서 채운다.
stage_report() {
  local result="$RUN_DIR/result.json"
  # 실제 실행은 회차 기록 자리에 쓴다. dry-run 은 레포를 건드리지 않으므로 실행 자리에만 쓴다.
  local session="$REPO_ROOT/dev-package/sessions/DR-4-run-$(date -u +%Y-%m-%d).md"
  [ "$DRY_RUN" = 1 ] && session="$RUN_DIR/DR-4-run-$(date -u +%Y-%m-%d).md"
  python3 "$RESEED_DIR/report.py" \
    --run-dir "$RUN_DIR" --run-id "$RUN_ID" --target-sha "${TARGET_SHA:-}" \
    --stages "$(printf '%s,' "${STAGES[@]}")" --dry-run "$DRY_RUN" \
    --schema "$RESEED_DIR/result-schema.json" --out "$result" --session-out "$session" || return 1
  log "결과 JSON = $(relpath "$result")"
  log "회차 기록 뼈대 = $(relpath "$session")"
}
