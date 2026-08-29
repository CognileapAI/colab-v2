#!/usr/bin/env bash
# 게이트 실행기 — WU-D3에서 실제 검사를 채운다.
#
# 원칙: 미구현 게이트는 red다. 조용히 green이 되는 게이트는 게이트가 아니며,
#       v1에서 CI가 DB 없이 돌아 RLS 테스트를 green-by-skip 했던 실패를 반복하지 않는다.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATE="${1:-}"

# 전 게이트 목록 — `all` 이 도는 대상이다. 여기서 빠진 게이트는 `all` 이 보지 않는다.
ALL_GATES=(
  planning-freshness contract-lint contract-breaking event-lint event-breaking
  seam-consistency generated-up-to-date import-boundary banned-import
  ai-no-lineage-write db-boundary migration-single-head schema-diff
  rls-coverage rls-effect work-item-consistency stage2-markers autometa-loss
  contract-selftest event-selftest boundary-selftest db-boundary-selftest
  db-selftest rls-effect-selftest seam-consistency-selftest
  generated-selftest work-item-selftest stage2-markers-selftest
  autometa-loss-selftest
)

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
  db-boundary)
    # 배포 단위별 DB 체인 경계 (CLAUDE.md §3-1 · §3-3). 정본 = gates/config/db-boundaries.toml.
    # import-boundary 가 못 보는 계열 — 횡단이 import 가 아니라 **DB 접속**일 때.
    # 2026-08-25 에 ai-service 가 COLAB_AI_CATALOG_DB_URL 로 D3 에 직접 붙었고 전 게이트가 green 이었다.
    exec python3 "$REPO_ROOT/gates/tools/db_boundary.py"
    ;;
  db-boundary-selftest)
    # 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — 위 위반의 실물 재현 포함.
    exec "$REPO_ROOT/gates/tools/db-boundary-selftest.sh"
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
  stage2-markers)
    # 휴면(`stage2` 대기) 모듈의 시험이 **CI 에서 계속 도는지** (〈71〉-㉰).
    # 수집 0 건 · skipped · failed 는 전부 red — 「안 돌리면 휴면은 부식」.
    exec "$REPO_ROOT/gates/tools/stage2-markers.sh"
    ;;
  autometa-loss)
    # 사건이 발행되고도 장부에 반영되지 않았는가 (`〈190〉-㉱`). **대상 0건도 red 다.**
    # 적용 DB 가 없으면 red — schema-diff 와 같은 규율이다(환경 부재를 skip 으로 세지 않는다).
    exec "$REPO_ROOT/gates/tools/autometa-loss.sh"
    ;;
  autometa-loss-selftest)
    # 위 게이트가 red fixture 로 fail-closed 임을 증명한다 — 유실·대상 0건·환경 부재 셋 다.
    exec "$REPO_ROOT/gates/tools/autometa-loss-selftest.sh"
    ;;
  stage2-markers-selftest)
    # 위 게이트가 red fixture 로 fail-closed 임을 증명한다 (0 건 · skip · fail).
    exec "$REPO_ROOT/gates/tools/stage2-markers-selftest.sh"
    ;;
  selftest)
    # 증명 셋을 한 번에. 하나라도 red 면 red.
    # stage2-markers-selftest 는 여기 없다 — pipeline-worker 런타임 의존(rasterio 등)이 필요해
    # contract-gates 잡의 환경으로는 못 돈다. CI 는 dormant-tests 잡에서 따로 부른다.
    rc=0
    for s in contract-selftest event-selftest boundary-selftest db-boundary-selftest db-selftest rls-effect-selftest seam-consistency-selftest generated-selftest work-item-selftest; do
      echo "══ $s ══════════════════════════════════════════════"
      "$REPO_ROOT/gates/run.sh" "$s" || rc=1
    done
    exit $rc
    ;;
  work-item-consistency)
    # 개발 항목 상태의 **대장 ↔ 산문** 불일치 (Ted 판정 2026-08-28).
    # 정본 = dev-package/work-items.yaml. 상태가 산문 세 곳에 흩어져 사람 기억으로
    # 동기화되던 것을 기계가 받는다 — 「관례를 두지 않는다」의 마지막 사각지대였다.
    # 검사 6종: 스키마 · 완주 체크리스트 · 진실원 표 · 보류 항목 혼입 · 기한 경과 · conflict 잔존.
    exec python3 "$REPO_ROOT/gates/tools/work_item_consistency.py"
    ;;
  work-item-selftest)
    # 위 게이트가 red fixture 로 fail-closed 임을 증명한다 (검사 6종 각각 + 정상 대장 대조군).
    exec "$REPO_ROOT/gates/tools/work-item-selftest.sh"
    ;;
  generated-up-to-date)
    # 생성물 등기부(contracts/codegen/manifest.toml)의 엔트리를 실제로 재생성해 커밋본과 diff.
    # 등기부 밖의 「generated」 마커 파일도 red — codegen 통제 밖 자칭 생성물은 드리프트 발원지다.
    # 빈 등기부·등기부 부재·재생성 실패는 전부 red (CLAUDE.md §4 green-by-skip 금지).
    exec "$REPO_ROOT/gates/tools/generated-up-to-date.sh"
    ;;
  generated-selftest)
    # 위 게이트가 red fixture 로 fail-closed 임을 증명한다 (stale·손수정·부재·빈 등기부·미등기 마커).
    exec "$REPO_ROOT/gates/tools/generated-selftest.sh"
    ;;
  all)
    # 전 게이트를 병렬로 돈다. **검사 내용은 하나도 바뀌지 않는다** — 순서만 바뀌고,
    # 출력은 목록 순서로 되돌려 재생한다. 하나라도 red 면 red 다.
    ncpu="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)"
    jobs_n=2
    if [ "${2:-}" = "-j" ]; then jobs_n="${3:-2}"; fi
    [ "$jobs_n" -ge 1 ] 2>/dev/null || jobs_n=1
    # 안쪽 selftest 풀의 몫을 나눠 준다 — 바깥 병렬과 곱해져 코어를 넘기지 않게.
    inner=$(( ncpu / jobs_n )); [ "$inner" -ge 1 ] || inner=1
    outdir="$(mktemp -d -p "${TMPDIR:-/tmp}" gates-all-XXXXXX)"
    for g in "${ALL_GATES[@]}"; do
      while [ "$(jobs -rp | wc -l)" -ge "$jobs_n" ]; do wait -n 2>/dev/null || break; done
      # set -e 아래서 자식의 red 가 이 서브셸을 먼저 죽이면 종료코드를 못 적는다.
      # 종료코드 없는 게이트는 「미실행」으로 red 가 되므로, 반드시 받아 적는다.
      { if COLAB_GATE_JOBS="$inner" "$REPO_ROOT/gates/run.sh" "$g" >"$outdir/$g.out" 2>&1
        then echo 0 > "$outdir/$g.rc"; else echo $? > "$outdir/$g.rc"; fi; } &
    done
    wait
    rc=0
    for g in "${ALL_GATES[@]}"; do
      grc="$(cat "$outdir/$g.rc" 2>/dev/null || echo 111)"
      echo "══ $g (exit $grc) ═════════════════════════════════════════"
      cat "$outdir/$g.out"
      [ "$grc" -eq 0 ] 2>/dev/null || rc=1
    done
    echo "── 요약 ────────────────────────────────────────────────────"
    for g in "${ALL_GATES[@]}"; do
      grc="$(cat "$outdir/$g.rc" 2>/dev/null || echo 111)"
      if [ "$grc" -eq 0 ] 2>/dev/null; then echo "  green  $g"
      elif [ "$grc" = 111 ]; then echo "  red    $g (미실행 — 종료코드 없음)"
      else echo "  red    $g (exit $grc)"; fi
    done
    rm -rf "$outdir"
    exit $rc
    ;;
  "")
    echo "usage: gates/run.sh <gate> | gates/run.sh all [-j N]" >&2
    exit 2
    ;;
  *)
    echo "::error::알 수 없는 게이트 '$GATE'"
    exit 2
    ;;
esac
