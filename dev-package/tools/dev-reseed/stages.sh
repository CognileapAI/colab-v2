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
  printf '%s python /tmp/reset.py --target dev --yes-reset-dev \\\n' "$(reset_docker_prefix "${1:-}" "${2:-}")"
  printf '    --platform-url-file /s/platform.url --ai-url-file /s/ai.url'
}

# 계수가 필요한 단계(`count` · `schema` 의 DROP 직전 재계수 · `s3-plan` 의 지금 DB 참조 키) 전용 —
# BYPASSRLS 읽기 롤(`colab_backup`) URL 파일 **두 체인**을 더 건다.
# 왜 = 소유자 롤은 FORCE RLS 에 걸리고, 연구실 경계를 걸어 세면 경계 밖 행과 `d3_file` 의
#   RESTRICTIVE `body_access` 에 잠긴 파일을 못 본다(2026-09-24 사고 · `.agents/rules/deploy.md` 10번).
#   AI 체인(d10_model_call 등)도 토큰 안에 있어야 한다(2026-09-25 검토).
#   그 롤은 백업 cron 이 이미 쓰는 자리다(`infra/dev/backup.sh` · `db-bootstrap.sh backup-role`).
COUNT_URL_FILE_NAME=backup-platform-db.url
COUNT_AI_URL_FILE_NAME=backup-ai-db.url
reset_count_cmd() {
  reset_docker_cmd "${1:-}" "-v $EC2_SECRETS_DIR/$COUNT_URL_FILE_NAME:/s/count.url:ro -v $EC2_SECRETS_DIR/$COUNT_AI_URL_FILE_NAME:/s/count-ai.url:ro"
  printf ' \\\n    --count-url-file /s/count.url --count-ai-url-file /s/count-ai.url'
}
# 계수 URL 파일이 없으면 docker -v 가 빈 폴더를 만들어 건다 — 그 전에 원격이 이름을 대고 멈춘다.
reset_count_precheck() {
  local f
  for f in "$COUNT_URL_FILE_NAME" "$COUNT_AI_URL_FILE_NAME"; do
    printf 'sudo test -f %s/%s || { echo "계수 URL 파일 %s 이 없다 — BYPASSRLS 계수 없이 초기화하지 않는다" >&2; exit 1; }\n' \
      "$EC2_SECRETS_DIR" "$f" "$f"
  done
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

# 정지 게이트 — 원격 `count-before.json` 을 **바이트 그대로**(base64) 실행 기록으로 가져와 판정한다.
#
# 무엇을 덮는가(도구 `_count_report` · 실제 보장 범위) — 두 체인 모든 기본 표의 행수와 행 내용 지문 ·
#   DB 가 가리키는 저장 키 목록 · `uploads/`·`previews/` 의 키·크기 목록 sha256 · 멀티파트 목록 sha256.
#   그래서 행 추가·삭제·내용 편집·키 교체가 있으면 계수 바이트가 바뀐다. **같은 키·같은 크기의 객체 덮어쓰기**
#   는 목록 조회(ETag 미수집)가 보지 못한다 — 업로드 키는 ULID 라 제품 경로에서 같은 키를 다시 쓰지 않는다.
# 「비어 있다」 = 표 일곱 행 0 · 참조 키 0 · `uploads/` 객체 0 · 멀티파트 0(고아 객체도 사람 자료다).
#
# ack = **사용자가 이 계수를 보고 준 명시 GO** 의 기록이다(`.agents/rules/deploy.md` 11번 증보 · 상시 승인 밖).
#   토큰 = sha256(계수 바이트 ‖ "\n" ‖ nonce). nonce 는 **거부한 회차가 원격에 남긴 1회용 challenge** 에 있고
#   만료(RESET_ACK_TTL_SECONDS)가 있으며, 한 번 쓰면 지운다 — export 해 둔 값은 다음 회차에 통하지 않는다.
#   GO 근거(COLAB_RESEED_ACK_BASIS · 누가 어디서)가 없으면 받지 않는다. 판정·근거는 `reset-ack.json` 에 남는다.
#   nonce 는 **원격 challenge 에만** 둔다 — 실행 자리(로그 · stderr · blocked.jsonl · reset-ack.json · 사본)에는
#   nonce·challenge 본문을 남기지 않고 감사용 `nonceSha256`·`ackTokenSha256` 만 남긴다(2026-09-25 dev 검증 — 거부
#   회차가 RUN 로그에 challenge base64 를, reset-ack.json 에 nonce 를 남겨 count-before.json 과 함께 토큰을 다시 셀 수 있었다).
#   ⛔ 에이전트는 두 값을 채우지 않는다. 공용 Bash 훅(`scripts/harness/hooks/git-guard.sh` ⑹)은 할당 꼴만 거부한다 —
#   우발적 주입 경로를 줄일 뿐 자동 보안 경계가 아니다(`AGENTS.md`). 남는 경로는 아래 토큰 출력 주석과 같다.
# 판정 불가(파일 없음 · 옛 모양 · 전수 경로 표지 없음 · 지문 없음 · 표 누락)는 0 으로 읽지 않고 멈춘다.
RESET_GATE_TABLES="d1_account account_admin.login_credential d3_dataset d3_file d5_upload d6_project d4_lineage_edge"
RESET_CHALLENGE=reset-challenge.json
RESET_ACK_TTL_SECONDS=1800
# 옛 회차가 남긴 원격 파일 — reset ① 이 계수 전에 지운다(`--from s3` 가 지난 계수로 겹침 0 을 내던 자리).
RESET_STALE_FILES="count-before.json count-at-drop.json schema.json plan.json s3-plan.json s3-apply.json count-after.json"

# 토큰은 **stdout 이 터미널일 때만** 그 터미널에 찍는다(`[ -t 1 ]`). 단계 로그·stderr·blocked.jsonl 에는
#   남기지 않는다. stdout 이 터미널이 아니면(에이전트 · 파이프 · 리다이렉트) 토큰 없이 「자기 터미널에서
#   다시 열어야 보인다」만 남긴다 — 에이전트가 거부 출력을 읽어 토큰을 채우는 우발적 경로를 줄인다(2026-09-25 검토 조건).
#   ⚠ 자동 보안 경계가 아니다. 남는 경로 — 의사 터미널(pty)로 stdout 받기 · 실행 자리 count-before.json ＋ 원격
#   challenge nonce(dev 호스트에서 sudo 로만 읽힌다 — 실행 자리에는 없다)로 토큰 로컬 재계산 · env 파일·Write 도구로 값 주입.
RESET_TOKEN_MARK="@@colab-reseed-reset-token@@"
RESET_CHALLENGE_MARK="@@colab-reseed-reset-challenge@@"
reset_show_token() {
  if [ -t 1 ]; then
    printf '   토큰 = %s\n' "$1"
    log "   토큰은 이 터미널(stdout)에만 찍었다 — 단계 로그·실행 기록에는 남기지 않는다"
  else
    log "   토큰은 찍지 않았다 — stdout 이 터미널이 아니다. 사용자가 자기 터미널에서 reset 을 다시 열어야 이번 회차 토큰이 보인다"
  fi
}

reset_nonempty_gate() {
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY 정지 게이트 — ssh <dev> sudo base64 -w0 $REMOTE_OUT/count-before.json → 실행 자리 count-before.json"
    log "DRY   표 [$RESET_GATE_TABLES] · DB 참조 키 · uploads/ 객체 · 멀티파트 중 하나라도 0 이 아니면 멈추고 1회용 challenge 를 남긴다"
    log "DRY   넘기는 것은 사용자 GO 뿐 — COLAB_RESEED_ACK_NONEMPTY(이번 challenge 토큰) ＋ COLAB_RESEED_ACK_BASIS(GO 근거)"
    return 0
  fi
  local b64 rc=0 chal
  b64="$(ssh_dev_capture "sudo base64 -w0 $REMOTE_OUT/count-before.json")" || rc=$?
  if [ "$rc" -ne 0 ] || [ -z "$b64" ]; then
    blocked_add reset "정지 게이트 판정 불가 — count-before.json 을 받지 못했다(ssh 종료코드 $rc)"
    log "⛔ 정지 게이트 — count-before.json 을 받지 못했다. 0 으로 읽지 않는다"
    return 1
  fi
  ( umask 077; printf '%s' "$b64" | base64 -d > "$RUN_DIR/count-before.json" ) || {
    blocked_add reset "정지 게이트 판정 불가 — count-before.json base64 복원 실패"; return 1; }
  # challenge(nonce)는 메모리로만 오간다 — 실행 자리에 사본을 두지 않고, 원격에는 표준입력으로 싣는다.
  chal="$(ssh_dev_capture "sudo base64 -w0 $REMOTE_OUT/$RESET_CHALLENGE 2>/dev/null || true")"
  local out chal_out; rc=0
  out="$(RESET_TOKEN_MARK="$RESET_TOKEN_MARK" RESET_CHALLENGE_MARK="$RESET_CHALLENGE_MARK" RESET_CHALLENGE_B64="$chal" python3 - "$RUN_DIR" "$RUN_ID" "${COLAB_RESEED_OPERATOR:-$(id -un)}" "$RESET_GATE_TABLES" \
      "${COLAB_RESEED_ACK_NONEMPTY-}" "${COLAB_RESEED_ACK_BASIS-}" "$RESET_ACK_TTL_SECONDS" \
      "d3_dataset=${EXPECT_DATASETS:-} d6_project=${EXPECT_PROJECTS:-} d4_lineage_edge=${EXPECT_EDGES:-}" <<'PY'
import base64, datetime, hashlib, json, os, secrets, sys
run_dir, run_id, who, tables, ack, basis, ttl, baseline = sys.argv[1:9]
tables = tables.split()
raw = open(os.path.join(run_dir, "count-before.json"), "rb").read()
content = hashlib.sha256(raw).hexdigest()
now = datetime.datetime.now(datetime.timezone.utc)
stamp = lambda t: t.isoformat(timespec="seconds")
def token_of(nonce): return hashlib.sha256(raw + b"\n" + nonce.encode("ascii")).hexdigest()
TOKEN_MARK = os.environ["RESET_TOKEN_MARK"]
CHALLENGE_MARK = os.environ["RESET_CHALLENGE_MARK"]
sha = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
# 감사 기록에는 nonce 대신 그 sha256 만 — 기록과 count-before.json 으로 토큰을 다시 셀 수 없다.
audit = lambda c: {"nonceSha256": sha(c["nonce"]), "issuedAt": c.get("issuedAt"), "expiresAt": c.get("expiresAt")}

nonempty, refs, orphans, excess, challenge = {}, None, None, {}, None
def done(decision, lines, code, **extra):
    body = {"schema": "colab-reseed-reset-ack/3", "runId": run_id, "operator": who,
            "recordedAt": stamp(now), "countBefore": "count-before.json", "countBeforeSha256": content,
            "decision": decision, "nonEmpty": nonempty, "referencedKeys": refs, "orphanUploads": orphans,
            "excessOverSeed": excess, "challenge": challenge, "ackProvided": bool(ack),
            "ackTokenSha256": sha(ack) if decision == "acknowledged" else None,
            "ackBasis": basis if decision == "acknowledged" else None,
            "toolAckSha256": content if decision == "acknowledged" else None}
    body.update(extra)
    fd = os.open(os.path.join(run_dir, "reset-ack.json"), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, indent=2)
    print("\n".join(lines))
    sys.exit(code)

try:
    body = json.loads(raw)
    plat, ai, s3 = body["db"]["platform"], body["db"]["ai"], body["s3"]
    rows = plat["rows"]
    refs = body["referencedKeys"]["count"]
    ref_keys = body["referencedKeys"]["keys"]
    bad = [t for t in tables if not isinstance(rows.get(t), int)]
    marks = (plat.get("countPath"), ai.get("countPath"))
    if (body.get("phase") != "count" or marks != ("bypassrls:row_security=off",) * 2 or bad
            or not isinstance(refs, int) or not isinstance(plat.get("tables"), dict)
            or not isinstance(ai.get("tables"), dict) or not isinstance(s3.get("objectsSha256"), dict)
            or "multipartSha256" not in s3):
        raise ValueError(f"전수 경로 표지 {marks} · 빠진 표 {bad} · 표 지문·S3 키 목록 지문 유무")
    uploads = int(s3["objects"]["uploads/"]); multipart = int(s3["multipartUploads"])
except (ValueError, KeyError, TypeError) as exc:
    done("undecidable", [f"⛔ 정지 게이트 판정 불가 — 계수 파일이 BYPASSRLS 전수·지문 계수 모양이 아니다 ({exc}). 0 으로 읽지 않는다."], 2)

nonempty = {t: rows[t] for t in tables if rows[t] != 0}
if refs:
    nonempty["referencedKeys"] = refs
if uploads:
    nonempty["s3:uploads/"] = uploads
if multipart:
    nonempty["s3:multipartUploads"] = multipart
orphans = max(0, uploads - sum(1 for k in ref_keys if k.startswith("uploads/")))
for pair in baseline.split():
    name, _, want = pair.partition("=")
    if want.isdigit() and name in rows:
        excess[name] = rows[name] - int(want)
counts = " · ".join(f"{t} {rows[t]}" for t in tables) + f" · 참조 키 {refs}"
s3line = f"S3 uploads/ 객체 {uploads}(그중 DB 가 가리키지 않는 고아 {orphans}) · 멀티파트 {multipart}"
if not nonempty:
    done("empty", [f"정지 게이트 — 빈 DB ({counts} · {s3line}) · 토큰 불요"], 0, consumeChallenge=True)

try:
    chal = json.loads(base64.b64decode(os.environ.get("RESET_CHALLENGE_B64", ""), validate=True) or b"null")
except ValueError:
    chal = None
why = None
if not ack:
    why = "COLAB_RESEED_ACK_NONEMPTY 가 없다"
elif len(ack) != 64 or set(ack) - set("0123456789abcdef"):
    why = "COLAB_RESEED_ACK_NONEMPTY 가 sha256 꼴이 아니다"
elif not isinstance(chal, dict) or not isinstance(chal.get("nonce"), str):
    why = "이번 거부 회차의 1회용 challenge 가 원격에 없다(이미 썼거나 지워졌다)"
elif chal.get("countBeforeSha256") != content:
    why = "challenge 를 낸 뒤 자료가 바뀌었다(계수 바이트가 다르다)"
elif stamp(now) >= str(chal.get("expiresAt", "")):
    why = "challenge 가 만료됐다"
elif ack != token_of(chal["nonce"]):
    why = "COLAB_RESEED_ACK_NONEMPTY 가 이번 challenge 의 토큰이 아니다(지난 회차 값이거나 nonce 없는 계수 sha256)"
elif not basis.strip():
    why = "COLAB_RESEED_ACK_BASIS(사용자 GO 근거 — 누가 · 어디서 · 언제)가 없다"
if why is None:
    challenge = audit(chal)
    done("acknowledged", [f"정지 게이트 — 비어 있지 않음 ({counts} · {s3line}) · 사용자 GO 토큰 일치 · 근거 「{basis}」 · challenge 소진"],
         0, consumeChallenge=True)

nonce = secrets.token_hex(16)
issued = {"nonce": nonce, "issuedAt": stamp(now),
          "expiresAt": stamp(now + datetime.timedelta(seconds=int(ttl)))}
chal_b64 = base64.b64encode(json.dumps(dict(issued, schema="colab-reseed-reset-challenge/1", runId=run_id,
                                            countBeforeSha256=content), ensure_ascii=False).encode("utf-8")).decode("ascii")
challenge = audit(issued)
over = [f"{t} +{n} ({rows[t]}/기준 {rows[t] - n})" for t, n in excess.items() if n > 0]
first = ("⛔ 정지 게이트 — 시드 기준선 초과: " + " · ".join(over) + " — 시드가 아닌 행일 수 있다") if over else \
        "⛔ 정지 게이트 — 시드 기준선 초과 없음(행수만의 판정이다 — 사람 자료가 없다는 증거가 아니다)"
done("refused", [
    first,
    f"   dev 가 비어 있지 않다: {counts}",
    f"   {s3line}",
    f"   {why}. 앱 정지·DROP·S3 는 하나도 하지 않았다.",
    f"   이번 계수 = 실행 자리 count-before.json · 1회용 challenge 만료 {challenge['expiresAt']}",
    f"{TOKEN_MARK}{token_of(nonce)}",
    f"{CHALLENGE_MARK}{chal_b64}",
    "   넘기는 것은 **사용자**가 이 계수를 보고 명시 GO 를 준 뒤 **자기 터미널에서** 한다 —",
    "   COLAB_RESEED_ACK_NONEMPTY 에 이번 토큰, COLAB_RESEED_ACK_BASIS 에 GO 근거(누가 · 어디서 · 언제)를 두고",
    "   reset 부터 다시 연다. 에이전트는 이 값을 채우지 않는다(.agents/rules/deploy.md 11번 증보).",
], 1)
PY
)" || rc=$?
  # challenge 줄은 원격으로만 보낸다 — 단계 로그·stderr·blocked.jsonl 로 가는 out 에서 먼저 뺀다.
  chal_out="$(printf '%s\n' "$out" | sed -n "s/^$RESET_CHALLENGE_MARK//p")"
  out="$(printf '%s\n' "$out" | grep -vF -- "$RESET_CHALLENGE_MARK")"
  printf '%s\n' "$out" | while IFS= read -r line; do
    case "$line" in
      "$RESET_TOKEN_MARK"*) reset_show_token "${line#"$RESET_TOKEN_MARK"}" ;;
      *) log "$line" ;;
    esac
  done
  if [ "$rc" -ne 0 ]; then
    blocked_add reset "$(printf '%s\n' "$out" | grep -vF -- "$RESET_TOKEN_MARK" | head -2 | tr '\n' ' ')"
    if [ -n "$chal_out" ]; then
      # 표준입력으로 싣는다 — argv 에 실으면 RUN 로그(단계 로그 · stderr)와 원격 ps 에 challenge 가 남는다.
      printf '%s' "$chal_out" \
        | ssh_dev "umask 077; base64 -d | sudo tee $REMOTE_OUT/$RESET_CHALLENGE >/dev/null && sudo chmod 600 $REMOTE_OUT/$RESET_CHALLENGE" \
        || warn "1회용 challenge 를 원격에 남기지 못했다 — 위 토큰은 통하지 않는다. 다시 연다"
    fi
    chal_out=""
    return 1
  fi
  # 비었거나 GO 가 확인됐으면 challenge 를 지운다(1회 소진). 못 지우면 같은 토큰이 다시 통하므로 멈춘다.
  ssh_dev "sudo rm -f $REMOTE_OUT/$RESET_CHALLENGE" \
    || { blocked_add reset "1회용 challenge 소진 실패 — 같은 토큰이 다시 통할 수 있어 멈춘다"; return 1; }
  return 0
}

