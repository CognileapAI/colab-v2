#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# `PostToolUse` (matcher: Edit|Write) — **코드 편집이면 Ponytail 경계를 맥락에 싣는다.**
#
# 무엇을 해소하나:
#   `colab-ponytail` 은 `colab-v2-work` 를 읽은 세션에만 닿는다. 그 절차를 읽지 않은 세션과
#   서브에이전트의 코드 편집에는 단순화 순서가 실리지 않는다. 첫 코드 편집 직후에 요지와
#   본문 경로를 실으면 이후 편집이 그 순서를 보고 이뤄진다.
#
# ⚠ **막지 않는다.** 훅은 본문을 맥락에 싣는 데까지만 강제하고 준수 판정은 하지 않는다.
#   언제나 exit 0 이고, 판독이 실패해도 조용히 넘어간다.
# ⚠ 같은 세션·에이전트에는 한 번만 싣는다. 표식이 60분을 넘기면 다시 싣는다 —
#   맥락이 요약되면 앞서 실은 문구가 남아 있다고 볼 수 없다.
# ⚠ 코드 경로가 아닌 편집에서는 **python3 를 부르기 전에** 끝낸다(`css-edit-audit.sh` 와 같다).
#
# ── 출력 (stdout · 문서 인용) ─────────────────────────────────────────────────
#   https://code.claude.com/docs/en/hooks — 입력 스키마 전문은 `git-guard.sh` 머리말에 있다.
#   · `hookSpecificOutput.additionalContext` 가 모델 맥락에 실린다. Codex 는
#     `scripts/agent-bridge.py` 가 이 JSON 에서 본문만 꺼내 같은 자리에 싣는다.
#   · `session_id` 는 서브에이전트 안에서도 같다 — 표식은 `agent_id` 까지 묶는다.
set -uo pipefail

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi
[ -n "$payload" ] || exit 0

# ── 값싼 선별 — 코드 루트 이름이 payload 에 없으면 여기서 끝이다(python 미기동).
case "$payload" in
  *contracts/*|*db/*|*frontend/*|*services/*|*infra/*|*scripts/*|*gates/*) : ;;
  *) exit 0 ;;
esac
command -v python3 >/dev/null 2>&1 || exit 0

mapfile -t _f < <(printf '%s' "$payload" | python3 -c '
import json,re,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
if not isinstance(d,dict): sys.exit(0)
ti=d.get("tool_input") or {}
if not isinstance(ti,dict): ti={}
print(d.get("tool_name",""))
print(d.get("cwd",""))
print(str(ti.get("file_path") or ""))
print(re.sub(r"[^\w-]","",str(d.get("session_id") or "")+"-"+str(d.get("agent_id") or "main")))
' 2>/dev/null)

TOOL="${_f[0]:-}"
CWD="${_f[1]:-}"
FP="${_f[2]:-}"
KEY="${_f[3]:-}"

case "$TOOL" in Edit|Write) : ;; *) exit 0 ;; esac
[ -n "$FP" ] && [ -n "$KEY" ] || exit 0
[ -n "$CWD" ] || CWD="$PWD"

TOP="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$TOP" ] || exit 0
REL="$FP"
case "$FP" in "$TOP"/*) REL="${FP#"$TOP"/}" ;; esac

# 코드 루트 = `.agents/harness.yaml` 의 package_roots + 하네스 코드(scripts·gates). 문서는 뺀다.
case "$REL" in *.md) exit 0 ;; esac
case "$REL" in
  contracts/*|db/*|frontend/*|services/*|infra/*|scripts/*|gates/*) : ;;
  *) exit 0 ;;
esac

MARK_DIR="${TMPDIR:-/tmp}/colab-ponytail"
MARK="$MARK_DIR/$KEY"
mkdir -p "$MARK_DIR" 2>/dev/null || exit 0
if [ -f "$MARK" ] && [ -z "$(find "$MARK" -mmin +60 2>/dev/null)" ]; then exit 0; fi
touch "$MARK" 2>/dev/null || exit 0

# 본문은 큰따옴표·줄바꿈 없는 한 줄이다 — JSON 을 printf 로 그대로 낸다.
MSG='[ponytail] 코드 편집이다. `.agents/skills/colab-ponytail/SKILL.md` 를 읽고 적용한다(기본 full) — 필요 여부 → 이 저장소의 기존 코드 재사용 → 표준 라이브러리 → 플랫폼 기능 → 설치된 의존성 → 최소 구현. 명시한 기능·수용 조건·접근성·보안·데이터 손실 방지·필수 검증은 줄이지 않는다. 사용자가 이 세션에서 포니테일 해제를 요청했으면 적용하지 않는다.'
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$MSG"
exit 0
