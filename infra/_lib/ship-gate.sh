#!/usr/bin/env bash
# 환경별 반입 게이트 — dev=develop, prod=product.
#
# 왜 여기 있나 — 종전에는 이 본문이 `infra/dev/ship.sh` **안에만** 있었다. prod 를 세우면서
# 같은 것을 한 벌 더 두면 한쪽만 고쳐져 갈린다(문구·종료코드·`MAIN_SHA` 형식). 형식이 갈리면
# `deploy_doctor` ⑮ 가 「형식 불일치」로 ✗ 를 낸다 — 그 ✗ 의 원인이 복사본인 것이
# 제일 찾기 어렵다. ⟹ **게이트 본문은 한 벌이고 dev·prod 가 그것을 부른다.**
#
# 부르는 쪽 = `infra/dev/ship.sh` · `infra/prod/ship.sh` (`. "$REPO/infra/_lib/ship-gate.sh"`).
# 끝나는 자리는 셋뿐이다 — 통과 · 거절(**65**) · 준비 실패(**78**). 조용한 경로는 없다.
# 시험 = `infra/dev/tests/ship-gate.sh` · `infra/prod/tests/ship-gate.sh`
#        ＋ `services/core-api/tests/test_deploy_doctor.py` 의 생산자·소비자 대조.

# ── ship_gate_source_ancestor <저장소> <후보 sha> <환경> ─────────────────────
#: 후보가 환경별 원천 ref의 조상인지 본다. 통과하면 세 값을 채운다 —
#:   SHIP_GATE_SOURCE_REF = develop | product
#:   SHIP_GATE_SOURCE_SHA = 원천 ref의 12자리
#:   SHIP_GATE_ANCESTOR  = yes (거부는 비영 종료)
#: 과거 `COLAB_SHIP_ALLOW_NONMAIN`은 새 원천 정책의 우회로 해석하지 않는다.
ship_gate_source_ancestor() {
  local repo="$1" sha="$2" environment="$3" source_ref
  case "$environment" in
    dev) source_ref=develop ;;
    prod) source_ref=product ;;
    *) echo "알 수 없는 배포 환경: $environment" >&2; exit 64 ;;
  esac
  git -C "$repo" fetch -q origin "+refs/heads/$source_ref:refs/remotes/origin/$source_ref" \
    || { echo "origin 조회 실패 — 진행 금지" >&2; exit 78; }
  SHIP_GATE_SOURCE_REF="$source_ref"
  SHIP_GATE_SOURCE_SHA="$(git -C "$repo" rev-parse --short=12 "origin/$source_ref")"
  if git -C "$repo" merge-base --is-ancestor "$sha" "origin/$source_ref"; then
    SHIP_GATE_ANCESTOR=yes
  else
    echo "sha 가 origin/$source_ref 조상이 아니다: $sha" >&2
    exit 65
  fi
}

# ── ship_gate_require_prod_tag <저장소> <후보 sha> ────────────────────────────
#: **prod 전용 · 우회 변수가 없다.** 규칙 6 — prod 는 `prod-YYYYMMDD` 태그에서만 배포한다
#: (`docs/BRANCHING.md` §1 규칙 6 · 승인된 사람 병합 후보의 prod 태그).
#: 검사 대상은 **반입 후보 sha** 다 — 통상 그것이 `HEAD` 지만 후보는 `dist/colab-v2-prod.sha`
#: 가 정하므로, `HEAD` 가 그 뒤로 움직인 날에도 실제로 실리는 커밋을 본다.
#: 통과하면 SHIP_GATE_PROD_TAG 에 첫 태그 이름을 채운다.
ship_gate_require_prod_tag() {
  local repo="$1" sha="$2" tags
  tags="$(git -C "$repo" tag --points-at "$sha" 'prod-*')" \
    || { echo "태그 조회 실패 — 진행 금지" >&2; exit 78; }
  if [ -z "$tags" ]; then
    echo "prod 태그가 없다: $sha — prod 는 \`prod-YYYYMMDD\` 태그에서만 배포한다" >&2
    echo "  (docs/BRANCHING.md 규칙 6 · 승인된 사람 병합 후보 · 도구 infra/dev/tag-release.sh prod)" >&2
    echo "  ⛔ 이 검사에는 우회 선언이 없다 — 태그를 먼저 찍는다" >&2
    exit 65
  fi
  SHIP_GATE_PROD_TAG="$(printf '%s\n' "$tags" | head -1)"
  echo "prod 태그 확인: $SHIP_GATE_PROD_TAG ($sha)"
}
