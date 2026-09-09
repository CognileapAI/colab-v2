#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# H4 — `PreToolUse` (matcher: Edit|Write) · 스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절.
#
# 무엇을 해소하나: **이미 `origin/main` 에 올라간 Alembic revision 을 고치는 것은 계약 파괴다.**
#   그 파일은 남의 DB 에서 이미 돌았다. 내용을 바꿔도 `alembic_version` 은 같은 id 를 들고 있어
#   **아무도 다시 돌리지 않는다** — 선언과 적용이 조용히 갈리고, 그 차이는 `schema-diff` 가
#   red 를 낼 때까지(또는 배포가 깨질 때까지) 보이지 않는다. 고치는 방법은 **새 revision** 하나다.
#
# ⚠ **조건은 「추적 중」이 아니라 `git cat-file -e origin/main:<경로>` 성공이다**(스펙 C H4 축자).
#   레인이 자기 첫 커밋 뒤 **자기 신규 revision** 을 다시 고치는 경우는 `origin/main` 에 없으므로
#   **통과한다.** 그것을 막으면 회차 안의 정상 작업이 전부 걸린다.
#
# ── PreToolUse 입력 스키마 (stdin · 문서 인용) ────────────────────────────────
#   https://code.claude.com/docs/en/hooks — 스키마 전문은 `git-guard.sh` 머리말에 있다.
#   · `cwd` — "Current working directory when the hook is invoked"
#   · `tool_name`·`tool_input` — "The `tool_name`, `tool_input`, and `tool_use_id` fields are
#     event-specific."  ⇒ Edit·Write 의 대상 파일은 `tool_input.file_path` 한 자리다.
#   · matcher — "`Edit\|Write` and `Edit, Write` each match either tool exactly"
#   · exit 2 = "Blocks the tool call" · "The blocking message is … your stderr text otherwise."
#   ⚠ exit 1 은 통과다. 판정을 못 하면 통과가 기본값이다.
# Effective 2026-09-09: malformed applicable input blocks; historical fail-open comments are superseded.
set -uo pipefail

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

# ── 1. 레포 상대경로로 바꾼다 ────────────────────────────────────────────────
# 문서·경로 규약상 절대경로를 판정 기준으로 쓰지 않는다(`CLAUDE.md §5`). `origin/main:<경로>` 도
# 레포 뿌리 기준 상대경로만 받는다.
TOP="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$TOP" ] || exit 0
REL="$FP"
case "$FP" in "$TOP"/*) REL="${FP#"$TOP"/}" ;; esac

# ── 2. Alembic 회차 파일인가 ─────────────────────────────────────────────────
# 실측 자리 둘 — `db/platform/versions/*.py` · `db/ai/versions/*.py`
# (`CLAUDE.md §3-3`: D9·D10 저장소는 D1~D8 과 마이그레이션 체인이 분리된다).
case "$REL" in
  db/platform/versions/*.py|db/ai/versions/*.py) : ;;
  *) exit 0 ;;
esac

# ── 3. `origin/main` 에 이미 있는가 ──────────────────────────────────────────
# 있으면 그 revision 은 이미 남의 DB 에서 돌았다 — 내용 수정은 선언과 적용을 갈라놓는다.
if git -C "$CWD" cat-file -e "origin/main:$REL" 2>/dev/null; then
  echo "⛔ 차단(H4 migration-guard) — 계약 파괴: origin/main의 마이그레이션은 수정 불가 — 새 revision을 만든다 ($REL)." >&2
  exit 2
fi
exit 0
