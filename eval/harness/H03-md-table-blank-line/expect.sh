#!/usr/bin/env bash
# H03 판정 정본 — 표 사이에 낀 빈 줄로 행이 표 밖으로 떨어진 것을 잡는가
# (`CLAUDE.md §5-b` 3번 줄 · `VENDORED.md` 2회).
# 사실 = 빈 줄은 13행. 그 뒤 14·15행 두 줄이 표 밖으로 떨어진다 → 2건.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *있음'                      || no "판정이 「있음」 이 아니다 — 깨진 표를 성한 것으로 읽었다."
printf '%s' "$OUT" | grep -Eq '빈 줄: *(행 *)?13(행|줄)?( |$|[^0-9])' || no "빈 줄 위치가 13행이 아니다."
printf '%s' "$OUT" | grep -Eq '표 밖으로 떨어진 행: *2건'         || no "떨어진 행 계수가 2건이 아니다."
printf '%s' "$OUT" | grep -Eq '확인 명령:.*(sed -n|cat -n|grep -n|rg -n|awk|Get-Content.*ForEach-Object.*\$[[:alnum:]_]+\+\+.*-f)' || no "행이 붙어 있는지 보는 확인 명령이 없다."

# ── 음성 — 빈 줄 앞 행까지 떨어졌다고 세면 red ──────────────────────────────
printf '%s' "$OUT" | grep -Eq '표 밖으로 떨어진 행: *(0|1|3|4|5)건' && no "떨어진 행을 잘못 셌다(빈 줄 앞뒤를 가르지 못했다)."

exit "$FAIL"
