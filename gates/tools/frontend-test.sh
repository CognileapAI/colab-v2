#!/usr/bin/env bash
# frontend-test 게이트 — **화면 동작 시험(vitest)이 게이트 안에서 돈다.**
#
# 왜 생겼나 (2026-09-03 화면 검수):
#   `frontend/test` 에 시험 25파일이 이미 있는데 **게이트 39개 어디에도 없었다.**
#   `frontend-typecheck` 는 타입만 본다 — 라벨·문구·표기 규칙 같은 **화면 동작**은
#   아무도 재지 않았다. 그래서 정본과 어긋난 화면(검수 30행)이 전 게이트 green 인 채로
#   staging 에 서 있었다. 아무도 재지 않는 검사는 「원래 그렇다」로 굳는다.
#
# 무엇을 강제하나:
#   `frontend/package.json` 의 `test` 스크립트가 도는 것과 **같은 명령**(`vitest run`)을
#   레포의 `vite.config.ts` 설정 그대로 돌린다. 게이트가 자기 사본 설정을 만들면 그 순간
#   「게이트는 green 인데 실제 시험은 red」가 열린다.
#
# fail-closed (CLAUDE.md §4 green-by-skip 금지):
#   · `frontend/node_modules` 부재        → red(준비 · 78). skip 이 아니다
#   · `node_modules/.bin/vitest` 부재     → red(준비 · 78)
#   · `frontend/vite.config.ts` 부재      → red (검사 설정이 없으면 검사가 아니다)
#   · `test` 스크립트가 `vitest run` 아님 → red (검사가 옆길로 샜다)
#   · vitest 비영 종료                    → red
#   · ⭑ **수집된 시험 0건 → red.** 통과 0 · 실패 0 은 「전부 통과」가 아니라 「아무것도
#     검사하지 않았다」다. include 패턴이 빗나가거나 시험 자리가 비면 vitest 는 **종료
#     코드 0** 을 낼 수 있다 — 이 레포의 대표 실패 유형(green-by-skip)이 바로 그 모양이다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
FE="${COLAB_FRONTEND_DIR:-$REPO_ROOT/frontend}"
READINESS_EXIT=78

red() { echo "::error::frontend-test red — $*"; exit 1; }
ready_red() {
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    frontend-test "$1" "대기 없음" "0초" "$2"
  echo "::error::frontend-test red(준비) — **검사기가 돌지 못했다.** 판정 red 가 아니다.
   기다린 것: $1
   사유: $2
   ⚠ 준비 실패도 **red 다.** 건너뛰기로 green 을 만들지 않는다."
  exit "$READINESS_EXIT"
}

[ -d "$FE" ] || red "프런트 자리가 없다: $FE. 대상 0건은 통과가 아니다."
PKG="$FE/package.json"; VITECFG="$FE/vite.config.ts"
[ -f "$PKG" ]     || red "$PKG 가 없다."
[ -f "$VITECFG" ] || red "$VITECFG 가 없다 — 시험 설정(include·environment·setupFiles)이 없으면 검사가 아니다."

# ⑴ package.json 이 도는 것과 같은 명령인가. 갈리면 red.
TEST_SCRIPT="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["scripts"].get("test",""))' "$PKG")"
case "$TEST_SCRIPT" in
  "vitest run"*) : ;;
  *) red "frontend/package.json 의 test 스크립트가 \`vitest run\` 으로 시작하지 않는다: «$TEST_SCRIPT».
   이 게이트는 레포가 선언한 시험 명령을 그대로 돈다. 둘이 갈리면 게이트가 옆길로 샌다." ;;
esac

# ⑵ 준비 — 없으면 red(준비). 「못 돌았음」을 「통과」로 세지 않는다.
[ -d "$FE/node_modules" ] || ready_red "frontend/node_modules" \
  "의존 트리가 이 체크아웃에 없다. frontend/ 에서 npm ci 를 돌리거나 main 체크아웃의 node_modules 를 심볼릭 링크한 뒤 재실행한다."
VITEST="$FE/node_modules/.bin/vitest"
[ -x "$VITEST" ] || ready_red "frontend/node_modules/.bin/vitest" \
  "vitest 실행 파일이 없다. frontend/ 에서 npm ci 를 돌린 뒤 재실행한다."

# ⑶ 판정 — package.json 이 선언한 그 명령.
OUT="$(cd "$FE" && CI=1 "$VITEST" run --reporter=default 2>&1)"; rc=$?

# ⑷ 수집 0건 검사 — **종료 코드보다 먼저 본다.** 0건인데 green 은 이 레포의 대표 실패 유형이다.
SUMMARY="$(printf '%s\n' "$OUT" | grep -E '^[[:space:]]*(Tests|Test Files)[[:space:]]+' || true)"
NTESTS="$(printf '%s\n' "$OUT" | sed -n 's/.*[[:space:]]\([0-9][0-9]*\) passed.*/\1/p' | tail -1)"
if printf '%s\n' "$OUT" | grep -qE 'No test files found|Tests[[:space:]]+no tests'; then
  echo "::error::frontend-test red — **수집된 시험이 0건이다.** 통과 0·실패 0 은 「전부 통과」가 아니라
   「아무것도 검사하지 않았다」다(CLAUDE.md §4 green-by-skip). vite.config.ts 의 test.include 와
   frontend/test 자리를 확인한다.
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
  exit 1
fi
if [ "$rc" -ne 0 ]; then
  echo "::error::frontend-test red — vitest run 이 실패로 종료했다(코드 $rc).
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
  exit 1
fi
if [ -z "${NTESTS:-}" ] || [ "$NTESTS" -eq 0 ] 2>/dev/null; then
  echo "::error::frontend-test red — 통과 시험 건수를 요약에서 읽지 못했거나 0 이다.
   건수를 못 읽는 통과는 통과로 세지 않는다(CLAUDE.md §5 — 재지 않은 것을 잰 것처럼 쓰지 않는다).
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
  exit 1
fi
echo "frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 ${NTESTS}건 · 실패 0건."
printf '%s\n' "$SUMMARY" | sed 's/^/   /'
