#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# H5 — `PreToolUse` (matcher: Edit|Write) · 스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절.
#
# 무엇을 해소하나 (D3): **결정 번호 〈N〉 은 예약하지 않는다.** 두 레인이 각자 착수 시점의 다음 빈
#   번호를 집으면 같은 번호가 둘 난다 — 2026-08-29 에 `〈192〉`·`〈193〉` 이, 2026-08-31 에 `〈241〉` 이
#   실제로 그렇게 겹쳤다(`PLAN-SoT §9` 번호 발급 규율 · `rules/colab-rules.md §4-1`).
#   규율 요지 — 병합 직전 통합 브랜치의 원격 판(현재 `origin/develop`)을 다시 받아 마지막으로 쓰인
#   번호를 센다 · 착수 시점에 센 번호는 근거가 아니다. 그 재실측을 사람 기억에서 훅으로 내린다.
#   (2026-09-26 A6 — 기준을 통합 브랜치 develop 으로 옮겼다. 종전 기준은 과거 기본 브랜치였다.)
#
# ── 판정 규칙 ────────────────────────────────────────────────────────────────
#   대상 = `dev-package/PLAN-SoT.md` 를 고치는 Edit·Write 하나뿐.
#   ⚠ **§9 표의 「행 머리」만 본다.** 정규식 정본은 게이트가 이미 쓰는 것과 **같은 것**을 쓴다 —
#     `gates/tools/work_item_consistency.py:136`
#       DECISION_ROW_RE = re.compile(r"^\|\s*〈\s*(\d+)\s*〉\s*\|")
#     같은 파일 주석 축자: 「본문 안의 `〈n〉` 은 다른 결정을 **가리키는 인용**이라 중복이 정상이다」.
#     ⇒ 본문·다른 문서에서 기존 〈N〉 을 **인용만** 하는 편집에는 발동하지 않는다.
#   기대값 = `origin/develop` 의 최대 번호 + 1(그 사이 이 브랜치가 이미 쓴 번호는 건너뛴다).
#   여러 행을 한 번에 더하면 연속(N, N+1, …)이어야 한다.
#
# ── PreToolUse 입력 (stdin · 문서 인용) ──────────────────────────────────────
#   https://code.claude.com/docs/en/hooks — 스키마 전문은 `git-guard.sh` 머리말.
#   · `tool_name`·`tool_input` — "The `tool_name`, `tool_input`, and `tool_use_id` fields are
#     event-specific."  ⇒ 새 본문은 Edit 의 `tool_input.new_string`, Write 의 `tool_input.content`.
#   · `cwd` — "Current working directory when the hook is invoked"
#   · exit 2 = "Blocks the tool call" · "The blocking message is … your stderr text otherwise."
#   ⚠ 실패 방향은 2단이다. ⑴ 준비 실패 = exit 2 차단 — python3 부재 · envelope 이상(아래 validate-input,
#     2026-09-09 계약) · 새 결정 번호 후보가 있는데 기준(`origin/develop`)을 못 읽음(`git fetch origin develop`
#     뒤 재시도). ⑵ 그 밖의 판정 불가(대상 밖 도구·경로 · 후보 없음 · checkout 미해석) = 통과.
#     exit 1 은 Claude Code 규약상 비차단이나 이 hook 은 exit 1 을 내지 않는다.
# Effective 2026-09-09: malformed applicable input blocks; historical fail-open comments are superseded.
set -uo pipefail

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
case "$FP" in */dev-package/PLAN-SoT.md|dev-package/PLAN-SoT.md) : ;; *) exit 0 ;; esac
[ -n "$CWD" ] || CWD="$PWD"

TOP="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$TOP" ] || exit 0

# ── 기대값의 기준선 = `origin/develop` 의 최대 번호 ──────────────────────────
# 규율이 「병합 직전 통합 브랜치 원격 판 기준 재실측」이므로 워킹트리가 아니라 원격 판을 센다.
# 못 읽으면(원격 미등록·오프라인·미fetch) BASE 가 빈 채로 판정에 넘긴다 — 새 결정 번호 후보가 있을
# 때만 준비 실패(exit 2)로 막고, 후보가 없으면 통과한다. 워킹트리로 조용히 대체하지 않는다
# (워킹트리 판은 이 브랜치가 이미 쓴 번호를 포함해 기준이 될 수 없다).
BASE_SRC="origin/develop"
BASE="$(git -C "$CWD" show origin/develop:dev-package/PLAN-SoT.md 2>/dev/null \
        | grep -o '〈[0-9]\+〉' | tr -d '〈〉' | sort -n | tail -1)"

printf '%s' "$payload" | BASE="$BASE" BASE_SRC="$BASE_SRC" LEDGER="$TOP/dev-package/PLAN-SoT.md" \
python3 -c '
import json,os,re,sys

# 정본 = gates/tools/work_item_consistency.py:136 과 **같은 정규식**. 두 벌로 두면 언젠가 갈린다.
ROW = re.compile(r"^\|\s*〈\s*(\d+)\s*〉\s*\|", re.M)

try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
ti = d.get("tool_input") or {}
new = ti.get("new_string")
if new is None: new = ti.get("content")
if not isinstance(new, str) or not new: sys.exit(0)

ledger = os.environ["LEDGER"]
try:
    cur = open(ledger, encoding="utf-8").read()
except Exception:
    cur = ""
existing = {int(m) for m in ROW.findall(cur)}
incoming = [int(m) for m in ROW.findall(new)]
fresh = sorted({n for n in incoming if n not in existing})
if not fresh: sys.exit(0)

# 새 결정 번호 후보가 있는데 기준을 못 읽었다 — 판정할 수 없으므로 준비 실패로 막는다.
if not os.environ.get("BASE", "").isdigit():
    sys.stderr.write(
        "hook readiness failure(H5 decision-number-guard): %s 부재 — 새 결정 번호 %s 을(를) 대조할 기준이 없다"
        " · `git fetch origin develop` 뒤 재시도한다. 훅을 비활성화하지 않는다.\n"
        % (os.environ["BASE_SRC"], ", ".join("〈%d〉" % n for n in fresh)))
    sys.exit(2)
base = int(os.environ["BASE"])

# 이 브랜치가 이미 쓴 번호는 건너뛴 다음 자리가 기대값이다.
nxt = base + 1
while nxt in existing: nxt += 1
want = list(range(nxt, nxt + len(fresh)))
if fresh == want: sys.exit(0)

got = ", ".join("〈%d〉" % n for n in fresh)
exp = ", ".join("〈%d〉" % n for n in want)
sys.stderr.write(
    "⛔ 차단(H5 decision-number-guard) — 새 결정 번호 %s 은(는) 기대값 %s 과 다르다"
    " (기준 %s 최대 〈%d〉 + 1 · 번호는 예약하지 않고 병합 직전 재실측한다)"
    " · 승인된 번호 발급 절차로 돌아가며 훅을 비활성화하지 않는다.\n"
    % (got, exp, os.environ["BASE_SRC"], base))
sys.exit(2)
'
rc=$?
[ "$rc" -eq 2 ] && exit 2
exit 0