# 도구에 넘기는 재계수 대조값 — acknowledged 면 이번 계수 파일 sha256, 비었으면 없다.
reset_tool_ack() {
  python3 - "$RUN_DIR/reset-ack.json" <<'PY' 2>/dev/null || true
import json, sys
b = json.load(open(sys.argv[1]))
v = b.get("toolAckSha256") if b.get("decision") == "acknowledged" else None
if isinstance(v, str) and len(v) == 64 and not set(v) - set("0123456789abcdef"):
    print(v)
PY
}

stage_reset() {
  write_approval_record || return 1

  # ── 읽기 전용 구간 ── 여기서 실패하면 dev 는 계속 돌고 있다(정지 전이다).
  log "① 실행 전 계수 — BYPASSRLS 롤(두 체인) · row_security=off · 모든 기본 표의 행수·내용 지문(읽기 전용)"
  ssh_dev "mkdir -p $REMOTE_OUT && chmod 700 $REMOTE_OUT" || return 1
  # 옛 회차 파일을 먼저 지운다 — 계수가 실패해도 지난 계수가 이번 것처럼 남지 않는다.
  ssh_dev "sudo rm -f$(printf " $REMOTE_OUT/%s" $RESET_STALE_FILES)" || return 1
  rm -f "$RUN_DIR/count-before.json" "$RUN_DIR/count-at-drop.json" "$RUN_DIR/reset-ack.json" \
        "$RUN_DIR/challenge-in.json" "$RUN_DIR/challenge-out.json"
  ssh_script "reset:count" <<EOF || return 1
set -euo pipefail
$(reset_count_precheck)
$(reset_count_cmd) --phase count --report /out/count-before.json
test -s $REMOTE_OUT/count-before.json
EOF

  # ── 정지 게이트 ── 비어 있지 않으면 **여기서** 멈춘다. 아래는 앱 정지 · DROP · S3 다.
  #   2026-09-24 08:33Z 사고 = 계수가 비어 있지 않았는데 `test -s` 만 보고 지나갔다.
  log "①ᵇ 정지 게이트 — 비어 있지 않으면 사용자 GO(1회용 challenge 토큰 ＋ 근거) 없이 파괴 걸음에 들어가지 않는다"
  reset_nonempty_gate || return 1
  local tool_ack; tool_ack="$(reset_tool_ack)"

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

  # 도구가 DROP 직전 같은 프로세스에서 다시 센다 — 비어 있지 않은데 ack 가 그 재계수와 다르면 지우지 않는다.
  log "② 두 체인 스키마 재생성 — 도구가 DROP 직전 재계수(count-at-drop.json)로 한 번 더 판정한다"
  ssh_script "reset:schema" <<EOF || { blocked_add reset "스키마 재생성 실패(재계수 판정 포함)"; reset_recover_apps "② 스키마 재생성 실패"; return 1; }
set -euo pipefail
$(reset_count_precheck)
$(reset_count_cmd) --phase schema --report /out/schema.json --count-report /out/count-at-drop.json${tool_ack:+ --ack-sha256 $tool_ack}
EOF

  # s3 계획은 이 파일(이번 reset 의 DROP 직전 계수)과 그 sha256 에만 묶인다.
  log "②ᵇ DROP 직전 재계수를 실행 자리로 — s3 계획이 이번 reset 에 묶이는 근거"
  local b64
  b64="$(ssh_dev_capture "sudo base64 -w0 $REMOTE_OUT/count-at-drop.json")" && [ -n "$b64" ] \
    && ( umask 077; printf '%s' "$b64" | base64 -d > "$RUN_DIR/count-at-drop.json" ) \
    || { blocked_add reset "DROP 은 끝났다 — count-at-drop.json 을 실행 자리로 받지 못했다(s3 는 이 파일 없이 돌지 않는다)"; return 1; }
}

