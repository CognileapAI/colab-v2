#!/usr/bin/env bash
# PLAN-SoT §9 의 현재 최대 결정 번호 〈N〉 을 잰다.
#
# 왜 이 스크립트인가 — `PLAN-SoT.md` 는 1.17 MB 다. 개발 세션이 번호 하나를 알려고
# 통째로 읽으면 세션이 그 자리에서 무거워진다. 이 한 줄만 돈다.
#
# 규율 — 번호를 **예약하지 않는다.** 병합 직전 `origin/main` 기준으로 다시 재고,
# 그 시점의 최대 + 1 이 이번 회차의 번호다. 착수 시점 값은 참고값이다.
#   2026-09-05 실측 최대 = 〈326〉 (커밋 370ed99 · ed8ceb3 에 실려 있다)
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
grep -o '〈[0-9]\+〉' "$REPO_ROOT/dev-package/PLAN-SoT.md" | tr -d '〈〉' | sort -n | tail -1
