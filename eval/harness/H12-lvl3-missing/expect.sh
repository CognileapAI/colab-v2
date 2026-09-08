#!/usr/bin/env bash
# H12 판정 정본 — TSX 가 내는 클래스와 CSS 규칙 집합을 대조해 **빠진 한 단**을 잡는가.
# 사실 = `CatalogTable.tsx:162` 가 `lvl-${displayLevel(row)}` 를 낸다(0~3).
#        픽스처 `catalog.css` 에는 `.lvl-0`·`.lvl-1`·`.lvl-2` 만 있고 `.lvl-3` 규칙이 없다.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *있음'            || no "판정이 「있음」 이 아니다 — 빠진 규칙을 놓쳤다."
printf '%s' "$OUT" | grep -Eq '빠진 규칙:.*\.?lvl-3'   || no "빠진 규칙이 `.lvl-3` 이 아니다."
printf '%s' "$OUT" | grep -Eq '증상:.*(무색|색이 (없|안)|배경.*없|칩이 비|기본|스타일이 (없|안))' \
                                                       || no "증상 줄이 「색 없이 그려진다」를 말하지 않는다."

# ── 음성 — 이미 있는 규칙을 빠졌다고 하면 red ───────────────────────────────
printf '%s' "$OUT" | grep -Eq '빠진 규칙:.*\.?lvl-(0|1|2)( |$|[^0-9])' && no "실재하는 `.lvl-0`~`.lvl-2` 를 빠졌다고 적었다."

exit "$FAIL"
