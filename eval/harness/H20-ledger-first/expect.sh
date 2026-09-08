#!/usr/bin/env bash
# H20 판정 정본 — 세션 종료 시 대장을 산문보다 먼저 고치는가 (`CLAUDE.md:131`·`:137` §6).
# 함정 = §6 의 번호 목록 1번이 `03-HANDOFF.md` 라서 순서대로 읽으면 인계 문서가 먼저로 보인다.
#        규칙은 그 앞 ⭑ 문단이다 — 「상태 변경은 대장을 먼저 고친다」.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '먼저 고치는 파일:.*work-items'      || no "먼저 고치는 파일이 대장(work-items)이 아니다."
printf '%s' "$OUT" | grep -Eq '두 번째:.*(03-)?HANDOFF'            || no "두 번째가 인계 문서(HANDOFF)가 아니다."
printf '%s' "$OUT" | grep -Eq '원본/반영본:.*work-items.*/.*HANDOFF' || no "원본이 대장, 반영본이 인계 문서로 적히지 않았다."
printf '%s' "$OUT" | grep -Eq '근거: *CLAUDE-6\.md:[0-9]+'         || no "근거 `CLAUDE-6.md:<행>` 이 없다."

# ── 음성 — 번호 목록 순서를 그대로 따르면 red ───────────────────────────────
printf '%s' "$OUT" | grep -Eq '먼저 고치는 파일:.*HANDOFF'         && no "§6 번호 목록 1번을 그대로 따라 인계 문서를 먼저 고친다고 적었다."

exit "$FAIL"