# 승인 기록 — 누가 · 언제 · 어느 sha · 어느 게이트를 통과했는가.
# 게이트 다섯의 문면은 `.agents/rules/deploy.md` 11번 증보 문단(2026-09-25 개정)이 정본이다.
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
    "basis": "빈 dev 는 dev 한정 상시 승인 · 비어 있지 않은 dev 는 회차별 사용자 명시 GO(reset-ack.json 의 ackBasis) — .agents/rules/deploy.md 11번 증보(2026-09-25 개정)",
    "gatesPassed": [
        {"id": 1, "text": "--target dev ＋ --yes-reset-dev", "evidence": "reseed.sh 가 두 인자를 고정으로 넘긴다"},
        {"id": 2, "text": "COLAB_CORE_S3_BUCKET 정확 일치", "evidence": bucket},
        {"id": 3, "text": "두 DB URL 호스트에 -dev 포함", "evidence": "reset_dev_environment.py ENV_HOST_MARK 가 판정한다"},
        {"id": 4, "text": "계획 키가 uploads/·previews/ 안", "evidence": "s3 단계의 계획 검토와 도구 NEVER_TOUCH_PREFIXES 가 판정한다"},
        {"id": 5, "text": "BYPASSRLS 전수·지문 계수(두 체인 · 계수 롤 BYPASSRLS)가 비어 있지 않으면 사용자 명시 GO(1회용 challenge 토큰 ＋ 근거) 없이 정지 · 도구가 DROP 직전 재계수로 한 번 더 판정", "evidence": "reset ①ᵇ 정지 게이트 판정 = reset-ack.json · 도구 schema 보고서 countAtDrop · deploy.md 11번 증보(2026-09-25 개정)"},
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
    log "DRY ⓪ 실행 자리의 reset 판정(reset-ack.json · empty|acknowledged)과 count-at-drop.json 이 없으면 멈춘다 — --from s3 는 reset 을 돈 같은 --run-dir 로만"
    log "DRY ① ssh <dev> — 원격 옛 plan.json·s3-plan.json·s3-apply.json·count-after.json 삭제 뒤 $(reset_count_cmd | tr -d '\\\n') --phase s3-plan --plan-out /out/plan.json --report /out/s3-plan.json --referenced-keys /out/count-at-drop.json --referenced-sha256 <실행 자리 count-at-drop.json sha256> [--ack-sha256 <reset-ack.json toolAckSha256>]"
    log "DRY ② ssh <dev> — 같은 컨테이너(--user 0) 안에서 계획 검토(_ops/ 0 건 · 접두사 uploads/·previews/ · 모드 0600 · 소유자 일치 · sha256 기재)"
    log "DRY ③ ssh <dev> — 같은 도구 --phase s3-apply --apply-plan /out/plan.json --plan-sha256 <① 출력값> --report /out/s3-apply.json"
    log "DRY ④ ssh <dev> — 같은 도구 --phase count --report /out/count-after.json"
    return 0
  fi
  # ⭑ 계획은 스키마 DROP **뒤**에 선다 — DB 가 가리키던 키는 **이번 실행 자리의 reset** 이 받아 둔
  #   DROP 직전 재계수(count-at-drop.json)에서만 읽는다. 원격 고정 경로의 파일은 지난 회차 것일 수 있다
  #   (2026-09-25 검토 — `--from s3` 가 지난 회차 계수로 겹침 0 을 내고 새 업로드를 계획에 실었다).
  #   환경의 COLAB_RESEED_ACK_NONEMPTY 는 쓰지 않는다 — ack 는 이번 reset 판정(reset-ack.json)에서만 온다.
  local decision at_drop_sha tool_ack
  decision="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("decision",""))' \
    "$RUN_DIR/reset-ack.json" 2>/dev/null || true)"
  case "$decision" in
    empty|acknowledged) : ;;
    *) blocked_add s3-plan "이번 실행 자리에 reset 판정(empty·acknowledged)이 없다 — --from s3 는 reset 을 돈 같은 --run-dir 로만 잇는다"
       log "⛔ s3 — 실행 자리 $(relpath "$RUN_DIR") 에 reset 판정이 없다(판정 [${decision:-없음}]). 계획을 세우지 않는다"
       return 1 ;;
  esac
  at_drop_sha="$(sha256sum "$RUN_DIR/count-at-drop.json" 2>/dev/null | cut -d' ' -f1)"
  [ -n "$at_drop_sha" ] || { blocked_add s3-plan "실행 자리에 count-at-drop.json(이번 reset 의 DROP 직전 계수)이 없다"; return 1; }
  tool_ack="$(reset_tool_ack)"
  log "① s3-plan — exact-key 계획 ＋ sha256 · 이번 reset 의 DROP 직전 계수(sha256 대조) · 지금 DB 참조 키 0 확인"
  local out; out="$(ssh_script "s3:plan" <<EOF
set -euo pipefail
sudo rm -f$(printf " $REMOTE_OUT/%s" plan.json s3-plan.json s3-apply.json count-after.json)
$(reset_count_precheck)
$(reset_count_cmd) --phase s3-plan --plan-out /out/plan.json --report /out/s3-plan.json \\
    --referenced-keys /out/count-at-drop.json --referenced-sha256 $at_drop_sha${tool_ack:+ --ack-sha256 $tool_ack}
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
$(reset_count_precheck)
$(reset_count_cmd) --phase count --report /out/count-after.json
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
  operator_grant "prelude:operator" || return 1
}

