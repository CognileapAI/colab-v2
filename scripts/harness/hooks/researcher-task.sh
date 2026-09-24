#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# R1 — `SubagentStart` (matcher: researcher) · spec `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md`.
#
# 무엇을 해소하나: researcher 가 `lifecycle begin` 없이 스폰되면 H6(`uncommitted-artifacts.sh`)가
#   모든 정지를 막아 턴 한도까지 반송한다(A3 실측). 절차를 지시문 기억에 맡기지 않고
#   스폰 시점에 read-only task 를 하나 열어 task_id·run_id·handoff 명령을 맥락에 싣는다.
#
# ⚠ 자동 task 는 `--agent-id` 를 넣지 않는다. `stop()` 은 task 에 agent_id 가 있을 때만 payload 와
#   대조한다. SubagentStart·SubagentStop payload 의 agent_id 일치가 미증명이므로 정지 조건에 걸지 않는다.
#   payload agent_id 는 출력에만 찍어 researcher 가 산출물 task 를 열 때 쓴다.
#
# ⚠ 비차단이다. 무슨 일이 있어도 exit 0 — 실패는 「begin 실패」 한 줄과 직접 begin 명령으로 알린다.
#   stdout 은 평문으로 subagent 맥락에 실린다(Codex 는 bridge 가 additionalContext 로 옮긴다).
#
# 입력(stdin JSON): `cwd` · `agent_id` · `agent_type`. `$CLAUDE_PROJECT_DIR` 이 아니라 `cwd` 의
#   체크아웃에서 begin 한다(worktree 에서 뜬 researcher 는 그 사본에 task 를 가져야 한다).
set -o pipefail

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi

hook_field() { # $1=key — python3 이 없거나 JSON 이 깨져도 죽지 않는다
  local key="$1" v=""
  if command -v python3 >/dev/null 2>&1; then
    v="$(printf '%s' "$payload" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
v=d.get(sys.argv[1],"") if isinstance(d,dict) else ""
print(v if isinstance(v,str) else "")' "$key" 2>/dev/null || true)"
  fi
  [ -n "$v" ] || v="$(printf '%s' "$payload" | sed -n "s/.*\"$key\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1)"
  printf '%s' "$v"
}

[ "$(hook_field agent_type)" = "researcher" ] || exit 0

CWD="$(hook_field cwd)"
AGENT_ID="$(hook_field agent_id)"
[ -n "$CWD" ] || CWD="$PWD"
BEGIN="python3 scripts/agent-bridge.py lifecycle begin --role researcher"

fail() { # $1=사유 · $2=begin 을 실행할 위치
  echo "researcher-task: begin 실패 · 사유 $(printf '%s' "$1" | tr '\n' ' ' | cut -c1-200) · 직접 begin 명령 cd '$2' && $BEGIN"
  exit 0
}

command -v python3 >/dev/null 2>&1 || fail "python3 부재" "$CWD"
ROOT="$(git -C "$CWD" rev-parse --show-toplevel 2>&1)" || fail "git 체크아웃이 아니다: $ROOT" "$CWD"
[ -f "$ROOT/scripts/agent-bridge.py" ] || fail "scripts/agent-bridge.py 부재" "$ROOT"

OUT="$(cd "$ROOT" && $BEGIN 2>&1)" || fail "$(printf '%s' "$OUT" | tail -1)" "$ROOT"
IDS="$(printf '%s' "$OUT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print(d["task_id"], d["run_id"])' 2>/dev/null)" || fail "begin 출력 해석 불가: $(printf '%s' "$OUT" | tail -1)" "$ROOT"
TASK_ID="${IDS%% *}"
RUN_ID="${IDS##* }"

if [ -n "$AGENT_ID" ]; then ARTIFACT_BEGIN="$BEGIN --agent-id $AGENT_ID"; else ARTIFACT_BEGIN="$BEGIN"; fi

cat <<EOF
researcher-task: H6 작업 증거를 자동으로 열었다(read-only · --agent-id 없음). 명령은 체크아웃 루트에서 실행한다.
  checkout : $ROOT
  task_id  : $TASK_ID
  run_id   : $RUN_ID
  agent_id : ${AGENT_ID:-(payload 에 없음)}
마지막 단계: python3 scripts/agent-bridge.py lifecycle handoff --task $TASK_ID --mode read-only --summary '<요지>'
  출력된 COLAB_HANDOFF 줄을 최종 메시지 마지막 줄에 그대로 붙인다.
파일 산출물이 필요하면 $ARTIFACT_BEGIN --artifact runtime:artifacts/<파일> 로 task 를 하나 더 열고 그 task 로 handoff 한다.
이 task 가 열린 동안 같은 체크아웃에 커밋하면 인계가 거부된다.
EOF
exit 0
