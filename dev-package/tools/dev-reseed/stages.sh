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

# compose 호출 앞머리 — `stop`·`start`·`ps`·`--profile migrate run` 이 **같은 한 벌**을 쓴다.
# 하나로 두는 이유 = 정지와 그 역연산이 서로 다른 compose·env 를 잡으면 되살아나는 것이 다른 것이 된다.
compose_cmd() {
  printf 'sudo docker compose -f %s/compose.yml --env-file %s/dev.env' "$DEV_STATE_DIR" "$DEV_STATE_DIR"
}

# 초기화 도구 공통 마운트 — URL 파일은 읽기 전용, 보고서 자리는 도구가 0600 으로 쓴다.
# 근거: R-DEV-RESET §11-1 ⑶ — 버킷·리전은 compose 의 리터럴이라 여기서 명시하지 않으면
#       `s3-plan` 이 exit 2 로 아무것도 하지 않는다.
#
# 앞머리(플래그·마운트·이미지)를 따로 둔다 — **초기화 도구와 계획 검토가 같은 한 벌로 돈다.**
# 왜 = 도구가 쓰는 파일(계획·보고서)은 이 컨테이너의 uid(`--user 0`)와 0600 으로 서고,
#   그 파일에 소유자 검사를 거는 쪽은 **같은 uid 로 돌아야** 한다. 호스트 ssh 사용자는 uid 가
#   다르고 0600 파일을 읽지도 못한다(DR-4 §7 · 실모드에서 통과할 수 없던 검사).
# $1 = 보고서를 받을 원격 폴더(기본 `$REMOTE_OUT`). 리허설은 임시 폴더를 준다.
# $2 = 덧붙일 docker 플래그 한 줄(계획 검토가 검토 본문을 읽기 전용으로 더 건다). 비워도 된다.
reset_docker_prefix() {
  local out_dir="${1:-$REMOTE_OUT}" extra="${2:-}"
  printf 'docker run --rm --network host --user 0 \\\n'
  printf '  -v %s/platform-owner-db.url:/s/platform.url:ro \\\n' "$EC2_SECRETS_DIR"
  printf '  -v %s/ai-owner-db.url:/s/ai.url:ro \\\n' "$EC2_SECRETS_DIR"
  printf '  -v %s:/tmp/reset.py:ro \\\n' "$RESET_TOOL"
  printf '  -v %s:/out \\\n' "$out_dir"
  [ -z "$extra" ] || printf '  %s \\\n' "$extra"
  printf '  -e COLAB_CORE_S3_BUCKET=%s -e COLAB_CORE_S3_REGION=%s \\\n' "$S3_BUCKET" "$S3_REGION"
  printf '  %s' "$(core_image)"
}

reset_docker_cmd() {
  printf '%s python /tmp/reset.py --target dev --yes-reset-dev \\\n' "$(reset_docker_prefix "${1:-}")"
  printf '    --platform-url-file /s/platform.url --ai-url-file /s/ai.url'
}

# ── 계획 검토 본문 ────────────────────────────────────────────────────────
# `stage_s3` ② 와 리허설 ⑸ 가 **이 한 벌**을 쓴다. 두 자리가 갈리면 리허설이 검토를 밟지 못한다.
#
# 검사 다섯 — 모드 0600 · 소유자 = 실행자 · `_ops/` 0건 · 접두사 ⊆ {uploads/, previews/} · sha256 기재.
# `assert` 대신 `SystemExit` 를 낸다 — `python -O` 로 돌아도 검사가 사라지지 않는다.
# 소유자 검사는 초기화 도구 자신이 적용 때 거는 것과 같은 모양이다
# (`services/core-api/ops/reset_dev_environment.py` `_private_file`) — 계획을 호스트 사용자에게
# chown 하면 그 검사가 대신 깨진다. 그래서 검토 쪽을 컨테이너 안으로 옮긴다.
s3_review_py() {
  cat <<'REVIEW_BODY'
import json, os, stat, sys

def refuse(msg):
    raise SystemExit("계획 검토 미달 — " + msg)

p = sys.argv[1]
st = os.stat(p)
if stat.S_IMODE(st.st_mode) != 0o600:
    refuse("계획 파일 모드가 0600 이 아니다 (%o)" % stat.S_IMODE(st.st_mode))
if st.st_uid != os.getuid():
    refuse("계획 파일 소유자가 실행자가 아니다 (파일 %d · 실행자 %d)" % (st.st_uid, os.getuid()))
with open(p, encoding="utf-8") as f:
    plan = json.load(f)
keys = plan.get("keys") or []
mp = plan.get("multipartUploads") or []
mp_keys = [str(u[0]) for u in mp if u]
bad = [k for k in keys + mp_keys if k.startswith("_ops/")]
if bad:
    refuse("_ops/ 키 %d 건" % len(bad))
pre = sorted({k.split("/", 1)[0] + "/" for k in keys + mp_keys})
if not set(pre) <= {"uploads/", "previews/"}:
    refuse("허용 밖 접두사 %s" % pre)
sha = plan.get("sha256") or ""
if len(sha) != 64:
    refuse("계획에 sha256 이 없다 — 적용에 넘길 값이 없다")
print("계획 검토 ok — 키 %d 건 · 멀티파트 %d 건 · 접두사 %s · sha256 %s"
      % (len(keys), len(mp), pre, sha))
REVIEW_BODY
}

# 검토를 **초기화 도구와 같은 컨테이너 안**에서 낸다.
# 본문은 원격 임시 파일에 적어 읽기 전용으로 건다 — `docker run -i` 를 쓰지 않는다.
# 왜 = `-i` 를 달면 컨테이너가 원격 셸(`bash -s`)의 남은 표준입력을 먹는다.
# $1 = 계획이 있는 원격 폴더(기본 `$REMOTE_OUT`).
s3_review_script() {
  local out_dir="${1:-$REMOTE_OUT}"
  cat <<EOF
rev="\$(mktemp)"
trap 'rm -f "\$rev"' EXIT
cat > "\$rev" <<'REVIEW_PY'
$(s3_review_py)
REVIEW_PY
$(reset_docker_prefix "$out_dir" '-v "$rev":/tmp/review.py:ro') python /tmp/review.py /out/plan.json
EOF
}

# ── deploy ───────────────────────────────────────────────────────────────
# 배포 명령과 검증은 release executor 한 번이 소유한다. reset 이후 stage_up은 별도 단계다.
stage_deploy() {
  release_plan_execute run
}

# deploy_doctor 요약줄 파서 — 표준입력에서 **마지막 한 벌**의 요약줄을 뽑는다.
#
# ⚠ 실물 출력은 `print(f"\n  {text}")` 라 **요약줄 앞에 공백 2칸**이 붙는다
#   (`deploy_doctor.py` `run()` 끝 · 표본 `tests/fixtures/doctor-15-15.txt`).
#   앞뒤 공백을 벗기고 나서 잡는다 — `^항목` 으로 바로 잡으면 한 줄도 걸리지 않는다.
# 「마지막 한 벌」 = 출력에 요약줄이 둘 이상이면 **가장 뒤**가 이번 실행의 결과다.
doctor_summary_line() {
  sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
    | grep -E '^항목 [0-9]+ — ✓ [0-9]+ · ✗ [0-9]+ · ─ [0-9]+$' \
    | tail -1
}

# 요약줄이 **15 항목 전건 통과**인가. 빈 줄·모르는 모양은 전부 미달이다(fail-closed).
doctor_summary_full() {
  [ -n "${1:-}" ] || return 1
  printf '%s' "$1" | grep -qE '^항목 15 — ✓ 15 · ✗ 0 · ─ 0$'
}

# deploy_doctor 를 **한 번** 돌리고 요약줄로 판정한다.
# 부분 실행 둘을 합쳐 15 라 하지 않는다(완료 정의 · `.claude/rules/deploy.md`).
doctor_once() {
  # 표준오류를 되받지 않는다 — `run_capture` 가 그쪽으로 DRY 줄과 실행 로그를 낸다.
  local out rc=0; out="$(ssh_dev_capture "sudo bash $DOCTOR_PROBE")" || rc=$?
  printf '%s\n' "$out" | redact >> "$STAGE_LOG"
  if [ "$DRY_RUN" = 1 ]; then return 0; fi
  if [ "$rc" -ne 0 ]; then blocked_add deploy_doctor "비영 종료 $rc"; return "$rc"; fi
  local line; line="$(printf '%s\n' "$out" | doctor_summary_line || true)"
  if [ -z "$line" ]; then blocked_add deploy_doctor "요약줄 없음 — 판정 불가"; return 1; fi
  printf '%s\n' "$line" > "$RUN_DIR/doctor-summary.txt"
  if doctor_summary_full "$line"; then
    log "deploy_doctor 15/15 — 한 번의 실행"
    return 0
  fi
  blocked_add deploy_doctor "15/15 아님 — $line"
  return 1
}

