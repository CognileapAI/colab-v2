#!/usr/bin/env bash
# 백업 → 파괴 → 복원 왕복 실증 (리허설).
#
# **대상은 일회용 리허설 인스턴스다. 살아 있는 staging 이 아니다** —
# staging 에는 아직 데이터 저장소가 없다(infra/staging/README.md).
# 그래도 경로 전체(덤프·검사·보관·복원·대조)를 실제로 한 번 통과시켜 둔다.
#
# 만드는 컨테이너: d1_pg_src / d1_pg_dst — 호스트 포트를 열지 않고, 끝나면 지운다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
. "$HERE/lib.sh"

IMG="${COLAB_REHEARSAL_PG_IMAGE:-postgres:16-alpine}"
SRC=d1_pg_src; DST=d1_pg_dst
WORK="$(mktemp -d)"
export COLAB_BACKUP_CONFIG="$WORK/rehearsal.env"
cat > "$COLAB_BACKUP_CONFIG" <<CFG
COLAB_BACKUP_TARGET=postgres
COLAB_BACKUP_PG_CONTAINER=$SRC
COLAB_BACKUP_PG_DB=colab
COLAB_BACKUP_PG_USER=postgres
COLAB_BACKUP_DIR=$WORK/backups
COLAB_BACKUP_MIN_TABLES=20
COLAB_BACKUP_MIN_ROWS=1
CFG

cleanup() { docker rm -f "$SRC" "$DST" >/dev/null 2>&1 || true; }
trap 'cleanup' EXIT

up() { # $1=name
  docker rm -f "$1" >/dev/null 2>&1 || true
  # PGDATA 를 tmpfs 에 둔다 — 이 WSL 호스트에서 기본 볼륨은 initdb 의 chmod 가 막힌다.
  # 일회용 리허설이라 메모리 위가 맞다. 호스트 포트는 열지 않는다.
  docker run -d --name "$1" --tmpfs /pgdata:rw,size=512m -e PGDATA=/pgdata/db \
    -e POSTGRES_PASSWORD=rehearsal -e POSTGRES_DB=colab "$IMG" >/dev/null
  for _ in $(seq 60); do
    docker exec "$1" pg_isready -U postgres -d colab >/dev/null 2>&1 && return 0
    sleep 1
  done
  die "$1 기동 실패"
}

echo "== 1. 원본 인스턴스 생성 · 스키마 정본 적용 · 씨앗 적재"
up "$SRC"
docker exec -i "$SRC" psql -q -v ON_ERROR_STOP=1 -U postgres -d colab < "$REPO/db/platform/schema.sql" >/dev/null || die "스키마 적용 실패"
docker exec -i "$SRC" psql -q -v ON_ERROR_STOP=1 -U postgres -d colab < "$HERE/seed.sql" >/dev/null || die "씨앗 적재 실패"
echo "-- 백업 전 행 수"
docker exec -i "$SRC" psql -U postgres -d colab -At -F$'\t' -f - < "$HERE/count-query.sql" | tee "$WORK/before.tsv"
diff <(sort "$HERE/expected-counts.tsv") <(sort "$WORK/before.tsv") >/dev/null || die "씨앗 적재 결과가 기대치와 다르다"
BEFORE_DIGEST="$(docker exec -i "$SRC" psql -U postgres -d colab -At -f - < "$HERE/content-digest.sql")"
echo "-- 내용 다이제스트(전): $BEFORE_DIGEST"

echo "== 2. 백업"
"$HERE/backup.sh" || die "백업 실패"
ART="$(ls -1t "$WORK"/backups/platform-*.sql.gz | head -1)"
echo "산출물: $(basename "$ART") ($(wc -c < "$ART") B)"

echo "== 3. 원본 파괴"
docker rm -f "$SRC" >/dev/null
echo "$SRC 제거됨"

echo "== 4. 새 인스턴스에 복원"
up "$DST"
gunzip -c "$ART" | docker exec -i "$DST" psql -q -v ON_ERROR_STOP=1 -U postgres -d colab >/dev/null || die "복원 실패"

echo "== 5. 대조 — 행 수"
"$HERE/verify-restore.sh" "$DST" colab postgres "$HERE/expected-counts.tsv" || die "복원 검사 RED"

echo "== 6. 대조 — 내용 다이제스트"
AFTER_DIGEST="$(docker exec -i "$DST" psql -U postgres -d colab -At -f - < "$HERE/content-digest.sql")"
echo "-- 내용 다이제스트(후): $AFTER_DIGEST"
[ "$BEFORE_DIGEST" = "$AFTER_DIGEST" ] || die "다이제스트 불일치 — 행 수는 같으나 내용이 다르다"
echo "다이제스트 일치"

echo "== 7. 정리"
docker rm -f "$DST" >/dev/null; trap - EXIT
rm -rf "$WORK"
echo "왕복 실증 GREEN"
