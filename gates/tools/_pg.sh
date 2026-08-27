#!/usr/bin/env bash
# DB 게이트용 일회용 postgres 확보. source 해서 쓴다.
#
# 원칙 (CLAUDE.md §4): 도커가 없거나 컨테이너가 안 뜨면 **skip 이 아니라 red** 다.
#   "DB 가 없어서 검사를 못 했다"를 통과로 세는 것이 정확히 v1 의 실패다.
#
# 이 호스트에는 staging 컨테이너(colab_v2_staging_*)가 돈다. 절대 건드리지 않는다:
#   - 컨테이너 이름은 colab_v2_gatepg_<pid>_<rand> — staging 접두사와 겹치지 않는다
#   - **포트를 하나도 publish 하지 않는다.** 모든 질의는 docker exec 로 컨테이너 안에서 돈다 → 포트 충돌이 원천적으로 없다
#   - PGDATA 는 tmpfs. 호스트 파일시스템에 아무것도 남기지 않는다 (WSL 바인드 마운트의 chmod 제약도 피한다)
#   - trap 으로 반드시 지운다
#
# 환경변수
#   COLAB_PG_IMAGE   기본 postgres:16-alpine
#   COLAB_PG_FORCE_UNAVAILABLE=1  selftest 전용 — 도커 부재를 흉내낸다
#   COLAB_PG_NETWORK  일회용 컨테이너를 붙일 도커 네트워크(기본: 없음 = 기본 브리지).
#     적용 DB 가 다른 컴포즈 네트워크의 서비스 이름으로만 닿을 때 쓴다(schema-diff 를 staging 에 댈 때).
#     **포트는 여전히 하나도 publish 하지 않는다** — 네트워크에 참가할 뿐이다.

PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
PGC=""

pg_cleanup() {
  [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1
  PGC=""
}

# $1 = 게이트 이름(메시지용). 성공하면 $PGC 가 컨테이너 이름이다.
pg_start() {
  local gate="$1"
  if [ "${COLAB_PG_FORCE_UNAVAILABLE:-0}" = "1" ]; then
    echo "::error::$gate red — 일회용 postgres 를 띄울 수 없다(주입된 부재). 검사를 못 한 것은 통과가 아니다."
    return 1
  fi
  command -v docker >/dev/null 2>&1 || {
    echo "::error::$gate red — docker 가 없다. DB 가 필요한 게이트를 DB 없이 green 으로 세지 않는다 (CLAUDE.md §4).
   → CI 에서는 postgres 서비스 컨테이너를 띄우거나 docker 를 쓸 수 있게 한다."; return 1; }
  docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 || {
    echo "::error::$gate red — 이미지 $PG_IMAGE 를 확보하지 못했다(네트워크/레지스트리). skip 아님."; return 1; }

  PGC="colab_v2_gatepg_$$_${RANDOM}"
  local netarg=()
  [ -n "${COLAB_PG_NETWORK:-}" ] && netarg=(--network "$COLAB_PG_NETWORK")
  docker run -d --rm --name "$PGC" "${netarg[@]}" \
    --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
    -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust \
    "$PG_IMAGE" >/dev/null 2>&1 || {
      echo "::error::$gate red — 일회용 postgres 컨테이너를 띄우지 못했다."; PGC=""; return 1; }
  trap pg_cleanup EXIT INT TERM

  local i
  for i in $(seq 1 60); do
    docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && return 0
    sleep 1
  done
  echo "::error::$gate red — postgres 가 60초 안에 뜨지 않았다."
  pg_cleanup
  return 1
}

# psql 을 컨테이너 안에서 돌린다. $1=DB 이름, 나머지는 psql 인자.
pg_psql() { local db="$1"; shift; docker exec -i "$PGC" psql -U postgres -d "$db" -v ON_ERROR_STOP=1 "$@"; }

# 호스트의 .sql 파일을 컨테이너 안 DB 에 적용한다. $1=DB $2=파일
pg_apply() {
  local db="$1" f="$2"
  docker exec "$PGC" createdb -U postgres "$db" >/dev/null 2>&1 || return 1
  docker exec -i "$PGC" psql -U postgres -d "$db" -q -v ON_ERROR_STOP=1 < "$f"
}
