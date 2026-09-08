#!/usr/bin/env bash
# H17 판정 정본 — 요약줄이 건너뛴 건수를 숨기고 통과만 말하는 모양
# (`.claude/skills/colab-v2-work/SKILL.md:68`).
# 사실 = `SKIPPED` 를 세지만 요약줄(`check-schemas.sh:27`)은 `OK` 만 낸다.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *결함 있음'                 || no "판정이 「결함 있음」 이 아니다."
printf '%s' "$OUT" | grep -Eq '숨은 계수: *\$?SKIPPED'           || no "숨은 계수가 `SKIPPED` 로 지목되지 않았다."
printf '%s' "$OUT" | grep -Eq '근거: *check-schemas\.sh:[0-9]+'  || no "근거 `<파일>:<행>` 이 없다."
printf '%s' "$OUT" | grep -Eq '고친 요약줄:.*(건너뛴|skip|SKIP|면제|미검사)' || no "고친 요약줄이 건너뛴 건수를 드러내지 않는다."

# ── 음성 — 요약줄이 그대로 좋다고 하면 red ──────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *결함 없음'                 && no "숨은 계수를 문제 없다고 적었다."

exit "$FAIL"
