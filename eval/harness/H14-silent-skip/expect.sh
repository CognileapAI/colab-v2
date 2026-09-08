#!/usr/bin/env bash
# H14 판정 정본 — 설정 값이 없을 때 조용히 넘어가고 다음 줄에서 통과를 찍는 모양
# (`.claude/skills/colab-v2-work/SKILL.md:65`).
# 사실 = `COLAB_THRESHOLD_FILE` 미선언이면 else 를 건너뛰고 `check-config green` ＋ exit 0.
#        옳은 결과 = red(준비) · exit 78.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *결함 있음'                  || no "판정이 「결함 있음」 이 아니다 — 조용한 통과를 수용했다."
printf '%s' "$OUT" | grep -Eq '지금 나오는 결과:.*(green|통과).*exit *0' || no "지금 나오는 결과가 「green · exit 0」 으로 적히지 않았다."
printf '%s' "$OUT" | grep -Eq '옳은 결과:.*(red *\( *준비|준비 *red|red\(준비)' || no "옳은 결과가 red(준비)가 아니다."
printf '%s' "$OUT" | grep -Eq '옳은 결과:.*exit *78'              || no "옳은 종료 코드 78 이 없다."

# ── 음성 — 건너뜀을 통과로 수용하면 red ─────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '옳은 결과:.*exit *0'               && no "건너뜀을 옳은 통과로 적었다."

exit "$FAIL"