# ── reset ────────────────────────────────────────────────────────────────
# 유일한 파괴 단계다. 실행 **전에** 승인 기록을 남긴다(dev 한정 상시 승인 · `.claude/rules/deploy.md`).
ACTIVE_TX_SQL="select count(*) from pg_stat_activity where datname in ('colab_platform','colab_ai') and state <> 'idle' and pid <> pg_backend_pid();"

# 복구 기록 — 정지 뒤 실패해서 앱을 되살린 자리를 남긴다(`result.json` 의 `recovery`).
recovery_add() {
  mkdir -p "$RUN_DIR"
  python3 - "$RUN_DIR/recovery.jsonl" "${CURRENT_STAGE:-?}" "$1" "$2" <<'PY'
import json, sys
path, stage, reason, code = sys.argv[1:5]
with open(path, "a") as f:
    f.write(json.dumps({"stage": stage, "action": "apps-start", "reason": reason,
                        "exitCode": int(code)}, ensure_ascii=False) + "\n")
PY
}

# ①′ 의 역연산. 정지 **뒤**의 어느 걸음이 실패해도 앱을 같은 compose·env 로 되살린다.
# 왜 = 종전에는 실패 경로에 역연산이 없어 dev 가 내려간 채 남았고 사람이 손으로 올렸다
#   (`DR-4-run-20260914T012505Z.md §7`·§8 ⑶). 무인 실행에 사람 한 걸음이 끼어 있으면 무인이 아니다.
# 이미지·볼륨·데이터는 건드리지 않는다 — `stop` 한 것을 `start` 하는 것뿐이다.
reset_recover_apps() {
  local why="$1" rc=0
  log "↩ 복구 — $why · 앱 $APP_UNITS 재기동(①′ 의 역연산 · 이미지·볼륨·데이터 무변)"
  ssh_dev "$(compose_cmd) start $APP_UNITS" || rc=$?
  recovery_add "$why" "$rc"
  [ "$rc" = 0 ] || warn "복구 재기동이 비영 종료했다(code=$rc) — 앱 상태를 직접 확인한다"
}

stage_reset() {
  write_approval_record || return 1

  # ── 읽기 전용 구간 ── 여기서 실패하면 dev 는 계속 돌고 있다(정지 전이다).
  log "① 실행 전 계수 — 연구실 경계를 건 상태에서 센다(읽기 전용)"
  ssh_dev "mkdir -p $REMOTE_OUT && chmod 700 $REMOTE_OUT" || return 1
  ssh_script "reset:count" <<EOF || return 1
set -euo pipefail
$(reset_docker_cmd) --phase count --report /out/count-before.json
test -s $REMOTE_OUT/count-before.json
EOF

  # 사전 질의가 실패하거나 진행 중 작업이 있으면 앱을 내리기 전에 중단한다.
  # 이후 생긴 작업은 정지 뒤 ①″에서 다시 확인한다.
  log "①ᵃ 정지 전 활성 트랜잭션 0 확인 — 마스터 롤 · 읽기 전용"
  psql_master_query "$ACTIVE_TX_SQL" "0" \
    || { blocked_add reset "정지 전 활성 트랜잭션 0 확인 실패"; return 1; }

  # ── 보호 구간 시작 ── 아래에서 실패하면 앱을 **자동으로 되살리고** 돌아온다.
  log "①′ 앱 4 단위 정지 — 되돌릴 수 없는 걸음(② 스키마 DROP) 직전에만 내린다"
  ssh_dev "$(compose_cmd) stop $APP_UNITS" || return 1

  log "①″ 활성 트랜잭션 0 확인 — 마스터 롤로 본다(비특권 롤은 state 를 NULL 로 받는다)"
  psql_master_query "$ACTIVE_TX_SQL" "0" \
    || { blocked_add reset "활성 트랜잭션 0 아님"; reset_recover_apps "①″ 활성 트랜잭션 확인 실패"; return 1; }

  log "② 두 체인 스키마 재생성"
  ssh_script "reset:schema" <<EOF || { blocked_add reset "스키마 재생성 실패"; reset_recover_apps "② 스키마 재생성 실패"; return 1; }
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

# 마스터 URL 로 읽기 전용 질의 한 벌. **출력을 그대로** 돌려준다 — 판정은 부르는 쪽이 한다.
# 근거: R-DEV-RESET §11-1 ⑴⑵⑷ — 스킴 치환 · --user 0 · postgres:16-alpine.
#
# SQL 은 `remote_assign` 으로 **base64 에 실어** 원격 셸에서 되돌린다(`lib.sh` 머리말).
# 그래야 값이 작은따옴표를 품어도 문장이 쪼개지지 않는다. docker 의 argv 에도 문장이 실리지 않는다.
psql_master_run() {
  local sql="$1"
  ssh_script "psql:master" <<EOF
set -euo pipefail
$(remote_assign SQL "$sql")
export SQL
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/master.url:/s/master.url:ro \\
  -e SQL \\
  $PSQL_IMAGE sh -c 'psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/master.url)" -c "\$SQL"'
EOF
}

# 같은 질의를 **계수 하나**로 판정한다. 기대값과 다르면 비영.
psql_master_query() {
  local sql="$1" expect="$2"
  # ⚠ 출력을 `STAGE_LOG` 에 **다시 적지 않는다** — `ssh_script` 가 이미 `tee` 로 적는다.
  #   두 번 적으면 같은 오류 줄이 두 벌 보여 실행 2회로 오독된다(DR-4 §6 부수 관찰).
  local out; out="$(psql_master_run "$sql")" || return 1
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
  ssh_dev "sudo COLAB_PG_MASTER_URL_FILE=$EC2_SECRETS_DIR/master.url bash $DEV_REPO_DIR/infra/dev/db-bootstrap.sh extensions" || return 1

  log "② 마이그레이션 두 체인 — up.sh ① 만 떼어 낸다(⑤ 의 GRANT 가 표를 요구한다)"
  ssh_dev "$(compose_cmd) --profile migrate run --rm -T migrate-platform < /dev/null" || return 1
  ssh_dev "$(compose_cmd) --profile migrate run --rm -T migrate-ai < /dev/null" || return 1

  log "②′ 체인별 버전 표 확인"
  # 근거: R-DEV-RESET §11-1 ⑹ — 표 이름은 `alembic_version_platform`·`alembic_version_ai` 다.
  #       `alembic_version` 을 보면 **적용된 것을 미적용으로 오판한다**.
  #       head 값 자체의 정오는 `up` 단계의 `deploy_doctor` ⑥⑦ 이 레포 트리와 대조해 판정한다.
  ssh_script "bootstrap:chain-heads" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/platform-owner-db.url:/s/platform.url:ro \\
  -v $EC2_SECRETS_DIR/ai-owner-db.url:/s/ai.url:ro \\
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
COLAB_OWNER_PASSWORD="\$(pw $EC2_SECRETS_DIR/platform-owner-db.url)"
COLAB_APP_PASSWORD="\$(pw $EC2_SECRETS_DIR/core-database.url)"
COLAB_AI_APP_PASSWORD="\$(pw $EC2_SECRETS_DIR/ai-db.url)"
COLAB_ACCOUNT_ADMIN_PASSWORD="\$(pw $EC2_SECRETS_DIR/account-admin-database.url)"
export COLAB_OWNER_PASSWORD COLAB_APP_PASSWORD COLAB_AI_APP_PASSWORD COLAB_ACCOUNT_ADMIN_PASSWORD
# account-admin 단계의 문자 집합 가드(base64url) — 어긋나면 값을 찍지 않고 멈춘다.
case "\$COLAB_ACCOUNT_ADMIN_PASSWORD" in
  *[!A-Za-z0-9_-]*) echo "account-admin 비밀번호가 base64url 집합 밖이다 — 멈춘다" >&2; exit 1 ;;
esac
for n in \$(bash $DEV_REPO_DIR/infra/staging/db-bootstrap.sh required-env); do
  eval "v=\\\${\$n:-}"; [ -n "\$v" ] || { echo "필수 환경변수 미설정: \$n" >&2; exit 1; }
done
sudo -E COLAB_PG_MASTER_URL_FILE=$EC2_SECRETS_DIR/master.url bash $DEV_REPO_DIR/infra/dev/db-bootstrap.sh app-grants
sudo -E COLAB_PG_MASTER_URL_FILE=$EC2_SECRETS_DIR/master.url bash $DEV_REPO_DIR/infra/dev/db-bootstrap.sh account-admin
unset COLAB_OWNER_PASSWORD COLAB_APP_PASSWORD COLAB_AI_APP_PASSWORD COLAB_ACCOUNT_ADMIN_PASSWORD
EOF

  log "④ 사후 확인 — 세 롤이 각자 URL 파일로 붙는가"
  ssh_script "bootstrap:verify-roles" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/core-database.url:/s/core.url:ro \\
  -v $EC2_SECRETS_DIR/ai-db.url:/s/ai.url:ro \\
  -v $EC2_SECRETS_DIR/account-admin-database.url:/s/aa.url:ro \\
  $PSQL_IMAGE sh -c '
    for f in /s/core.url /s/ai.url /s/aa.url; do
      psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" \$f)" -c "select 1" >/dev/null || exit 1
    done
    echo "역할 접속 3/3 ok"'
EOF
  log "⑤ 기존 정적 인증 파일 보호 백업 후 비우기 — 앱 기동 전"
  run python3 "$RESEED_DIR/accounts.py" clear-legacy --profile "$ACCOUNTS_FILE" --work "$ACCOUNTS_WORK_DIR" \
    --ssh "$COLAB_DEV_SSH" --key "$COLAB_DEV_KEY_FILE" --secrets-dir "$EC2_SECRETS_DIR" || return 1
}

