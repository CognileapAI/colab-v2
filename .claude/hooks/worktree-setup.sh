#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# H2 — `SubagentStart` (matcher: lane-worker) · 스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절.
#
# 무엇을 해소하나 (D1): 새 워크트리는 **추적 파일만** 들어온 신선한 체크아웃이라
#   `frontend/node_modules` 와 `services/*/.venv` 가 없다. 그 상태의 첫 전수는 red(준비) 10건이고,
#   그때까지 레인은 「내 코드가 깼나」를 20분 뒤진다. 그 10건을 스폰 시점에 지운다.
#
# ⚠ **비차단이다.** 무슨 일이 있어도 exit 0 — 실패는 종료코드가 아니라 **요약에 이름으로** 적힌다.
#   차단은 exit 2 만 유효하므로 여기서 1 을 내도 통과지만 「훅 오류」 잡음이 남는다. 0 으로 끝낸다.
#
# ⚠ venv 는 **복사가 아니라 재생성**이다. venv 안에는 절대경로가 박혀 있다 —
#   `pyvenv.cfg` 의 `command =` 줄, `bin/*` 스크립트의 shebang. 형제 워크트리에서 복사해 오면
#   그 경로가 남의 워크트리를 가리키고, pip·pytest 가 조용히 남의 트리를 고친다.
#
# ── SubagentStart 입력 스키마 (stdin · 문서 인용) ─────────────────────────────
#   https://code.claude.com/docs/en/hooks
#   "The `SubagentStart` hook fires when a subagent is spawned. Here is the complete input schema:"
#     {
#       "session_id": "abc123",
#       "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
#       "cwd": "/home/user/my-project",
#       "hook_event_name": "SubagentStart",
#       "agent_id": "unique-subagent-id",
#       "agent_type": "Explore"
#     }
#   · `cwd`: "Current working directory when the hook is invoked"
#   · `agent_type`: "Agent name (e.g. \"Explore\", \"Plan\", custom agent names, or plugin-scoped
#      names like `plugin:my-plugin:reviewer`)"
#
# ── 왜 `cwd` 를 읽고 `$CLAUDE_PROJECT_DIR` 을 쓰지 않나 (문서 인용) ───────────
#   https://code.claude.com/docs/en/worktrees — "Hook paths don't follow the worktree."
#   · "`${CLAUDE_PROJECT_DIR}` stays put: it still points at the project root where the session
#      started, so a hook command such as `${CLAUDE_PROJECT_DIR}/.claude/hooks/check-style.sh`
#      still runs the script in the main checkout."
#   · "`cwd` follows Claude: the `cwd` field in the hook's input JSON is the worktree root,
#      and it moves again when Claude runs `cd`. Read it when a hook needs the worktree path."
#   ⇒ **스크립트 자리는 `$CLAUDE_PROJECT_DIR`(settings.json 의 등록줄), 작업 대상은 `cwd`.**
#
# ── stdout 의 행선지 (문서 인용) ──────────────────────────────────────────────
#   "Unlike most hook events where plain-text stdout goes to the debug log only, `SessionStart`
#    and `SubagentStart` hooks add plain-text stdout as context that Claude can see and act on"
#   ⇒ 요약은 **한 화면**을 넘기지 않는다. 여기 적히는 줄은 레인의 컨텍스트를 먹는다.
set -uo pipefail

t0=$(date +%s)

# ── 1. 입력 ───────────────────────────────────────────────────────────────────
payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi

hook_field() { # $1=키 — python3 이 없거나 JSON 이 깨져도 훅은 죽지 않는다
  local key="$1" v=""
  if command -v python3 >/dev/null 2>&1; then
    v="$(printf '%s' "$payload" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
print(d.get(sys.argv[1],"") if isinstance(d,dict) else "")' "$key" 2>/dev/null || true)"
  fi
  [ -n "$v" ] || v="$(printf '%s' "$payload" | sed -n "s/.*\"$key\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1)"
  printf '%s' "$v"
}

WT="$(hook_field cwd)"
AGENT="$(hook_field agent_type)"
[ -n "$WT" ] || WT="$PWD"

echo "── worktree-setup (H2) ──────────────────────────────────────"
echo "  워크트리 : $WT"
echo "  에이전트 : ${AGENT:-(미상)}"

if [ ! -d "$WT" ] || [ ! -f "$WT/gates/run.sh" ]; then
  echo "  건너뜀 — CoLAB v2 체크아웃이 아니다(gates/run.sh 부재). env 를 세우지 않았다."
  echo "─────────────────────────────────────────────────────────────"
  exit 0
