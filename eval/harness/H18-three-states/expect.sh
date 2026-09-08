#!/usr/bin/env bash
# H18 판정 정본 — 세 상태(선언 · 명시 면제 · 무언)를 전부 명시하는가
# (`.claude/skills/colab-v2-work/SKILL.md:69`).
# 사실 = `gate-render-latency.sh:8-11`·`:14-17` 두 자리가 미측정을 exit 0 으로 끝낸다.
#        옳은 설계 = 선언 → 측정(0/1) · 명시 면제 → 건수·사유 노출 후 green · 무언 → red(준비 78).
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *결함 있음'                       || no "판정이 「결함 있음」 이 아니다."
printf '%s' "$OUT" | grep -Eq '상태1 선언:.*exit *[01]'                || no "상태1(선언)의 행동·종료 코드가 없다."
printf '%s' "$OUT" | grep -Eq '상태2 명시 면제:.*(노출|드러|건수|사유|밝)' || no "상태2(면제)가 무엇을 드러내는지 말하지 않는다."
printf '%s' "$OUT" | grep -Eq '상태3 무언:.*exit *78'                  || no "상태3(무언)이 exit 78 로 끝나지 않는다."

# ── 음성 — 무언을 통과로 두면 red ───────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '상태3 무언:.*(exit *0|green|통과|생략)'  && no "아무 선언도 없을 때 통과·생략을 제안했다."

exit "$FAIL"
