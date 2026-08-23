#!/usr/bin/env bash
# generated-up-to-date 게이트 — 생성물이 계약보다 낡음을 잡는다 (contracts/README.md 규칙 3·4).
#
# 정본 = contracts/codegen/manifest.toml (생성물 등기부). 엔트리마다 재생성해 byte-diff 하고,
# 등기부 밖의 「generated」 마커 파일(codegen 통제 밖 자칭 생성물)도 red 다.
# 빈 등기부·등기부 부재·도구 부재는 전부 red (CLAUDE.md §4 green-by-skip 금지).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENGINE="$REPO_ROOT/gates/tools/generated_up_to_date.py"

red() { echo "::error::generated-up-to-date red — $*"; exit 1; }

command -v python3 >/dev/null 2>&1 || red "python3 가 없다. 검사를 못 한 것은 통과가 아니다."
[ -f "$ENGINE" ] || red "검사 엔진이 없다: gates/tools/generated_up_to_date.py"

exec python3 "$ENGINE" "$@"
