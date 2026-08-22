#!/usr/bin/env bash
# 게이트 실행기 — WU-D3에서 실제 검사를 채운다.
#
# 원칙: 미구현 게이트는 red다. 조용히 green이 되는 게이트는 게이트가 아니며,
#       v1에서 CI가 DB 없이 돌아 RLS 테스트를 green-by-skip 했던 실패를 반복하지 않는다.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATE="${1:-}"

case "$GATE" in
  planning-freshness)
    # 기획 정본 패키지 HTML의 임베드 md ↔ 원본 md 일치 검사.
    # 정본이 마운트되지 않으면 skip이 아니라 red다 (CLAUDE.md §4 green-by-skip 금지).
    exec python3 "$REPO_ROOT/dev-package/tools/check-package-freshness.py"
    ;;
  contract-lint|contract-breaking|generated-up-to-date|\
  import-boundary|banned-import|ai-no-lineage-write|\
  migration-single-head|schema-diff|rls-coverage|selftest)
    echo "::error::게이트 '$GATE' 미구현 — WU-D3에서 구현한다. 미구현은 red다."
    exit 1
    ;;
  "")
    echo "usage: gates/run.sh <gate>" >&2
    exit 2
    ;;
  *)
    echo "::error::알 수 없는 게이트 '$GATE'"
    exit 2
    ;;
esac