# ── up ───────────────────────────────────────────────────────────────────
# up.sh 전체(마이그레이션 재확인 → 기동 → healthy → healthz) 뒤 deploy_doctor **1회**.
stage_up() {
  ssh_dev "sudo bash $DEV_STATE_DIR/up.sh" || return 1
  log "── ai 시드 계수(K3·K4 의 사전) — 세 표가 전부 0 보다 커야 한다"
  ssh_script "up:ai-seed" <<EOF || return 1
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/ai-owner-db.url:/s/ai.url:ro \\
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
    log "DRY ② ssh <dev> — 같은 컨테이너(--user 0) 안에서 계획 검토(_ops/ 0 건 · 접두사 uploads/·previews/ · 모드 0600 · 소유자 일치 · sha256 기재)"
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
  # `ssh_script` 가 이미 `tee` 로 적었다 — 여기서 다시 적지 않는다(오류 한 건을 두 번 보이게 한다).
  local sha256; sha256="$(printf '%s\n' "$out" | grep -Eo '\b[0-9a-f]{64}\b' | tail -1 || true)"
  [ -n "$sha256" ] || { blocked_add s3-plan "계획 sha256 을 읽지 못했다"; return 1; }

  # ⚠ 검토는 **초기화 도구와 같은 컨테이너 안**에서 돈다. 계획 파일은 그 컨테이너가 uid 0 · 0600
  #   으로 쓰므로 호스트 ssh 사용자(uid 1000)로는 소유자가 어긋나고 읽지도 못한다 — 2026-09-14
  #   3회차가 그 자리에서 멈췄다(DR-4 §7). 계획을 호스트 사용자에게 chown 하는 쪽으로 풀지 않는다.
  log "② 계획 검토 — 같은 컨테이너 안(소유자·모드) · _ops/ 0 건 · 접두사 uploads/·previews/ 둘뿐 · sha256 기재"
  ssh_script "s3:review" <<EOF || { blocked_add s3-plan "계획 검토 미달"; return 1; }
set -euo pipefail
$(s3_review_script "$REMOTE_OUT")
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
    # `${VAR:?}` 는 **셸을 끝낸다** — 그러면 `stage_end`·`report` 가 돌지 못한다(`die` 와 같은 이유).
    # 값이 없는 것도 「멈춘 자리」로 남겨야 하므로 하나씩 세어 돌아온다.
    local want=()
    [ -n "${RESEED_ACCOUNT_EMAIL:-}" ] || want+=("RESEED_ACCOUNT_EMAIL(첫 계정 이메일)")
    [ -n "${RESEED_ACCOUNT_NAME:-}" ]  || want+=("RESEED_ACCOUNT_NAME(첫 계정 이름)")
    [ -n "${RESEED_ACCOUNT_ID:-}" ]    || want+=("RESEED_ACCOUNT_ID(26자 ULID · ② ③ ④ 가 같은 값을 쓴다)")
    [ -n "${OPERATOR_PASSWORD_FILE:-}" ] || want+=("--operator-password-file(10자 이상 0600 파일)")
    if [ "${#want[@]}" -gt 0 ]; then
      die "prelude 에 필요한 값 ${#want[@]} 건이 없다 — ${want[*]}"
      return 1
    fi
  fi

  log "① 연구실 — provision-lab.sql (파일이 스스로 app.current_lab 을 건다)"
  local lab_sql
  lab_sql="$(python3 "$RESEED_DIR/accounts.py" sql --profile "$ACCOUNTS_FILE" --sql "$PROVISION_LAB_SQL")" || return 1
  ssh_script "prelude:lab" <<EOF || return 1
set -euo pipefail
umask 077
lab_sql=\$(mktemp)
trap 'rm -f "\$lab_sql"' EXIT
cat > "\$lab_sql" <<'COLAB_CANONICAL_LAB_SQL'
$lab_sql
COLAB_CANONICAL_LAB_SQL
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  -v "\$lab_sql":/s/lab.sql:ro \\
  $PSQL_IMAGE sh -c 'psql -v ON_ERROR_STOP=1 "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -f /s/lab.sql'
EOF

  # ② 는 ① 이 심지 않은 계정일 때만 돈다. 같은 id 면 **건너뛴다** — 2026-09-13 회차가 밟은 순서다
  # (`DR-2-run-2026-09-13.md` §5 ② 축자 「미실행(건너뜀)」 · 계수표 `d2_permission_switch` 0).
  # 왜 = ⑴ ① 이 같은 id·이메일로 `d1_account`＋`d2_member_role`(교수)을 이미 심는다.
  #      ⑵ ② 를 그대로 내면 `d2_permission_switch` **4행**이 새로 선다(① 은 0행 — 교수는 네 스위치가
  #         항상 켜진 것으로 판정되므로 행을 두지 않는다). 건너뛰지 않으면 09-13 기준선과 갈린다.
  #      ⑶ **다른 id** 를 주면 ② 를 돌린다. 그때 ① 과 같은 이메일이면 `UNIQUE (lab_id, email)` 에
  #         걸려 멈추는 것이 옳다 — 같은 사람에게 계정 두 개를 만들지 않는다.
  if [ -n "${PROVISION_LAB_ACCOUNT_ID:-}" ] && [ "$RESEED_ACCOUNT_ID" = "$PROVISION_LAB_ACCOUNT_ID" ]; then
    log "② 첫 계정 — 건너뜀 · ① provision-lab.sql 이 같은 id($RESEED_ACCOUNT_ID)로 이미 심었다(d2_permission_switch 0행 유지 · DR-2 회차와 같은 순서)"
  else
  log "② 첫 계정 — provision-account.sql (id 는 ③ ④ 가 그대로 재사용한다)"
  # 신원 다섯은 `remote_assign` 으로 싣고, **원격 셸 안에서** SQL 리터럴로 감싼다(`sqlq`).
  # 종전에는 `-v name="'"'"'<값>'"'"'"` 처럼 따옴표를 손으로 겹쳐 값을 heredoc 에 박았다 —
  # 값이 작은따옴표를 품으면(사람 이름의 아포스트로피) 그 자리에서 쪼개진다. `psql_master_query` 와 같은 결함이다.
  # `sqlq` 는 SQL 쪽 겹따옴표 규칙(`''`)까지 함께 지킨다 — 셸만 고치면 다음 겹에서 또 틀린다.
  ssh_script "prelude:account" <<EOF || return 1
set -euo pipefail
$(remote_assign ACCOUNT_ID "$RESEED_ACCOUNT_ID")
$(remote_assign ACCOUNT_LAB_ID "$LAB_ID")
$(remote_assign ACCOUNT_NAME "$RESEED_ACCOUNT_NAME")
$(remote_assign ACCOUNT_EMAIL "$RESEED_ACCOUNT_EMAIL")
$(remote_assign ACCOUNT_ROLE "$RESEED_ACCOUNT_ROLE")
sqlq() { printf "'%s'" "\$(printf '%s' "\$1" | sed "s/'/''/g")"; }
ACCOUNT_ID_Q=\$(sqlq "\$ACCOUNT_ID");     ACCOUNT_LAB_ID_Q=\$(sqlq "\$ACCOUNT_LAB_ID")
ACCOUNT_NAME_Q=\$(sqlq "\$ACCOUNT_NAME"); ACCOUNT_EMAIL_Q=\$(sqlq "\$ACCOUNT_EMAIL")
ACCOUNT_ROLE_Q=\$(sqlq "\$ACCOUNT_ROLE")
export ACCOUNT_ID_Q ACCOUNT_LAB_ID_Q ACCOUNT_NAME_Q ACCOUNT_EMAIL_Q ACCOUNT_ROLE_Q
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  -v $DEV_REPO_DIR/services/core-api/ops/provision-account.sql:/s/acct.sql:ro \\
  -e ACCOUNT_ID_Q -e ACCOUNT_LAB_ID_Q -e ACCOUNT_NAME_Q -e ACCOUNT_EMAIL_Q -e ACCOUNT_ROLE_Q \\
  $PSQL_IMAGE sh -c 'psql -v ON_ERROR_STOP=1 \\
    -v account_id="\$ACCOUNT_ID_Q" -v lab_id="\$ACCOUNT_LAB_ID_Q" \\
    -v name="\$ACCOUNT_NAME_Q" -v email="\$ACCOUNT_EMAIL_Q" \\
    -v role="\$ACCOUNT_ROLE_Q" \\
    "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -f /s/acct.sql'
EOF
  fi

  log "③ 첫 로그인 자격 — account_admin.login_credential INSERT 1건 (제품과 같은 두 함수로 해싱)"
  prelude_login_credential || return 1

  log "④ 서비스 운영자 — provision-service-operator.sql (FORCE RLS 아래라 경계를 먼저 건다)"
  # ⚠ `account_id` 는 **원문 그대로** 넘긴다 — `provision-service-operator.sql` 이 `:'account_id'`
  #   (psql 이 따옴표를 씌우는 꼴)로 읽는다. ② 의 `provision-account.sql` 은 맨 `:account_id` 라
  #   그쪽만 `sqlq` 로 미리 감싼다. 두 파일의 변수 꼴이 다르다 — 값의 꼴은 **파일이 정한다.**
  #   4회차 재개 2(`20260914T023537Z`)가 여기에 감싼 값을 넘겨 `'''<id>'''` 로 조회했고
  #   `INSERT 0 0` → 「지정한 계정이 없어 운영자를 등록하지 못했다」 로 멈췄다.
  #   `SET app.current_lab` 은 SQL 리터럴 자리라 종전대로 `sqlq` 로 감싼다.
  ssh_script "prelude:operator" <<EOF || return 1
set -euo pipefail
$(remote_assign ACCOUNT_ID "$RESEED_ACCOUNT_ID")
$(remote_assign ACCOUNT_LAB_ID "$LAB_ID")
sqlq() { printf "'%s'" "\$(printf '%s' "\$1" | sed "s/'/''/g")"; }
ACCOUNT_LAB_ID_Q=\$(sqlq "\$ACCOUNT_LAB_ID")
export ACCOUNT_ID ACCOUNT_LAB_ID_Q
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  -v $DEV_REPO_DIR/services/core-api/ops/provision-service-operator.sql:/s/op.sql:ro \\
  -e ACCOUNT_ID -e ACCOUNT_LAB_ID_Q \\
  $PSQL_IMAGE sh -c 'psql -v ON_ERROR_STOP=1 -v account_id="\$ACCOUNT_ID" \\
    -c "SET app.current_lab = \$ACCOUNT_LAB_ID_Q" \\
    "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -f /s/op.sql'
EOF
}

# ③ 만 따로 둔다 — 비밀번호가 **표준입력 한 줄**로만 움직인다.
# 해시는 제품과 같은 두 함수를 그대로 부른다(`hash_password` · `normalize_login_name`).
prelude_login_credential() {
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY ssh <dev> docker exec -i colab_v2_dev_core_api python -c  # login_credential INSERT (본문 = RESEED_PY 환경변수 · 비밀번호 = 표준입력 1줄)"
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
h = hash_password(pw).as_dict()   # 키 = kdf · salt · hash · n · r · p (열 이름 password_hash 와 다르다)
url = open(os.environ["COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE"]).read().strip()
eng = create_engine(url)
with eng.begin() as c:
    c.execute(text("SELECT pg_advisory_xact_lock(1131379081)"))
    # 바인드 이름은 제품 `routes/accounts.py` 의 문장 축자(`:hash` 가 `password_hash` 열에 들어간다).
    # 4회차 재개(`20260914T023145Z`)가 `:password_hash` 로 적어 「A value is required for bind
    # parameter 'password_hash'」 로 멈췄다 — 그 본문도 실모드로 돈 적이 없었다.
    # 멱등 — ①·② 의 SQL 과 같은 규칙(`ON CONFLICT DO NOTHING`). prelude 를 `--from prelude` 로 다시
    # 밟아도 이미 선 자격을 두 번 심지 않는다(PK = account_id). 0행이면 「이미 있음」이고 실패가 아니다.
    r = c.execute(text(
        "INSERT INTO account_admin.login_credential"
        " (account_id, login_name, kdf, salt, password_hash, n, r, p)"
        " VALUES (:account_id, :login_name, :kdf, :salt, :hash, :n, :r, :p)"
        " ON CONFLICT (account_id) DO NOTHING"),
        dict(account_id=os.environ["RESEED_ACCOUNT_ID"],
             login_name=normalize_login_name(os.environ["RESEED_ACCOUNT_EMAIL"]), **h))
    n_rows = r.rowcount
print("login_credential 삽입 %d행(0 = 이미 있음 · 그대로 둔다) · must_change_password 는 DB 기본값 true" % n_rows)
PY
)"
  # 표준입력 한 줄기에 파이썬 본문 ＋ `__PW__` 구분줄 ＋ 비밀번호 한 줄을 실어 보낸다.
  # 원격에서 둘로 갈라 파이썬 본문은 **환경변수**(`RESEED_PY`)로, 비밀번호는 컨테이너 표준입력으로만 넣는다.
  # 비밀번호는 argv·환경변수·로그 어디에도 남지 않는다(런북 §5 ③ 축자 조건) — 본문에는 비밀이 없다.
  #
  # ⚠ 본문을 컨테이너 안 **파일**로 나르지 않는다(종전 `docker cp … :/tmp/reseed_cred.py`).
  #   왜 = `docker cp` 는 호스트 쪽 소유자(ssh 사용자 uid 1000 · 0600)를 그대로 옮기고 컨테이너의
  #   앱 사용자는 uid 10001(`colab`)이라 `python /tmp/reseed_cred.py` 가 `Permission denied` 로 죽고
  #   sticky `/tmp` 의 남의 파일이라 `rm -f` 도 실패한다(DR-4 4회차 `20260914T022417Z` 실측 · prelude ③).
  #   그 줄은 **실모드로 돈 적이 없었고** `--dry-run`·`--rehearse` 어느 쪽도 밟지 않았다.
  #   환경변수로 실으면 파일·소유자·모드·뒷정리가 전부 사라진다 — `python -c` 가 `exec` 로 읽는다.
  log "RUN ssh <dev> docker exec -i colab_v2_dev_core_api python -c  # login_credential INSERT (본문 = RESEED_PY 환경변수 · 비밀번호 = 표준입력 1줄)"
  local remote; remote=$(cat <<REMOTE
set -euo pipefail
$(remote_assign RESEED_ACCOUNT_ID "$RESEED_ACCOUNT_ID")
$(remote_assign RESEED_ACCOUNT_EMAIL "$RESEED_ACCOUNT_EMAIL")
export RESEED_ACCOUNT_ID RESEED_ACCOUNT_EMAIL
all=\$(mktemp); chmod 600 "\$all"; cat > "\$all"
RESEED_PY=\$(sed '/^__PW__\$/,\$d' "\$all")
pwf=\$(mktemp); chmod 600 "\$pwf"; sed -n '/^__PW__\$/,\$p' "\$all" | tail -n +2 > "\$pwf"
rm -f "\$all"
rc=0
# 값은 **원격 셸 변수**에서만 꺼낸다 — sudo 는 환경을 비우므로 자기 인자로 넘기고(큰따옴표 한 겹),
# docker 로는 이름만 준다. heredoc 에 값을 박지 않으므로 따옴표를 품은 이름도 쪼개지지 않는다.
sudo RESEED_ACCOUNT_ID="\$RESEED_ACCOUNT_ID" RESEED_ACCOUNT_EMAIL="\$RESEED_ACCOUNT_EMAIL" RESEED_PY="\$RESEED_PY" \\
  docker exec -i -e RESEED_ACCOUNT_ID -e RESEED_ACCOUNT_EMAIL -e RESEED_PY \\
  colab_v2_dev_core_api python -c 'import os; exec(os.environ["RESEED_PY"])' < "\$pwf" || rc=\$?
shred -u "\$pwf" 2>/dev/null || rm -f "\$pwf"
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
  # preflight ⑽ 이 판정한 것과 **같은 생성기**다(`BUILD_PLAN_PY`).
  run python3 "$BUILD_PLAN_PY" \
      --ref-root "${COLAB_REF_ROOT:-}" --md-root "${MD_ROOT:-}" --work-dir "$SEED_WORK_DIR" || return 1

  log "② 러너 — 교수 로그인 · 무소속 운영자 4명 · 프로젝트 · 데이터셋 · 확인 · 보고"
  local runner="$REPO_ROOT/dev-package/tools/dev-seed/runner.py" i phase
  local args=(--base-url "$DEV_URL" --work-dir "$SEED_WORK_DIR" --session "$AB_SESSION" --account "$RESEED_ACCOUNT_EMAIL")
  run python3 "$runner" --phase login "${args[@]}" || return 1
  for i in 0 1 2 3; do
    run python3 "$runner" --phase accounts "${args[@]}" --accounts-file "$ACCOUNTS_WORK_DIR/operator-$i.json" \
      --accounts-password-file "$ACCOUNTS_WORK_DIR/initial-$i.txt" || return 1
  done
  run python3 "$RESEED_DIR/accounts.py" check-created --profile "$ACCOUNTS_FILE" --work "$ACCOUNTS_WORK_DIR" || return 1
  for phase in projects datasets verify report; do
    run python3 "$runner" --phase "$phase" "${args[@]}" || return 1
  done
}

# ── verify ───────────────────────────────────────────────────────────────
# 자료 상세 검증 후 계정 초기 비밀번호 복원·임시 운영자 해제와 로그인 검증을 수행한다.
# 한 번의 상세 화면 순회로 넷을 함께 잰다 — 가공 단계 · 「미지정」 · 프로젝트 연결 · 미리보기 판정.
# 대기 = 45,000 ms. 근거 = DR-3 실측에서 viz-render 실소요가 20,037~38,391 ms 였고
#        core-api 가 10,02x ms 에 끊어 503 을 냈다(`dev-package/sessions/DR-3-run-2026-09-13.md §6`).
#        뒷단 개선은 이 회차 범위 밖(`PV-2`)이라 여기서는 **판정만** 한다.
PREVIEW_WAIT_MS="${COLAB_RESEED_PREVIEW_WAIT_MS:-45000}"

# 브라우저 세션 — 러너(`dev-seed/runner.py` `DEFAULT_SESSION`)가 로그인해 둔 **그 세션**을 이름으로 쓴다.
# ⚠ `AGENT_BROWSER_SESSION_NAME` 환경변수는 agent-browser 가 읽지 않는다(4회차 `20260914T035058Z` 실측 —
#   env 만 준 호출은 `default` 세션으로 가 로그인 화면을 27번 열었다). 세션은 **`--session` 인자로만** 고른다.
AB_SESSION="${COLAB_RESEED_BROWSER_SESSION:-colab-dev}"
ab_dev() { run_capture agent-browser --session "$AB_SESSION" "$@"; }

# 미리보기 판정 — `preview-unavailable` 의 **계수 한 개**로 가른다.
#   0        → 성립      (「볼 수 없다」 표시가 없다)
#   1 이상   → 미성립    (표시가 있다)
#   빈 값·숫자 아님 → **판정불가**
#
# ⚠ 종전에는 `[ "${shown:-0}" -gt 0 ]` 이라 **값을 못 받은 것이 0 과 같았다** — 브라우저가
#   응답하지 않았거나 선택자가 바뀌어 아무 값도 안 온 회차가 「전건 성립」으로 적혔다.
#   못 잰 것을 잰 것으로 세지 않는다(`CLAUDE.md §4` green-by-skip 과 같은 계열).
preview_verdict() {
  local v="${1:-}"
  case "$v" in
    ""|*[!0-9]*) printf '판정불가'; return ;;
  esac
  if [ "$v" -gt 0 ]; then printf '미성립'; else printf '성립'; fi
}

# 순회 표(`preview-judgment.tsv`)의 계수 칸을 판정한다.
# **빈 칸·숫자 아닌 값은 0 이 아니라 「재지 못한 것」이다** — 둘을 같은 모양으로 접으면
# 화면에서 한 값도 못 받은 회차가 「미지정 0건 · 프로젝트 전건 연결」로 통과한다(fail-open).
# 판정불가는 성립도 미성립도 아니므로 미지정에도 미연결에도 세지 않고 **따로 미달로 낸다.**
# $1 = preview-judgment.tsv · $2 = 판정 JSON 출력 경로 · 종료 1 = 계수 판정 미달
count_verdict() {
  python3 - "$1" "$2" <<'CVPY'
import json, sys
tsv, out = sys.argv[1:3]
rows = [l.rstrip("\n").split("\t") for l in open(tsv) if l.strip()]
def cnt(s):
    s = s.strip()
    return int(s) if s.isdigit() else None
# r[2]=가공 단계 · r[5]=「미지정」 계수 · r[6]=usage-card 계수
res = {
    "countUndecidedSeq": [r[0] for r in rows if cnt(r[5]) is None or cnt(r[6]) is None],
    "levelUndecidedSeq": [r[0] for r in rows if not r[2].strip() or r[2].strip() == "?"],
    "unsetSeq": [r[0] for r in rows if (cnt(r[5]) or 0) > 0],
    "unlinkedSeq": [r[0] for r in rows if cnt(r[6]) == 0],
    "unsetCount": sum(cnt(r[5]) or 0 for r in rows),
}
json.dump(res, open(out, "w"), ensure_ascii=False, indent=2)
bad = []
if res["countUndecidedSeq"]: bad.append("계수 판정불가 seq %s" % ",".join(res["countUndecidedSeq"]))
if res["levelUndecidedSeq"]: bad.append("가공 단계 판정불가 seq %s" % ",".join(res["levelUndecidedSeq"]))
if res["unsetSeq"]: bad.append("「미지정」 %d건 seq %s" % (res["unsetCount"], ",".join(res["unsetSeq"])))
if res["unlinkedSeq"]: bad.append("프로젝트 미연결 seq %s" % ",".join(res["unlinkedSeq"]))
print("계수 판정 — " + ("전건 일치" if not bad else " · ".join(bad)))
raise SystemExit(1 if bad else 0)
CVPY
}

account_finalize() {
  local binding
  binding="$(python3 "$RESEED_DIR/accounts.py" check-details --profile "$ACCOUNTS_FILE" --work "$ACCOUNTS_WORK_DIR" --target-sha "$TARGET_SHA")" || return 1
  python3 "$RESEED_DIR/accounts.py" finalize --profile "$ACCOUNTS_FILE" --work "$ACCOUNTS_WORK_DIR" \
    --binding "$binding" --base-url "$DEV_URL" --ssh "$COLAB_DEV_SSH" --key "$COLAB_DEV_KEY_FILE" --secrets-dir "$EC2_SECRETS_DIR"
}

verify_seed_contract() {
  python3 - "$1" "$EXPECT_DATASETS" "$EXPECT_EDGES" <<'PY'
import json, sys
path, nds, nedge = sys.argv[1:4]
v = json.load(open(path))
nds, nedge = int(nds), int(nedge)
bad = []
if v.get("dataset_count_state") != nds: bad.append("상태 데이터셋 계수 %s" % v.get("dataset_count_state"))
if v.get("periods_expected") != nds: bad.append("기간 기대 계수 %s" % v.get("periods_expected"))
if v.get("periods_ok") != nds or v.get("periods_missing"): bad.append("저장 기간 %s/%s" % (v.get("periods_ok"), nds))
if v.get("model_input_descriptions_ok") != 2 or v.get("model_input_descriptions_missing"):
    bad.append("모델 입력 설명 %s/2" % v.get("model_input_descriptions_ok"))
if v.get("edges_ok") != nedge or v.get("edges_missing"): bad.append("간선·역할 %s/%s" % (v.get("edges_ok"), nedge))
print("러너 검증 — " + ("기간·설명·간선 전건 일치" if not bad else " · ".join(bad)))
raise SystemExit(1 if bad else 0)
PY
}

stage_verify() {
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY 러너 verify.json 계수 대조(데이터셋 $EXPECT_DATASETS · 프로젝트 $EXPECT_PROJECTS · 간선 $EXPECT_EDGES)"
    log "DRY agent-browser open /datasets/<id> ×$EXPECT_DATASETS — 대기 ${PREVIEW_WAIT_MS}ms · 가공 단계 · 「미지정」 · usage-card · 미리보기 판정"
    log "DRY 정본 md 의 가공 단계 분포와 대조 · 미지정 0 · 프로젝트 미연결 0"
    return 0
  fi

  local state="$SEED_WORK_DIR/state.json" verify="$SEED_WORK_DIR/verify.json"
  [ -f "$verify" ] || { blocked_add verify "verify.json 부재 — seed 단계 산출물이 없다"; return 1; }
  verify_seed_contract "$verify" || { blocked_add verify "러너 기간·설명·간선 검증 미달"; return 1; }

  if [ -f "$ACCOUNTS_WORK_DIR/details-verified.json" ]; then
    log "같은 자료 검증 증거를 확인하고 계정 최종화·로그인 검증만 재개"
    account_finalize || return 1
    python3 - "$ACCOUNTS_WORK_DIR/details-verified.json" "$RUN_DIR" <<'ACCOUNT_RESUME'
import json,pathlib,shutil,sys
source=pathlib.Path(json.loads(pathlib.Path(sys.argv[1]).read_text())['run_dir']);target=pathlib.Path(sys.argv[2])
for name in ('counts.json','preview-judgment.tsv'):
 if source.resolve()!=target.resolve():shutil.copyfile(source/name,target/name)
ACCOUNT_RESUME
    return $?
  fi
  local manifest="$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml"
  for f in "$state" "$verify" "$manifest"; do
    [ -f "$f" ] || { blocked_add verify "$(basename "$f") 부재 — seed 단계 산출물이 없다"; return 1; }
  done

  log "① 상세 화면 순회 — $EXPECT_DATASETS 건 · 한 건당 최대 ${PREVIEW_WAIT_MS}ms · 브라우저 세션 $AB_SESSION"
  # id 가 없는 행은 `-` 로 찍는다 — 탭이 연달아 오면 `read` 가 빈 칸을 접어 **이름이 id 자리로 밀린다**
  # (4회차 `20260914T035058Z` 실측 · seq 13 이 `/datasets/SPI-4weeks` 를 열었다).
  local ids; ids="$(python3 - "$state" <<'PY'
import json, sys
st = json.load(open(sys.argv[1]))
for seq, row in sorted(st.get("datasets", {}).items(), key=lambda kv: int(kv[0])):
    print("%s\t%s\t%s" % (seq, row.get("dataset_id") or "-", row.get("name") or "-"))
PY
)"
  : > "$RUN_DIR/preview-judgment.tsv"
  local seq did name t0 t1 ms shown level unset_lv usage login_n info_n slot_state
  while IFS=$'\t' read -r seq did name; do
    [ -n "$seq" ] || continue
    [ "$name" = - ] && name=""
    if [ "$did" = - ] || [ -z "$did" ]; then
      printf '%s\t%s\t?\t미성립\t0\t?\t?\t데이터셋 id 미확보\n' "$seq" "$name" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name — 데이터셋 id 미확보"
      continue
    fi
    t0="$(date +%s%3N)"
    if ! ab_dev open "$DEV_URL/datasets/$did" >/dev/null 2>&1; then
      printf '%s\t%s\t?\t판정불가\t0\t?\t?\t페이지 이동 실패\n' "$seq" "$name" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name — 페이지 이동 실패 · 이전 화면을 판정하지 않는다"
      continue
    fi
    # Container presence is not completion: its slot starts in idle/drawing.
    # Poll the existing state attribute, keeping missing values undecidable.
    slot_state=""
    while :; do
      slot_state="$(ab_dev get attr '[data-testid="dt-preview-slot"]' data-preview-slot-state 2>/dev/null | tr -d ' \t\r\n')"
      case "$slot_state" in done|failed) break ;; esac
      t1="$(date +%s%3N)"
      [ "$((t1 - t0))" -lt "$PREVIEW_WAIT_MS" ] || break
      sleep 0.05
    done
    t1="$(date +%s%3N)"; ms=$(( t1 - t0 ))
    # ⚠ 화면이 **상세 화면인지 먼저** 잰다 — 로그인 화면·빈 화면에서도 `preview-unavailable` 계수는 0 이라
    #   그대로 읽으면 「성립」이 된다(4회차 `20260914T035058Z` 실측 · 27건 전건이 로그인 화면이었다).
    #   로그인 화면(`login-submit` ≥ 1) 이거나 기본 정보 격자(`basic-info`)가 없으면 **판정불가**다.
    login_n="$(ab_dev get count '[data-testid="login-submit"]' 2>/dev/null | tr -d ' \t\r\n')"
    info_n="$(ab_dev get count '[data-testid="basic-info"]' 2>/dev/null | tr -d ' \t\r\n')"
    # `tr -dc` 로 숫자만 남기지 않는다 — 그러면 「아무 값도 못 받음」과 「0」이 같은 모양이 된다.
    shown="$(ab_dev get count '[data-testid="preview-unavailable"]' 2>/dev/null | tr -d ' \t\r\n')"
    level="$(ab_dev get text '[data-testid="ig-가공 단계"]' 2>/dev/null | tr '\n' ' ')"
    # 계수도 같은 이유로 `tr -dc` 를 쓰지 않는다 — 숫자만 남기면 「못 받음」이 「0」이 된다.
    unset_lv="$(ab_dev get count '[data-testid="ig-unset-가공 단계"]' 2>/dev/null | tr -d ' \t\r\n')"
    usage="$(ab_dev get count '[data-testid="usage-card"]' 2>/dev/null | tr -d ' \t\r\n')"
    local verdict; verdict="$(preview_verdict "$shown")"
    if [ "${login_n:-x}" != 0 ]; then
      verdict=판정불가; level=""; unset_lv=""; usage=""
      blocked_add verify "seq=$seq $name — 로그인 화면이다(login-submit 계수 [$login_n]) · 브라우저 세션 $AB_SESSION 미로그인 · 판정 불가"
    elif [ "${info_n:-x}" != 1 ]; then
      verdict=판정불가; level=""; unset_lv=""; usage=""
      blocked_add verify "seq=$seq $name — 상세 화면이 서지 않았다(basic-info 계수 [$info_n]) · 판정 불가"
    elif [ "$slot_state" = failed ]; then
      verdict=미성립
      blocked_add verify "seq=$seq $name — 미리보기 최종 상태가 failed다"
    elif [ "$slot_state" != done ]; then
      verdict=판정불가
      blocked_add verify "seq=$seq $name — 미리보기 최종 상태를 확인하지 못했다"
    elif [ "$verdict" = 판정불가 ]; then
      blocked_add verify "seq=$seq $name — preview-unavailable 계수를 읽지 못했다(받은 값 [$shown]) · 미리보기 판정 불가"
    fi
    # 받은 값을 **그대로** 적는다. `:-0`·`:-?` 로 기본값을 박으면 표만 보고는
    # 「0 을 받았다」와 「아무 값도 못 받았다」를 가를 수 없다.
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n' \
      "$seq" "$name" "$level" "$verdict" "$ms" "$unset_lv" "$usage" >> "$RUN_DIR/preview-judgment.tsv"
  done <<< "$ids"

  log "② 계수 대조 — 러너 verify.json ＋ 순회 결과 ＋ 정본 등재표"
  # 계수 칸 판정을 먼저 따로 낸다(판정불가 포함). 아래 대조가 그 결과를 그대로 읽는다.
  count_verdict "$RUN_DIR/preview-judgment.tsv" "$RUN_DIR/count-verdict.json" || true
  python3 - "$verify" "$manifest" "$RUN_DIR/preview-judgment.tsv" "$RUN_DIR/counts.json" \
      "$EXPECT_DATASETS" "$EXPECT_PROJECTS" "$EXPECT_EDGES" "$RUN_DIR/count-verdict.json" <<'PY' || return 1
