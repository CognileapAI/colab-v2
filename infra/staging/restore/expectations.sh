#!/usr/bin/env bash
# 복원 기대치를 **짝 덤프에서 읽는다.**
#
# ⭑ **이 스크립트가 있는 이유 = `R1-RESTORE-DRAFT §4.6-②` 의 규칙이다.**
#   「129 · 12 · 6」은 **상수가 아니라 복원 시점의 기대치**다. 실제로 여러 문서가 계보 간선을
#   「5」로 적고 있었고 실측은 6 이었다(`〈159〉`) — **상수를 박아 두면 문서가 낡는 만큼 오라클이 틀린다.**
#   그래서 어떤 숫자도 이 파일에 없다. 되돌릴 덤프를 읽어 그 회차의 기대치를 만든다.
#
# 사용: expectations.sh <덤프.sql.gz> <테이블> [테이블 …]
# 출력: `<테이블><TAB><행수>` 줄 목록 (verify-restore.sh 의 기대치 파일 형식과 같다)
# 종료코드: 0 = 전건 읽었다 / 1 = 하나라도 COPY 블록이 없다(=지어내지 않고 실패한다)
set -uo pipefail
DUMP="${1:-}"; shift || true
[ -n "$DUMP" ] && [ $# -gt 0 ] || { echo "사용: expectations.sh <덤프.sql.gz> <테이블> [테이블 …]" >&2; exit 2; }
[ -f "$DUMP" ] || { echo "덤프를 찾지 못했다: $(basename "$DUMP")" >&2; exit 1; }

TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
gunzip -c "$DUMP" > "$TMP" 2>/dev/null || { echo "덤프를 열지 못했다" >&2; exit 1; }

BAD=0
for T in "$@"; do
  OUT="$(awk -v tbl="$T" '
    BEGIN{incopy=0; n=0; found=0}
    incopy==0 && $0 ~ ("^COPY (public\\.)?\"?" tbl "\"? ") { found=1; incopy=1; next }
    incopy==1 && $0=="\\." { incopy=0; next }
    incopy==1 { n++ }
    END{ printf("%d\t%d\n", found, n) }' "$TMP")"
  F="$(printf '%s' "$OUT" | cut -f1)"; N="$(printf '%s' "$OUT" | cut -f2)"
  if [ "$F" != "1" ]; then
    echo "  ⚠ $T — COPY 블록이 덤프에 없다. **기대치를 지어내지 않는다**" >&2
    BAD=$((BAD+1)); continue
  fi
  printf '%s\t%s\n' "$T" "$N"
done
exit $(( BAD > 0 ))
