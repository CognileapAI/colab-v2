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

# ── 일회용 postgres 의 **선언된 동시성 한도** ────────────────────────────────
# 왜 있는가: `gates/run.sh all -j N` 은 DB 를 쓰는 게이트를 여럿 동시에 띄운다. 컨테이너 생성은
#   도커 데몬의 **공유 자원**(네트워크 엔드포인트·iptables·스토리지 드라이버)을 거치고, 그 자리의
#   실패는 게이트 내용과 무관하게 red 를 만든다 — 검사기가 아니라 **환경이 낸 red** 다.
#   그래서 병렬도를 낮추는 대신(그건 결함을 감추는 것이다) **이 자원만** 한도를 선언한다.
#   게이트 목록·검사 내용·판정 기준은 한 글자도 바뀌지 않는다. 바뀌는 것은 **착수 시각뿐**이다.
#
# ⚠ 슬롯을 못 얻으면 **red 다.** 기다렸다 건너뛰거나 재시도해서 green 을 만드는 경로는 없다
#   (`CLAUDE.md §4` — 못 돈 것을 통과로 세지 않는다). 무엇이 없었는지도 함께 적는다.
#
#   COLAB_PG_MAX_CONCURRENT  동시 컨테이너 수 (기본 4)
#   COLAB_PG_SLOT_WAIT       슬롯 대기 상한 초 (기본 900). 넘기면 red.
PG_SLOT_FD=""
PG_SLOT_DIR="${COLAB_PG_SLOT_DIR:-${TMPDIR:-/tmp}/colab-v2-gatepg-slots}"

pg_slot_acquire() { # $1=게이트 이름 → 0=획득 / 1=red
  local gate="$1"
  local max="${COLAB_PG_MAX_CONCURRENT:-4}" wait_s="${COLAB_PG_SLOT_WAIT:-900}" i
  [ "$max" -ge 1 ] 2>/dev/null || max=1
  command -v flock >/dev/null 2>&1 || return 0   # flock 이 없으면 한도를 걸지 않는다(검사는 그대로 돈다)
  mkdir -p "$PG_SLOT_DIR" 2>/dev/null || return 0
  local deadline=$(( $(date +%s) + wait_s ))
  while :; do
    for (( i = 0; i < max; i++ )); do
      exec {PG_SLOT_FD}>"$PG_SLOT_DIR/slot-$i" 2>/dev/null || { PG_SLOT_FD=""; return 0; }
      if flock -n "$PG_SLOT_FD"; then return 0; fi
      eval "exec ${PG_SLOT_FD}>&-"; PG_SLOT_FD=""
    done
    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "::error::$gate red — 일회용 postgres 동시성 슬롯(${max}개)을 ${wait_s}초 안에 얻지 못했다.
   **검사를 못 돈 것은 통과가 아니다** — 무엇이 없었나: 실행 슬롯. 한도는 COLAB_PG_MAX_CONCURRENT 로 선언된다."
      return 1
    fi
    sleep 1
  done
}

pg_slot_release() {
  [ -n "$PG_SLOT_FD" ] || return 0
  eval "exec ${PG_SLOT_FD}>&-" 2>/dev/null
  PG_SLOT_FD=""
}

pg_cleanup() {
  [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1
  PGC=""
  pg_slot_release
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

  pg_slot_acquire "$gate" || return 1
  trap pg_cleanup EXIT INT TERM

  PGC="colab_v2_gatepg_$$_${RANDOM}"
  local netarg=()
  [ -n "${COLAB_PG_NETWORK:-}" ] && netarg=(--network "$COLAB_PG_NETWORK")
  local runerr
  runerr="$(docker run -d --rm --name "$PGC" "${netarg[@]}" \
    --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
    -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust \
    "$PG_IMAGE" 2>&1 >/dev/null)" || {
      # ⚠ 종전에는 도커의 실패 사유를 통째로 버렸다 — red 만 남고 **왜** 가 없어
      #   병렬에서 간헐로 나는 red 를 사후에 귀속할 수 없었다. 사유를 그대로 싣는다.
      echo "::error::$gate red — 일회용 postgres 컨테이너를 띄우지 못했다.
   도커가 낸 말: ${runerr:-(출력 없음)}"; PGC=""; return 1; }

  local i
  for i in $(seq 1 60); do
    docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && return 0
    sleep 1
  done
  echo "::error::$gate red — postgres 가 60초 안에 뜨지 않았다.
   컨테이너 상태: $(docker inspect -f '{{.State.Status}}' "$PGC" 2>/dev/null || echo '(조회 실패)') · 호스트 부하: $(uptime | sed 's/.*load average/load average/')
   마지막 로그: $(docker logs --tail 3 "$PGC" 2>&1 | tr '\n' ' ' | cut -c1-300)
   ⚠ 이것은 **red 다.** 못 돈 검사를 통과로 세지 않는다. 동시성 한도는 COLAB_PG_MAX_CONCURRENT 로 선언된다."
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