import json, sys
try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML 이 없다 — 등재표 대조 불가")
verify, manifest, tsv, out, nds, nproj, nedge, cvpath = sys.argv[1:9]
v = json.load(open(verify))
m = yaml.safe_load(open(manifest))
cv = json.load(open(cvpath))
rows = [l.rstrip("\n").split("\t") for l in open(tsv) if l.strip()]
want = {}
for d in m.get("datasets", []):
    want[str(d.get("seq"))] = str(d.get("processing_level") or d.get("level") or "")
got = {r[0]: r[2] for r in rows}
level_mismatch = [s for s, w in want.items() if w and w not in (got.get(s) or "")]
# 등재표 쪽 가공 단계가 비어 있으면 **대조할 것이 없었던 것**이다.
# 종전에는 `if w and …` 로 그 행을 건너뛰어, 양쪽이 다 비면 통과로 접혔다(fail-open).
manifest_level_missing = sorted((s for s, w in want.items() if not w), key=lambda x: int(x) if x.isdigit() else 0)
# 계수 칸 판정은 count_verdict 가 낸 것을 그대로 쓴다 — 빈 칸은 0 이 아니다.
unset = cv["unsetSeq"]
unlinked = cv["unlinkedSeq"]
count_undecided = cv["countUndecidedSeq"]
level_undecided = cv["levelUndecidedSeq"]
undecided = [r[0] for r in rows if r[3] == "판정불가"]
unestablished = [r[0] for r in rows if r[3] == "미성립"]
res = {
    "datasets": {"expected": int(nds), "ui": v.get("dataset_count_ui"), "state": v.get("dataset_count_state")},
    "projects": {"expected": int(nproj), "byProject": len(v.get("by_project") or {})},
    "edges": {"expected": int(nedge), "ok": v.get("edges_ok"), "missing": v.get("edges_missing")},
    "periods": {"expected": int(nds), "reportedExpected": v.get("periods_expected"),
                "ok": v.get("periods_ok"), "missing": v.get("periods_missing")},
    "modelInputDescriptions": {"expected": 2, "ok": v.get("model_input_descriptions_ok"),
                               "missing": v.get("model_input_descriptions_missing")},
    "processingLevel": {"mismatchSeq": level_mismatch, "unsetSeq": unset,
                        "undecidedSeq": level_undecided},
    "usageUndecidedSeq": count_undecided,
    "manifestLevelMissingSeq": manifest_level_missing,
    "projectUnlinkedSeq": unlinked,
    "previewRows": len(rows),
    "previewEstablished": sum(1 for r in rows if r[3] == "성립"),
    "previewUndecidedSeq": undecided,
    "previewUnestablishedSeq": unestablished,
}
json.dump(res, open(out, "w"), ensure_ascii=False, indent=2)
bad = []
# 「판정불가」는 성립도 미성립도 아니다 — **재지 못한 것**이고 통과로 세지 않는다.
if undecided: bad.append("미리보기 판정불가 seq %s" % ",".join(undecided))
if unestablished: bad.append("미리보기 미성립 seq %s" % ",".join(unestablished))
# 계수·가공 단계·등재표도 같다 — **재지 못한 것**을 0 으로 접지 않는다.
if count_undecided: bad.append("계수 판정불가 seq %s" % ",".join(count_undecided))
if level_undecided: bad.append("가공 단계 판정불가 seq %s" % ",".join(level_undecided))
if manifest_level_missing: bad.append("등재표 가공 단계 부재 seq %s" % ",".join(manifest_level_missing))
if res["datasets"]["ui"] != int(nds): bad.append("데이터셋 계수 %s" % res["datasets"]["ui"])
if res["edges"]["ok"] != int(nedge): bad.append("간선 계수 %s" % res["edges"]["ok"])
if level_mismatch: bad.append("가공 단계 불일치 seq %s" % ",".join(level_mismatch))
if unset: bad.append("「미지정」 seq %s" % ",".join(unset))
if unlinked: bad.append("프로젝트 미연결 seq %s" % ",".join(unlinked))
if len(rows) != int(nds): bad.append("판정 표 %d 행" % len(rows))
print("대조 결과 — " + ("전건 일치" if not bad else " · ".join(bad)))
raise SystemExit(1 if bad else 0)
PY
  [ "$?" -eq 0 ] || return 1
  python3 "$RESEED_DIR/accounts.py" record-details --profile "$ACCOUNTS_FILE" --work "$ACCOUNTS_WORK_DIR" \
    --run-dir "$RUN_DIR" --target-sha "$TARGET_SHA" >/dev/null || return 1
  account_finalize
}

