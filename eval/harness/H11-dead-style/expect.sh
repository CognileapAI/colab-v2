#!/usr/bin/env bash
# H11 판정 정본 — 덮인 선언 한 쌍과 미정의 토큰 참조 11건을 세는가.
# 사실 = `lineageGraph.css:33` `display:inline-block` 이 `:29` `display:inline-flex` 를 덮는다.
#        미정의 토큰 참조 **11건** — `:30`(accent-50·accent-200) `:31`(accent-700) `:48` `:49`(gray-300)
#        `:51`(primary-800) `:57`(primary-200·primary-800) `:83`(accent-700·accent-50) `:84`(--color-ai).
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq 'lineageGraph\.css:33'          || no "덮는 선언 `lineageGraph.css:33` 이 없다."
printf '%s' "$OUT" | grep -Eq 'lineageGraph\.css:29'          || no "덮인 선언 `lineageGraph.css:29` 가 없다."
printf '%s' "$OUT" | grep -Eq '미정의 토큰 참조: *11건'        || no "미정의 토큰 참조 계수가 11건이 아니다."

# ── 음성 — 참조가 아니라 토큰 이름 가짓수(8)를 적으면 red ───────────────────
printf '%s' "$OUT" | grep -Eq '미정의 토큰 참조: *(6|7|8|9|10)건' && no "참조 건수가 아니라 토큰 가짓수를 셌다."

exit "$FAIL"
