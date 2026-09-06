#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# H1 — `SessionStart` (matcher: startup|clear) · 스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절.
#
# 무엇을 해소하나 (D7·D20): 종전 `CLAUDE.md §1` 은 문서 5개를 순서대로 읽으라고 했고, 그 합이
#   2.4MB 였다. 세션은 느려지고, 컨텍스트가 요약되면서 규칙이 유실되고, 메인 세션이 대형 문서
#   본문을 끌어와 지시가 누락됐다. **읽을 것은 라운드 파일 하나다.**
#
# ⚠ **비차단이다** — 안내만 하고 exit 0. 라운드 파일이 0건인 신규 회차에도 「없음」을 찍고 통과한다.
#
# ── SessionStart 입력 스키마 (stdin · 문서 인용) ──────────────────────────────
#   https://code.claude.com/docs/en/hooks
#     {
#       "session_id": "abc123",
#       "transcript_path": "/home/user/.claude/projects/.../transcript.jsonl",
#       "cwd": "/home/user/my-project",
#       "permission_mode": "default",
#       "hook_event_name": "SessionStart"
#     }
#   matcher 값 — "startup"(새 세션) · "resume" · "clear" · "compact" · "fork".
#   이 훅은 `startup|clear` 에만 건다. resume·compact 는 이미 읽은 것을 다시 안내할 뿐이다.
#
# ── stdout 의 행선지 (문서 인용) ──────────────────────────────────────────────
#   "Unlike most hook events where plain-text stdout goes to the debug log only, `SessionStart`
#    and `SubagentStart` hooks add plain-text stdout as context that Claude can see and act on
#    in the session."
#   ⇒ 이 훅의 출력은 그대로 세션 컨텍스트다. **부트스트랩을 줄이러 온 훅이 스스로 길면 안 된다.**
set -uo pipefail

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi

# `cwd` 를 읽는다 — 워크트리 세션에서는 이것이 워크트리 뿌리다
# ("`cwd` follows Claude … Read it when a hook needs the worktree path" · worktrees 문서).
ROOT=""
if command -v python3 >/dev/null 2>&1; then
  ROOT="$(printf '%s' "$payload" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
print(d.get("cwd","") if isinstance(d,dict) else "")' 2>/dev/null || true)"
fi
[ -n "$ROOT" ] || ROOT="$(printf '%s' "$payload" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
[ -n "$ROOT" ] || ROOT="$PWD"

SPEC="docs/superpowers/specs/2026-09-06-harness-fable51-design.md"
RDIR="$ROOT/dev-package/prd/rounds"

# 최신 라운드 파일 = mtime 최신. 같은 mtime 이 여럿이면(체크아웃 직후 워크트리가 그렇다)
# 이름 사전순 뒤엣것을 고른다 — 「아무거나」가 되지 않게 가르는 축을 하나 더 둔다.
ROUND=""
if [ -d "$RDIR" ]; then
  ROUND="$(find "$RDIR" -maxdepth 1 -name 'R-*.md' -type f -printf '%T@\t%p\n' 2>/dev/null \
            | sort -t"$(printf '\t')" -k1,1n -k2,2 | tail -1 | cut -f2-)"
fi

echo "── 세션 시작 안내 (bootstrap-diet · H1) ─────────────────────"
if [ -n "$ROUND" ]; then
  echo "  읽을 것은 **라운드 파일 하나다** : ${ROUND#"$ROOT"/}"
else
  echo "  읽을 것은 **라운드 파일 하나다** : 없음 (dev-package/prd/rounds/R-*.md 가 아직 없다)"
fi
echo "  하네스 스펙(필요할 때만 · 링크로) : $SPEC"
echo "  ⛔ 종전 §1 의 **문서 5개 순서 읽기(03-HANDOFF · DOMAINS · WORK-UNITS · PLAN-SoT · sessions/)"
echo "     를 하지 않는다.** 합이 2.4MB 라 컨텍스트가 요약되면서 규칙이 유실된다(D7·D20)."
echo "     대형 문서는 통독하지 않고 **grep 한 줄**로 필요한 값만 꺼낸다. 링크로만 따라간다."
echo "─────────────────────────────────────────────────────────────"
exit 0
