#!/usr/bin/env bash
# H09 판정 정본 — 보더 두 층이 같은 토큰인 것을 두 줄로 지목하는가.
# 사실 = `detail.css:59`(컨테이너 `border: 1px solid var(--color-border)`)
#        와 `detail.css:62`(칸 구분선 `border-right: 1px solid var(--color-border)`)가 같은 토큰이다.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *있음'          || no "판정이 「있음」 이 아니다."
printf '%s' "$OUT" | grep -Eq 'detail\.css:59'       || no "컨테이너 선 `detail.css:59` 를 지목하지 않았다."
printf '%s' "$OUT" | grep -Eq 'detail\.css:62'       || no "칸 구분선 `detail.css:62` 를 지목하지 않았다."
printf '%s' "$OUT" | grep -Eq '\-\-color-border'     || no "토큰 이름(`--color-border`)이 없다."

# ── 음성 — 두 선이 서로 다른 토큰이라고 적으면 red ──────────────────────────
printf '%s' "$OUT" | grep -Eq '토큰:.*--color-border-strong *\/ *var\(--color-border\)' && no "토큰이 서로 다르다고 적었다 — 둘 다 `--color-border` 다."

exit "$FAIL"
