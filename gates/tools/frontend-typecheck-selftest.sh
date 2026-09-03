#!/usr/bin/env bash
# frontend-typecheck 이 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 — red 여섯 · green 하나. 판정은 전부 **실제 사본 트리**에서 난다(진짜 frontend/ 는
# 한 글자도 건드리지 않는다). 사본은 `COLAB_FRONTEND_DIR` 로 게이트에 넘긴다.
#   ⓐ node_modules 부재                 → red(준비 · 코드 78)  ← 「못 돌았음」은 통과가 아니다
#   ⓑ .bin/tsc 부재                     → red(준비 · 코드 78)
#   ⓒ tsconfig.json 부재                → red
#   ⓓ tsconfig include 에서 `test` 제거 → red  ← **범위 축소로 green 을 만드는 길을 막는다**
#   ⓔ build 스크립트가 `tsc --noEmit` 아님 → red  ← 이미지가 도는 검사와 갈리면 red
#   ⓕ ⭑ **`74deb54` 실물 결함 재현** — 시험 파일이 `node:fs`·`node:path`·`__dirname` 을 쓴다
#        → red. 이 무늬가 2026-09-02 에 `main` 을 10시간 반 배포 불가로 만들었고 **어떤 게이트도
#        보지 않았다.** 이 케이스가 green 이 되면 게이트는 존재 이유를 잃는다.
#   ⓖ 깨끗한 트리                        → green
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/frontend-typecheck.sh"
FE="$REPO_ROOT/frontend"
rc=0

red() { echo "::error::frontend-typecheck-selftest red — $*"; exit 1; }
[ -x "$GATE" ] || red "판정 재료가 없다: gates/tools/frontend-typecheck.sh"
[ -d "$FE/node_modules" ] || {
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    frontend-typecheck-selftest "frontend/node_modules" "대기 없음" "0초" "의존 트리 부재"
  echo "::error::frontend-typecheck-selftest red(준비) — frontend/node_modules 가 없어 사본 트리를 만들 수 없다.
   frontend/ 에서 npm ci 를 돌린 뒤 재실행한다. 준비 실패도 red 다."
  exit 78
}

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" fe-typecheck-st-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

# 사본 트리 — 소스·시험은 실물을 복사하고, 의존 트리만 링크로 빌린다(수 GB 복사를 하지 않는다).
mk_tree() { # $1 = 만들 자리
  local d="$1"; mkdir -p "$d"
  cp "$FE/package.json" "$FE/tsconfig.json" "$FE/vite.config.ts" "$FE/Dockerfile" "$d/"
  cp -r "$FE/src" "$FE/test" "$d/"
  ln -s "$(cd "$FE/node_modules" && pwd)" "$d/node_modules"
  # 초안 md 를 `?raw` 로 읽는 시험이 있다 — 사본에서도 그 상대 경로가 살아 있어야 한다.
  mkdir -p "$d/../dev-package"
  [ -e "$d/../dev-package/sessions" ] || ln -s "$REPO_ROOT/dev-package/sessions" "$d/../dev-package/sessions"
}

expect() { # $1=기대(red|red-ready|green) $2=이름 $3=트리
  local want="$1" name="$2" dir="$3" out ec
  out="$(COLAB_FRONTEND_DIR="$dir" "$GATE" 2>&1)"; ec=$?
  case "$want" in
    green)     [ "$ec" -eq 0 ] && { echo "  ✓ $name — green"; return; } ;;
    red-ready) [ "$ec" -eq 78 ] && { echo "  ✓ $name — red(준비 · 78)"; return; } ;;
    red)       [ "$ec" -eq 1 ] && { echo "  ✓ $name — red"; return; } ;;
  esac
  echo "::error::frontend-typecheck-selftest red — 케이스 $name 이 기대($want)와 다른 종료 코드 $ec 를 냈다."
  printf '%s\n' "$out" | sed 's/^/     /'
  rc=1
}

base="$TMP/case/fe"; mk_tree "$base"

# ⓖ 깨끗한 트리 → green  (먼저 돈다 — 이것이 green 이 아니면 아래 red 들은 의미가 없다)
expect green "ⓖ 깨끗한 트리" "$base"

# ⓕ ⭑ `74deb54` 실물 결함 — Node 전용 API 를 쓰는 시험 파일
cat > "$base/test/zz-selftest-node-import.test.ts" <<'FIX'
// selftest 전용 red fixture — 74deb54 가 main 에 넣은 결함의 실물 무늬다.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
const p = join(__dirname, '..', 'package.json');
describe('fixture', () => {
  it('reads', () => {
    expect(readFileSync(p, 'utf8').split('\n').filter((l) => l.length > 0).length).toBeGreaterThan(0);
  });
});
FIX
expect red "ⓕ 시험 파일이 node:fs·node:path·__dirname 을 쓴다 (74deb54 재현)" "$base"
rm "$base/test/zz-selftest-node-import.test.ts"

# ⓓ include 에서 `test` 제거 → red (범위 축소)
d="$TMP/noinclude/fe"; mk_tree "$d"
python3 - "$d/tsconfig.json" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p,encoding='utf-8'))
c['include']=[x for x in c['include'] if x!='test']
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
PY
expect red "ⓓ tsconfig include 에서 test 제거" "$d"

# ⓔ build 스크립트가 이미지가 도는 검사와 갈린다 → red
d="$TMP/nobuild/fe"; mk_tree "$d"
python3 - "$d/package.json" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p,encoding='utf-8'))
c['scripts']['build']='vite build'
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
PY
expect red "ⓔ build 스크립트에서 tsc --noEmit 이 빠짐" "$d"

# ⓒ tsconfig 부재 → red
d="$TMP/nots/fe"; mk_tree "$d"; rm "$d/tsconfig.json"
expect red "ⓒ tsconfig.json 부재" "$d"

# ⓑ .bin/tsc 부재 → red(준비)
d="$TMP/notsc/fe"; mk_tree "$d"; rm "$d/node_modules"
mkdir -p "$d/node_modules/.bin"
expect red-ready "ⓑ node_modules/.bin/tsc 부재" "$d"

# ⓐ node_modules 부재 → red(준비)
d="$TMP/nonm/fe"; mk_tree "$d"; rm "$d/node_modules"
expect red-ready "ⓐ node_modules 부재" "$d"

exit $rc