fi

# ── 1-b. 파이썬 판을 **레포가 요구하는 것**으로 고정한다 ─────────────────────
# ⚠ `uv venv` 를 `--python` 없이 부르면 uv 가 관리하는 **최신**(2026-09 기준 3.13)을 잡는다.
#   그런데 `services/*/pyproject.toml` 은 `requires-python = "==3.12.*"`, CI 는 `setup-python 3.12`,
#   Dockerfile 은 `python:3.12-slim` 이다. **금지된 판에서 돈 시험의 green 은 3.12 의 증거가 아니다.**
# 핀은 pyproject 가 쥔다 — 여기서 두 번째 정본을 적지 않고 그 줄을 읽는다.
PYV="$(sed -n 's/^requires-python[[:space:]]*=[[:space:]]*"[^0-9]*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' \
        "$WT"/services/*/pyproject.toml 2>/dev/null | head -1)"
[ -n "$PYV" ] || PYV="3.12"

# 판을 못 구하면 **짓지 않는다.** 틀린 판으로 지으면 시험이 돌긴 도는데 거짓말을 한다.
PY_BASE=""
if command -v uv >/dev/null 2>&1; then PY_BASE="$(uv python find "$PYV" 2>/dev/null | head -1 || true)"; fi
[ -x "$PY_BASE" ] || PY_BASE="$(command -v "python$PYV" 2>/dev/null || true)"
if [ -x "$PY_BASE" ]; then
  echo "  파이썬   : $PY_BASE (요구 $PYV · services/*/pyproject.toml)"
else
  echo "  ⚠ 파이썬 : python $PYV 를 못 찾았다 — venv 를 짓지 않는다(틀린 판의 green 은 증거가 아니다)."
fi

# ── 2. 각 자리를 따로 세운다 ─────────────────────────────────────────────────
LOGDIR="$(mktemp -d -p "${TMPDIR:-/tmp}" wt-setup-XXXXXX)"
SERVICES="core-api ai-service viz-render pipeline-worker"

sha_of() { # 인자로 받은 파일들의 sha256 을 한 줄로 — 핀이 바뀌면 다시 깐다
  local acc="" f
  for f in "$@"; do [ -f "$f" ] && acc="$acc$(sha256sum "$f" | cut -d' ' -f1)"; done
  printf '%s' "$acc" | sha256sum | cut -d' ' -f1
}

STAMP=".colab-worktree"   # <venv>/.colab-worktree — 1줄: 지을 때의 워크트리 절대경로 · 2줄: 파이썬 판

# ⚠ 「내 것인가」를 venv 스스로에게 물으면 안 된다. venv 안에서 `sys.prefix` 는 **부른 경로**에서
#   유도되므로 언제나 `$venv` 와 같다 — 항진명제다(복사본도 통과한다). uv venv 는 `command =` 를
#   적지 않고 `bin/pip` 도 없어서 옛 검사 3개가 전부 헛돌았다. 그래서 **우리가 스탬프를 박고**
#   다음 회차에 그 스탬프를 되읽는다. 스탬프가 없거나 남의 트리를 가리키면 낡은 것이다.
venv_is_stale() { # $1=venv 경로 — 「이 워크트리 것인가 · 요구한 판인가」 둘을 되묻는다
  local venv="$1" py="$1/bin/python" cfg="$1/pyvenv.cfg" root ver cfgver
  [ -x "$py" ] || return 0                              # ⑴ 실물이 없다
  [ -f "$venv/$STAMP" ] || return 0                     # ⑵ 우리가 짓지 않았다(스탬프 이전 판 포함)
  root="$(sed -n 1p "$venv/$STAMP" 2>/dev/null || true)"
  [ "$root" = "$WT" ] || return 0                       # ⑶ 남의 워크트리에서 복사돼 왔다
  ver="$(sed -n 2p "$venv/$STAMP" 2>/dev/null || true)"
  case "$ver" in "$PYV".*) : ;; *) return 0 ;; esac      # ⑷ 스탬프가 다른 판을 말한다
  # 스탬프만 믿지 않는다 — pyvenv.cfg 의 실물 판도 본다(stdlib=version · uv=version_info).
  if [ -f "$cfg" ]; then
    cfgver="$(sed -n 's/^version[[:space:]]*=[[:space:]]*//p' "$cfg" | head -1)"
    [ -n "$cfgver" ] || cfgver="$(sed -n 's/^version_info[[:space:]]*=[[:space:]]*//p' "$cfg" | head -1)"
    case "$cfgver" in ""|"$PYV".*) : ;; *) return 0 ;; esac   # ⑸ 3.13 venv 는 다시 짓는다
  fi
  return 1
}