# ── 임시 운영자 창(窓) ───────────────────────────────────────────────────
# 교수에게 주는 서비스 운영자 자격은 **`accounts` 국면 하나에만** 필요하다(무소속 운영자 4명은
# `canManageServiceAccounts` 가 있어야 화면에서 만들 수 있다). 그 자격이 켜져 있는 동안
# 생성 넷(`createProject`·`createUpload`·`initiateUploadTransfer`·`createDataset`)은
# `X-CoLAB-Target-Lab` 헤더를 **요구한다** — `services/core-api/src/colab_core/app/target_scope.py:8·42-43`.
# 교수(비운영자)에게는 그 요구가 아예 없고, 오히려 헤더를 실으면 거절된다(`target_scope.py:31-34`).
# 러너는 그 칸을 채우지 않으므로(`dev-package/tools/dev-seed/runner.py:880-887`)
# 2026-09-24 회차의 `seed` 가 첫 프로젝트에서 「대상 연구실을 선택해 주세요.」로 멈췄다.
# ⇒ 창을 `accounts` 국면으로 좁힌다. 화면 세 자리에 연구실 선택을 새로 붙이는 대신
#   **DR-4 가 28/28 을 세운 그 단일 연구실 경로**로 되돌리는 쪽이다.
#
# ⚠ **제품 API(`set_operator`)로 내리지 않는다.** 그 경로는 자격 버전을 올리고 열린 세션을
#   끊는다(`services/core-api/src/colab_core/kernel/db_credentials.py:260-264`) — 러너의 로그인이
#   그 자리에서 죽는다. 운영자 여부는 **매 요청 다시 읽으므로**(`kernel/auth.py:25`)
#   `account_admin.service_operator` 의 행 하나만 빼면 세션을 건드리지 않고 즉시 반영된다.
#   그 표에는 RLS 가 걸려 있지 않다(`db/platform/schema.sql:155-158`) — 경계를 걸 GUC 가 필요 없다.
operator_grant() { # $1 = 원격 라벨
  # ⚠ `account_id` 는 **원문 그대로** 넘긴다 — `provision-service-operator.sql` 이 `:'account_id'`
  #   (psql 이 따옴표를 씌우는 꼴)로 읽는다. ② 의 `provision-account.sql` 은 맨 `:account_id` 라
  #   그쪽만 `sqlq` 로 미리 감싼다. 두 파일의 변수 꼴이 다르다 — 값의 꼴은 **파일이 정한다.**
  #   4회차 재개 2(`20260914T023537Z`)가 여기에 감싼 값을 넘겨 `'''<id>'''` 로 조회했고
  #   `INSERT 0 0` → 「지정한 계정이 없어 운영자를 등록하지 못했다」 로 멈췄다.
  #   `SET app.current_lab` 은 SQL 리터럴 자리라 종전대로 `sqlq` 로 감싼다.
  ssh_script "$1" <<EOF || return 1
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

# 내리는 문장은 **배포된 트리에 없다**(그 자리는 대상 ref 의 파일만 걸 수 있다) — 그래서
# 본문을 base64 로 실어 `psql -f -` 의 표준입력으로 넣는다(`lib.sh` `remote_assign` 머리말).
# 판정 두 개를 같은 트랜잭션(`-1`)에 둔다 — 거절이 서면 DELETE 도 함께 되돌아간다.
#   ⑴ 그 계정의 행이 남아 있으면 거절     ⑵ 운영자가 **한 명도** 남지 않으면 거절
# ⑵ 는 제품이 지키는 불변식과 같다(「마지막 관리자는 해제할 수 없다」 · `db_credentials.py:250-252`).
operator_revoke() { # $1 = 원격 라벨
  local sql
  sql="$(cat <<'SQL'
\set ON_ERROR_STOP on
DELETE FROM account_admin.service_operator WHERE account_id=:'account_id';
SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''임시 운영자를 내리지 못했다''; END $check$'
 WHERE EXISTS (SELECT 1 FROM account_admin.service_operator WHERE account_id=:'account_id')
\gexec
SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''운영자가 한 명도 남지 않는다 — 내리지 않는다''; END $check$'
 WHERE NOT EXISTS (SELECT 1 FROM account_admin.service_operator)
\gexec
SQL
)"
  ssh_script "$1" <<EOF || return 1
set -euo pipefail
$(remote_assign ACCOUNT_ID "$RESEED_ACCOUNT_ID")
$(remote_assign REVOKE_SQL "$sql")
export ACCOUNT_ID
printf '%s\\n' "\$REVOKE_SQL" | docker run --rm -i --network host --user 0 \\
  -v $EC2_SECRETS_DIR/platform-owner-db.url:/s/owner.url:ro \\
  -e ACCOUNT_ID \\
  $PSQL_IMAGE sh -c 'psql -1 -v ON_ERROR_STOP=1 -v account_id="\$ACCOUNT_ID" \\
    "\$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/owner.url)" -f -'
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
  # 창은 **이 국면이 스스로 연다** — 첫 login 앞에서 올린다(멱등 · `ON CONFLICT DO NOTHING`).
  # ⚠ prelude 의 올림에 기대면 `--from seed` 재개가 죽는다. 앞 회차가 ③ 에서 이미 내렸으므로
  #   교수는 평범한 교수이고, `accounts` 국면이 계정 관리 화면(`account-create`)을 열지 못한다
  #   (2026-09-24 로컬 검증 실측 — `runner.py` 「계정 관리 화면(account-create)이 열리지 않았다」).
  #   login **앞**이어야 하는 이유 = 올림 뒤의 세션만 운영자 주장을 싣는다(④ 와 같은 설계 —
  #   `kernel/login_sessions.py:226-228`). 이미 열린 교수 세션은 여기서 거절되고 login 이 새로 든다.
  operator_grant "seed:operator-grant" || return 1
  run python3 "$runner" --phase login "${args[@]}" || return 1
  for i in 0 1 2 3; do
    run python3 "$runner" --phase accounts "${args[@]}" --accounts-file "$ACCOUNTS_WORK_DIR/operator-$i.json" \
      --accounts-password-file "$ACCOUNTS_WORK_DIR/initial-$i.txt" || return 1
  done
  run python3 "$RESEED_DIR/accounts.py" check-created --profile "$ACCOUNTS_FILE" --work "$ACCOUNTS_WORK_DIR" || return 1

  log "③ 임시 운영자 해제 — 여기서부터 교수 자격 하나로 돈다(대상 연구실 헤더 요구가 사라진다)"
  # 계정 넷이 선 것을 확인한 **뒤**에 내린다. 여기부터 `projects`·`datasets`·`verify` 는
  # DR-4 가 28/28 을 세운 것과 같은 단일 연구실 경로다.
  operator_revoke "seed:operator-revoke" || return 1

  log "④ 재로그인 — 자격이 바뀐 세션은 제품이 거절한다(설계대로다)"
  # ⚠ **이 한 줄을 빼면 `projects` 가 로그인 화면을 본다.** 토큰은 발급 시점의 운영자 여부를
  #   주장으로 싣고, 세션 확인이 `service_operator` 를 **매 요청 다시 읽어** 주장과 어긋나면
  #   그 세션을 거절한다 — `kernel/session_token.py:59-61` · `kernel/login_sessions.py:192-206`.
  #   즉 자격을 어떤 길로 내리든(제품 API든 SQL이든) **열린 세션은 반드시 닫힌다.**
  #   2026-09-24 재개 1 이 이 자리에서 「지목점 project-new-button 해소 실패」로 멈췄고,
  #   덤프에 찍힌 것은 프로젝트 목록이 아니라 **로그인 화면**이었다.
  #   `phase_login` 은 멱등이다 — 이미 들어가 있으면 건너뛰고, 아니면 갱신된 자격으로 다시 든다.
  run python3 "$runner" --phase login "${args[@]}" || return 1

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
# 보기 전 정착 규칙 — 러너 `preview_settled`(`dev-seed/runner.py`)와 같다.
#   파일 선택값 있음 · 보기 활성 · slot `idle` 이 PREVIEW_STABLE_MS 이상 **이어진** 뒤에만 누른다(대기 상한 PREVIEW_WAIT_MS).
# ⚠ 이미 선택된 파일을 다시 고르지 않는다 — 배포 프론트(`ea21d8c2aa54` DatasetPreviewSection.tsx)는
#   같은 파일 재선택에서 onPick 이 설명을 비우고(:347-351) 파일 id 가 바뀔 때만 다시 받아(:169-183)
#   보기가 영구 비활성(:355)이 된다. agent-browser 0.27.0 은 비활성 버튼 클릭도 성공으로 답한다.
# 누른 뒤 PREVIEW_CLICK_ACK_MS 안에 slot 이 idle 을 떠나지 않으면 「클릭 미반영」으로 적는다(전체 대기 없이).
PREVIEW_STABLE_MS="${COLAB_RESEED_PREVIEW_STABLE_MS:-1000}"
PREVIEW_CLICK_ACK_MS="${COLAB_RESEED_PREVIEW_CLICK_ACK_MS:-5000}"

# 브라우저 세션 — 러너(`dev-seed/runner.py` `DEFAULT_SESSION`)가 로그인해 둔 **그 세션**을 이름으로 쓴다.
# ⚠ `AGENT_BROWSER_SESSION_NAME` 환경변수는 agent-browser 가 읽지 않는다(4회차 `20260914T035058Z` 실측 —
#   env 만 준 호출은 `default` 세션으로 가 로그인 화면을 27번 열었다). 세션은 **`--session` 인자로만** 고른다.
AB_SESSION="${COLAB_RESEED_BROWSER_SESSION:-colab-dev}"
ab_dev() { run_capture agent-browser --session "$AB_SESSION" "$@"; }

# ── 보기 누름 — 적중 검사 · 초점 ＋ Enter · JS click 폴백 (러너 `press_preview_draw` 와 같은 규칙) ──
# ⚠ dev 2026-09-25 00:45–01:00 KST(7ba6cdaf) — 정착 확인 뒤 `click` 이 26행 모두 종료 0 인데 slot 이 idle 에
#   머물렀다(onClick → draw() 미실행 · 배포 프론트 `ea21d8c2aa54` DatasetPreviewSection.tsx:224-250,354).
#   로컬 대역 페이지 실측(agent-browser 0.27.0): 좌표 클릭은 버튼이 화면 밖이면 스크롤 없이 화면 밖을 누르고,
#   버튼 중심이 고정 층에 덮이면 그 층을 누른다 — 둘 다 종료 0 · 처리기 0회.
#   그래서 누르기 전에 버튼 중심의 적중 대상을 재어 로그·판정표 비고에 남기고, 초점 ＋ Enter 로 누른 뒤
#   slot 이 idle 을 떠났는지 본다. 떠나지 않으면 JS click 한 번으로 폴백하고 먹힌 방법을 적는다.
PREVIEW_DRAW_SEL='[data-testid="dt-preview-draw"]'
AB_JS_SUB="e""val"
PREVIEW_HIT_JS="$(cat <<'HITJS'
(() => {
  const btn = document.querySelector('[data-testid="dt-preview-draw"]');
  if (!btn) return '보기 단추 없음';
  const probe = () => {
    const r = btn.getBoundingClientRect();
    const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2);
    const where = '(' + x + ',' + y + ')';
    if (!(x >= 0 && y >= 0 && x < innerWidth && y < innerHeight)) return where + ' 화면 밖(창 ' + innerWidth + 'x' + innerHeight + ')';
    const el = document.elementFromPoint(x, y);
    if (!el) return where + ' 적중 요소 없음';
    if (el === btn || btn.contains(el)) return where + ' = 보기 단추';
    const near = el.closest('[data-testid]');
    const cls = typeof el.className === 'string' ? el.className : (el.getAttribute('class') || '');
    const text = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 80);
    return where + ' 을 덮은 요소 = ' + el.tagName.toLowerCase()
      + (el.getAttribute('data-testid') ? ' testid=' + el.getAttribute('data-testid') : '')
      + (near && near !== el ? ' 조상testid=' + near.getAttribute('data-testid') : '')
      + (cls ? ' class=' + cls.slice(0, 80) : '') + (text ? ' 「' + text + '」' : '');
  };
  const before = probe();
  btn.scrollIntoView({block: 'center', inline: 'nearest', behavior: 'instant'});
  return ('스크롤 전 중심 ' + before + ' · 스크롤 뒤 중심 ' + probe()).replace(/["\\\t\r\n]/g, ' ');
})()
HITJS
)"
PREVIEW_JS_CLICK="(() => { const b = document.querySelector('[data-testid=\"dt-preview-draw\"]'); if (!b) return 'none'; b.click(); return 'clicked'; })()"

# 표준출력 = 적중 검사 한 줄(못 재면 빈 값). 버튼을 화면 가운데로 옮긴다.
preview_hit_test() {
  ab_dev "$AB_JS_SUB" --stdin <<< "$PREVIEW_HIT_JS" 2>/dev/null | head -1 | sed 's/^"//; s/"$//'
}

# $1 = 상한 ms. slot 이 idle 을 떠나면 그 값을 찍고 0, 아니면 마지막 값을 찍고 1.
preview_wait_left_idle() {
  local t0 s; t0="$(date +%s%3N)"
  while :; do
    s="$(ab_dev get attr '[data-testid="dt-preview-slot"]' data-preview-slot-state 2>/dev/null | tr -d ' \t\r\n')"
    if [ -n "$s" ] && [ "$s" != idle ]; then printf '%s' "$s"; return 0; fi
    [ "$(( $(date +%s%3N) - t0 ))" -lt "$1" ] || { printf '%s' "$s"; return 1; }
    sleep 0.05
  done
}

# 표준출력 = `방법|slot` (방법 = focus+Enter · js-click · none). none 이면 종료 1.
preview_press() {
  local s=""
  if ab_dev focus "$PREVIEW_DRAW_SEL" >/dev/null 2>&1 && ab_dev press Enter >/dev/null 2>&1; then
    if s="$(preview_wait_left_idle "$PREVIEW_CLICK_ACK_MS")"; then printf 'focus+Enter|%s' "$s"; return 0; fi
  fi
  ab_dev "$AB_JS_SUB" --stdin <<< "$PREVIEW_JS_CLICK" >/dev/null 2>&1
  if s="$(preview_wait_left_idle "$PREVIEW_CLICK_ACK_MS")"; then printf 'js-click|%s' "$s"; return 0; fi
  printf 'none|%s' "$s"; return 1
}

# 보기 전 정착 대기 — 파일 선택값 있음 · 보기 활성 · slot idle 이 PREVIEW_STABLE_MS 이상 이어질 때까지(상한 PREVIEW_WAIT_MS).
# 호출한 쪽(stage_verify)의 preview_file · draw_enabled · slot_state · unsupported_n 에 마지막 관측값을 남긴다.
# $1 = unsupported 면 미지원 표시(`dt-preview-unsupported`)도 함께 본다 — 그릴 조각이 아예 없으면 배포 프론트가
#      열자마자 그 표시를 세우고 보기는 비활성으로 둔다(`ea21d8c2aa54` DatasetPreviewSection.tsx:155-156,355).
# 종료 0 = 정착 · 1 = 상한까지 정착 못 함 · 2 = 누르기 전에 미지원 표시가 섰다.
preview_settle() {
  local t_end now stable_since=""
  t_end=$(( $(date +%s%3N) + PREVIEW_WAIT_MS ))
  while :; do
    now="$(date +%s%3N)"; [ "$now" -lt "$t_end" ] || return 1
    if [ "${1:-}" = unsupported ]; then
      unsupported_n="$(ab_dev get count '[data-testid="dt-preview-unsupported"]' 2>/dev/null | tr -d ' \t\r\n')"
      [ "$unsupported_n" = 1 ] && return 2
    fi
    preview_file="$(ab_dev get value '[data-testid="dt-pick-file"]' 2>/dev/null | tr -d '\r\n')"
    draw_enabled="$(ab_dev is enabled "$PREVIEW_DRAW_SEL" 2>/dev/null | tr -d ' \t\r\n')"
    slot_state="$(ab_dev get attr '[data-testid="dt-preview-slot"]' data-preview-slot-state 2>/dev/null | tr -d ' \t\r\n')"
    if [ -n "$preview_file" ] && [ "$draw_enabled" = true ] && [ "$slot_state" = idle ]; then
      [ -n "$stable_since" ] || stable_since="$now"
      [ "$(( $(date +%s%3N) - stable_since ))" -lt "$PREVIEW_STABLE_MS" ] || return 0
    else
      stable_since=""
    fi
    sleep 0.05
  done
}

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
  # `seed` 가 내린 임시 운영자를 **되올린 뒤에** 최종화한다. `accounts.py` 의 최종화는
  # 교수 계정 최종화의 전제 표식으로 그 운영자 행을 읽고, 없으면
  # 「final professor credential drift; refusing another reset」 로 거절한다.
  # 최종화 자신이 마지막에 그 행을 다시 내리므로(`set_operator(..., False)`) 끝 상태는 같다.
  # 멱등이다 — `provision-service-operator.sql` 이 `ON CONFLICT DO NOTHING` 이다.
  operator_grant "verify:operator-grant" || return 1
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

