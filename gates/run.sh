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
  event-lint)
    # 이벤트 계약(contracts/events/**) — ajv 로 스키마 유효성 + 인스턴스 픽스처 검증.
    # contract-lint(spectral)는 seams 만, contract-breaking(oasdiff)은 OpenAPI 만 본다.
    # 이 게이트가 없으면 이벤트 계약은 아무도 보지 않는 사각지대다 (WU-D2b).
    exec "$REPO_ROOT/gates/tools/event-lint.sh"
    ;;
  event-breaking)
    # 이벤트 계약의 $defs 단위 파괴적 변경 검출 (기준=git HEAD 판 · 대상=워킹트리 판).
    # 파괴의 정의(규칙표) = dev-package/sessions/D2b.md §2.
    exec "$REPO_ROOT/gates/tools/event-breaking.sh"
    ;;
  event-selftest)
    # 위 두 게이트가 red fixture로 fail-closed임을 증명한다.
    exec "$REPO_ROOT/gates/tools/event-selftest.sh"
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
  migration-single-head)
    # alembic head 분기 검출 — db/platform · db/ai 두 체인 각각 (CLAUDE.md §3-3).
    # DB 접속 없이 down_revision 그래프를 직접 판정한다. 마이그레이션 0건은 red.
    exec python3 "$REPO_ROOT/gates/tools/migration_single_head.py"
    ;;
  schema-diff)
    # 선언 스키마(db/<체인>/schema.sql) ↔ 적용 DB 드리프트.
    # DB 가 필요한 검사다. DB 가 없으면 skip 이 아니라 red — 그 skip 이 v1 의 실패였다.
    exec "$REPO_ROOT/gates/tools/schema-diff.sh"
    ;;
  rls-coverage)
    # allow-list 밖 테이블의 RLS 누락 검출 (CLAUDE.md §3-5 · PLAN-SoT §9-㉖).
    # allow-list 정본 = gates/config/rls-allowlist.toml 하나뿐.
    exec "$REPO_ROOT/gates/tools/rls-coverage.sh"
    ;;
  rls-effect)
    # RLS 가 **실제로 막는지** — 오라클 3종 (WORK-UNITS D3b).
    # rls-coverage 가 「정책이 걸려 있는가」를 보는 자리라면, 여기는 「행이 안 보이는가」를 본다.
    # NOBYPASSRLS · 비소유자 롤로 붙는다. 우회 롤로 돌면 red — 거짓 green 을 만들 여지를 두지 않는다.
    exec "$REPO_ROOT/gates/tools/rls-effect.sh"
    ;;
  rls-effect-selftest)
    # 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — 보호 장치를 실제로 떼어 본다.
    exec "$REPO_ROOT/gates/tools/rls-effect-selftest.sh"
    ;;
  db-selftest)
    # 위 세 게이트가 red fixture 로 fail-closed 임을 증명한다.
    exec "$REPO_ROOT/gates/tools/db-selftest.sh"
    ;;
  seam-consistency)
    # seam ↔ 이벤트 계약의 **사이**를 본다 (WU-D2c §2-13 · 〈61〉-㉠·㉡).
    # contract-* 는 seams 만, event-* 는 events 만 봐서 DR-7(위임 산문 오배정)이 살아남았다.
    # 검사 4종: G-e 산문 위임 참조 · G-b source const 능력 주장 · ㉠ 정본 근거 대조 · ㉡ E-04 흐름 완주.
    exec "$REPO_ROOT/gates/tools/seam-consistency.sh"
    ;;
  seam-consistency-selftest)
    # 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — 개정 전 위임 산문 원문(DR-7 실물) 포함.
    exec "$REPO_ROOT/gates/tools/seam-consistency-selftest.sh"
    ;;
  selftest)
    # 증명 셋을 한 번에. 하나라도 red 면 red.
    rc=0
    for s in contract-selftest event-selftest boundary-selftest db-selftest rls-effect-selftest seam-consistency-selftest; do
      echo "══ $s ══════════════════════════════════════════════"
      "$REPO_ROOT/gates/run.sh" "$s" || rc=1
    done
    exit $rc
    ;;
  generated-up-to-date)
    echo "::error::게이트 '$GATE' 미구현 — 후속 WU에서 구현한다. 미구현은 red다."
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