make_venv() { # $1=venv 경로 — 판을 준 채로 짓고, 지어진 판을 되확인한 뒤 스탬프를 박는다
  local venv="$1" v
  [ -x "$PY_BASE" ] || { echo "python $PYV 를 못 찾았다(uv python find · PATH 둘 다)"; return 1; }
  if command -v uv >/dev/null 2>&1; then uv venv --python "$PY_BASE" "$venv" || return 1
  else "$PY_BASE" -m venv "$venv" || return 1; fi
  v="$("$venv/bin/python" -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])' 2>/dev/null || true)"
  case "$v" in "$PYV".*) : ;; *) echo "지어진 판이 다르다: ${v:-미상} (요구 $PYV)"; return 1 ;; esac
  printf '%s\n%s\n' "$WT" "$v" > "$venv/$STAMP"
}

setup_service() { # $1=단위 이름 — 로그 1개 · 상태 1줄을 남긴다
  local s="$1" dir venv log st want have rc=0 t
  dir="$WT/services/$s"; venv="$dir/.venv"
  log="$LOGDIR/$s.log"; st="$LOGDIR/$s.state"; t=$(date +%s)
  if [ ! -d "$dir" ]; then echo "없음|0|단위 자리가 없다" > "$st"; return 0; fi
  want="$(sha_of "$dir/requirements.txt" "$dir/requirements-dev.txt" "$dir/pyproject.toml")"
  have="$(cat "$venv/.colab-worktree-setup.sha" 2>/dev/null || true)"
  if ! venv_is_stale "$venv" && [ "$want" = "$have" ] && "$venv/bin/python" -c 'import pytest' >/dev/null 2>&1; then
    echo "재사용|0|핀 동일 · pytest 실물 · py $PYV" > "$st"; return 0
  fi
  if venv_is_stale "$venv"; then
    rm -rf "$venv"
    if ! make_venv "$venv" >"$log" 2>&1; then
      # 판을 못 구한 것을 「깔았다」로 세지 않는다 — 요약에 이름으로 남고 전수에서 red(준비)로 선다.
      echo "실패|$(( $(date +%s) - t ))|venv 미생성 — $(tail -2 "$log" | tr '\n' ' ' | cut -c1-120)" > "$st"
      return 0
    fi
  fi
  {
    if command -v uv >/dev/null 2>&1; then
      uv pip install --python "$venv/bin/python" -q -r "$dir/requirements.txt"
      [ -f "$dir/requirements-dev.txt" ] && uv pip install --python "$venv/bin/python" -q -r "$dir/requirements-dev.txt"
      uv pip install --python "$venv/bin/python" -q -e "$dir"
    else
      "$venv/bin/pip" install -q --disable-pip-version-check -r "$dir/requirements.txt"
      [ -f "$dir/requirements-dev.txt" ] && "$venv/bin/pip" install -q --disable-pip-version-check -r "$dir/requirements-dev.txt"
      "$venv/bin/pip" install -q --disable-pip-version-check -e "$dir"
    fi
  } >>"$log" 2>&1 || rc=$?
  if [ "$rc" -eq 0 ] && "$venv/bin/python" -c 'import pytest' >/dev/null 2>&1; then
    printf '%s' "$want" > "$venv/.colab-worktree-setup.sha"
    echo "신설|$(( $(date +%s) - t ))|" > "$st"
  else
    # 「깔았다」와 「pytest 가 실물로 있다」는 다른 사실이다 — CI 가 같은 스텝을 따로 둔다.
    echo "실패|$(( $(date +%s) - t ))|$(tail -3 "$log" | tr '\n' ' ' | cut -c1-160)" > "$st"
  fi
}

setup_frontend() {
  local dir="$WT/frontend" log="$LOGDIR/frontend.log" st="$LOGDIR/frontend.state" rc=0 t
  t=$(date +%s)
  if [ ! -f "$dir/package.json" ]; then echo "없음|0|frontend 자리가 없다" > "$st"; return 0; fi
  if [ -d "$dir/node_modules" ] && [ -x "$dir/node_modules/.bin/tsc" ]; then
    echo "재사용|0|node_modules · .bin/tsc 실물 확인" > "$st"; return 0
  fi
  if ! command -v npm >/dev/null 2>&1; then echo "실패|0|npm 이 PATH 에 없다" > "$st"; return 0; fi
  if [ -f "$dir/package-lock.json" ]; then
    ( cd "$dir" && npm ci ) >"$log" 2>&1 || rc=$?
  else
    ( cd "$dir" && npm install ) >"$log" 2>&1 || rc=$?
  fi
  if [ "$rc" -eq 0 ] && [ -x "$dir/node_modules/.bin/tsc" ]; then
    echo "신설|$(( $(date +%s) - t ))|" > "$st"
  else
    echo "실패|$(( $(date +%s) - t ))|$(tail -3 "$log" | tr '\n' ' ' | cut -c1-160)" > "$st"
  fi
}

