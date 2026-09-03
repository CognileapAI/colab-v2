#!/usr/bin/env bash
# frontend-typecheck 게이트 — **프런트 타입 검사가 이미지 빌드 밖에서도 돈다.**
#
# 왜 생겼나 (2026-09-02 사고):
#   `frontend/Dockerfile:11` 의 `npm run build` 가 `tsc --noEmit && vite build` 다. 즉 프런트
#   타입 검사는 **이미지 빌드 안에만** 있었고 게이트에는 한 줄도 없었다(`grep -rl 'tsc --noEmit' gates/`
#   = 0). 그래서 `node:fs` 를 import 한 시험 파일이 `main` 에 들어간 12:01 부터 22:32 의 staging
#   배포가 이미지 빌드 단계에서 깨질 때까지 **`main` 이 배포 불가인 채로 전 게이트 green** 이었다.
#   더 나쁜 것은 그 사이 다섯 레인이 「tsc 오류 4건 = main 동일」을 보고했고 그것이 **기존 상태로
#   수용**됐다는 점이다 — 아무도 재지 않는 검사는 「원래 그렇다」로 굳는다.
#
# 무엇을 강제하나:
#   Dockerfile 이 도는 것과 **같은 검사**를 같은 tsconfig 로 돌린다 — `frontend/tsconfig.json`
#   기준 `tsc --noEmit`. 게이트가 자기 사본을 만들면 그 순간 「게이트는 green 인데 이미지는 red」가
#   다시 열린다. 그래서 ⑴ 명령을 `frontend/package.json` 의 `build` 스크립트에서 **읽어 대조**하고
#   갈리면 red 다.
#
# fail-closed (CLAUDE.md §4 green-by-skip 금지):
#   · `frontend/node_modules` 부재            → red(준비). skip 이 아니다
#   · `node_modules/.bin/tsc` 부재            → red(준비)
#   · `frontend/tsconfig.json` 부재           → red
#   · `build` 스크립트가 `tsc --noEmit` 로 시작하지 않음 → red (검사가 이미지에서 빠진 것이다)
#   · `tsconfig.json` `include` 에 `test` 없음 → red (범위 축소로 green 을 만드는 길을 막는다)
#   · `tsc` 비영 종료                          → red (오류를 이름으로 찍는다)
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
FE="${COLAB_FRONTEND_DIR:-$REPO_ROOT/frontend}"
READINESS_EXIT=78

red() { echo "::error::frontend-typecheck red — $*"; exit 1; }
ready_red() { # 준비 실패도 red 다. 다른 게이트와 같은 표식·종료코드를 쓴다.
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    frontend-typecheck "$1" "대기 없음" "0초" "$2"
  echo "::error::frontend-typecheck red(준비) — **검사기가 돌지 못했다.** 판정 red 가 아니다.
   기다린 것: $1
   사유: $2
   ⚠ 준비 실패도 **red 다.** 건너뛰기로 green 을 만들지 않는다."
  exit "$READINESS_EXIT"
}

[ -d "$FE" ] || red "프런트 자리가 없다: $FE. 대상 0건은 통과가 아니다."
PKG="$FE/package.json"; TSCONFIG="$FE/tsconfig.json"; DOCKERFILE="$FE/Dockerfile"
[ -f "$PKG" ]       || red "$PKG 가 없다."
[ -f "$TSCONFIG" ]  || red "$TSCONFIG 가 없다 — 검사 기준이 없으면 검사가 아니다."

# ⑴ 이미지가 도는 것과 같은 검사인가. 갈리면 red — 이 대조가 없으면 게이트가 조용히 옆길로 샌다.
BUILD_SCRIPT="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["scripts"].get("build",""))' "$PKG")"
case "$BUILD_SCRIPT" in
  "tsc --noEmit"*) : ;;
  *) red "frontend/package.json 의 build 스크립트가 \`tsc --noEmit\` 으로 시작하지 않는다: «$BUILD_SCRIPT».
   이 게이트는 **이미지 빌드가 도는 검사**를 그대로 돈다. 둘이 갈리면 게이트가 green 인데 배포가 깨진다." ;;
esac
if [ -f "$DOCKERFILE" ] && ! grep -q 'npm run build' "$DOCKERFILE"; then
  red "frontend/Dockerfile 이 더 이상 \`npm run build\` 를 돌지 않는다 — 이 게이트가 보는 명령과 이미지가 도는 명령이 갈렸다."
fi

# ⑵ 검사 범위. `include` 에서 `test` 를 빼는 편집은 **범위 축소**이지 수정이 아니다 (CLAUDE.md §3).
python3 - "$TSCONFIG" <<'PY' || exit 1
import json, re, sys
raw = open(sys.argv[1], encoding='utf-8').read()
raw = re.sub(r'(?m)^\s*//.*$', '', raw)
inc = json.loads(raw).get('include') or []
missing = [d for d in ('src', 'test') if d not in inc]
if missing:
    print("::error::frontend-typecheck red — tsconfig include 에 %s 가 없다. "
          "검사 대상을 줄여 green 을 만드는 것은 수정이 아니다 (CLAUDE.md §3)." % '·'.join(missing))
    sys.exit(1)
PY

# ⑶ 준비 — 없으면 red(준비). 「못 돌았음」을 「통과」로 세지 않는다.
[ -d "$FE/node_modules" ] || ready_red "frontend/node_modules" \
  "의존 트리가 이 체크아웃에 없다. frontend/ 에서 npm ci 를 돌리거나 main 체크아웃의 node_modules 를 심볼릭 링크한 뒤 재실행한다."
TSC="$FE/node_modules/.bin/tsc"
[ -x "$TSC" ] || ready_red "frontend/node_modules/.bin/tsc" \
  "타입스크립트 컴파일러 실행 파일이 없다. frontend/ 에서 npm ci 를 돌린 뒤 재실행한다."

# ⑷ 판정 — Dockerfile 이 도는 그 검사.
OUT="$(cd "$FE" && "$TSC" --noEmit 2>&1)"; rc=$?
if [ "$rc" -ne 0 ]; then
  n="$(printf '%s\n' "$OUT" | grep -c 'error TS' || true)"
  echo "::error::frontend-typecheck red — tsc --noEmit 이 오류 ${n}건으로 종료했다(코드 $rc).
   **이 오류는 frontend 이미지 빌드를 그대로 깨뜨린다**(frontend/Dockerfile: npm run build).
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
  exit 1
fi
echo "frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건."