# ② 계수 대조 — 판정표(`$RUN_DIR/preview-judgment.tsv`) ＋ 러너 verify.json ＋ 등재표 ＋ 알려진 결함 면제.
# 순회 경로와 `--verify-from` 경로가 같은 대조를 쓴다. 출력은 단계 로그(실행 기록)에 남긴다.
# $1 = verify.json · $2 = plan-manifest.yaml · 종료 1 = 대조 미달(면제 목록 판정 불가 포함)
verify_compare() {
  local verify="$1" manifest="$2"
  # 면제 목록은 레포의 `known-defects.json` 하나다. 다른 목록(`KNOWN_DEFECTS_FILE`)은 픽스처 표지
  # (`COLAB_RESEED_FIXTURE=1`)가 있을 때만 받는다 — 실운영에서 주면 승인 목록 밖 면제가 흔적 없이 들어오므로 실패한다.
  local kd_file="$RESEED_DIR/known-defects.json" kd_label="dev-package/tools/dev-reseed/known-defects.json"
  if [ -n "${KNOWN_DEFECTS_FILE:-}" ]; then
    if [ "${COLAB_RESEED_FIXTURE:-}" != 1 ]; then
      log "대조 결과 — 알려진 결함 면제 목록 판정 불가 · KNOWN_DEFECTS_FILE 은 픽스처(COLAB_RESEED_FIXTURE=1) 전용이다 — 레포 목록만 쓴다"
      return 1
    fi
    kd_file="$KNOWN_DEFECTS_FILE"; kd_label="fixture:$(basename "$KNOWN_DEFECTS_FILE")"
  fi
  # 계수 칸 판정을 먼저 따로 낸다(판정불가 포함). 아래 대조가 그 결과를 그대로 읽는다.
  count_verdict "$RUN_DIR/preview-judgment.tsv" "$RUN_DIR/count-verdict.json" || true
  python3 - "$verify" "$manifest" "$RUN_DIR/preview-judgment.tsv" "$RUN_DIR/counts.json" \
      "$EXPECT_DATASETS" "$EXPECT_PROJECTS" "$EXPECT_EDGES" "$RUN_DIR/count-verdict.json" \
      "$kd_file" "$RUN_DIR/blocked.jsonl" "$kd_label" <<'PY' | log_lines
import hashlib, json, os, re, sys
try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML 이 없다 — 등재표 대조 불가")
verify, manifest, tsv, out, nds, nproj, nedge, cvpath, kdpath, blockedpath, kdlabel = sys.argv[1:12]
v = json.load(open(verify))
m = yaml.safe_load(open(manifest))
cv = json.load(open(cvpath))
rows = [l.rstrip("\n").split("\t") for l in open(tsv) if l.strip()]
want = {}
preview_expected = {}
for d in m.get("datasets", []):
    want[str(d.get("seq"))] = str(d.get("processing_level") or d.get("level") or "")
    preview_expected[str(d.get("seq"))] = str(d.get("preview_expected") or "").strip()
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
no_preview_text = "미성립(포맷 미지원 · 판정 표에 이름으로)"
allowed_no_preview_names = {"SPI-4weeks", "SPEI-4weeks"}
manifest_preview_missing = sorted((s for s, value in preview_expected.items() if not value), key=int)
invalid_no_preview = sorted((str(d.get("seq")) for d in m.get("datasets", [])
                             if str(d.get("preview_expected") or "").strip() == no_preview_text
                             and d.get("name") not in allowed_no_preview_names), key=int)
expected_unestablished = sorted((s for s, value in preview_expected.items()
                                 if value == no_preview_text), key=int)
unexpected_unestablished = sorted(set(unestablished) - set(expected_unestablished), key=int)
# 「기대와 달리 미리보기 성립」은 **실제로 성립한 행**에만 붙인다 — 판정불가는 재지 못한 것이지 성립이 아니다
# (판정불가는 위 「미리보기 판정불가」로 따로 낸다).
established = [r[0] for r in rows if r[3] == "성립"]
missing_unestablished = sorted(set(expected_unestablished) & set(established), key=int)
# ── 알려진 제품 결함 면제(`known-defects.json` · 면제 수용 = 사용자 확인 — approved 칸) ──────────────────────
# 면제 = seq·이름·관측 판정·비고 머리(notePrefix)·비고 필수 조각(noteContains **전부**)이 모두 목록 항목과 맞는 행.
#   비고 조각이 결함의 모양을 못 박는다 — 13·14(#133)는 로그인 [0]·상세 [1]·보기 활성 [false]·미지원 표시 [0]·누름 없음,
#   16(#134)은 slot [failed]·preview-unavailable [0]. 로그아웃·빈 화면·다른 원인의 실패는 같은 판정이어도 면제하지 않는다.
# 판정불가 면제 행의 파생(계수·가공 단계 판정불가, 가공 단계 불일치)은 그 칸 값이 **정확히 `?`** 일 때만 함께 면제한다 —
#   빈 값·숫자 아닌 값·실제로 읽은 값의 불일치 · 「미지정」 · 미연결 · 다른 행은 면제하지 않는다.
# 목록이 없거나 틀리면 **빈 목록으로 접지 않고** 대조를 실패시킨다.
def kd_fail(why):
    print("대조 결과 — 알려진 결함 면제 목록 판정 불가(%s) · %s" % (kdlabel, why))
    raise SystemExit(1)
try:
    kd_bytes = open(kdpath, "rb").read()
    kd = json.loads(kd_bytes.decode("utf-8"))
except FileNotFoundError:
    kd_fail("파일 부재")
except (OSError, ValueError) as exc:
    kd_fail("읽지 못함 %s" % type(exc).__name__)
if not isinstance(kd, dict) or kd.get("schema") != "colab-reseed-known-defects/1":
    kd_fail("스키마가 colab-reseed-known-defects/1 이 아니다")
if not isinstance(kd.get("entries"), list):
    kd_fail("entries 목록이 없다")
manifest_names = {str(d.get("seq")): str(d.get("name") or "") for d in m.get("datasets", [])}
defects = {}
for e in kd["entries"]:
    s = e.get("seq") if isinstance(e, dict) else None
    if isinstance(s, bool) or not (isinstance(s, int) or (isinstance(s, str) and s.isdigit())):
        kd_fail("seq 가 숫자가 아닌 항목")
    s = str(s)
    for k in ("name", "notePrefix", "reason", "approved"):
        if not isinstance(e.get(k), str) or not e[k].strip():
            kd_fail("seq %s 의 %s 칸이 비었다" % (s, k))
    nc = e.get("noteContains")
    if not isinstance(nc, list) or not nc or not all(isinstance(x, str) and x.strip() for x in nc):
        kd_fail("seq %s 의 noteContains 가 비어 있지 않은 조각 목록이 아니다" % s)
    if not re.fullmatch(r"#[0-9]+", str(e.get("issue") or "")):
        kd_fail("seq %s 의 issue 가 #번호 가 아니다" % s)
    if e.get("expectedVerdict") not in ("판정불가", "미성립"):
        kd_fail("seq %s 의 expectedVerdict 가 판정불가·미성립 이 아니다" % s)
    if s in defects:
        kd_fail("seq %s 중복" % s)
    if s not in manifest_names:
        kd_fail("seq %s 가 등재표에 없다" % s)
    if manifest_names[s] != e["name"]:
        kd_fail("seq %s 이름이 등재표(%s)와 다르다" % (s, manifest_names[s]))
    defects[s] = e
rowmap = {r[0]: r for r in rows}
def kd_matches(s, e):
    r = rowmap.get(s)
    return (bool(r) and len(r) > 7 and r[1] == e["name"] and r[3] == e["expectedVerdict"]
            and r[7].startswith(e["notePrefix"]) and all(x in r[7] for x in e["noteContains"]))
exempt = {s: e for s, e in defects.items() if kd_matches(s, e)}
derived = {s for s, e in exempt.items() if e["expectedVerdict"] == "판정불가"}
def q_only(*cells):  # 파생 면제 = 재지 못한 칸이 **정확히 `?`** 뿐일 때(빈 값·다른 값은 다른 실패다)
    return all(c.strip() == "?" or c.strip().isdigit() for c in cells) and any(c.strip() == "?" for c in cells)
f_undecided = [s for s in undecided if s not in exempt]
f_unexpected_unestablished = [s for s in unexpected_unestablished if s not in exempt]
f_count_undecided = [s for s in count_undecided if not (s in derived and q_only(rowmap[s][5], rowmap[s][6]))]
f_level_undecided = [s for s in level_undecided if not (s in derived and rowmap[s][2].strip() == "?")]
f_level_mismatch = [s for s in level_mismatch if not (s in derived and rowmap[s][2].strip() == "?")]
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
    "previewExpectedUnestablishedSeq": expected_unestablished,
}
bad = []
# 「판정불가」는 성립도 미성립도 아니다 — **재지 못한 것**이고 통과로 세지 않는다.
if f_undecided: bad.append("미리보기 판정불가 seq %s" % ",".join(f_undecided))
if manifest_preview_missing: bad.append("등재표 미리보기 기대 부재 seq %s" % ",".join(manifest_preview_missing))
if invalid_no_preview: bad.append("미리보기 없음 기대 대상 오류 seq %s" % ",".join(invalid_no_preview))
if f_unexpected_unestablished: bad.append("예상 밖 미리보기 미성립 seq %s" % ",".join(f_unexpected_unestablished))
if missing_unestablished: bad.append("기대와 달리 미리보기 성립 seq %s" % ",".join(missing_unestablished))
# 계수·가공 단계·등재표도 같다 — **재지 못한 것**을 0 으로 접지 않는다.
if f_count_undecided: bad.append("계수 판정불가 seq %s" % ",".join(f_count_undecided))
if f_level_undecided: bad.append("가공 단계 판정불가 seq %s" % ",".join(f_level_undecided))
if manifest_level_missing: bad.append("등재표 가공 단계 부재 seq %s" % ",".join(manifest_level_missing))
if res["datasets"]["ui"] != int(nds): bad.append("데이터셋 계수 %s" % res["datasets"]["ui"])
if res["edges"]["ok"] != int(nedge): bad.append("간선 계수 %s" % res["edges"]["ok"])
if f_level_mismatch: bad.append("가공 단계 불일치 seq %s" % ",".join(f_level_mismatch))
if unset: bad.append("「미지정」 seq %s" % ",".join(unset))
if unlinked: bad.append("프로젝트 미연결 seq %s" % ",".join(unlinked))
if len(rows) != int(nds): bad.append("판정 표 %d 행" % len(rows))
failing = set(f_undecided) | set(f_unexpected_unestablished) | set(missing_unestablished) | set(f_count_undecided) \
    | set(f_level_undecided) | set(f_level_mismatch) | set(unset) | set(unlinked)
