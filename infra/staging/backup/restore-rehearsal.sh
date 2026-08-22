#!/usr/bin/env bash
# 복원 리허설 — **실 staging 백업**을 일회용 인스턴스에 복원해 내용을 대조한다.
#
# roundtrip.sh 와의 차이: 저쪽은 씨앗을 심은 리허설 원본을 쓴다. 여기는 실 staging 에서
# 방금 뜬 산출물을 쓴다. 살아 있는 DB 는 **읽기만** 한다 — 복원은 언제나 일회용 인스턴스에만 한다.
#
# 만드는 컨테이너: is3_pg_<프로파일>. 호스트 포트를 열지 않고, 끝나면 지운다.
# 종료코드 0 = 모든 프로파일에서 테이블 수·테이블별 행 수·총 행 수가 일치
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
load_config
[ "$COLAB_BACKUP_TARGET" = "postgres" ] || die "대상 미연결 — 리허설할 백업이 없다"
SRC_CT="${COLAB_BACKUP_PG_CONTAINER:?컨테이너 경유 설정이 필요하다}"
U="${COLAB_BACKUP_PG_USER:?}"
IMG="${COLAB_REHEARSAL_PG_IMAGE:-postgres:16-alpine}"
W="$(mktemp -d)"
MADE=""
cleanup() { for c in $MADE; do docker rm -f "$c" >/dev/null 2>&1 || true; done; rm -rf "$W"; }
trap cleanup EXIT

BAD=0
for P in $(backup_profiles); do
  DB="$(profile_db "$P")"; DST="is3_pg_$P"
  echo "════════ 프로파일 $P (db=$DB)"
  ART="$(ls -1t "$COLAB_BACKUP_DIR/$P"-*.sql.gz 2>/dev/null | head -1)"
  [ -n "$ART" ] || { echo "  산출물이 없다"; BAD=$((BAD+1)); continue; }
  echo "  산출물: $(basename "$ART") ($(wc -c < "$ART") B)"

  # ① 살아 있는 staging 에서 기대치를 뜬다 — 읽기 전용.
  docker exec "$SRC_CT" psql -U "$U" -d "$DB" -At -F$'\t' \
    -c "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname" > "$W/$P.expected.tsv"
  SRC_TABLES="$(docker exec "$SRC_CT" psql -U "$U" -d "$DB" -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
  echo "  원본 테이블 $SRC_TABLES 개 · 행 합계 $(awk -F'\t' '{s+=$2} END{print s+0}' "$W/$P.expected.tsv")"

  # ② 일회용 인스턴스에 복원. 살아 있는 DB 에는 절대 쓰지 않는다.
  docker rm -f "$DST" >/dev/null 2>&1 || true
  docker run -d --name "$DST" --tmpfs /pgdata:rw,size=512m -e PGDATA=/pgdata/db \
    -e POSTGRES_PASSWORD=rehearsal -e POSTGRES_DB="$DB" "$IMG" >/dev/null
  MADE="$MADE $DST"
  for _ in $(seq 60); do docker exec "$DST" pg_isready -U postgres -d "$DB" >/dev/null 2>&1 && break; sleep 1; done
  T0=$(date +%s)
  if ! gunzip -c "$ART" | docker exec -i "$DST" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" >/dev/null; then
    echo "  복원 실패"; BAD=$((BAD+1)); docker rm -f "$DST" >/dev/null; continue
  fi
  T1=$(date +%s)
  echo "  복원 소요 $((T1-T0)) 초"

  # ③ 대조 — exit 0 을 성공으로 보지 않는다. 내용을 센다.
  COLAB_BACKUP_MIN_TABLES="$(profile_min_tables "$P")" \
  COLAB_BACKUP_MIN_ROWS="$(profile_min_rows "$P")" \
    "$HERE/verify-restore.sh" "$DST" "$DB" postgres "$W/$P.expected.tsv" || BAD=$((BAD+1))

  DST_TABLES="$(docker exec "$DST" psql -U postgres -d "$DB" -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
  if [ "$DST_TABLES" = "$SRC_TABLES" ]; then echo "  PASS  테이블 수 원본=복원 $DST_TABLES"; else echo "  FAIL  테이블 수 원본 $SRC_TABLES ≠ 복원 $DST_TABLES"; BAD=$((BAD+1)); fi

  # ④ 내용 다이제스트 — 행 수만 보면 값이 뒤바뀐 복원도 통과한다.
  #     테이블마다 COPY 로 본문을 뽑아 정렬 후 md5. 살아 있는 쪽은 읽기만 한다.
  digest() { # $1=컨테이너 $2=사용자
    local t
    while IFS=$'\t' read -r t _; do
      [ -n "$t" ] || continue
      printf '%s\n' "$t"
      docker exec "$1" psql -U "$2" -d "$DB" -At -c "COPY (SELECT * FROM \"$t\") TO STDOUT" 2>/dev/null | LC_ALL=C sort
    done < "$W/$P.expected.tsv" | md5sum | awk '{print $1}'
  }
  D_SRC="$(digest "$SRC_CT" "$U")"; D_DST="$(digest "$DST" postgres)"
  if [ "$D_SRC" = "$D_DST" ]; then echo "  PASS  내용 다이제스트 일치 $D_SRC"; else echo "  FAIL  내용 다이제스트 원본 $D_SRC ≠ 복원 $D_DST"; BAD=$((BAD+1)); fi

  # ⑤ K2 시드 22 행은 이름으로 못 박아 따로 센다 (ai 프로파일).
  if [ "$P" = "ai" ]; then
    K2="$(docker exec "$DST" psql -U postgres -d "$DB" -At -c "SELECT (SELECT count(*) FROM d9_method_term)+(SELECT count(*) FROM d9_place_alias)+(SELECT count(*) FROM d9_topic_synonym)")"
    if [ "$K2" = "22" ]; then echo "  PASS  K2 시드 22 행 복원됨"; else echo "  FAIL  K2 시드 $K2 행 (기대 22)"; BAD=$((BAD+1)); fi
  fi
  docker rm -f "$DST" >/dev/null; MADE="${MADE/ $DST/}"
done

echo
if [ "$BAD" -eq 0 ]; then echo "복원 리허설 GREEN"; exit 0; fi
echo "복원 리허설 RED — $BAD 건 불일치"; exit 1
