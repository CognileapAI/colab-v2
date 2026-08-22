#!/usr/bin/env bash
# contract-lint 게이트 (WU-D2) — seam OpenAPI 를 spectral 로 린트한다.
#
# 원칙 (CLAUDE.md §4):
#   - 도구가 없거나 네트워크가 죽어 검사를 못 하면 **skip 이 아니라 red** 다.
#   - 검사 대상이 0건이어도 red 다. 계약이 하나도 없는데 계약 게이트가 green 이면
#     그건 green-by-skip 이고, D2 완료 판정("spectral + oasdiff green")이 공짜가 된다.
#
# 환경변수 (selftest 전용 — 평시엔 건드리지 않는다)
#   COLAB_SEAM_DIR      린트 대상 디렉터리 (기본: contracts/seams)
#   COLAB_CONTRACTS_DIR 도구·룰셋이 있는 contracts 루트 (기본: contracts/)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTRACTS="${COLAB_CONTRACTS_DIR:-$REPO_ROOT/contracts}"
SEAM_DIR="${COLAB_SEAM_DIR:-$CONTRACTS/seams}"
RULESET="$CONTRACTS/.spectral.yaml"
SPECTRAL="$CONTRACTS/node_modules/.bin/spectral"

red() { echo "::error::contract-lint red — $*"; exit 1; }

[ -f "$RULESET" ] || red "룰셋이 없다: contracts/.spectral.yaml"

# ── 도구 확보 ────────────────────────────────────────────────────────────────
# 버전은 contracts/package.json + package-lock.json 이 고정한다. npx 최신 끌어오기 금지.
if [ ! -x "$SPECTRAL" ]; then
  echo "spectral 미설치 — contracts/package-lock.json 기준으로 설치를 시도한다."
  if ! (cd "$CONTRACTS" && npm ci --no-audit --no-fund >/dev/null 2>&1); then
    red "spectral 을 설치하지 못했다 (네트워크/npm 실패). 검사를 못 한 것은 통과가 아니다.
   → 온라인에서 'npm ci --prefix contracts' 를 한 번 돌린 뒤 재실행한다."
  fi
fi
[ -x "$SPECTRAL" ] || red "spectral 바이너리가 여전히 없다: contracts/node_modules/.bin/spectral"

# ── 대상 수집 ────────────────────────────────────────────────────────────────
mapfile -t SPECS < <(find "$SEAM_DIR" -maxdepth 2 -type f \
  \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) 2>/dev/null | sort)

if [ "${#SPECS[@]}" -eq 0 ]; then
  red "seam 계약이 0건이다 ($SEAM_DIR).
   D2 는 seam OpenAPI 3종(frontend-core · core-viz · core-ai)을 동결하는 WU다.
   대상이 없는 계약 게이트를 green 으로 세는 것이 곧 green-by-skip 이다."
fi

echo "# 대상 ${#SPECS[@]}건 — $(cd "$REPO_ROOT" && printf '%s ' "${SPECS[@]#$REPO_ROOT/}")"
# --fail-severity=warn : 룰셋이 warn 으로 남겨 둔 spectral:oas 기본 룰도 red 로 센다.
#   seam 은 동결 대상이라 "경고인 채로 머무는 계약"이라는 상태가 없다.
"$SPECTRAL" lint --ruleset "$RULESET" --fail-severity=warn --display-only-failures "${SPECS[@]}"
rc=$?
[ $rc -eq 0 ] || red "spectral 위반 (exit $rc)"
echo "contract-lint green — seam ${#SPECS[@]}건, 룰 위반 0."
