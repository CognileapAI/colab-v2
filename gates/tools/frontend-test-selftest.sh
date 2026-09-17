#!/usr/bin/env bash
# frontend-test 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 — green 하나 · red 셋. 판정은 전부 **사본 트리**에서 난다(진짜 `frontend/` 는 한 글자도
# 건드리지 않는다). 사본은 `COLAB_FRONTEND_DIR` 로 게이트에 넘긴다 — `frontend-typecheck-selftest`
# 와 같은 배치다. 사본의 시험은 **작게 지어 넣는다**(진짜 446건을 네 번 돌리지 않는다) — 여기서
# 증명할 것은 「시험이 통과하는가」가 아니라 **「게이트가 red 를 낼 수 있는가」** 다.
#   ⓐ 깨끗한 트리(통과 시험 1건)      → green
#   ⓑ 시험 1건이 실패                 → red     ← 실패를 못 잡으면 게이트가 아니다
#   ⓒ ⭑ **수집된 시험 0건**           → red     ← green-by-skip 금지. 이 레포의 대표 실패 유형이다
#   ⓓ vitest 실행 파일 부재            → red(준비 · 78)  ← 「못 돌았음」은 통과가 아니다
#   ⓔ vitest 워커 기동 시간초과        → red(준비 · 78)  ← 「돌지 못했다」와 「돌아서 틀렸다」는 다르다
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/frontend-test.sh"
FE="$REPO_ROOT/frontend"
rc=0

red() { echo "::error::frontend-test-selftest red — $*"; exit 1; }
[ -x "$GATE" ] || red "판정 재료가 없다: gates/tools/frontend-test.sh"
if grep -q 'dev-package/sessions' "$FE/vite.config.ts"; then
  red "vite 시험 설정이 세션 문서 경로를 런타임 입력으로 허용한다"
fi
[ -d "$FE/node_modules" ] || {
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    frontend-test-selftest "frontend/node_modules" "대기 없음" "0초" "의존 트리 부재"
  echo "::error::frontend-test-selftest red(준비) — frontend/node_modules 가 없어 사본 트리를 만들 수 없다.
   frontend/ 에서 npm ci 를 돌린 뒤 재실행한다. 준비 실패도 red 다."
  exit 78
}

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" fe-test-st-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

mk_tree() { # $1 = 만들 자리. 설정은 실물을 복사하고 의존 트리는 링크로 빌린다(읽기).
  local d="$1"; mkdir -p "$d/test"
  cp "$FE/package.json" "$FE/vite.config.ts" "$FE/test/setup.ts" "$d/" 2>/dev/null
  mv "$d/setup.ts" "$d/test/setup.ts"
  ln -s "$(cd "$FE/node_modules" && pwd)" "$d/node_modules"
}
pass_test() { cat > "$1/test/zz-selftest-pass.test.ts" <<'T'
import { describe, expect, it } from 'vitest';
describe('selftest fixture', () => { it('passes', () => { expect(1 + 1).toBe(2); }); });
T
}

LAST_OUT=""
expect_case() { # $1=기대(red|red-ready|green) $2=이름 $3=트리
  local want="$1" name="$2" dir="$3" out ec
  out="$(COLAB_FRONTEND_DIR="$dir" "$GATE" 2>&1)"; ec=$?
  LAST_OUT="$out"
  case "$want" in
    green)     [ "$ec" -eq 0 ]  && { echo "  ✓ $name — green"; return; } ;;
    red-ready) [ "$ec" -eq 78 ] && { echo "  ✓ $name — red(준비 · 78)"; return; } ;;
    red)       [ "$ec" -eq 1 ]  && { echo "  ✓ $name — red"; return; } ;;
  esac
  echo "::error::frontend-test-selftest red — 케이스 $name 이 기대($want)와 다른 종료 코드 $ec 를 냈다."
  printf '%s\n' "$out" | sed 's/^/     /'
  rc=1
}

# 종료 코드만 맞으면 「무엇이 깨졌는지」는 여전히 사라질 수 있다. 직전 케이스가 실제로
# 그 표식 줄을 찍었는지 본다 — 표식이 없으면 게이트 행의 `failures` 열이 빈 채로 선다.
expect_last_output() { # $1=이름 $2=있어야 하는 축자 문자열
  case "$LAST_OUT" in
    *"$2"*) echo "  ✓ $1" ;;
    *) echo "::error::frontend-test-selftest red — $1: 출력에 「$2」가 없다."
       printf '%s\n' "$LAST_OUT" | sed 's/^/     /'; rc=1 ;;
  esac
}

# ⓐ 깨끗한 트리 → green (이것이 green 이 아니면 아래 red 들은 의미가 없다)
d="$TMP/clean/fe"; mk_tree "$d"; pass_test "$d"
expect_case green "ⓐ 깨끗한 트리(통과 시험 1건)" "$d"

# ⓑ 시험 1건이 실패 → red  ＋ **실패한 시험의 파일·이름이 표식으로 선다**
d="$TMP/failing/fe"; mk_tree "$d"; pass_test "$d"
cat > "$d/test/zz-selftest-fail.test.ts" <<'T'
import { describe, expect, it } from 'vitest';
describe('selftest fixture', () => { it('fails on purpose', () => { expect(1 + 1).toBe(3); }); });
T
expect_case red "ⓑ 시험 1건 실패" "$d"
expect_last_output 'ⓑ′ 실패 시험명이 ::gate-failure:: 표식으로 선다' \
  '::gate-failure::gate=frontend-test|file=test/zz-selftest-fail.test.ts|test=selftest fixture > fails on purpose'

# ⓒ ⭑ 수집된 시험 0건 → red. **통과 0·실패 0 은 「전부 통과」가 아니다** (CLAUDE.md §4)
d="$TMP/notests/fe"; mk_tree "$d"
expect_case red "ⓒ 수집된 시험 0건 (green-by-skip 금지)" "$d"

# ⓓ vitest 실행 파일 부재 → red(준비)
d="$TMP/novitest/fe"; mk_tree "$d"; pass_test "$d"; rm "$d/node_modules"
mkdir -p "$d/node_modules/.bin"
expect_case red-ready "ⓓ node_modules/.bin/vitest 부재" "$d"

# ⓔ ⭑ 워커 기동 시간초과 → red(준비 · 78). **판정 red 가 아니다.**
#   진짜 시간초과를 재현하지 않는다 — 그 자체가 부하 의존 시험이 된다. 대신 ⓓ 와 같은 방식으로
#   심볼릭 링크를 지우고 `node_modules/.bin/vitest` 자리에 **실물 축자 문면을 찍고 비영으로
#   끝나는 스텁**을 놓아 분류기를 결정적으로 때린다. 문면 출처는 `gates/tools/frontend-test.sh`
#   의 주석에 적힌 `vitest/dist/chunks/cli-api.CnMVyzaz.js:3531` 이다.
d="$TMP/workertimeout/fe"; mk_tree "$d"; pass_test "$d"; rm "$d/node_modules"
mkdir -p "$d/node_modules/.bin"
cat > "$d/node_modules/.bin/vitest" <<'STUB'
#!/usr/bin/env bash
echo "[vitest-pool]: Timeout starting forks runner."
exit 1
STUB
chmod +x "$d/node_modules/.bin/vitest"
expect_case red-ready "ⓔ 워커 기동 시간초과" "$d"
expect_last_output 'ⓔ′ 준비 실패 표식이 선다' '::gate-readiness-failure::gate=frontend-test'

exit $rc
