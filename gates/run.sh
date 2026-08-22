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
  contract-lint)
    # seam OpenAPI 린트 (spectral, 룰셋 contracts/.spectral.yaml).
    # 도구 부재·네트워크 실패·대상 0건은 전부 red다 (CLAUDE.md §4 green-by-skip 금지).
    exec "$REPO_ROOT/gates/tools/contract-lint.sh"
    ;;
  contract-breaking)
    # seam 계약의 파괴적 변경 검출 (oasdiff, 기준=git HEAD 판 · 대상=워킹트리 판).
    exec "$REPO_ROOT/gates/tools/contract-breaking.sh"
    ;;
  contract-selftest)
    # 위 두 게이트가 red fixture로 fail-closed임을 증명한다.
    exec "$REPO_ROOT/gates/tools/contract-selftest.sh"
    ;;
  import-boundary)
    # 도메인 간 직접 참조 금지 (import-linter, 계약=gates/config/importlinter.ini).
    # 코드가 없으면 red — 대상 0건인 경계 게이트는 통과가 아니다.
    exec "$REPO_ROOT/gates/tools/import-boundary.sh"
    ;;
  banned-import)
    # 배포 단위별 import allow/deny. 금지 목록 정본 = gates/config/boundaries.toml.
    exec python3 "$REPO_ROOT/gates/tools/banned-import.py"
    ;;
  ai-no-lineage-write)
    # 음성 게이트 — D10 → D4 쓰기 경로가 계약·코드·마이그레이션 어디에도 없음을 증명한다.
    exec "$REPO_ROOT/gates/tools/ai-no-lineage-write.sh"
    ;;
  boundary-selftest)
    # 위 세 게이트가 red fixture로 fail-closed임을 증명한다.
    exec "$REPO_ROOT/gates/tools/boundary-selftest.sh"
    ;;
  generated-up-to-date|\
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
