#!/usr/bin/env bash
# import-boundary 게이트 (WU-D3) — 도메인 간 직접 참조를 import-linter 로 막는다.
#
# 강제하는 것: CLAUDE.md §3-1 (도메인은 자기 테이블 + D1 만, cross-domain 은 Port 경유),
#              DOMAINS.md §4 (배포 단위 5개는 서로 import 로 붙지 않는다).
# 계약 정본: gates/config/importlinter.ini · 모듈 경로 관례: dev-package/sessions/D3-boundary.md §2
#
# 원칙 (CLAUDE.md §4):
#   - 도구 부재·설치 실패는 **red**. skip 없음.
#   - 검사 대상(파이썬 패키지)이 없으면 **red**. 없는 코드를 통과시킨 게이트는 green-by-skip 이다.
#     P0 이전의 이 게이트는 red 이고, red 인 것이 정상이다.
#
# 환경변수 (selftest 전용 — 평시엔 건드리지 않는다)
#   COLAB_SERVICES_DIR        배포 단위 루트 (기본: services/)
#   COLAB_BOUNDARY_CONFIG     boundaries.toml 경로
#   COLAB_IMPORTLINTER_CONFIG importlinter.ini 경로
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICES="${COLAB_SERVICES_DIR:-$REPO_ROOT/services}"
BCONF="${COLAB_BOUNDARY_CONFIG:-$REPO_ROOT/gates/config/boundaries.toml}"
ILCONF="${COLAB_IMPORTLINTER_CONFIG:-$REPO_ROOT/gates/config/importlinter.ini}"

red() { echo "::error::import-boundary red — $*"; exit 1; }

[ -f "$BCONF" ]  || red "설정이 없다: ${BCONF#$REPO_ROOT/}"
[ -f "$ILCONF" ] || red "계약 파일이 없다: ${ILCONF#$REPO_ROOT/}"

# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_venv.sh"
ensure_gate_venv import-boundary || exit 1

# ── 대상 확보 ────────────────────────────────────────────────────────────────
# boundaries.toml 이 배포 단위 ↔ 패키지 대응의 정본이다. 여기서 경로를 다시 적지 않는다.
MISSING=()
PYPATH=""
while IFS=$'\t' read -r unit dir pkg; do
  src="$SERVICES/$dir/src"
  if [ -f "$src/$pkg/__init__.py" ]; then
    PYPATH="$src:$PYPATH"
  else
    MISSING+=("$unit → ${src#$REPO_ROOT/}/$pkg/__init__.py")
  fi
done < <("$GATE_PY" - "$BCONF" <<'PY'
import sys, tomllib
cfg = tomllib.load(open(sys.argv[1], "rb"))
for name, u in cfg["units"].items():
    print(f"{name}\t{u['dir']}\t{u['package']}")
PY
)

if [ "${#MISSING[@]}" -gt 0 ]; then
  red "검사할 파이썬 패키지가 없다. 대상 0건인 경계 게이트는 통과가 아니다.
   없는 것:
$(printf '     - %s\n' "${MISSING[@]}")
   모듈 경로 관례는 dev-package/sessions/D3-boundary.md §2 가 정본이며, P0 가 그 자리에 코드를 놓는다.
   그때까지 이 게이트는 red 다 — 이건 버그가 아니다 (CLAUDE.md §4)."
fi

echo "# 계약 ${ILCONF#$REPO_ROOT/} · 대상 PYTHONPATH=${PYPATH//$REPO_ROOT\//}"
LINTER="${GATE_PY%/python}/lint-imports"
[ -x "$LINTER" ] || red "lint-imports 실행체가 없다: $LINTER"
PYTHONPATH="$PYPATH" "$LINTER" --config "$ILCONF" --no-cache
rc=$?
[ $rc -eq 0 ] || red "경계 계약 위반 (import-linter exit $rc).
   우회하지 말고 멈추고 보고한다 — Port 추가인가 / 도메인 분할이 틀렸는가 / 기획이 애매한가
   (CLAUDE.md §4 '경계를 넘어야 할 때')."
echo "import-boundary green — 계약 전부 통과."
