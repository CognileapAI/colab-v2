#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# H6 — `SubagentStop` (matcher: `researcher`) · 스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절.
#
# 무엇을 해소하나 (D9 — 하루 4회): 서브에이전트는 자기 워크트리에서 돈다. 조사 산출물이
#   **미추적인 채로** 끝나면 다음 워크트리에서 그 파일이 보이지 않고, 지시문이 그것을 근거로
#   지목하면 다음 레인은 읽지 못한다(`.claude/rules/colab-rules.md §2-2` — 2026-08-29 한 세션에서 4회).
#
# ⛔ **자동 커밋하지 않는다**(v1 H9 철회 · 스펙 C H6 행 축자):
#   「⚠ **자동 커밋하지 않는다**(v1 H9 철회). 미추적 파일이 `dev-package/sessions/`·`reports/`
#     아래 있으면 exit 2 + 경로 열거 → researcher 가 `git add <경로>` 로 직접 커밋.
#     `git add -A`·push 금지. 오케스트레이터 체크아웃의 무관한 변경을 쓸어담지 않는다」
#
# ⚠ 차단 조건은 **미추적(`??`)뿐이다.** 추적 중인 파일의 수정분은 차단하지 않는다 —
#   스펙이 「미추적 파일이 … 있으면」이라고만 못박았고, 넓히면 편집 중인 문서가 종료를 막는다.
#   대신 **stdout 에 안내로 적는다**(exit 0 의 stdout 은 「shown to Claude as context」).
#
# ── SubagentStop 입력 스키마 (stdin · 문서 인용 https://code.claude.com/docs/en/hooks) ──────
#     {
#       "session_id": "abc123",
#       "cwd": "/home/user/my-project",
#       "permission_mode": "default",
#       "hook_event_name": "SubagentStop",
#       "agent_id": "agent_abc123",
#       "agent_type": "security-reviewer",
#       "last_assistant_message": "…",
#       "stop_hook_active": false
#     }
#   · `cwd` — "Current working directory when the hook is invoked" ⇒ **판정 대상은 이 자리**다.
#     서브에이전트의 워크트리이며 `$CLAUDE_PROJECT_DIR`(세션이 뜬 체크아웃)와 다르다.
#   · `agent_type` — "Agent name (for example, `\"Explore\"` or `\"security-reviewer\"`).
#     Present when the session uses `--agent` or the hook fires inside a subagent."
#   · `agent_id` — "Present only when the hook fires inside a subagent call."
#   · `stop_hook_active` — "Boolean indicating whether a `Stop` hook is currently running.
#     When `true`, a `SubagentStop` hook shouldn't start long-running operations…"
#     ⇒ 이 훅은 `git status` 한 번뿐이라 그 조건에서도 그대로 돈다(장기 작업 없음).
#   · matcher — "For `SubagentStart` and `SubagentStop`, the matcher filters the agent type."
#     ⇒ 걸러 주는 것은 하네스이고, 아래 방어는 **직접 호출·오등록** 대비다.
#
# ── 차단 규약 (문서 인용) ─────────────────────────────────────────────────────
#   exit 2 = "SubagentStop: **Prevents the subagent from stopping**. The blocking message is the
#   reason from your JSON's blocking decision when it makes one, and your stderr text otherwise."
#   ⇒ **stderr 가 곧 차단 사유**다. exit 0 의 stdout 은 "For `Stop` and `SubagentStop`, stdout is
#   shown to Claude as context" ⇒ 안내는 stdout 으로 적는다.
#   ⚠ **exit 1 은 통과다**(스펙 C 「차단은 exit 2 만 유효」). 판정 불가(payload 파싱 실패·
#     python3 부재·체크아웃 아님)는 **통과**로 둔다 — 훅이 세션을 세우면 곧 상시 무력화로 끝난다.
set -uo pipefail

WATCH_DIRS=(dev-package/sessions dev-package/reports dev-package/intent)

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi
[ -n "$payload" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

read_fields() {
  printf '%s' "$payload" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
if not isinstance(d,dict): sys.exit(0)
print(d.get("cwd") or "")
print(d.get("agent_type") or "")
print(str(d.get("stop_hook_active") or ""))
' 2>/dev/null
}

mapfile -t _f < <(read_fields)
CWD="${_f[0]:-}"
AGENT="${_f[1]:-}"
[ -n "$CWD" ] || exit 0
[ -d "$CWD" ] || exit 0
# matcher 가 이미 걸렀다. 다른 타입으로 들어오면(직접 호출·오등록) 판정하지 않고 통과한다.
case "$AGENT" in ""|researcher) ;; *) exit 0 ;; esac

# `--untracked-files=all` — 디렉터리 하나로 접히면 그 안의 파일 이름이 안 보이고,
# 그러면 「`git add <경로>` 로 열거된 것만」이라는 지시가 성립하지 않는다.
status="$( ( cd "$CWD" && git status --porcelain --untracked-files=all -- "${WATCH_DIRS[@]}" ) 2>/dev/null )" || exit 0

untracked="$(printf '%s\n' "$status" | grep '^?? ' | sed 's/^?? //' || true)"
modified="$(printf '%s\n' "$status" | grep -v '^?? ' | grep -v '^$' || true)"

if [ -n "$untracked" ]; then
  {
    echo "⛔ 차단(H6 uncommitted-artifacts) — 조사 산출물이 **미추적**으로 남아 있다. 미추적 파일은 다음 워크트리에서 보이지 않는다(rules §2-2)."
    printf '%s\n' "$untracked" | sed 's/^/   · /'
    echo "   → \`git add <경로>\` 로 **열거된 경로만** 커밋한다. \`git add -A\` 금지 · push 금지(병합·push 는 오케스트레이터 몫)."
    [ -n "$modified" ] && {
      echo "   (참고 — 추적 중이면서 수정된 것들. 차단 사유는 아니다:)"
      printf '%s\n' "$modified" | sed 's/^/     /'
    }
    echo "   정말 남겨야 하면 \`COLAB_HOOKS=0\` 을 앞에 붙여 다시 부른다."
  } >&2
  exit 2
fi

if [ -n "$modified" ]; then
  echo "H6 — 미추적 0건(통과). 추적 중인 수정분이 있다(차단 사유 아님 · 커밋 여부는 판단해서 정한다):"
  printf '%s\n' "$modified" | sed 's/^/   /'
fi
exit 0
