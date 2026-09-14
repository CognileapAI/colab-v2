#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# `PreToolUse` (matcher: Edit|Write) — **선언된 fix 회차에 시험·계약을 고치지 못하게 막는다.**
#
# 무엇을 해소하나 (playbook 「hook blocks agent from editing test files during fix」):
#   결함을 고치라는 지시를 받은 에이전트에게 **가장 싼 green 은 코드가 아니라 시험을 고치는 것**이다.
#   기대값을 실측값으로 바꾸거나 케이스를 지우면 red 가 사라진다 — 결함은 그대로 있고 그것을
#   말해 주던 유일한 자리만 없어진다. 게이트도 같다: `gates/` 를 완화하거나 `contracts/` 의
#   기대를 낮추면 판정이 통과로 바뀐다. 이 레포의 대표 실패형(green-by-skip)의 **편집판**이다.
#   사람이 사후에 diff 를 읽어야만 보이는 종류라, 그 자리에서 막는다.
#
# ⚠ **조건은 「fix 회차라고 선언됐는가」다.** `COLAB_FIX_LANE=1` 이 없으면 **조용히 통과**한다 —
#   TDD 레인은 시험을 먼저 쓰는 것이 정상 작업이고(design-review SKILL §3 「RED → GREEN」),
#   그것까지 막으면 회차 안의 정당한 일이 전부 걸린다. 훅은 선언된 맥락에서만 말한다.
#
# 막는 자리 (fix 회차일 때):
#   frontend/test/**        화면 동작 시험
#   services/*/tests/**     서비스 pytest 묶음
#   gates/**                게이트 판정부·픽스처
#   contracts/**            seam·이벤트 계약
# 예외 = `COLAB_ALLOW_TEST_EDIT=1` — 시험 자체가 틀렸다는 판단은 **사람이 선언한 뒤** 한다.
#
# ── PreToolUse 입력 스키마 (stdin · 문서 인용) ────────────────────────────────
#   https://code.claude.com/docs/en/hooks — 스키마 전문은 `git-guard.sh` 머리말에 있다.
#   · `tool_name`·`tool_input` 은 이벤트별이고, Edit·Write 의 대상은 `tool_input.file_path` 한 자리다.
#   · exit 2 = "Blocks the tool call" · 차단 메시지는 stderr.
#   ⚠ exit 1 은 통과다. 판정을 못 하면 통과가 기본값이다 — 훅이 깨져 작업이 멈추지 않게.
# Effective 2026-09-09: malformed applicable input blocks; historical fail-open comments are superseded.
set -uo pipefail

# 선언되지 않은 회차는 이 훅의 대상이 아니다. **python3 를 부르기 전에** 끝낸다.
[ "${COLAB_FIX_LANE:-}" = "1" ] || exit 0
[ "${COLAB_ALLOW_TEST_EDIT:-}" = "1" ] && exit 0

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi
# 2026-09-09 shared envelope contract: malformed applicable input fails closed.
command -v python3 >/dev/null 2>&1 || { echo 'hook readiness failure: python3 missing' >&2; exit 2; }
payload="$(printf '%s' "$payload" | python3 "$(dirname "${BASH_SOURCE[0]}")/lifecycle_contract.py" validate-input --field file_path)" || exit 2

[ -n "$payload" ] || exit 0
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
[ -n "$CWD" ] || CWD="$PWD"

# 레포 상대경로로 바꾼다 — 절대경로를 판정 기준으로 쓰지 않는다(`CLAUDE.md §5` · migration-guard 와 같은 자리).
TOP="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || true)"
REL="$FP"
if [ -n "$TOP" ]; then
  case "$FP" in "$TOP"/*) REL="${FP#"$TOP"/}" ;; esac
fi

WHY=""
case "$REL" in
  frontend/test/*)    WHY="화면 동작 시험(frontend/test)" ;;
  services/*/tests/*) WHY="서비스 시험 묶음(services/*/tests)" ;;
  gates/*)            WHY="게이트 판정부·픽스처(gates/)" ;;
  contracts/*)        WHY="seam·이벤트 계약(contracts/)" ;;
  *) exit 0 ;;
esac

echo "⛔ 차단(test-file-guard) — 선언된 fix 회차(COLAB_FIX_LANE=1)에서는 $WHY 를 고칠 수 없다: \`$REL\`
   red 를 없애는 가장 싼 길은 시험·게이트를 고치는 것이고, 그러면 결함은 남고 그것을 말해 주던 자리만 사라진다.
   승인된 구현 범위를 고친다. 시험 자체 수정이 필요하면 승인된 시험 작성 단계로 돌아가 RED를 확인한 뒤 fix 구현 단계로 재진입한다. 훅을 비활성화하지 않는다." >&2
exit 2