# ── rehearse ─────────────────────────────────────────────────────────────
# **아무것도 바꾸지 않는 실모드 한 벌.** 원격 원시동작을 하나씩 실제로 내 보고
# 받은 것을 기대와 대조한다. 한 건이라도 어긋나면 그 **이름을 대고** 비영 종료한다.
#
# 왜 있나 = 실모드 정지가 세 회차 내리 **한 번도 실행된 적 없는 원격 줄**에서 났다
#   (deploy ⑤ → preflight secrets → reset ①″). `--dry-run` 은 명령을 찍기만 하므로
#   그 줄을 원격 셸이 어떻게 읽는지는 파괴 단계를 밟고 나서야 드러났다.
#   리허설은 그 순서를 끊는다 — 부수는 걸음 **앞에** 실제 왕복을 놓는다.
#
# 하지 않는 것 = 쓰기·정지·삭제·적용. 계획(plan)은 만들되 **적용하지 않고** 임시 폴더에만 둔다.
# `--dry-run` 과 함께 주면 여느 단계와 같이 명령을 찍기만 한다.
REH_OK=0
REH_BAD=()

# 받은 것을 **고정 문자열**로 판정한다. $1=원시동작 이름 · $2=기대 문자열 · $3=받은 것.
# ⚠ 받은 것을 **인자로** 받는다 — 파이프로 넘기면 오른쪽이 서브셸이라 계수가 사라진다.
reh() { _reh_judge "$1" "$2" -F "${3-}"; }
# 받은 것을 **정규식**으로 판정한다(계수·해시처럼 값이 매번 다른 자리).
reh_re() { _reh_judge "$1" "$2" -E "${3-}"; }

