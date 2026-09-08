#!/usr/bin/env bash
# H06 판정 정본 — 카드 그림자를 지목하면서 팝오버 예외를 함께 유지하는가.
# 사실 = `catalog.css:31` `.catalog-page .card { … box-shadow: var(--shadow-sm) … }` · 예외 `catalog.css:80` `.colmenu`.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *있음'            || no "판정이 「있음」 이 아니다 — 카드 그림자를 놓쳤다."
printf '%s' "$OUT" | grep -Eq 'catalog\.css:31'        || no "근거가 `catalog.css:31` 이 아니다."
printf '%s' "$OUT" | grep -Eq '유지할 예외:.*colmenu'  || no "팝오버 예외 `.colmenu` 를 유지 대상으로 적지 않았다."

# ── 음성 — 팝오버까지 제거 대상으로 지목하면 red ────────────────────────────
printf '%s' "$OUT" | grep -Eq '근거:.*colmenu'         && no "예외인 팝오버를 제거 대상 근거로 지목했다."

exit "$FAIL"