unneeded = [s for s in defects if s not in exempt and s in rowmap and s not in failing]
# 통과한 회차의 면제 행 차단 항목(순회가 그 행에서 낸 것)은 면제 기록으로 옮긴다 — 남기면 result.json 이
# failed 로 선다. 실패한 회차는 blocked.jsonl 을 그대로 둔다.
moved = {s: [] for s in exempt}
if not bad and exempt and os.path.exists(blockedpath):
    kept = []
    for line in open(blockedpath, encoding="utf-8"):
        if not line.strip():
            continue
        b = json.loads(line)
        hit = next((s for s, e in exempt.items() if b.get("stage") == "verify"
                    and str(b.get("reason", "")).startswith("seq=%s %s — " % (s, e["name"]))), None)
        if hit:
            moved[hit].append(b["reason"])
        else:
            kept.append(line if line.endswith("\n") else line + "\n")
    with open(blockedpath, "w", encoding="utf-8") as f:
        f.writelines(kept)
key = lambda s: int(s) if s.isdigit() else 0
res["knownDefects"] = {
    "file": kdlabel, "sha256": hashlib.sha256(kd_bytes).hexdigest(),
    "declared": len(defects), "exemptedCount": len(exempt),
    "exempted": [{"seq": s, "name": e["name"], "issue": e["issue"], "verdict": e["expectedVerdict"],
                  "reason": e["reason"], "approved": e["approved"], "blocked": moved[s]}
                 for s, e in sorted(exempt.items(), key=lambda kv: key(kv[0]))],
    "unneeded": [{"seq": s, "name": defects[s]["name"], "issue": defects[s]["issue"]} for s in sorted(unneeded, key=key)],
}
json.dump(res, open(out, "w"), ensure_ascii=False, indent=2)
print("알려진 결함 면제 %d건%s · 목록 %s sha256 %s" % (len(exempt), (" — " + " ; ".join(
    "%s · %s · %s" % (s, e["name"], e["issue"]) for s, e in sorted(exempt.items(), key=lambda kv: key(kv[0])))) if exempt else "",
    kdlabel, res["knownDefects"]["sha256"][:12]))
for s, e in sorted(exempt.items(), key=lambda kv: key(kv[0])):
    print("면제 승인 상태 — %s · %s · %s" % (s, e["issue"], e["approved"]))
for s in sorted(unneeded, key=key):
    print("면제 불필요 — %s · %s · %s — known-defects.json 에서 뺄 것" % (s, defects[s]["name"], defects[s]["issue"]))
for s in sorted(set(defects) - set(exempt) - set(unneeded), key=key):
    r = rowmap.get(s) or ["", "", "", "행 없음"]
    print("면제 조건 불일치 — %s · %s · %s (관측 판정 %s) — 종전 판정대로 센다" % (s, defects[s]["name"], defects[s]["issue"], r[3]))
print("대조 결과 — " + ("전건 일치" if not bad else " · ".join(bad)))
raise SystemExit(1 if bad else 0)
PY
  [ "${PIPESTATUS[0]}" -eq 0 ] || return 1
}

# 파이프로 받은 줄을 단계 로그(실행 기록)에 남긴다 — 대조·재개 판정이 표준출력에만 머물지 않게.
log_lines() { local l; while IFS= read -r l; do log "$l"; done; }

# `--verify-from <앞 실행 자리>` — 앞 실행의 판정표를 이어받고 **그 판정표에서 실패한 행만** 다시 잰다
# (2026-09-25 사용자 요청 「재시드에서 실패한 것만 · 전수할 필요 없다」).
# $1 = check | apply · $2 = state.json · $3 = plan-manifest.yaml
#   check = 로컬 검사만(판정표를 쓰지 않음 — reseed.sh 가 preflight 전에 · dry-run 이 부른다). 재순회 대상은 `$RUN_DIR/rewalk-seq.txt`.
#   apply = 검사 ＋ 앞 판정표 보관(`prior-preview-judgment.tsv`) ＋ 통과 행만 이번 판정표로 옮김 ＋ 출처(`verify-from.json`).
#   앞 counts.json 은 옮기지 않는다 — 대조가 이번 판정표로 다시 만든다(옮기면 대조가 죽을 때 앞 계수가 이번 결과로 남는다).
# 거부 = 자리·파일 부재 · 이번 실행 자리와 같음 · 앞 result.json 스키마·dryRun·대상 sha(hex 12/40) · 승인 기록과 sha 불일치 ·
#        데이터셋/프로젝트/간선 기대 불일치 · 앞 seed 가 ok 아님 · 앞 verify 미실행 · 판정표 seq·이름 ≠ state.json ·
#        state.json 의 dataset_id 가 앞 실행 verify 로그(상세 화면을 연 줄 · 재개 묶음 줄)에 없음 = 다른 적재를 잰 판정표.
# 앞·이번 대상 sha 가 다르면 거부하지 않고 주의 줄과 기록을 남긴다(다시 잰 행은 이번 배포에서 잰다).
verify_from_prior() {
  local mode="$1"
  python3 - "$mode" "$VERIFY_FROM" "$RUN_DIR" "$2" "$3" "${TARGET_SHA:-}" "$EXPECT_DATASETS" "$EXPECT_PROJECTS" \
      "$EXPECT_EDGES" <<'VFPY' | log_lines
import hashlib, json, pathlib, re, shutil, sys
mode, prior, run, state, manifest, sha, nds, nproj, nedge = sys.argv[1:10]
def refuse(why):
    print("verify-from 거부 — " + why)
    raise SystemExit(1)
HEX = re.compile(r"[0-9a-f]{12}|[0-9a-f]{40}")
p, r = pathlib.Path(prior), pathlib.Path(run)
if not p.is_dir():
    refuse("앞 실행 자리가 없다")
if p.resolve() == r.resolve():
    refuse("앞 실행 자리가 이번 실행 자리와 같다 — --run-dir 을 새 자리로 둔다")
for name in ("preview-judgment.tsv", "counts.json", "result.json", "logs/verify.log"):
    if not (p / name).is_file():
        refuse("앞 실행 자리에 %s 이 없다" % name)
if not pathlib.Path(state).is_file():
    refuse("seed 상태(state.json)가 없다 — COLAB_SEED_WORK_DIR 을 앞 실행이 쓴 폴더로 둔다")
try:
    res = json.loads((p / "result.json").read_text(encoding="utf-8"))
except ValueError:
    refuse("앞 result.json 을 읽지 못했다")
if res.get("schema") != "colab-reseed-result/1":
    refuse("앞 result.json 스키마가 colab-reseed-result/1 이 아니다")
if res.get("dryRun") is not False:
    refuse("앞 result.json 이 실제 실행이 아니다(dryRun %s)" % res.get("dryRun"))
counts = res.get("counts") or {}
for key, label, want in (("datasets", "데이터셋", nds), ("projects", "프로젝트", nproj), ("edges", "간선", nedge)):
    got = (counts.get(key) or {}).get("expected")
    if got != int(want):
        refuse("앞 실행의 %s 기대 %s ≠ 지금 %s — 다른 계획으로 적재한 판정표다" % (label, got, want))
prior_sha = str(res.get("targetSha") or "")
if not prior_sha:
    refuse("앞 result.json 에 대상 sha 가 없다 — 판정표를 잰 배포를 알 수 없다")
if not HEX.fullmatch(prior_sha):
    refuse("앞 result.json 대상 sha [%s] 가 hex 12/40자가 아니다" % prior_sha)
approval = p / "approval-record.json"
approval_sha = ""
if approval.is_file():
    approval_sha = str(json.loads(approval.read_text(encoding="utf-8")).get("targetSha") or "")
    if approval_sha and not (approval_sha.startswith(prior_sha) or prior_sha.startswith(approval_sha)):
        refuse("앞 실행의 result.json 대상 sha [%s] 와 승인 기록 대상 sha [%s] 가 다르다" % (prior_sha, approval_sha))
stages = {s.get("stage"): s.get("status") for s in res.get("stages") or []}
if stages.get("seed") != "ok":
    refuse("앞 실행의 seed 가 ok 가 아니다(%s)" % stages.get("seed"))
if stages.get("verify") in (None, "skipped"):
    refuse("앞 실행이 verify 를 돌지 않았다 — 판정표가 없다")
rows = [l.split("\t") for l in (p / "preview-judgment.tsv").read_text(encoding="utf-8").splitlines() if l.strip()]
st = json.load(open(state)).get("datasets", {})
want_names = {str(k): str(v.get("name") or "") for k, v in st.items()}
got_names = {row[0]: (row[1] if len(row) > 1 else "") for row in rows}
if len(rows) != len(got_names) or got_names != want_names:
    refuse("앞 판정표의 seq·이름이 지금 seed 상태(state.json)와 다르다")
ids = {str(k): str(v.get("dataset_id") or "") for k, v in st.items()}
if any(not v for v in ids.values()):
    refuse("seed 상태에 데이터셋 id 미확보 행이 있다")
# 적재 묶음 — 판정표가 **이 seed 적재**를 잰 것인지. 앞 실행 verify 로그에 이 state 의 dataset_id 가 모두 있어야 한다
# (상세 화면을 연 `…/datasets/<id>` 줄, 또는 앞 실행이 재개였으면 그 실행이 남긴 「verify-from 묶음」 줄).
seen = set()
for line in (p / "logs/verify.log").read_text(encoding="utf-8", errors="replace").splitlines():
    if " open " in line:
        seen.update(re.findall(r"/datasets/([^\s/?#]+)", line))
    elif "verify-from 묶음 dataset_id " in line:
        seen.update(line.split("verify-from 묶음 dataset_id ", 1)[1].split())
unbound = sorted((s for s, i in ids.items() if i not in seen), key=int)
if unbound:
    refuse("seed 상태의 dataset_id 가 앞 실행 verify 로그에 없다(seq %s) — 다른 적재를 잰 판정표다" % ",".join(unbound))
# 앞 판정표에서 실패한 행 = 이번에 다시 잴 행 — 판정이 성립(정본 포맷 미지원 행은 미성립)이 아니거나, 가공 단계를
# 못 읽었거나 등재표와 다르거나, 「미지정」·usage 계수가 숫자가 아니거나 미지정 > 0 · usage 0 인 행.
# 나머지(통과 행)는 앞 판정표 행을 그대로 잇는다.
import yaml
m = yaml.safe_load(open(manifest))
NO_PREVIEW = "미성립(포맷 미지원 · 판정 표에 이름으로)"
plan = {str(d.get("seq")): d for d in m.get("datasets", [])}
def failing(row):
    d = plan.get(row[0])
    if d is None or len(row) < 8:
        return True
    exp = str(d.get("preview_expected") or "").strip()
    want_level = str(d.get("processing_level") or d.get("level") or "")
    ok_verdict = (row[3] == "미성립") if exp == NO_PREVIEW else (row[3] == "성립")
    lv, u, g = row[2].strip(), row[5].strip(), row[6].strip()
    return (not ok_verdict or not lv or lv == "?" or not want_level or want_level not in row[2]
            or not u.isdigit() or not g.isdigit() or int(u) > 0 or int(g) == 0)
rewalk = sorted((row[0] for row in rows if failing(row)), key=int)
(r / "rewalk-seq.txt").write_text("".join(s + "\n" for s in rewalk), encoding="utf-8")
sha_match = bool(HEX.fullmatch(sha)) and (prior_sha.startswith(sha) or sha.startswith(prior_sha))
summary = ("앞 실행 %s(runId %s · 대상 sha %s · 결과 %s/%s) 판정표 %d행 — 통과 %d행은 잇고 실패 %d행(seq %s)만 다시 잰다"
           % (p.name, res.get("runId"), prior_sha, res.get("outcome"), res.get("failedStage"), len(rows),
              len(rows) - len(rewalk), len(rewalk), ",".join(rewalk) or "없음"))
if mode == "check":
    print("verify-from 검사 통과 — " + summary)
    raise SystemExit(0)
if not sha_match:
    print("verify-from 주의 — 이은 행은 대상 sha %s 에서 잰 것이고 이번 대상 sha 는 %s 다 · 두 배포 사이 미리보기 경로 변경은 사람이 확인한다"
          % (prior_sha, sha or "없음"))
shutil.copyfile(p / "preview-judgment.tsv", r / "prior-preview-judgment.tsv")
keep = set(rewalk)
(r / "preview-judgment.tsv").write_text("".join("\t".join(row) + "\n" for row in rows if row[0] not in keep), encoding="utf-8")
prior_files = {name: hashlib.sha256((p / name).read_bytes()).hexdigest() for name in ("preview-judgment.tsv", "counts.json")}
prov = {"schema": "colab-reseed-verify-from/1", "priorRunDirName": p.name, "priorRunId": res.get("runId"),
        "priorTargetSha": prior_sha, "priorApprovalTargetSha": approval_sha or None,
        "targetSha": sha or None, "targetShaMatches": sha_match,
        "priorOutcome": res.get("outcome"), "priorFailedStage": res.get("failedStage"),
        "carriedRows": len(rows) - len(rewalk), "rewalkedSeq": rewalk, "files": prior_files}
json.dump(prov, open(r / "verify-from.json", "w"), ensure_ascii=False, indent=2)
# 이 줄이 다음 재개의 적재 묶음 근거다(이번 verify 로그에는 다시 잰 행의 상세 화면만 열린다).
print("verify-from 묶음 dataset_id " + " ".join(ids[s] for s in sorted(ids, key=int)))
print("verify-from — " + summary)
VFPY
  [ "${PIPESTATUS[0]}" -eq 0 ] && return 0
  [ "$mode" = apply ] && blocked_add verify "verify-from 거부 — 앞 실행 자리의 판정표를 이을 수 없다(단계 로그 참조)"
  return 1
}

