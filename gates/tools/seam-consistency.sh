#!/usr/bin/env bash
# seam-consistency 게이트 (WU-D2c §2-13 · 〈61〉-㉠·㉡) — seam ↔ 이벤트 계약의 **사이**를 본다.
#
# 왜 새 게이트인가: contract-lint(spectral)·contract-breaking(oasdiff)은 contracts/seams/** 만,
#   event-lint·event-breaking 은 contracts/events/** 만 본다. 둘 사이를 보는 게이트가 없어서
#   DR-7(위임 산문 오배정 — 업로드 세계가 FE 표면에서 통째로 사라짐)이 살아남았다.
#
# 검사 4종 — G-e(산문 위임 참조) · G-b(source const 능력 주장) · ㉠(정본 근거 대조) · ㉡(E-04 흐름 완주).
# G-a(식별자 도달성)·G-c(짝 op 대칭)·G-d(공유 값 집합 재선언)는 미구현이다 — 감추지 않는다
# (D2c §2-13 최소 채택선 = G-e·G-b. 미구현 사실은 gates/README.md 에도 적혀 있다).
#
# 원칙 (CLAUDE.md §4): 도구 부재·대상 0건·fixture 부재는 전부 red. skip 없음.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENGINE="$REPO_ROOT/gates/tools/seam_consistency.py"

red() { echo "::error::seam-consistency red — $*"; exit 1; }

command -v python3 >/dev/null 2>&1 || red "python3 가 없다. 검사를 못 한 것은 통과가 아니다."
[ -f "$ENGINE" ] || red "검사 엔진이 없다: gates/tools/seam_consistency.py"

exec python3 "$ENGINE" "$@"
