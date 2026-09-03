#!/usr/bin/env bash
# frontend-fixture-reach 게이트 — 운영 진입점(`frontend/src/main.tsx`)에서 **실제로 닿는** 모듈
# 그래프에 개발용 픽스처(`fixture.ts` · `graphFixture.ts` · `localEngine.ts`)가 섞여드는지 본다.
#
# 왜 있는가 (레인 E · `CODE-REVIEW-20260903-E.md §5·§8`):
#   `frontend/scripts/reachable-from-entry.mjs` 는 픽스처 폴백 제거(리뷰 9)의 회귀 방지로 만들어졌지만
#   **사람이 손으로 부를 때만 돌았다.** rc 로 말하도록 이미 짜여 있는데(닿으면 exit 1) 아무도 그 rc 를
#   게이트로 세지 않으면, 다음 폴백 회귀는 사람이 그 명령을 다시 손으로 치기 전까지 아무도 모른다.
#
# 판정부는 그대로 쓴다 — 게이트가 자기 워커를 새로 만들면 그 순간 「게이트가 보는 것」과
# 「스크립트가 보는 것」이 갈릴 여지가 생긴다 (`gates/tools/frontend-typecheck.sh` 와 같은 원칙).
#
# ⚠ 이 워커의 한계 (정직하게, `CODE-REVIEW-20260903-E.md §8`):
#   `resolveSpecifier` 는 `.` 로 시작하는 **상대 import 만** 따라간다. `tsconfig.json` 의
#   `paths`/`baseUrl` 또는 `vite.config.ts` 의 `resolve.alias` 로 이름을 붙이면, 별칭 뒤에 숨은
#   import 는 이 워커가 아예 못 본다 — **닿지 못한 모듈은 검사 대상에서 조용히 빠지고 게이트는
#   green 을 찍는다.** 오늘(2026-09-03)은 실물에 둘 다 없음을 확인했다(레인 E 실측). 그래서 이
#   게이트는 그 값을 매 회차 다시 확인해, 하나라도 생기면 **자기 능력을 실제보다 크게 말하지
#   않기 위해** 스스로 red 를 낸다 — 자동으로 조용히 덜 세는 것보다 사람이 별칭 해석기를
#   붙이거나 「레포 내부 import 는 상대 경로만」을 강제하는 편이 싸다.
#
# fail-closed (CLAUDE.md §4 green-by-skip 금지):
#   · node 실행 파일 부재                        → red(준비 · 78)
#   · frontend/scripts/reachable-from-entry.mjs 부재 → red(준비 · 78)
#   · 운영 진입점(기본 src/main.tsx) 부재         → red(준비 · 78)
#   · tsconfig paths/baseUrl 또는 vite resolve.alias 선언 → red (워커가 별칭 뒤를 못 본다)
#   · 금지 모듈(fixture.ts·graphFixture.ts·localEngine.ts) 도달 → red
#   · 진입점 말고 도달한 모듈이 0건            → red (그래프가 비면 아무것도 검사하지 않은 것과 같다)
#   · 그 외                                       → green (도달 모듈 수를 요약줄에 낸다)
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
FE="${COLAB_FRONTEND_DIR:-$REPO_ROOT/frontend}"
ENTRY="${COLAB_FIXTURE_REACH_ENTRY:-src/main.tsx}"
READINESS_EXIT=78

red() { echo "::error::frontend-fixture-reach red — $*"; exit 1; }
ready_red() { # 준비 실패도 red 다. frontend-typecheck.sh 와 같은 표식·종료코드를 쓴다.
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    frontend-fixture-reach "$1" "대기 없음" "0초" "$2"
  echo "::error::frontend-fixture-reach red(준비) — **검사기가 돌지 못했다.** 판정 red 가 아니다.
   기다린 것: $1
   사유: $2
   ⚠ 준비 실패도 **red 다.** 건너뛰기로 green 을 만들지 않는다."
  exit "$READINESS_EXIT"
}

[ -d "$FE" ] || red "프런트 자리가 없다: $FE. 대상 0건은 통과가 아니다."

