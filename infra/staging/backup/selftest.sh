#!/usr/bin/env bash
# fail-closed 증명 — "빈 백업이 성공으로 기록되지 않는다" 를 fixture 로 강제한다.
#
# 각 fixture 는 **반드시 RED 를 내야 한다.** 하나라도 GREEN 이면 이 셀프테스트가 실패한다.
# 8주간 빈 백업을 성공으로 기록한 가드(DEPLOY-CURRENT §8)가 여기서 재현·차단된다.
#
# F1~F5 는 docker 없이 돈다. F6 은 docker 가 있을 때만 돈다(없으면 SKIP 이 아니라 목록에서 빠졌다고 알린다).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
W="$(mktemp -d)"; trap 'rm -rf "$W"; docker rm -f d1_pg_selftest >/dev/null 2>&1 || true' EXIT
BAD=0; RAN=0

expect_red() { # $1=이름  $2...=명령
  local name="$1"; shift
  RAN=$((RAN+1))
  echo "──────── $name"
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  echo "$out" | sed 's/^/    /'
  if [ $rc -ne 0 ]; then
    echo "  → 기대대로 RED (exit $rc)"
  else
    echo "  → ✗ GREEN 이 나왔다. fail-closed 아님."; BAD=$((BAD+1))
  fi
}

# 정상본을 하나 만들어 둔다 — "검사기가 아무거나 red 로 만드는 것" 이 아님을 보이는 대조군.
GOOD="$W/good.sql.gz"
{ for i in $(seq 1 20); do echo "CREATE TABLE t$i (a int);"; done
  echo "COPY t1 (a) FROM stdin;"; for i in $(seq 1 50); do echo "$i"; done; echo '\.'
  head -c 60000 /dev/urandom | base64 | sed 's/^/-- /'; } | gzip -c > "$GOOD"

echo "════ 대조군 (RED 가 아니어야 한다)"
if "$HERE/verify-artifact.sh" "$GOOD" >/dev/null 2>&1; then
  echo "  대조군 GREEN — 검사기는 정상본을 통과시킨다"
else
  echo "  ✗ 대조군이 RED 다. 검사기가 무조건 red 를 내고 있다 — 증명이 성립하지 않는다"
  "$HERE/verify-artifact.sh" "$GOOD" | sed 's/^/    /'
  BAD=$((BAD+1))
fi

echo; echo "════ fixture — 전부 RED 여야 한다"

# F1 0바이트 산출물
: > "$W/f1.sql.gz"
expect_red "F1 0바이트 산출물" "$HERE/verify-artifact.sh" "$W/f1.sql.gz"

# F2 빈 gzip (20바이트) — PoC 사건의 실물 형태
printf '' | gzip -c > "$W/f2.sql.gz"
expect_red "F2 빈 gzip 20바이트 (2026-07 사건의 실물 형태)" "$HERE/verify-artifact.sh" "$W/f2.sql.gz"

# F3 파일은 있고 크기도 있으나 테이블·행이 없다
{ echo "-- PostgreSQL database dump"; for i in $(seq 1 200); do echo "SET statement_timeout = 0;"; done; } | gzip -c > "$W/f3.sql.gz"
expect_red "F3 크기는 있으나 테이블·행이 없다" "$HERE/verify-artifact.sh" "$W/f3.sql.gz"

# F4 스키마만 있고 데이터 행이 0 — "구조는 왔는데 내용이 없다"
{ for i in $(seq 1 20); do echo "CREATE TABLE t$i (a int);"; done
  echo "COPY t1 (a) FROM stdin;"; echo '\.'; } | gzip -c > "$W/f4.sql.gz"
expect_red "F4 테이블 20개 · 데이터 행 0" "$HERE/verify-artifact.sh" "$W/f4.sql.gz"

# F5 절단된 gzip
head -c $(( $(wc -c < "$GOOD") / 2 )) "$GOOD" > "$W/f5.sql.gz"
expect_red "F5 절단·손상 gzip" "$HERE/verify-artifact.sh" "$W/f5.sql.gz"

