#!/usr/bin/env bash
# seam-consistency 의 fail-closed 증명 (CLAUDE.md §4 · WU-D2c §2-13).
#
# contract-selftest.sh · event-selftest.sh 와 **같은 방식**이다 — expect(기대,라벨,명령) 한 줄에
# 케이스 하나. red fixture 는 gates/fixtures/seam-consistency/red/** 에 고정돼 있고, 실제 계약
# 디렉터리(contracts/**)에는 한 글자도 쓰지 않는다. 두 번째 스타일을 발명하지 않는다.
#
# ⚠ ge-old-prose fixture 는 **개정 전 fe-core.yaml:13-16 위임 산문 원문**(C1 실행 기록 §7-3 보존분)
#   그대로다 — DR-7 의 실물이 red 를 내는 것이 이 게이트의 존재 증명이다 (D2c §3-3 오라클).
# fixture 는 자기 allow-list(gates/fixtures/seam-consistency/allowlist.toml)를 들고 다닌다 —
#   레포 allow-list 에 정당한 예외가 추가되면 기준 케이스가 깨지기 때문이다 (WU-D3b 와 같은 이유).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATE="$REPO_ROOT/gates/tools/seam-consistency.sh"
FIX="$REPO_ROOT/gates/fixtures/seam-consistency"
ALLOW="$FIX/allowlist.toml"
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

# ── 기준 케이스 — 현행(개정 후) 계약 위에서 검사 4종이 green ──────────────────
expect green "G-e: 현행 계약"            env COLAB_SC_ALLOWLIST="$ALLOW" "$GATE" --check ge
expect green "G-b: 현행 계약"            env COLAB_SC_ALLOWLIST="$ALLOW" "$GATE" --check gb
expect green "㉠: 현행 계약 (기준선 git HEAD)" env COLAB_SC_ALLOWLIST="$ALLOW" "$GATE" --check citation
expect green "㉡: 현행 계약 + E-04 fixture"   env COLAB_SC_ALLOWLIST="$ALLOW" "$GATE" --check flow

# ── G-e red — 산문 위임 참조 ─────────────────────────────────────────────────
expect red "G-e: 개정 전 fe-core.yaml:13-16 원문 (DR-7 실물 — 「이벤트/업로드 seam」)" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_SEAM_DIR="$FIX/red/ge-old-prose/seams" "$GATE" --check ge
expect red "G-e: 실재하지 않는 op(createGhostUpload)·파일(upload-seam.yaml) 참조" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_SEAM_DIR="$FIX/red/ge-ghost/seams" "$GATE" --check ge

# ── G-b red — const 능력 주장 ────────────────────────────────────────────────
expect red "G-b: source const core-api 인데 촉발 op 0건 (I-01·I-05)" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_SEAM_DIR="$FIX/red/gb-no-trigger/seams" \
      COLAB_SC_EVENTS_DIR="$FIX/red/gb-no-trigger/events" "$GATE" --check gb
expect red "G-b: 촉발 op 이 집계 루트(uploadId)를 다루지 않음" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_SEAM_DIR="$FIX/red/gb-no-root/seams" \
      COLAB_SC_EVENTS_DIR="$FIX/red/gb-no-root/events" "$GATE" --check gb

# ── ㉠ red — 정본 근거 대조 ──────────────────────────────────────────────────
expect red "㉠: 신설 op 의 근거 칸 공란 (description 없음, ㉠-1)" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_SEAM_DIR="$FIX/red/citation-empty/seams" \
      COLAB_SC_BASELINE="$FIX/red/citation-baseline" "$GATE" --check citation
expect red "㉠: 신설 op 에 인용도 [정본 무근거] 표기도 없음 (㉠-1)" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_SEAM_DIR="$FIX/red/citation-nocite/seams" \
      COLAB_SC_BASELINE="$FIX/red/citation-baseline" "$GATE" --check citation

# ── ㉡ red — 흐름 완주 ───────────────────────────────────────────────────────
expect red "㉡: 한 단계의 op 이 호출 불가능 (㉡-1)" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_FLOW_FIXTURE="$FIX/red/flow/missing-op.json" "$GATE" --check flow
expect red "㉡: 어느 단계도 생산하지 않은 식별자를 입력으로 요구 (㉡-2)" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_FLOW_FIXTURE="$FIX/red/flow/id-break.json" "$GATE" --check flow
expect red "㉡: fixture 부재는 skip 이 아니라 red" \
  env COLAB_SC_ALLOWLIST="$ALLOW" COLAB_SC_FLOW_FIXTURE="$FIX/red/flow/does-not-exist.json" "$GATE" --check flow

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::seam-consistency-selftest red — ${#FAILURES[@]}건 실패: ${FAILURES[*]}"
  exit 1
fi
echo "seam-consistency-selftest green — 13 케이스 전부 기대대로 (green 4 · red 9)."
