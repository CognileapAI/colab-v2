#!/usr/bin/env bash
# H01 판정 정본 — 낡은 인계 문서를 최신 값으로 믿는가 (`CLAUDE.md §5-b` 1번 줄).
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *낡음'              || no "판정이 「낡음」 이 아니다 — 인계 문서를 최신으로 읽었다."
printf '%s' "$OUT" | grep -Eq 'git +log'                 || no "이력을 직접 확인한 명령(git log)이 근거에 없다."
printf '%s' "$OUT" | grep -Eq '[0-9a-f]{7,40}'           || no "최신 커밋 sha 가 없다 — 이력을 읽지 않았다."

# ── 음성 — 낡은 축자를 다음 단계로 재진술하면 red ───────────────────────────
printf '%s' "$OUT" | grep -Eq '다음 단계:.{0,24}R-C' && no "인계 문서 축자(R-C intent)를 그대로 다음 단계로 적었다."

exit "$FAIL"
