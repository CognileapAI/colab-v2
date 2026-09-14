#!/usr/bin/env bash
# dev 재생성 공통 함수 — 로그 · 명령 실행 · 비밀 가리기 · 단계 기록.
#
# 이 파일은 단독 실행하지 않는다. `reseed.sh` 가 source 한다.
# 규약 셋 —
#   ⑴ 비밀 값(접속 문자열 · 비밀번호 · 키)은 argv·로그·결과 JSON 에 0건이다.
#       값이 움직이는 길은 표준입력과 원격 셸 안의 0600 파일 읽기 둘뿐이다.
#   ⑵ 외부 명령은 전부 `run`·`run_capture`·`ssh_dev`·`ssh_script` 를 거친다.
#       `--dry-run` 은 그 네 함수에서만 갈린다 — 단계 본문에 분기를 두지 않는다.
#   ⑶ 단계 하나가 비영 종료하면 그 자리에서 멈춘다. 자동 재시도는 없다.

# ── 비밀 가리기 ───────────────────────────────────────────────────────────
# 접속 문자열의 비밀번호 필드와 비밀번호 환경변수 이름 뒤의 값을 로그에 남기지 않는다.
# 이름 넷의 출처 = `infra/staging/db-bootstrap.sh` 의 `DB_BOOTSTRAP_REQUIRED_ENV`
# (근거: R-DEV-RESET §11-1 ⑸).
SECRET_ENV_NAMES=(COLAB_OWNER_PASSWORD COLAB_APP_PASSWORD COLAB_AI_APP_PASSWORD COLAB_ACCOUNT_ADMIN_PASSWORD)

redact() {
  sed -E \
    -e 's#(://[^:/@[:space:]]+):[^@[:space:]]+@#\1:***@#g' \
    -e 's/(COLAB_OWNER_PASSWORD|COLAB_APP_PASSWORD|COLAB_AI_APP_PASSWORD|COLAB_ACCOUNT_ADMIN_PASSWORD|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN)=[^[:space:]]*/\1=***/g'
}

# ── 로그 ─────────────────────────────────────────────────────────────────
# 단계마다 자기 로그 파일을 쓴다. 실패 보고에 그 경로를 그대로 싣는다.
log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | redact | tee -a "${STAGE_LOG:-/dev/null}"
}

warn() { log "⚠ $*"; }

# ⚠ **프로세스를 죽이지 않는다 — 비영으로 돌아온다.**
# 종전에는 `exit` 였고, 그러면 단계 순환이 끊겨 `stage_end` 와 `report` 가 돌지 못했다.
# 결과는 「실패했는데 `result.json` 이 없다」 — 멈춘 자리·종료코드·로그 경로가 어디에도 안 남는다.
# 부르는 쪽은 `... || return 1` 이 아니라 `die "..." ; return 1` 또는 `|| { die "..."; return 1; }`
# 형태로 쓴다. 종료코드는 단계 순환이 모아 마지막에 한 번 낸다.
die() {
  log "⛔ $*"
  blocked_add die "$*" 2>/dev/null || true
  return "${DIE_CODE:-1}"
}

