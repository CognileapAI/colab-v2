#!/usr/bin/env bash
# 반입 게이트 — `main` 이 유일한 배포 원천이다 (규칙 1 · `docs/BRANCHING.md` §1·§5 · WU-D2).
#
# 왜 여기 있나 — 종전에는 이 본문이 `infra/dev/ship.sh` **안에만** 있었다. prod 를 세우면서
# 같은 것을 한 벌 더 두면 한쪽만 고쳐져 갈린다(문구·종료코드·`MAIN_SHA` 형식). 형식이 갈리면
# `deploy_doctor` ⑮ 가 「형식 불일치」로 ✗ 를 낸다 — 그 ✗ 의 원인이 복사본인 것이
# 제일 찾기 어렵다. ⟹ **게이트 본문은 한 벌이고 dev·prod 가 그것을 부른다.**
#
# 부르는 쪽 = `infra/dev/ship.sh` · `infra/prod/ship.sh` (`. "$REPO/infra/_lib/ship-gate.sh"`).
# 끝나는 자리는 셋뿐이다 — 통과 · 거절(**65**) · 준비 실패(**78**). 조용한 경로는 없다.
# 시험 = `infra/dev/tests/ship-gate.sh`(dev 6 케이스) · `infra/prod/tests/ship-gate.sh`(prod 4 케이스)
#        ＋ `services/core-api/tests/test_deploy_doctor.py` 의 생산자·소비자 대조.

# ── ship_gate_main_ancestor <저장소> <후보 sha> ───────────────────────────────
#: 후보가 `origin/main` 의 조상인지 본다. 통과하면 두 값을 채운다 —
#:   SHIP_GATE_MAIN_SHA  = origin/main 의 12자리
#:   SHIP_GATE_ANCESTOR  = yes | bypass
#: `COLAB_SHIP_ALLOW_NONMAIN` 의 기본값 0 은 **거절** 쪽이다(관대한 기본값이 아니다).
#: 창 9(2026-09-06)는 `main` 밖 레인 sha 를 dev 에 실었고 그 ai 마이그레이션이 dev 에만 남았다.
ship_gate_main_ancestor() {
  local repo="$1" sha="$2"
  git -C "$repo" fetch -q origin main \
    || { echo "origin 조회 실패 — 진행 금지" >&2; exit 78; }
  SHIP_GATE_MAIN_SHA="$(git -C "$repo" rev-parse --short=12 origin/main)"
  if git -C "$repo" merge-base --is-ancestor "$sha" origin/main; then
    SHIP_GATE_ANCESTOR=yes
  elif [ "${COLAB_SHIP_ALLOW_NONMAIN:-0}" = "1" ]; then
    # 선언된 우회는 허용한다. 셋에 함께 남는다 — 이 줄 · MAIN_SHA 의 bypass · deploy_doctor ⑮ 의 ✗.
    SHIP_GATE_ANCESTOR=bypass
    echo "비조상 반입 · 우회 선언 — MAIN_SHA 에 ancestor=bypass 로 남고 deploy_doctor ⑮ 가 ✗ 로 잡는다"
  else
    echo "sha 가 origin/main 조상이 아니다: $sha" >&2
    echo "  긴급 반입이라면 COLAB_SHIP_ALLOW_NONMAIN=1 로 **선언**한다 (우회는 기록에 남는다)" >&2
    exit 65
  fi
}

# ── ship_gate_require_prod_tag <저장소> <후보 sha> ────────────────────────────
#: **prod 전용 · 우회 변수가 없다.** 규칙 6 — prod 는 `prod-YYYYMMDD` 태그에서만 배포한다
#: (`docs/BRANCHING.md` §1 규칙 6 · §2 수명 표 `prod-YYYYMMDD` 행 · 태그 주체 = Ted).
#: 검사 대상은 **반입 후보 sha** 다 — 통상 그것이 `HEAD` 지만 후보는 `dist/colab-v2-prod.sha`
#: 가 정하므로, `HEAD` 가 그 뒤로 움직인 날에도 실제로 실리는 커밋을 본다.
#: 통과하면 SHIP_GATE_PROD_TAG 에 첫 태그 이름을 채운다.
ship_gate_require_prod_tag() {
  local repo="$1" sha="$2" tags
  tags="$(git -C "$repo" tag --points-at "$sha" 'prod-*')" \
    || { echo "태그 조회 실패 — 진행 금지" >&2; exit 78; }
  if [ -z "$tags" ]; then
    echo "prod 태그가 없다: $sha — prod 는 \`prod-YYYYMMDD\` 태그에서만 배포한다" >&2
    echo "  (docs/BRANCHING.md 규칙 6 · 태그 주체 = Ted · 도구 infra/dev/tag-release.sh prod)" >&2
    echo "  ⛔ 이 검사에는 우회 선언이 없다 — 태그를 먼저 찍는다" >&2
    exit 65
  fi
  SHIP_GATE_PROD_TAG="$(printf '%s\n' "$tags" | head -1)"
  echo "prod 태그 확인: $SHIP_GATE_PROD_TAG ($sha)"
}
