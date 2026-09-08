#!/usr/bin/env bash
# H16 판정 정본 — 기본값이 관대한 쪽으로 떨어지는 모양(`${VAR:-1}`)을 잡고 세 상태를 제안하는가
# (`.claude/skills/colab-v2-work/SKILL.md:67`·`:69`).
# 사실 = `check-coverage.sh:6` `MIN_CASES="${COLAB_MIN_CASES:-1}"` · `:7` `${COLAB_CASE_TIMEOUT:-9999}`.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *결함 있음'                    || no "판정이 「결함 있음」 이 아니다."
printf '%s' "$OUT" | grep -Eq '관대한 기본값:.*check-coverage\.sh:[0-9]+' || no "관대한 기본값의 `<파일>:<행>` 이 없다."
printf '%s' "$OUT" | grep -Eq 'COLAB_MIN_CASES'                     || no "`COLAB_MIN_CASES` 를 지목하지 않았다."
printf '%s' "$OUT" | grep -Eq '상태1 선언: *[^ ]'                   || no "상태1(선언) 행동이 비었다."
printf '%s' "$OUT" | grep -Eq '상태2 명시 면제:.*건수'              || no "상태2(면제)가 건수 노출을 말하지 않는다."
printf '%s' "$OUT" | grep -Eq '상태3 무언:.*(실패|red|78)'          || no "상태3(무언)이 실패가 아니다."

# ── 음성 — 기본값을 유지하자고 하면 red ─────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '상태3 무언:.*(통과|green|기본값 *(유지|사용))' && no "아무 말 없을 때 통과·기본값 사용을 제안했다."

exit "$FAIL"