stage_verify() {
  if [ "$DRY_RUN" = 1 ]; then
    log "DRY 러너 verify.json 계수 대조(데이터셋 $EXPECT_DATASETS · 프로젝트 $EXPECT_PROJECTS · 간선 $EXPECT_EDGES)"
    if [ -n "${VERIFY_FROM:-}" ]; then
      # dry-run 도 앞 실행 자리를 실제로 검사한다(로컬 파일만) — 거부면 dry-run 도 실패한다.
      verify_from_prior check "$SEED_WORK_DIR/state.json" "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" || return 1
      local rewalk; rewalk="$(paste -sd, "$RUN_DIR/rewalk-seq.txt")"
      log "DRY verify-from $VERIFY_FROM — 통과 행은 앞 판정표를 잇는다 · 앞 판정표 보관 · 출처(runId·대상 sha·적재 묶음) 기록"
      log "DRY agent-browser open /datasets/<id> — 앞 판정표 실패 행만 seq ${rewalk:-없음} · 대기 ${PREVIEW_WAIT_MS}ms · 가공 단계 · 「미지정」 · usage-card · 미리보기 판정"
      log "DRY 대조(알려진 결함 면제 known-defects.json) → record-details → 계정 최종화"
    else
      log "DRY agent-browser open /datasets/<id> ×$EXPECT_DATASETS — 대기 ${PREVIEW_WAIT_MS}ms · 가공 단계 · 「미지정」 · usage-card · 미리보기 판정"
    fi
    log "DRY 정본 md 의 가공 단계 분포와 대조 · 미지정 0 · 프로젝트 미연결 0"
    return 0
  fi

  local state="$SEED_WORK_DIR/state.json" verify="$SEED_WORK_DIR/verify.json"
  [ -f "$verify" ] || { blocked_add verify "verify.json 부재 — seed 단계 산출물이 없다"; return 1; }
  verify_seed_contract "$verify" || { blocked_add verify "러너 기간·설명·간선 검증 미달"; return 1; }

  if [ -f "$ACCOUNTS_WORK_DIR/details-verified.json" ]; then
    log "같은 자료 검증 증거를 확인하고 계정 최종화·로그인 검증만 재개"
    [ -z "${VERIFY_FROM:-}" ] || log "verify-from 은 쓰지 않는다 — 자료 검증 증거(details-verified.json)가 이미 있다"
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

  # `--verify-from` = 앞 실행의 판정표를 잇고 **그 판정표에서 실패한 행만** 다시 잰다(2026-09-25 사용자 요청
  #   「재시드에서 실패한 것만」). 통과 행은 앞 판정표 행을 그대로 두고, 다시 잰 행을 덧붙인 뒤 seq 순으로 맞춘다.
  #   아래 ② 대조 → record-details → 계정 최종화는 같은 길로 간다.
  local walk_only=""
  if [ -n "${VERIFY_FROM:-}" ]; then
    verify_from_prior apply "$state" "$manifest" || return 1
    walk_only="$RUN_DIR/rewalk-seq.txt"
    log "① 상세 화면 순회 — 앞 판정표 실패 행만 seq $(paste -sd, "$walk_only") · 한 건당 최대 ${PREVIEW_WAIT_MS}ms · 브라우저 세션 $AB_SESSION"
  else
    log "① 상세 화면 순회 — $EXPECT_DATASETS 건 · 한 건당 최대 ${PREVIEW_WAIT_MS}ms · 브라우저 세션 $AB_SESSION"
    : > "$RUN_DIR/preview-judgment.tsv"
  fi
  # id 가 없는 행은 `-` 로 찍는다 — 탭이 연달아 오면 `read` 가 빈 칸을 접어 **이름이 id 자리로 밀린다**
  # (4회차 `20260914T035058Z` 실측 · seq 13 이 `/datasets/SPI-4weeks` 를 열었다).
  local ids; ids="$(python3 - "$state" "$manifest" "$walk_only" <<'PY'
import json, sys
import yaml
st = json.load(open(sys.argv[1]))
manifest = yaml.safe_load(open(sys.argv[2]))
only = set(open(sys.argv[3]).read().split()) if sys.argv[3] else None
expected = {str(row.get("seq")): str(row.get("preview_expected") or "")
            for row in manifest.get("datasets", [])}
for seq, row in sorted(st.get("datasets", {}).items(), key=lambda kv: int(kv[0])):
    if only is not None and seq not in only:
        continue
    print("%s\t%s\t%s\t%s" % (seq, row.get("dataset_id") or "-", row.get("name") or "-", expected.get(seq, "-")))
PY
)"
  local seq did name expected t0 t1 ms shown level unset_lv usage login_n info_n slot_state preview_file display_total unsupported_n
  local draw_enabled hit press press_method verdict u_press u_verdict u_unavail seen settle_rc
  while IFS=$'\t' read -r seq did name expected; do
    [ -n "$seq" ] || continue
    [ "$name" = - ] && name=""
    if [ "$did" = - ] || [ -z "$did" ]; then
      printf '%s\t%s\t?\t미성립\t0\t?\t?\t데이터셋 id 미확보\n' "$seq" "$name" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name — 데이터셋 id 미확보"
      continue
    fi
    if ! ab_dev open "$DEV_URL/datasets/$did" >/dev/null 2>&1; then
      printf '%s\t%s\t?\t판정불가\t0\t?\t?\t페이지 이동 실패\n' "$seq" "$name" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name — 페이지 이동 실패 · 이전 화면을 판정하지 않는다"
      continue
    fi
    if [ "$expected" = "미성립(포맷 미지원 · 판정 표에 이름으로)" ]; then
      # 배포 프론트의 `dt-preview-unsupported` 는 보기(draw)를 누르고 create 가 「그릴 수 없음」
      #   (NotRenderableError)으로 돌아온 뒤에만 그려진다(`ea21d8c2aa54` DatasetPreviewSection.tsx:239-240,362-366 ·
      #   그때 slot = failed). 누르지 않고 기다리기만 하면 끝내 서지 않는다(dev 1차 시도 seq 13·14 「미지원 상태 미확인」).
      # 그래서 다른 행과 같은 정착 → 적중 검사 → 초점 ＋ Enter(JS click 폴백)로 누른 뒤 표시를 기다린다.
      # 그릴 조각이 아예 없어 열자마자 표시가 서면(:155-156) 비활성 보기를 누르지 않는다.
      # 기대(미성립)는 바꾸지 않는다. 화면에 **실제로 보인 것**을 비고에 그대로 적어 판단 근거로 남긴다.
      unsupported_n=""; u_press="누름 없음"; ms=0; slot_state=""
      preview_settle unsupported; settle_rc=$?
      if [ "$settle_rc" = 0 ]; then
        hit="$(preview_hit_test)"; hit="${hit:-못 잼}"
        log "seq=$seq $name — 보기 적중 검사: $hit"
        t0="$(date +%s%3N)"
        press="$(preview_press)"; press_method="${press%%|*}"; slot_state="${press#*|}"
        log "seq=$seq $name — 보기 누름 = $press_method · slot [$slot_state]"
        u_press="누름 $press_method · 적중 $hit"
        if [ "$press_method" != none ]; then
          # 누른 순간부터 PREVIEW_WAIT_MS 안에 미지원 표시 · 또는 terminal(slot failed/done)을 기다린다.
          while :; do
            unsupported_n="$(ab_dev get count '[data-testid="dt-preview-unsupported"]' 2>/dev/null | tr -d ' \t\r\n')"
            [ "$unsupported_n" = 1 ] && break
            slot_state="$(ab_dev get attr '[data-testid="dt-preview-slot"]' data-preview-slot-state 2>/dev/null | tr -d ' \t\r\n')"
            case "$slot_state" in
              failed|done)
                unsupported_n="$(ab_dev get count '[data-testid="dt-preview-unsupported"]' 2>/dev/null | tr -d ' \t\r\n')"
                break ;;
            esac
            [ "$(( $(date +%s%3N) - t0 ))" -lt "$PREVIEW_WAIT_MS" ] || break
            sleep 0.05
          done
        fi
        ms=$(( $(date +%s%3N) - t0 ))
      elif [ "$settle_rc" = 1 ]; then
        log "seq=$seq $name — 보기 전 정착 미확인(${PREVIEW_WAIT_MS}ms · 파일 [$preview_file] · 보기 활성 [$draw_enabled] · slot [$slot_state]) · 보기를 누르지 않았다"
      fi
      login_n="$(ab_dev get count '[data-testid="login-submit"]' 2>/dev/null | tr -d ' \t\r\n')"
      info_n="$(ab_dev get count '[data-testid="basic-info"]' 2>/dev/null | tr -d ' \t\r\n')"
      level="$(ab_dev get text '[data-testid="ig-가공 단계"]' 2>/dev/null | tr '\n' ' ')"
      unset_lv="$(ab_dev get count '[data-testid="ig-unset-가공 단계"]' 2>/dev/null | tr -d ' \t\r\n')"
      usage="$(ab_dev get count '[data-testid="usage-card"]' 2>/dev/null | tr -d ' \t\r\n')"
      slot_state="$(ab_dev get attr '[data-testid="dt-preview-slot"]' data-preview-slot-state 2>/dev/null | tr -d ' \t\r\n')"
      draw_enabled="$(ab_dev is enabled "$PREVIEW_DRAW_SEL" 2>/dev/null | tr -d ' \t\r\n')"
      u_unavail="$(ab_dev get count '[data-testid="preview-unavailable"]' 2>/dev/null | tr -d ' \t\r\n')"
      seen="미지원 표시 [$unsupported_n] · slot [$slot_state] · 보기 활성 [$draw_enabled] · preview-unavailable [$u_unavail] · 로그인 [$login_n] · 상세 [$info_n] · $u_press"
      log "seq=$seq $name — 정본 미성립 행 화면: $seen"
      if [ "$login_n" = 0 ] && [ "$info_n" = 1 ] && [ "$unsupported_n" = 1 ]; then
        printf '%s\t%s\t%s\t미성립\t%s\t%s\t%s\t정본상 포맷 미지원 · %s\n' "$seq" "$name" "$level" "$ms" "$unset_lv" "$usage" "$seen" >> "$RUN_DIR/preview-judgment.tsv"
      elif [ "$login_n" = 0 ] && [ "$info_n" = 1 ] && [ "$slot_state" = done ]; then
        # 눌렀더니 그려졌다 — 기대(미성립)는 그대로 두고 불일치로 적는다(아래 대조가 「기대와 달리 미리보기 성립」을 낸다).
        printf '%s\t%s\t%s\t성립\t%s\t%s\t%s\t기대와 달리 미리보기 성립 · %s\n' "$seq" "$name" "$level" "$ms" "$unset_lv" "$usage" "$seen" >> "$RUN_DIR/preview-judgment.tsv"
        blocked_add verify "seq=$seq $name — 기대와 달리 미리보기 성립(정본 미성립 · 포맷 미지원) · $seen"
      elif [ "$login_n" = 0 ] && [ "$info_n" = 1 ]; then
        # 상세 화면은 섰다 — 읽은 가공 단계·「미지정」·usage 를 그대로 적어 그 칸들은 종전대로 대조받게 한다
        # (`?` 로 접으면 알려진 결함 면제 행의 가공 단계·미지정·프로젝트 연결이 한 번도 검사되지 않는다).
        printf '%s\t%s\t%s\t판정불가\t%s\t%s\t%s\t미지원 상태 미확인 · %s\n' "$seq" "$name" "$level" "$ms" "$unset_lv" "$usage" "$seen" >> "$RUN_DIR/preview-judgment.tsv"
        blocked_add verify "seq=$seq $name — 승인된 미지원 표시를 확인하지 못했다 · $seen"
      else
        printf '%s\t%s\t?\t판정불가\t%s\t?\t?\t미지원 상태 미확인 · %s\n' "$seq" "$name" "$ms" "$seen" >> "$RUN_DIR/preview-judgment.tsv"
        blocked_add verify "seq=$seq $name — 승인된 미지원 표시를 확인하지 못했다 · $seen"
      fi
      continue
    fi
    # 화면이 이미 고른 파일(기본 후보)을 그대로 쓴다 — 다시 고르지 않는다(위 PREVIEW_STABLE_MS 주석).
    preview_file=""; draw_enabled=""; slot_state=""
    preview_settle; settle_rc=$?
    if [ "$settle_rc" != 0 ]; then
      printf '%s\t%s\t?\t판정불가\t0\t?\t?\t미리보기 정착 미확인\n' "$seq" "$name" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name — 보기 전 정착 미확인(${PREVIEW_WAIT_MS}ms · 파일 [$preview_file] · 보기 활성 [$draw_enabled] · slot [$slot_state]) · 보기를 누르지 않았다"
      continue
    fi
    # 적중 검사 — 누르기 전에 보기 단추 중심이 무엇에 닿는지 남긴다(위 PREVIEW_HIT_JS 주석).
    hit="$(preview_hit_test)"; hit="${hit:-못 잼}"
    log "seq=$seq $name — 보기 적중 검사: $hit"
    t0="$(date +%s%3N)"
    # 누름 반영 확인 — 종료 0 은 반영의 증거가 아니다(비활성·덮인 버튼도 0). slot 이 idle 을 떠나야 한다.
    press="$(preview_press)"; press_method="${press%%|*}"; slot_state="${press#*|}"
    log "seq=$seq $name — 보기 누름 = $press_method · slot [$slot_state]"
    if [ "$press_method" = none ]; then
      printf '%s\t%s\t?\t판정불가\t%s\t?\t?\t클릭 미반영 · 누름 none · 적중 %s\n' "$seq" "$name" "$(( $(date +%s%3N) - t0 ))" "$hit" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name — 클릭 미반영(focus+Enter · JS click 모두 ${PREVIEW_CLICK_ACK_MS}ms 안에 slot 이 idle 을 떠나지 않았다 · 받은 값 [$slot_state] · 적중 검사 [$hit])"
      continue
    fi
    # Container presence is not completion: its slot starts in idle/drawing.
    # Poll the existing state attribute, keeping missing values undecidable.
    slot_state=""; display_total=""
    while :; do
      slot_state="$(ab_dev get attr '[data-testid="dt-preview-slot"]' data-preview-slot-state 2>/dev/null | tr -d ' \t\r\n')"
      display_total="$(ab_dev get text '[data-testid="dt-preview-total"]' 2>/dev/null | tr -d '\r\n')"
      case "$slot_state" in failed) break ;; done) [ -n "$display_total" ] && break ;; esac
      t1="$(date +%s%3N)"
      [ "$((t1 - t0))" -lt "$PREVIEW_WAIT_MS" ] || break
      sleep 0.05
    done
    t1="$(date +%s%3N)"; ms=$(( t1 - t0 ))
    if [ "$slot_state" != failed ] && { [ "$slot_state" != done ] || [ -z "$display_total" ]; }; then
      printf '%s\t%s\t?\t판정불가\t%s\t?\t?\t표시 완료 미확인\n' "$seq" "$name" "$ms" >> "$RUN_DIR/preview-judgment.tsv"
      blocked_add verify "seq=$seq $name — terminal/display 완료를 확인하지 못해 후속 요청을 중단한다"
      break
    fi
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
    verdict="$(preview_verdict "$shown")"
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
    # 비고 끝에 최종 slot 상태와 `preview-unavailable` 계수를 남긴다 — 미성립이 slot failed 인지 「볼 수 없다」 표시인지를
    # 판정표만으로 가른다(알려진 결함 면제가 그 조각을 요구한다). 거절 코드는 상세 화면 DOM 에 없어 적지 못한다.
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t누름 %s · 적중 %s · slot [%s] · preview-unavailable [%s]\n' \
      "$seq" "$name" "$level" "$verdict" "$ms" "$unset_lv" "$usage" "$press_method" "$hit" "$slot_state" "$shown" >> "$RUN_DIR/preview-judgment.tsv"
  done <<< "$ids"
  if [ -n "$walk_only" ]; then
    # 이은 행 ＋ 다시 잰 행을 seq 순으로 맞춘다(행 내용은 바꾸지 않는다).
    python3 - "$RUN_DIR/preview-judgment.tsv" <<'SORTPY'
