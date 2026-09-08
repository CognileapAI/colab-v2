#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# `PostToolUse` (matcher: Edit|Write) — **UI 작업에 되먹임 고리를 준다.**
#
# 무엇을 해소하나 (playbook 「give the agent a feedback loop on UI work」):
#   CSS 를 고치는 에이전트는 자기가 방금 무엇을 바꿨는지 **숫자로 보지 못한다.** 13px 미만 글자를
#   하나 줄였는지 하나 늘렸는지, 대비 미달 짝이 생겼는지, 정의 없는 토큰을 새로 참조했는지는
#   `css_audit.py` 를 손으로 부를 때만 보인다 — 그래서 아무도 부르지 않으면 회차가 끝날 때
#   design-review 가 그 값을 처음 재고, 그 시점에는 고칠 자리가 이미 여러 파일에 퍼져 있다.
#   저장 직후에 그 파일 한 줄만 찍어 주면 다음 편집이 그 값을 보고 이뤄진다.
#
# ⚠ **막지 않는다.** 이것은 판정이 아니라 맥락이다 — 판정은 게이트(`frontend-visual`)와
#   사람(design-review)이 한다. 언제나 exit 0 이고, 계측이 실패해도 조용히 넘어간다.
# ⚠ CSS 가 아닌 편집에서는 **python3 를 부르기 전에** 끝낸다 — 훅은 매 Edit·Write 마다 돌고,
#   여기서 인터프리터를 띄우면 그 비용이 모든 편집에 붙는다.
#
# ── PostToolUse 입력 스키마 (stdin · 문서 인용) ───────────────────────────────
#   https://code.claude.com/docs/en/hooks — 스키마 전문은 `git-guard.sh` 머리말에 있다.
#   · `tool_name`·`tool_input`·`tool_response` 는 이벤트별. Edit·Write 의 대상은
#     `tool_input.file_path` 한 자리다(PreToolUse 와 같다).
#   · PostToolUse 의 stdout 은 맥락으로 실려 들어간다 — 그래서 **한 줄만** 찍는다.
set -uo pipefail

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi
[ -n "$payload" ] || exit 0

# ── 값싼 선별 — `.css` 라는 글자가 payload 에 없으면 여기서 끝이다(python 미기동).
case "$payload" in *.css*) : ;; *) exit 0 ;; esac
command -v python3 >/dev/null 2>&1 || exit 0

mapfile -t _f < <(printf '%s' "$payload" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
if not isinstance(d,dict): sys.exit(0)
ti=d.get("tool_input") or {}
if not isinstance(ti,dict): ti={}
print(d.get("tool_name",""))
print(d.get("cwd",""))
print(str(ti.get("file_path") or ""))
' 2>/dev/null)

TOOL="${_f[0]:-}"
CWD="${_f[1]:-}"
FP="${_f[2]:-}"

case "$TOOL" in Edit|Write) : ;; *) exit 0 ;; esac
[ -n "$FP" ] || exit 0
case "$FP" in *.css) : ;; *) exit 0 ;; esac
[ -n "$CWD" ] || CWD="$PWD"

TOP="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$TOP" ] || exit 0
REL="$FP"
case "$FP" in "$TOP"/*) REL="${FP#"$TOP"/}" ;; esac

# 대상은 `frontend/src/**/*.css` 뿐이다 — 계측기의 토큰 정본(`frontend/src/shell/tokens.css`)이
# 그 트리 기준이라 밖의 파일은 「정의 없는 토큰」을 거짓으로 낸다.
case "$REL" in frontend/src/*) : ;; *) exit 0 ;; esac

AUDIT="$TOP/.claude/skills/design-review/scripts/css_audit.py"
[ -f "$AUDIT" ] || exit 0
[ -f "$TOP/$REL" ] || exit 0

# 요약표에서 **이 파일 행 하나만** 낸다. `--root frontend/src` 기준 상대경로가 행의 첫 칸이다.
ROW_KEY="${REL#frontend/src/}"
OUT="$(cd "$TOP" && python3 "$AUDIT" --root frontend/src "$REL" 2>/dev/null \
       | grep -F "| \`$ROW_KEY\` |" | head -1)" || true
[ -n "$OUT" ] || exit 0

# 칸 순서(정본 = css_audit.py 요약표): file · <13px · neg margin · undefined token ·
# local token def · box-shadow · motion decl · reduced-motion · contrast <4.5
echo "$OUT"
exit 0
