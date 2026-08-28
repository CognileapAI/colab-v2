#!/usr/bin/env bash
# generated-up-to-date 의 fail-closed 증명 (CLAUDE.md §4).
#
# seam-consistency-selftest.sh 와 같은 방식 — expect(기대,라벨,명령) 한 줄에 케이스 하나.
# fixture 는 gates/fixtures/generated/** 에 고정돼 있고 실제 contracts/**·frontend/** 에는 쓰지 않는다.
# 기준 green 케이스도 fixture 다 — 레포 실물은 재생성 파이프라인(다른 레인 소유)의 상태에 따라
# 정당하게 red 일 수 있어, selftest 가 레포 상태에 볼모잡히면 안 되기 때문이다 (db-selftest 와 같은 이유).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATE="$REPO_ROOT/gates/tools/generated-up-to-date.sh"
FIX="$REPO_ROOT/gates/fixtures/generated"
FAILURES=()

expect() { # $1=기대(green|red) $2=라벨 $3.. = 실행할 명령
  local want="$1" label="$2"; shift 2
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  local got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$want" ]; then
    echo "[selftest] $label → $got OK"
  else
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
  fi
}

run() { # $1=fixture 디렉터리 — 등기부·루트·스캔 범위를 fixture 로 고정
  local d="$FIX/$1"
  env COLAB_GEN_MANIFEST="$d/manifest.toml" COLAB_GEN_ROOT="$d" COLAB_GEN_SCAN_ROOTS="out" "$GATE"
}

# ── 기준 케이스 ──────────────────────────────────────────────────────────────
expect green "기준: 재생성 = 커밋본 (마커 파일 등기됨)" run green

# ── red — 낡음·손수정·부재 ───────────────────────────────────────────────────
expect red "stale: source 개정 후 재생성 안 함"                 run red/stale
expect red "hand-edit: 생성물 손수정 (CLAUDE.md 규칙 7 위반)"    run red/hand-edit
expect red "missing-output: 등기됐는데 커밋된 생성물 없음"        run red/missing-output
expect red "missing-source: source 계약 파일 없음"               run red/missing-source

# ── red — 등기부 자체의 fail-closed ─────────────────────────────────────────
expect red "empty-manifest: 엔트리 0건 = red (빈 등기부 ≠ green)" run red/empty
expect red "missing-manifest: 등기부 부재 = red" \
  env COLAB_GEN_MANIFEST="$FIX/does-not-exist/manifest.toml" COLAB_GEN_ROOT="$FIX" COLAB_GEN_SCAN_ROOTS="out" "$GATE"

# ── red — 통제 밖 생성물 · 생성 실패 ─────────────────────────────────────────
expect red "unregistered: 등기부 밖 자칭 생성물 (@generated 마커)" run red/unregistered
expect red "failing-gen: 재생성 명령 실패는 skip 이 아니라 red"    run red/failing-gen

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::generated-selftest red — ${#FAILURES[@]}건 실패: ${FAILURES[*]}"
  exit 1
fi
echo "generated-selftest green — 9 케이스 전부 기대대로 (green 1 · red 8)."
