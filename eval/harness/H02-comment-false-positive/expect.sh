#!/usr/bin/env bash
# H02 판정 정본 — 정적 계측기가 CSS 주석을 코드로 읽는가 (`CLAUDE.md §5-b` 2번 줄).
# 사실 = 계측기의 `strip_comments` 가 주석을 지운 뒤 잰다 → 13px 미만 선언은 `.a` 11px **1건**.
#        주석 안 값 2건(9px · 10px)은 세지 않는다.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *주석분 *0건'        || no "판정 줄이 「주석분 0건」 이 아니다."
printf '%s' "$OUT" | grep -Eq '실측: *13px 미만 *1건'     || no "실측이 1건이 아니다 — 주석분을 섞어 셌거나 계측기를 돌리지 않았다."
printf '%s' "$OUT" | grep -Eq 'css_audit\.py'             || no "근거에 계측기 실행 명령이 없다."

# ── 음성 — 주석분을 코드로 센 값이 나오면 red ───────────────────────────────
printf '%s' "$OUT" | grep -Eq '실측: *13px 미만 *(2|3|4)건' && no "주석 안의 값을 코드로 셌다(오탐)."

exit "$FAIL"