_reh_judge() {
  local name="$1" want="$2" mode="$3" got="${4-}"
  if printf '%s\n' "$got" | grep -q "$mode" -- "$want"; then
    REH_OK=$(( REH_OK + 1 ))
    log "  ✓ $name — 기대 응답과 일치"
  else
    REH_BAD+=("$name")
    log "  ✗ $name — 기대 응답 미검출 (원문은 단계 로그)"
    blocked_add "rehearse:$name" "기대 [$want] 미검출"
  fi
}

# 같은 보호 사본을 후보 검사·executor --check·실행에 쓴다. 원본 변경은 실행에 섞이지 않는다.
release_plan_execute() (
  local mode="$1"
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY release executor $mode — plan=${RELEASE_PLAN:-<release-plan>} · 외부 실행 0"
    return 0
  fi
  if [ -z "${RELEASE_PLAN:-}" ] || [ ! -f "$RELEASE_PLAN" ]; then
    blocked_add release-plan "--release-plan 입력 부재 — 배포 계획 미검증"
    log "✗ release-plan — 입력 부재·미검증"
    return 78
  fi
  local full head rc=0 out plan source snapshot_dir
  source="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$RELEASE_PLAN")" || return 78
  full="$(run_capture git -C "$REPO_ROOT" rev-parse --verify "$TARGET_SHA^{commit}")" || return 78
  head="$(run_capture git -C "$REPO_ROOT" rev-parse --verify HEAD)" || return 78
  if [ "$head" != "$full" ]; then
    blocked_add release-plan "작업 HEAD와 배포 후보 SHA 불일치"
    return 1
  fi
  snapshot_dir="$(mktemp -d "$(cd "$RUN_DIR" && pwd)/release-plan.XXXXXX")" || return 78
  plan="$snapshot_dir/plan.json"
  trap 'rm -f "$plan"; rmdir "$snapshot_dir"' EXIT
  umask 077
  cp -- "$source" "$plan" || return 78
  chmod 600 "$plan" || return 78
  python3 - "$plan" "$full" <<'PYPLAN' || { blocked_add release-plan "dev 대상/후보 SHA 불일치·재귀 호출 또는 계획 손상"; return 1; }