import sys
path = sys.argv[1]
rows = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip()]
rows.sort(key=lambda l: int(l.split("\t", 1)[0]) if l.split("\t", 1)[0].isdigit() else 0)
open(path, "w", encoding="utf-8").write("".join(l + "\n" for l in rows))
SORTPY
  fi

  log "② 계수 대조 — 러너 verify.json ＋ 판정표 ＋ 정본 등재표 ＋ 알려진 결함 면제"
  verify_compare "$verify" "$manifest" || return 1
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

  # ⑸ 초기화 도구 — **계수와 계획만** 낸다. 임시 폴더에 쓰고 지운다. `--phase s3-apply` 는 부르지 않는다.
  #   BYPASSRLS 계수(두 체인) → 그 파일을 참조 키로 준 `--dry-run` 계획 → `stage_s3` ② 와 **같은 검토 본문**.
  #   시드된 dev 는 지금 DB 가 키를 가리키므로 실행 모드 계획은 거부된다 — dry-run 은 거부 사유를 찍고
  #   `dryRun` 표지가 붙은(s3-apply 가 받지 않는) 계획을 쓴다. 그래서 검토 본문이 실모드로 한 번 돈다.
  #   왜 = 종전 ⑸ 는 계획만 내고 지워 ② 검토는 실모드로 돈 적이 없었다(DR-4 §7).
  got="$(ssh_script "rehearse:s3-plan" <<EOF
set -euo pipefail
mkdir -p $reh_out && chmod 700 $reh_out
$(reset_count_precheck)
$(reset_count_cmd "$reh_out") --phase count --report /out/count.json
ref_sha="\$(sudo sha256sum $reh_out/count.json | cut -c1-64)"
$(reset_count_cmd "$reh_out") --phase s3-plan --dry-run --plan-out /out/plan.json --report /out/s3-plan.json \\
    --referenced-keys /out/count.json --referenced-sha256 "\$ref_sha"
$(s3_review_script "$reh_out")
sudo rm -rf $reh_out
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
