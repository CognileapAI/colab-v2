#!/usr/bin/env bash
# H10 판정 정본 — 음수 상쇄 2건을 줄까지 지목하는가.
# 사실 = `detail.css:93` `margin: -12px 0 …` · `shell.css:58` `margin-left: -7px` = **2건**.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *있음'          || no "판정이 「있음」 이 아니다."
printf '%s' "$OUT" | grep -Eq '음수 상쇄: *2건'      || no "음수 상쇄 계수가 2건이 아니다."
printf '%s' "$OUT" | grep -Eq 'detail\.css:93'       || no "`detail.css:93` 을 지목하지 않았다."
printf '%s' "$OUT" | grep -Eq 'shell\.css:58'        || no "`shell.css:58` 을 지목하지 않았다."

# ── 음성 — 한 파일만 보고 1건으로 끝내면 red ────────────────────────────────
printf '%s' "$OUT" | grep -Eq '음수 상쇄: *(0|1)건'  && no "한 파일만 훑고 계수를 냈다(형제 미탐색)."

exit "$FAIL"