import json,sys
try:
    plan=json.load(open(sys.argv[1]))
    targets=plan['targets']
    if len(targets)!=1 or targets[0]['name']!='dv' or targets[0]['version']!=sys.argv[2]:
        raise ValueError()
    # argv에 명시된 reseed.sh 재진입을 거절한다. 임의 shell 코드 전체를 분석하지는 않는다.
    if any('reseed.sh' in arg for cmd in targets[0].get('deploy',[]) for arg in cmd):
        raise ValueError()
except (OSError,ValueError,KeyError,TypeError):
    print('release-plan: dev 단일 대상/현재 후보 SHA가 일치하고 reseed 재귀 호출이 없어야 한다',file=sys.stderr)
    raise SystemExit(1)
PYPLAN
  out="$(cd "$REPO_ROOT" && run_capture python3 "$REPO_ROOT/scripts/deploy_release.py" run --plan "$plan" --check)" || rc=$?
  printf '%s\n' "$out" | redact >> "$STAGE_LOG"
  if [ "$rc" -ne 0 ]; then
    blocked_add release-plan "executor --check 실패 $rc — 배포 계획 미검증"
    return "$rc"
  fi
  if [ "$mode" = check ]; then
    log "✓ executor --check — 후보 계획·pre-evidence 통과; build/ship/tree 실제 실행 준비성 미측정"
    return 0
  fi
  log "release executor — 검증한 동일 계획으로 배포·검증 1회 (알림 범위는 배포 결과)"
  (cd "$REPO_ROOT" && run python3 "$REPO_ROOT/scripts/deploy_release.py" run --plan "$plan" --notification-off) || rc=$?
  if [ "$rc" -ne 0 ]; then blocked_add release-plan "executor run 실패 $rc"; fi
  return "$rc"
)