setup_gate_venv() { # 게이트 도구 venv — 정본은 `gates/tools/_venv.sh` 다. 여기서 판을 다시 적지 않는다.
  local st="$LOGDIR/gates.state" log="$LOGDIR/gates.log" t rc=0
  t=$(date +%s)
  ( REPO_ROOT="$WT"; . "$WT/gates/tools/_venv.sh"; ensure_gate_venv worktree-setup ) >"$log" 2>&1 || rc=$?
  if [ "$rc" -eq 0 ]; then echo "확보|$(( $(date +%s) - t ))|gates/tools/_venv.sh 스탬프 기준" > "$st"
  else echo "실패|$(( $(date +%s) - t ))|$(tail -2 "$log" | tr '\n' ' ' | cut -c1-160)" > "$st"; fi
}

for s in $SERVICES; do setup_service "$s" & done
setup_frontend &
setup_gate_venv &
wait

# ── 3. 요약 — 한 화면 ────────────────────────────────────────────────────────
n_new=0; n_keep=0; n_fail=0
report() { # $1=이름 $2=state 파일
  local name="$1" state secs why
  if [ ! -f "$2" ]; then
    printf '  ⚠ 실패  %-28s 상태 파일이 없다(세우지 못했다)\n' "$name"; n_fail=$((n_fail+1)); return
  fi
  IFS='|' read -r state secs why < "$2"
  case "$state" in
    신설)        n_new=$((n_new+1));  printf '  신설    %-28s %s초\n' "$name" "$secs" ;;
    재사용|확보) n_keep=$((n_keep+1)); printf '  %s  %-28s %s\n' "$state" "$name" "${why:-이미 있다}" ;;
    없음)        printf '  없음    %-28s %s\n' "$name" "$why" ;;
    *)           n_fail=$((n_fail+1)); printf '  ⚠ 실패  %-28s %s초 — %s\n' "$name" "$secs" "$why" ;;
  esac
}
report "frontend/node_modules" "$LOGDIR/frontend.state"
for s in $SERVICES; do report "services/$s/.venv" "$LOGDIR/$s.state"; done
report "gates/.venv" "$LOGDIR/gates.state"

echo "  ── 계 : 신설 ${n_new} · 재사용 ${n_keep} · 실패 ${n_fail} · $(( $(date +%s) - t0 ))초"
if [ -f "${HOME}/.colab-v2-test.env" ]; then
  # ⚠ 이 스크립트는 `$CLAUDE_PROJECT_DIR`(= 세션이 뜬 체크아웃)에서 돌지만, 검사하는 대상은 `$WT` 다.
  #   `baseRef: fresh` 레인의 워크트리는 **origin/main** 이라 P-E 가 병합되기 전에는 그쪽 run.sh 에
  #   self-source 가 없다. 스크립트가 브랜치에 있다고 트리도 그렇다고 말하면 레인은 6 red(준비)를 본다.
  if grep -q COLAB_TEST_ENV_SOURCED "$WT/gates/run.sh" 2>/dev/null; then
    echo "  테스트 env : ~/.colab-v2-test.env 있음 — gates/run.sh 가 스스로 source 한다(직접 set -a 불요)"
  else
    echo "  테스트 env : ~/.colab-v2-test.env 있음 — 다만 **이 트리의 run.sh 는 아직 스스로 읽지 않는다**"
    echo "     (self-source 는 P-E 브랜치에만 있다 · 병합 전까지) → 전수 앞에 직접:"
    echo "     set -a; . ~/.colab-v2-test.env; set +a"
  fi
else
  echo "  ⚠ 테스트 env : ~/.colab-v2-test.env 가 없다 — 게이트는 red(준비·입력미선언 · exit 78)로 선다"
fi
if [ "$n_fail" -gt 0 ]; then
  echo "  ⚠ 실패 ${n_fail}건은 **red(준비)로 남는다.** 로그: $LOGDIR"
  echo "     건너뛴 것을 green 으로 세지 않는다 — 전수에서 그대로 red(준비)로 뜬다."
else
  rm -rf "$LOGDIR"
fi
echo "─────────────────────────────────────────────────────────────"
exit 0
