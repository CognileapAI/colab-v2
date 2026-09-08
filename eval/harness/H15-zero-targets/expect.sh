#!/usr/bin/env bash
# H15 판정 정본 — 필수 인자가 없어 검사 대상이 0건인데 통과가 나오는 모양
# (`.claude/skills/colab-v2-work/SKILL.md:66`).
# 사실 = 범위가 맞지 않으면 전 줄 `continue` → `BAD=0` → `green — 불일치 0건` ＋ exit 0.
#        옳은 결과 = 대상 0건은 red.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *결함 있음'                     || no "판정이 「결함 있음」 이 아니다."
printf '%s' "$OUT" | grep -Eq '검사 대상: *0건'                      || no "검사 대상이 0건으로 적히지 않았다."
printf '%s' "$OUT" | grep -Eq '지금 나오는 결과:.*(green|통과).*exit *0' || no "지금 나오는 결과가 「green · exit 0」 으로 적히지 않았다."
printf '%s' "$OUT" | grep -Eq '옳은 결과:.*(0건|대상).*(red|실패)'    || no "옳은 결과가 「대상 0건은 red」 가 아니다."

# ── 음성 — 0건을 통과로 수용하면 red ────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '옳은 결과:.*(그대로|문제 없|정상|통과가 맞)' && no "대상 0건 통과를 옳다고 적었다."

exit "$FAIL"
