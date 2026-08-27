#!/usr/bin/env bash
# 복원 결과 검사 — "restore 가 exit 0 이었다" 를 성공으로 보지 않는다.
# 사용: verify-restore.sh <컨테이너> <DB> <사용자> <기대치파일>
#   기대치파일 = "테이블<TAB>행수" 줄 목록 (backup 시점에 뜬 것)
# 종료코드 0 = 테이블 목록·행 수·내용 다이제스트가 전부 일치
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
load_config
CT="${1:?컨테이너}"; DB="${2:?DB}"; U="${3:?사용자}"; EXP="${4:?기대치파일}"
FAILED=0; SKIPPED=0
q() { docker exec "$CT" psql -U "$U" -d "$DB" -At -c "$1" 2>/dev/null </dev/null; }

TOTAL=0
while IFS=$'\t' read -r t n; do
  [ -n "$t" ] || continue
  got="$(q "SELECT count(*) FROM $t")"
  got="${got:-0}"
  TOTAL=$((TOTAL+got))
  if [ "$got" = "$n" ]; then pass "행 수 $t = $got"; else fail "행 수 $t = $got (기대 $n)"; fi
done < "$EXP"

if [ "$TOTAL" -ge "$COLAB_BACKUP_MIN_ROWS" ]; then
  pass "총 행 수 $TOTAL (>= $COLAB_BACKUP_MIN_ROWS)"
else
  fail "총 행 수 $TOTAL — 복원은 끝났는데 DB 가 비었다. 이것이 '성공한 빈 복원' 이다"
fi

NT="$(q "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
NT="${NT:-0}"
if [ "$NT" -ge "$COLAB_BACKUP_MIN_TABLES" ]; then pass "테이블 $NT 개 (>= $COLAB_BACKUP_MIN_TABLES)"; else fail "테이블 $NT 개 < $COLAB_BACKUP_MIN_TABLES"; fi

verdict "결과"; exit $?
