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
# ⚠ **조건은 두 가지다.** 어느 쪽도 아니면 **조용히 통과**한다 — TDD 레인은 시험을 먼저 쓰는 것이
#   정상 작업이고(design-review SKILL §3 「RED → GREEN」), 그것까지 막으면 회차 안의 정당한 일이 전부 걸린다.
#   ⑴ 열린 fix task 의 기록 RED 경로 — `lifecycle begin --role lane-worker --fix --red <시험>` 이 기록한
#      경로. 도구·env·agent_id 무관, 대조 기준 = `file_path` 가 속한 checkout. 출구 = 인계
#      (`handoff --mode complete`) · 버려진 task 는 부모가 그 worktree 를 제거 · PR 2 `handoff --mode blocked`.
#      정본 = `docs/development/lifecycle-evidence.md` 「fix 레인」.
#   ⑵ `COLAB_FIX_LANE=1` env 의 보호 4종(아래).
#
# 막는 자리 (⑵ fix 회차 env 일 때):
#   frontend/test/**        화면 동작 시험
#   services/*/tests/**     서비스 pytest 묶음
#   gates/**                게이트 판정부·픽스처
#   contracts/**            seam·이벤트 계약
# 예외 = `COLAB_ALLOW_TEST_EDIT=1` — ⑵ 에만. 시험 자체가 틀렸다는 판단은 **사람이 선언한 뒤** 한다.
#   ⑴ 의 잠금은 이 env 로 풀리지 않는다.
#
# ⚠ 경계 (2026-09-26 · spec S-HARNESS-IMPROVEMENT-20260925 A2·A3 · S-HARNESS-SRED-REDRUN-20260926):
#   · 대상 도구 = Edit/Write 뿐(`.claude/settings.json` PreToolUse matcher `Edit|Write`). `sed -i` ·
#     리다이렉션 · `tee` · `python -c` 같은 Bash 쓰기는 대상이 아니다 — ⑴ 은 인계 시 blob 대조가 잡는다.
#   · `COLAB_FIX_LANE=1` 은 Codex 경로(`scripts/agent-bridge.py` tool_environment · `scripts/dev.ps1`)만 넘긴다.
#     ⑴ 은 env 가 필요 없어 Claude·Codex 가 같다.
#   · 잠금 없는 세션의 비용 = bash `git rev-parse` + `ls` (python 호출 0 추가). 마커
#     `<git common dir>/colab-harness/red-locked/` 는 색인이고 판정은 task.json 이 한다.
#   · Bash 쓰기까지 잡는 사후 검사 = `lifecycle begin --scope <glob>` 를 선언한 task 의
#     handoff/H7 대조(인계 시점 · 도구 무관 · `docs/development/lifecycle-evidence.md` 「인계」).
#
# ── PreToolUse 입력 스키마 (stdin · 문서 인용) ────────────────────────────────
#   https://code.claude.com/docs/en/hooks — 스키마 전문은 `git-guard.sh` 머리말에 있다.
#   · `tool_name`·`tool_input` 은 이벤트별이고, Edit·Write 의 대상은 `tool_input.file_path` 한 자리다.
#   · exit 2 = "Blocks the tool call" · 차단 메시지는 stderr.
#   ⚠ 실패 방향은 2단이다. ⑴ 준비 실패(python3 부재 · envelope 이상 — 아래 validate-input) = exit 2
#     차단(2026-09-09 계약). ⑵ envelope 통과 뒤 판정 불가 = 통과. exit 1 은 Claude Code 규약상 비차단이나
#     이 hook 은 exit 1 을 내지 않는다.
# Effective 2026-09-09: malformed applicable input blocks; historical fail-open comments are superseded.
set -uo pipefail

# red-locked fast path — bash only; python runs only when a fix task is open.
# CLAUDE_PROJECT_DIR 부재(Claude 는 항상 준다 · bridge 는 ROOT) → LOCKED=1 로 두고 python 판정(보수 방향).
LOCKED=1
if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  COMMON="$(git -C "$CLAUDE_PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "$COMMON" ] && [ -z "$(ls -A "$COMMON/colab-harness/red-locked" 2>/dev/null)" ]; then LOCKED=0; fi
fi
# 잠금도 없고 선언된 회차도 아니면 이 훅의 대상이 아니다. **python3 를 부르기 전에** 끝낸다.
if [ "$LOCKED" = 0 ] && [ "${COLAB_FIX_LANE:-}" != "1" ]; then exit 0; fi

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi
# 2026-09-09 shared envelope contract: malformed applicable input fails closed.
command -v python3 >/dev/null 2>&1 || { echo 'hook readiness failure: python3 missing' >&2; exit 2; }
payload="$(printf '%s' "$payload" | python3 "$(dirname "${BASH_SOURCE[0]}")/lifecycle_contract.py" validate-input --field file_path)" || exit 2

[ -n "$payload" ] || exit 0

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
# 기준 = `file_path` 가 속한 checkout. 부모 세션이 lane worktree 의 파일을 고치면 payload cwd 는 부모지만
# 판정은 그 lane checkout 의 잠금으로 한다. 대상 디렉터리가 아직 없는 Write 는 cwd checkout 으로 폴백한다.
TOP="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || true)"
FTOP="$(git -C "$(dirname "$FP")" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$FTOP" ] || FTOP="$TOP"
REL="$FP"
if [ -n "$FTOP" ]; then
  case "$FP" in "$FTOP"/*) REL="${FP#"$FTOP"/}" ;; esac
fi

# ⑴ 열린 fix task 의 기록 RED 경로 — env·신원 무관. lookup 실패는 차단(잠금 상태에서만 도달).
if [ "$LOCKED" = 1 ] && [ -n "$FTOP" ]; then
  LOCK_OUT="$(python3 "$(dirname "${BASH_SOURCE[0]}")/lifecycle_contract.py" red-locked --checkout "$FTOP" --path "$REL")" \
    || { echo 'hook readiness failure: red-locked lookup failed' >&2; exit 2; }
  if [ -n "$LOCK_OUT" ]; then
    read -r LOCK_TASK LOCK_BLOB <<< "$LOCK_OUT"
    echo "⛔ 차단(test-file-guard · red-run) — 이 checkout 의 열린 fix task $LOCK_TASK 가 기록한 RED 시험 \`$REL\` 은 인계 전에 고칠 수 없다(blob $LOCK_BLOB 고정).
   출구: 제품 코드를 고쳐 GREEN 을 만든 뒤 handoff --mode complete · 시험 자체가 틀렸으면 부모가 재승인한 --red 로 새 task(버려진 task 의 잠금은 부모가 그 worktree 를 제거하면 풀린다 · PR 2 뒤 handoff --mode blocked).
   정본: docs/development/lifecycle-evidence.md 「fix 레인」. 훅을 비활성화하지 않는다." >&2
    exit 2
  fi
fi

# ⑵ 선언된 fix 회차(env)의 보호 4종. 사람 선언 예외는 이 분기에만 적용된다.
[ "${COLAB_FIX_LANE:-}" = "1" ] || exit 0
[ "${COLAB_ALLOW_TEST_EDIT:-}" = "1" ] && exit 0

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