# ── 명령 실행 ────────────────────────────────────────────────────────────
# 읽을 수 있게 찍는다 — 공백·메타문자가 든 인자만 작은따옴표로 감싼다.
_fmt_cmd() {
  local a out=""
  for a in "$@"; do
    case "$a" in
      *[[:space:]\'\"\$\`\\]*|"") out+="'${a//\'/\'\\\'\'}' " ;;
      *) out+="$a " ;;
    esac
  done
  printf '%s' "${out% }"
}

run() {
  local shown; shown="$(_fmt_cmd "$@")"
  if [ "$DRY_RUN" = 1 ]; then
    printf 'DRY %s\n' "$shown" | redact | tee -a "${STAGE_LOG:-/dev/null}"
    return 0
  fi
  log "RUN $shown"
  "$@" 2>&1 | redact | tee -a "${STAGE_LOG:-/dev/null}"
  return "${PIPESTATUS[0]}"
}

# 출력을 변수로 받는다. dry-run 에서는 실행하지 않고 빈 문자열을 돌려준다.
run_capture() {
  local shown; shown="$(_fmt_cmd "$@")"
  if [ "$DRY_RUN" = 1 ]; then
    # 출력을 되받는 자리라 표준출력에 찍으면 호출자의 변수로 들어간다 — 표준오류로 보인다.
    printf 'DRY %s\n' "$shown" | redact | tee -a "${STAGE_LOG:-/dev/null}" >&2
    return 0
  fi
  printf '%s RUN %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$shown" | redact >> "${STAGE_LOG:-/dev/null}"
  "$@" 2>>"${STAGE_LOG:-/dev/null}"
}

# ── EC2 접촉 ─────────────────────────────────────────────────────────────
# 호스트·키는 환경변수로만 받는다(`infra/dev/ship.sh` 머리말과 같은 이름).
# `BatchMode=yes` 로 고정한다 — 사람 입력을 요구하는 자리를 만들지 않는다(무인 실행 전제).
ssh_dev() {
  run ssh -o BatchMode=yes -o IdentitiesOnly=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" "$@"
}

ssh_dev_capture() {
  run_capture ssh -o BatchMode=yes -o IdentitiesOnly=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" "$@"
}

# 표준입력으로 원격 스크립트를 넘긴다 — 비밀 값을 다루는 단계는 전부 이 길을 쓴다.
# 스크립트 본문이 argv 에 오르지 않아 원격 `ps` 에 남지 않는다.
ssh_script() {
  local label="$1"
  local body; body="$(cat)"
  if [ "$DRY_RUN" = 1 ]; then
    # 되받는 호출이 있으므로 표준오류로 낸다(`run_capture` 와 같은 이유).
    printf 'DRY ssh <dev> bash -s  # %s (%s 줄 · 본문은 표준입력)\n' \
      "$label" "$(printf '%s\n' "$body" | wc -l | tr -d ' ')" | tee -a "${STAGE_LOG:-/dev/null}" >&2
    return 0
  fi
  log "RUN ssh <dev> bash -s  # $label"
  printf '%s\n' "$body" \
    | ssh -o BatchMode=yes -o IdentitiesOnly=yes -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'bash -s' 2>&1 \
    | redact | tee -a "${STAGE_LOG:-/dev/null}"
  return "${PIPESTATUS[1]}"
}

# ── 단계 기록 ────────────────────────────────────────────────────────────
# 단계마다 JSON 한 조각을 남긴다. `report` 단계가 조각을 모아 result.json 을 만든다.
stage_begin() {
  CURRENT_STAGE="$1"
  mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
  STAGE_LOG="$RUN_DIR/logs/$CURRENT_STAGE.log"
  STAGE_STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  STAGE_T0="$(date +%s)"
  : > "$STAGE_LOG"
  log "── 단계 $CURRENT_STAGE 시작"
}

stage_end() {
  local code="$1"
  local ended; ended="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local dur=$(( $(date +%s) - STAGE_T0 ))
  python3 - "$RUN_DIR/stages/$CURRENT_STAGE.json" "$CURRENT_STAGE" "$code" \
      "$STAGE_STARTED" "$ended" "$dur" "logs/$CURRENT_STAGE.log" <<'PY'
import json, sys
path, name, code, started, ended, dur, logpath = sys.argv[1:8]
json.dump({"stage": name, "exitCode": int(code), "startedAt": started,
           "endedAt": ended, "durationSec": int(dur), "log": logpath},
          open(path, "w"), ensure_ascii=False, indent=2)
PY
  log "── 단계 $CURRENT_STAGE 종료 code=$code ${dur}s"
}

# 차단 항목은 이름·사유로 남긴다(라운드 §5 WU-C4 ⑹).
blocked_add() {
  mkdir -p "$RUN_DIR"
  python3 - "$RUN_DIR/blocked.jsonl" "${CURRENT_STAGE:-?}" "$1" "$2" <<'PY'
import json, sys
path, stage, name, reason = sys.argv[1:5]
with open(path, "a") as f:
    f.write(json.dumps({"stage": stage, "name": name, "reason": reason}, ensure_ascii=False) + "\n")
PY
}