# F6 백업 단계가 non-zero 로 죽었는데 이전 성공본이 남아 있다
#    → 최종 경로에 새 파일이 생기면 안 되고, 남은 옛 파일은 신선도(C6)에서 red 여야 한다.
mkdir -p "$W/stale"
cp "$GOOD" "$W/stale/platform-old.sql.gz"; touch -d '8 days ago' "$W/stale/platform-old.sql.gz"
cat > "$W/stale.env" <<CFG
COLAB_BACKUP_TARGET=postgres
COLAB_BACKUP_PG_CONTAINER=d1_does_not_exist
COLAB_BACKUP_PG_DB=colab
COLAB_BACKUP_PG_USER=postgres
COLAB_BACKUP_DIR=$W/stale
CFG
expect_red "F6a 덤프가 non-zero 로 죽었다 (backup.sh 는 성공하지 않는다)" \
  env COLAB_BACKUP_CONFIG="$W/stale.env" "$HERE/backup.sh"
NEWCNT=$(ls -1 "$W/stale"/platform-*.sql.gz 2>/dev/null | grep -cv 'platform-old' || true)
RAN=$((RAN+1))
echo "──────── F6b 실패 후 최종 경로에 새 산출물이 생기지 않았다"
if [ "$NEWCNT" -eq 0 ] && [ -z "$(ls -A "$W/stale"/.inflight-* 2>/dev/null)" ]; then
  echo "  → 기대대로: 새 파일 0개 · inflight 잔해 0개"
else
  echo "  → ✗ 실패했는데 산출물이 남았다"; BAD=$((BAD+1))
fi
expect_red "F6c 남은 옛 성공본은 '오늘의 백업'이 아니다 (신선도 red)" \
  env COLAB_BACKUP_CONFIG="$W/stale.env" "$HERE/verify-artifact.sh" "$W/stale/platform-old.sql.gz"

# F7 대상이 붙지 않은 상태를 성공으로 기록하지 않는다
cat > "$W/none.env" <<'CFG'
COLAB_BACKUP_TARGET=none
CFG
expect_red "F7 대상 미연결(TARGET=none) 을 성공으로 기록하지 않는다" \
  env COLAB_BACKUP_CONFIG="$W/none.env" "$HERE/backup.sh"

# F8 복원은 exit 0 인데 DB 가 비었다 — "성공한 빈 복원"
if command -v docker >/dev/null 2>&1; then
  docker rm -f d1_pg_selftest >/dev/null 2>&1 || true
  # PGDATA 를 tmpfs 로 둔다 — 이 WSL 호스트에서 기본 볼륨은 initdb 의 chmod 가 막힌다.
  # 리허설 인스턴스는 어차피 일회용이므로 메모리 위가 맞다.
  docker run -d --name d1_pg_selftest --tmpfs /pgdata:rw,size=512m -e PGDATA=/pgdata/db \
    -e POSTGRES_PASSWORD=selftest -e POSTGRES_DB=colab "${COLAB_REHEARSAL_PG_IMAGE:-postgres:16-alpine}" >/dev/null
  for _ in $(seq 60); do docker exec d1_pg_selftest pg_isready -U postgres -d colab >/dev/null 2>&1 && break; sleep 1; done
  # 스키마만 넣고 데이터는 넣지 않는다 = psql 은 exit 0 으로 끝난다
  docker exec -i d1_pg_selftest psql -q -v ON_ERROR_STOP=1 -U postgres -d colab < "$REPO/db/platform/schema.sql" >/dev/null
  echo "  (참고: 복원 명령 자체는 exit 0 이었다)"
  expect_red "F8 복원 성공(exit 0) · 그러나 DB 가 비었다" \
    env COLAB_BACKUP_CONFIG="$W/none.env" "$HERE/verify-restore.sh" d1_pg_selftest colab postgres "$HERE/expected-counts.tsv"
  docker rm -f d1_pg_selftest >/dev/null
else
  echo "──────── F8 건너뜀 — docker 없음. 이 fixture 는 실행되지 않았다(증명 미완)"; BAD=$((BAD+1))
fi

echo
if [ "$BAD" -eq 0 ]; then
  echo "셀프테스트 GREEN — fixture $RAN 건 전부 기대대로 RED"
  exit 0
else
  echo "셀프테스트 RED — $BAD 건이 fail-closed 가 아니다"
  exit 1
fi