SCRIPT="$FE/scripts/reachable-from-entry.mjs"
[ -f "$SCRIPT" ] || ready_red "$SCRIPT" "판정부 스크립트가 없다. 레인 E 가 만든 도달성 워커가 이 체크아웃에 없으면 검사 대상을 한 건도 보지 못한다."

[ -f "$FE/$ENTRY" ] || ready_red "$FE/$ENTRY" "운영 진입점이 없다."

command -v node >/dev/null 2>&1 || ready_red "node 실행 파일" "node 가 PATH 에 없다. 이 워커는 zero-dependency 라 frontend/node_modules 없이도 돌지만 node 자체는 있어야 한다."

# ⑴ 별칭 가드 — 이 워커는 상대 import 만 따라간다(`resolveSpecifier` 의 `if (!spec.startsWith('.')) return null`).
#    tsconfig paths·baseUrl 또는 vite resolve.alias 가 선언되면 그 뒤로 숨은 import 를 못 보는데,
#    그 상태를 green 으로 찍으면 「덜 봤다」가 「문제 없다」로 둔갑한다. 그러니 선언을 발견하면
#    도달성 판정 자체를 하지 않고 여기서 멈춘다.
ALIAS_HIT="$(python3 - "$FE/tsconfig.json" "$FE/vite.config.ts" <<'PY'
import json, re, sys
tsconfig_path, vite_path = sys.argv[1], sys.argv[2]
hits = []
try:
    raw = open(tsconfig_path, encoding='utf-8').read()
    raw = re.sub(r'(?m)^\s*//.*$', '', raw)  # 주석 제거 — jsonc 관용
    co = json.loads(raw).get('compilerOptions', {}) or {}
    if co.get('paths'):
        hits.append('tsconfig.json compilerOptions.paths')
    if co.get('baseUrl'):
        hits.append('tsconfig.json compilerOptions.baseUrl')
except FileNotFoundError:
    pass
except json.JSONDecodeError:
    pass
try:
    vraw = open(vite_path, encoding='utf-8').read()
    if re.search(r'resolve\s*:\s*\{[^}]*alias', vraw, re.S):
        hits.append('vite.config.ts resolve.alias')
except FileNotFoundError:
    pass
print('\n'.join(hits))
PY
)"
if [ -n "$ALIAS_HIT" ]; then
  red "프런트가 경로 별칭을 선언했다 — 이 워커는 **상대 import 만** 따라간다(별칭 해석기가 없다).
   선언된 자리: $(printf '%s' "$ALIAS_HIT" | tr '\n' ';' | sed 's/;$//')
   별칭 뒤에 금지 모듈이 숨으면 이 게이트가 통과를 잘못 찍는다 — 워커에 별칭 해석기를 붙이거나
   레포 내부 import 를 상대 경로로 되돌리기 전까지는 이 검사를 신뢰하지 않는다."
fi

# ⑵ 판정 — 진짜 워커를 그대로 돈다. cwd 를 FE 로 두어 스크립트의 `resolve('.')` 가
#    이 트리를 루트로 보게 한다(selftest 가 픽스처 트리를 COLAB_FRONTEND_DIR 로 먹이는 방식과 짝).
OUT="$(cd "$FE" && node "scripts/reachable-from-entry.mjs" "$ENTRY" 2>&1)"; rc=$?
REACHED="$(printf '%s\n' "$OUT" | grep -o 'reached=[0-9]\+' | head -1 | cut -d= -f2)"

if [ -z "$REACHED" ]; then
  red "판정부 출력에서 도달 모듈 수(reached=)를 읽지 못했다 — 비정상 종료 가능성.
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
fi
if [ "$rc" -ne 0 ]; then
  red "운영 경로가 픽스처에 닿는다(rc=$rc).
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
fi

WALKED=$((REACHED - 1)) # 진입점 자신을 뺀, 실제로 당겨진 모듈 수.
if [ "$WALKED" -le 0 ]; then
  red "진입점 $ENTRY 말고 도달한 모듈이 0건이다 — 그래프가 비어 있으면 이 게이트는 아무것도 검사하지 않은 것과 같다.
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
fi

echo "frontend-fixture-reach green — 진입점 $ENTRY 에서 도달 ${REACHED}개(진입점 제외 ${WALKED}개), 금지 모듈(fixture.ts·graphFixture.ts·localEngine.ts) 0건."