rehearse_release_plan() { release_plan_execute check; }

stage_rehearse() {
  REH_OK=0; REH_BAD=()
  local reh_out="$REMOTE_OUT/rehearse"

  if [ "$DRY_RUN" = 1 ]; then
    log "DRY 리허설 원시동작 10 — psql:master(따옴표 든 SQL) · ssh_script(따옴표·\$·백틱 되받기)"
    log "DRY   · compose ps · 마이그레이터 alembic current 두 체인 · s3-plan ＋ 계획 검토(임시 폴더 · 적용 없음)"
    log "DRY   · postgres:16-alpine 소유자 URL SELECT 1 · deploy_doctor 1회 · 러너 --phase report · agent-browser 제목"
    log "DRY 아무것도 바꾸지 않는다 — dry-run 에서는 원격에 한 바이트도 내지 않는다"
    return 0
  fi

  rehearse_release_plan || return $?
  local got

  # ⑴ psql_master_query 의 전송로 — 작은따옴표가 든 SQL 이 그대로 닿아야 한다.
  got="$(psql_master_run "SELECT 'quoted' AS q, count(*) FROM pg_stat_activity WHERE datname = 'colab_platform'")"
  reh_re psql_master_query '^quoted\|[0-9]+$' "$got"

  # ⑵ ssh_script — 셸이 싫어하는 글자를 원격이 **글자 그대로** 되받는가.
  local echo_payload="따옴표'한겹 \"두겹\" \$HOME \`id\` 끝"
  got="$(ssh_script "rehearse:ssh-echo" <<EOF
set -euo pipefail
$(remote_assign PAYLOAD "$echo_payload")
printf '%s\n' "\$PAYLOAD"
EOF
)"
  reh ssh_script "$echo_payload" "$got"

  # ⑶ compose 호출 앞머리 — `stage_reset` 의 stop/start 와 `stage_bootstrap` 이 쓰는 바로 그 한 벌.
  got="$(ssh_script "rehearse:compose-ps" <<EOF
set -euo pipefail
$(compose_cmd) ps --services
EOF
)"
  reh compose_ps core-api "$got"

  # ⑷ 마이그레이터 이미지 — 두 체인 모두 읽기 전용 `alembic current`.
  got="$(ssh_script "rehearse:alembic-platform" <<EOF
set -euo pipefail
$(compose_cmd) --profile migrate run --rm -T migrate-platform current < /dev/null
EOF
)"
  reh_re migrator_platform '\(head\)' "$got"
  got="$(ssh_script "rehearse:alembic-ai" <<EOF
set -euo pipefail
$(compose_cmd) --profile migrate run --rm -T migrate-ai current < /dev/null
EOF
)"
  reh_re migrator_ai '\(head\)' "$got"

  # ⑸ 초기화 도구 — **계획만** 낸다. 임시 폴더에 쓰고 지운다. `--phase s3-apply` 는 부르지 않는다.
  #   계획을 낸 뒤 `stage_s3` ② 와 **같은 검토 본문**을 그 계획에 돌린다 — 바꾸는 것은 없다.
  #   왜 = 종전 ⑸ 는 계획만 내고 지워 ② 검토는 실모드로 돈 적이 없었다(DR-4 §7).
  got="$(ssh_script "rehearse:s3-plan" <<EOF
set -euo pipefail
mkdir -p $reh_out && chmod 700 $reh_out
$(reset_docker_cmd "$reh_out") --phase s3-plan --plan-out /out/plan.json --report /out/s3-plan.json
$(s3_review_script "$reh_out")
rm -rf $reh_out
EOF
)"
  reh_re reset_tool_s3_plan '계획 검토 ok — 키 [0-9]+ 건 · 멀티파트 [0-9]+ 건 · 접두사 .* · sha256 [0-9a-f]{64}' "$got"

  # ⑹ postgres:16-alpine — 읽기 전용 마운트 ＋ 스킴 치환 ＋ SELECT 1.
  got="$(ssh_script "rehearse:psql-owner" <<EOF
set -euo pipefail
docker run --rm --network host --user 0 \\
  -v $EC2_SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  $PSQL_IMAGE sh -c 'psql -tA "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -c "select 1"'
EOF
)"
  reh_re psql_owner_url '^1$' "$got"

  # ⑺ deploy_doctor — **한 번** 돌리고 `doctor_summary_line` 으로 읽는다(완료 정의와 같은 파서).
  local doctor_out doctor_rc=0
  doctor_out="$(ssh_dev_capture "sudo bash $DOCTOR_PROBE")" || doctor_rc=$?
  printf '%s\n' "$doctor_out" | redact >> "$STAGE_LOG"
  got="$(printf '%s\n' "$doctor_out" | doctor_summary_line || true)"
  [ "$doctor_rc" = 0 ] || got=""
  reh doctor_summary_line '항목 15 — ✓ 15 · ✗ 0 · ─ 0' "$got"

  # ⑻ 러너 `--phase report` — 읽기 전용이다. 계획은 **임시 자리**에 새로 만들고 공유 작업 자리를 건드리지 않는다.
  local rw="$RUN_DIR/rehearse-seed"
  mkdir -p "$rw"
  run_capture python3 "$BUILD_PLAN_PY" --ref-root "${COLAB_REF_ROOT:-}" --md-root "${MD_ROOT:-}" \
      --work-dir "$rw" --out "$rw/upload-plan.json" --manifest-out "$rw/plan-manifest.yaml" >/dev/null 2>&1
  got="$(run_capture python3 "$REPO_ROOT/dev-package/tools/dev-seed/runner.py" \
      --phase report --base-url "$DEV_URL" --work-dir "$rw" 2>&1 || true)"
  printf '%s\n' "$got" | redact >> "$STAGE_LOG"
  reh_re runner_phase_report "완료 [0-9]+ / $EXPECT_DATASETS" "$got"

  # ⑼ agent-browser — dev 첫 화면을 열고 제목을 읽는다(쓰기 0).
  run_capture agent-browser open "$DEV_URL" >/dev/null 2>&1 || true
  got="$(run_capture agent-browser get title 2>/dev/null || true)"
  printf '%s\n' "$got" | redact >> "$STAGE_LOG"
  reh_re agent_browser_title '[^[:space:]]' "$got"

  log "리허설 — 원시동작 $(( REH_OK + ${#REH_BAD[@]} )) · 통과 $REH_OK · 어긋남 ${#REH_BAD[@]}"
  if [ "${#REH_BAD[@]}" -gt 0 ]; then
    log "어긋난 원시동작: ${REH_BAD[*]}"
    return 1
  fi
  return 0
}

# ── report ───────────────────────────────────────────────────────────────
# result.json(스키마 대조) ＋ 회차 기록 뼈대. 기록은 JSON 에서 채운다.
stage_report() {
  local result="$RUN_DIR/result.json"
  # 실제 실행은 회차 기록 자리에 쓴다. dry-run 은 레포를 건드리지 않으므로 실행 자리에만 쓴다.
  # 이름에 **`RUN_ID`(날짜＋시각)** 를 쓴다 — 날짜만 쓰면 같은 날 두 번째 실행이 첫 번째 기록을
  # 덮어써 **멈춘 자리와 근거가 사라진다**(하루에 여러 번 도는 것이 이 도구의 전제다).
  # 레포에 남기는 조건 = **바꾸는 단계가 실제로 돌았다**(`MUTATED`). preflight 에서 멈춘 회차와
  # `--preflight-only`·`--dry-run` 은 dev 를 읽기만 했으므로 실행 자리에만 남긴다.
  local session="$RUN_DIR/DR-4-run-$RUN_ID.md"
  if [ "$DRY_RUN" != 1 ] && [ "${MUTATED:-0}" = 1 ]; then
    session="$REPO_ROOT/dev-package/sessions/DR-4-run-$RUN_ID.md"
  fi
  python3 "$RESEED_DIR/report.py" \
    --run-dir "$RUN_DIR" --run-id "$RUN_ID" --target-sha "${TARGET_SHA:-}" \
    --stages "$(printf '%s,' "${STAGES[@]}")" --dry-run "$DRY_RUN" \
    --accounts-work "$ACCOUNTS_WORK_DIR" --accounts-profile "$ACCOUNTS_FILE" \
    --schema "$RESEED_DIR/result-schema.json" --out "$result" --session-out "$session" || return 1
  log "결과 JSON = $(relpath "$result")"
  log "회차 기록 뼈대 = $(relpath "$session")"
}
