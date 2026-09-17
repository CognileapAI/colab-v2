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
# 색 코드는 판정부의 입력이 아니다 — 러너(GitHub Actions)는 CI=1 이어도 색을 켜서 「563 passed」 앞에
# ESC 시퀀스가 붙고, 아래 정규식이 건수를 못 읽어 통과한 시험을 red 로 냈다(draft PR #2 실측).
OUT="$(cd "$FE" && CI=1 NO_COLOR=1 FORCE_COLOR=0 "$VITEST" run --reporter=default 2>&1)"; rc=$?
OUT="$(printf '%s\n' "$OUT" | sed 's/\x1b\[[0-9;]*[A-Za-z]//g')"

# ⑶-b ⭑ ⟨2026-09-17 · 이슈 #55⟩ **워커가 못 떴으면 「돌아서 틀렸다」가 아니다.**
#   vitest 가 워커 프로세스를 띄우지 못하고 상한에서 끊기면 검사 대상은 **한 건도 판정되지 않았다.**
#   종전에는 아래 `rc != 0` 갈래가 그것을 무조건 red(판정 · 1)로 접었고, 준비 실패 통로는
#   `node_modules` 부재와 `vitest` 실행 파일 부재에만 걸려 있었다. 「돌지 못했다」와 「돌아서
#   틀렸다」가 갈리지 않으면 부하에서 나는 간헐 red 를 결함으로 오인한다(ADR-0004).
#
#   축자 문면 — vitest 4.1.11 실물에서 확인했다
#   (`frontend/node_modules/vitest/dist/chunks/cli-api.CnMVyzaz.js`). 두 자리다:
#     · `:3462` `const WORKER_START_TIMEOUT = 9e4;` → `:3531`
#       `` new Error(`[vitest-pool]: Timeout starting ${task.worker} runner.`) ``
#       — `task.worker` 는 풀 이름이고 fork 풀은 `:3125` `name = "forks"` 이므로 실물 문면은
#         「[vitest-pool]: Timeout starting forks runner.」 다.
#     · `:2861` `const START_TIMEOUT = 6e4;` → `:2973`
#       `this.withTimeout(this.waitForStart(), START_TIMEOUT)` → `:3108`
#       `new Error("[vitest-pool-runner]: Timeout waiting for worker to respond")`
#       — 워커를 띄운 뒤 `started` 응답을 기다리다 끊긴 자리다.
#   둘 다 **기동 대기**가 끊긴 것이므로 같은 갈래로 보낸다. 추측 문면을 쓰지 않았다 —
#   추측으로 정규식을 쓰면 red fixture 는 통과하는데 실물은 영영 안 걸리는 갈래가 선다.
#
#   ⚠ **자리는 ⑷ 수집 0건 검사보다 앞이다.** 워커가 못 뜬 회차의 출력이 `Tests  no tests` 를
#     함께 달고 나오는지는 실물로 확인하지 못했다(진짜 시간초과 재현은 그 자체가 부하 의존
#     시험이라 기각됐다). 뒤에 두면 그 경우 준비 실패가 판정 red 로 **선행 흡수**된다.
#     앞에 두어도 수집 0건 판정은 그대로다 — 이 표식이 없는 출력은 아래로 그냥 내려간다.
#   ⚠ `rc != 0` 을 함께 본다. 어떤 시험이 이 문자열을 본문에 담아 출력해도 green 을 뒤집지 않는다.
if [ "$rc" -ne 0 ] && printf '%s\n' "$OUT" \
     | grep -qE '\[vitest-pool(-runner)?\]: Timeout (starting .* runner\.|waiting for worker to respond)'; then
  ready_red "vitest 워커 기동" \
    "cause=워커기동실패 vitest 가 워커 프로세스를 상한 안에 띄우지 못했다(기동 상한 90초 · 응답 대기 상한 60초). 검사 대상은 한 건도 판정되지 않았다 — 판정 red 가 아니다. 호스트 부하를 내린 뒤 다시 돌린다. 상한을 늘려 green 을 만들지 않는다."
fi

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
  # ⭑ ⟨2026-09-17 · 이슈 #55⟩ **무엇이 깨졌는지 이름으로 남긴다.**
  #   종전에는 실패한 시험의 파일·이름이 요약 어디에도 없어 사람이 1300줄 출력을 뒤졌고,
  #   `gate-summary.json` 에는 그 값을 적을 열 자체가 없었다. 회차를 넘어 간헐 실패를 누적하려면
  #   값으로 남아야 한다. 표식은 공용이다 — 실행기가 집어 게이트 행의 5번째 열로 싣는다
  #   (`gates/run.sh` `summary_failure_marks()` · 형식은 `gates/README.md`).
  #
  #   vitest 4.1.11 기본 리포터의 실패 머리줄 축자 형태(이 워크트리의 실물 출력에서 확인):
  #       ` FAIL  test/zz-fail.test.ts > outer group > fails on purpose`
  #   = 선행 공백 ＋ `FAIL` ＋ 공백 ＋ 파일 경로 ＋ ` > ` ＋ (suite 사슬 ＋ 시험 이름).
  #   파일 적재 자체가 깨지면 ` > ` 없이 파일만 오는 줄도 있으므로 그때는 이름을 비운다.
  printf '%s\n' "$OUT" | awk '
    /^[[:space:]]*FAIL[[:space:]]/ {
      line = $0
      sub(/^[[:space:]]*FAIL[[:space:]]+/, "", line)
      if (line in seen) next
      seen[line] = 1
      idx = index(line, " > ")
      if (idx > 0) { file = substr(line, 1, idx - 1); name = substr(line, idx + 3) }
      else         { file = line; name = "" }
      printf "::gate-failure::gate=frontend-test|file=%s|test=%s\n", file, name
    }'
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
