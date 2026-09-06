#!/usr/bin/env bash
# `merge-work-items.py` 가 **자동으로 푸는 자리**와 **충돌로 물러서는 자리**를 둘 다 증명한다.
#
# 왜 둘 다인가: 「병합이 됐다」만 재는 증명은 드라이버가 조용히 한쪽을 골라도 통과한다.
#   이 레포의 대표 실패형(검사기가 통과를 보고했는데 아무것도 검사하지 않은 것)과 같은 모양이다.
#   그래서 케이스 6개 중 3개는 **exit 1(충돌)** 이 기대값이다.
#
# 소요도 잰다 — 스펙 K 미검증 1 「572KB·140항목에서 실용 속도인지 → P-G 에서 실측」.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRV="$ROOT/dev-package/tools/merge-work-items.py"
TD="$(mktemp -d -t wim-selftest-XXXXXX)"
trap 'rm -rf "$TD"' EXIT
rc=0

blk() { # $1=id $2=상태 — 최소 형태의 WU 블록 한 개
  printf '  - id: %s\n    name: 항목 %s\n    status: %s\n\n' "$1" "$1" "$2"
}
head_() { printf '# 대장 머리말\n\nitems:\n'; }

run_case() { # $1=이름 $2=기대 종료코드 $3=O $4=A $5=B  (결과는 $4 에 남는다)
  local name="$1" want="$2" o="$3" a="$4" b="$5" got
  python3 "$DRV" "$o" "$a" "$b" >/dev/null 2>&1; got=$?
  if [ "$got" -eq "$want" ]; then
    echo "  ✓ $name — exit $got"
  else
    echo "  ✗ $name — 기대 exit $want, 실측 $got"; rc=1
  fi
}

ids_of() { grep -o '^  - id: .*' "$1" | sed 's/^  - id: //' | tr '\n' ' ' | sed 's/ $//'; }

echo "── merge-work-items selftest ────────────────────────────────"

# ⓐ 양쪽이 각자 끝에 새 블록을 덧붙였다 — **충돌이 아니다**
{ head_; blk R0 done; } > "$TD/a.O"
{ head_; blk R0 done; blk WU-X todo; } > "$TD/a.A"
{ head_; blk R0 done; blk WU-Y todo; } > "$TD/a.B"
run_case "ⓐ 양쪽 덧붙임" 0 "$TD/a.O" "$TD/a.A" "$TD/a.B"
if [ "$(ids_of "$TD/a.A")" = "R0 WU-X WU-Y" ]; then echo "     ↳ 순서 = R0 WU-X WU-Y (상대 신규가 끝에)"
else echo "  ✗ ⓐ 순서 — 실측 [$(ids_of "$TD/a.A")]"; rc=1; fi

# ⓑ 상대만 어떤 WU 를 고쳤다 → 고친 쪽을 취한다
{ head_; blk R0 todo; blk WU-X todo; } > "$TD/b.O"
{ head_; blk R0 todo; blk WU-X todo; } > "$TD/b.A"
{ head_; blk R0 todo; blk WU-X done; } > "$TD/b.B"
run_case "ⓑ 한쪽만 수정" 0 "$TD/b.O" "$TD/b.A" "$TD/b.B"
if grep -q 'status: done' "$TD/b.A"; then echo "     ↳ 상대 수정본을 취했다"
else echo "  ✗ ⓑ 상대 수정이 유실됐다"; rc=1; fi

# ⓒ 상대가 지웠고 우리는 안 건드렸다 → 삭제를 따른다
{ head_; blk R0 todo; blk WU-X todo; } > "$TD/c.O"
{ head_; blk R0 todo; blk WU-X todo; } > "$TD/c.A"
{ head_; blk R0 todo; }               > "$TD/c.B"
run_case "ⓒ 한쪽 삭제" 0 "$TD/c.O" "$TD/c.A" "$TD/c.B"
if [ "$(ids_of "$TD/c.A")" = "R0" ]; then echo "     ↳ 삭제를 따랐다"
else echo "  ✗ ⓒ 실측 [$(ids_of "$TD/c.A")]"; rc=1; fi

# ⓓ 같은 WU 를 양쪽이 **다르게** 고쳤다 → 충돌 (사람이 본다)
{ head_; blk R0 todo; } > "$TD/d.O"
{ head_; blk R0 done; } > "$TD/d.A"
{ head_; blk R0 blocked; } > "$TD/d.B"
run_case "ⓓ 같은 WU 상충" 1 "$TD/d.O" "$TD/d.A" "$TD/d.B"

# ⓔ 양쪽이 **같은 id** 를 새로 만들었다 → 결과가 중복이므로 충돌
{ head_; blk R0 todo; } > "$TD/e.O"
{ head_; blk R0 todo; blk WU-Z todo; } > "$TD/e.A"
{ head_; blk R0 todo; blk WU-Z done; } > "$TD/e.B"
run_case "ⓔ 같은 새 id 를 양쪽이 만듦" 1 "$TD/e.O" "$TD/e.A" "$TD/e.B"

# ⓕ 머리말을 양쪽이 다르게 고쳤다 → 충돌
{ head_; blk R0 todo; } > "$TD/f.O"
{ printf '# 우리 머리말\n\nitems:\n'; blk R0 todo; } > "$TD/f.A"
{ printf '# 상대 머리말\n\nitems:\n'; blk R0 todo; } > "$TD/f.B"
run_case "ⓕ 머리말 상충" 1 "$TD/f.O" "$TD/f.A" "$TD/f.B"

# ── 실물 대장으로 소요 측정 (스펙 K 미검증 1) ────────────────────────────────
LEDGER="$ROOT/dev-package/work-items.yaml"
if [ -f "$LEDGER" ]; then
  cp "$LEDGER" "$TD/real.O"
  cp "$LEDGER" "$TD/real.A"; printf '  - id: WU-LANE-A\n    name: 레인 A\n    status: todo\n\n' >> "$TD/real.A"
  cp "$LEDGER" "$TD/real.B"; printf '  - id: WU-LANE-B\n    name: 레인 B\n    status: todo\n\n' >> "$TD/real.B"
  t0=$(date +%s%N)
  python3 "$DRV" "$TD/real.O" "$TD/real.A" "$TD/real.B" >/dev/null 2>&1; got=$?
  t1=$(date +%s%N)
  ms=$(( (t1 - t0) / 1000000 ))
  n=$(grep -c '^  - id:' "$TD/real.A")
  if [ "$got" -eq 0 ] && [ "$n" -eq "$(( $(grep -c '^  - id:' "$LEDGER") + 2 ))" ]; then
    echo "  ✓ ⓖ 실물 대장 $(wc -c < "$LEDGER") B · 두 레인 덧붙임 → 항목 $n · ${ms}ms"
  else
    echo "  ✗ ⓖ 실물 대장 — exit $got · 항목 $n"; rc=1
  fi
fi

echo "── 계 : $([ "$rc" -eq 0 ] && echo green || echo red)"
exit "$rc"
