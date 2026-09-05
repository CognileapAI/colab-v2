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

# ── 준비 실패(readiness) 를 판정 실패와 **가르는 자리** ──────────────────────
# 왜 있는가: DB 게이트의 red 는 두 가지 뜻을 겹쳐 갖고 있었다 —
#   ⑴ **검사 대상이 틀렸다**(판정 red · 고쳐야 할 결함) ⑵ **검사기가 아예 못 돌았다**(준비 red).
# 부하 아래에서 일회용 postgres 가 제때 뜨지 않으면 ⑵ 인데 출력만으로는 ⑴ 과 구분되지 않았고,
# 그 모호함이 이 레포의 **모든 측정값**을 신뢰할 수 없게 만들었다(병합 판정 포함).
#
# 규율 — 준비 실패는 **여전히 red 다.** 상한을 늘리거나 · 재시도하거나 · 병렬도를 낮추거나 ·
#   건너뛰어 green 으로 만들지 않는다. 바뀌는 것은 **red 가 자기 원인을 말한다**는 것뿐이다.
#
# 무엇을 남기나 (한 줄 · 기계가 읽는 표식):
#   ::gate-readiness-failure::gate=<게이트>|waited_for=<무엇을 기다렸나>|limit=<상한>|elapsed=<실경과>|detail=<사유>
# 실행기(gates/run.sh all)는 이 표식과 종료코드 78 로 요약에서 `red(준비)` 를 갈라 적는다.
# 표식 문자열을 자르는 자리는 `_readiness.sh` 가 쥔다 — 바이트 단위로 자르면 한글이 깨지고,
# 깨진 바이트가 있으면 `grep` 이 출력을 바이너리로 보아 **표식을 못 찾는다.**
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"
PG_READINESS_EXIT=78

pg_readiness_report() { # $1=게이트 $2=기다린 대상 $3=상한 $4=실경과 $5=사유
  local gate="$1" what="$2" limit="$3" elapsed="$4" detail="$5"
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    "$gate" "$what" "$limit" "$elapsed" "$(readiness_oneline "$detail" 400)"
  echo "::error::$gate red(준비) — **검사기가 돌지 못했다.** 판정 red 가 아니다.
   기다린 것: $what
   선언 상한: $limit · 실경과: $elapsed
   사유: $detail
   ⚠ 준비 실패도 **red 다.** 상한 연장·재시도·병렬도 축소·건너뛰기로 green 을 만들지 않는다."
}

pg_now() { date +%s; }

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
      pg_readiness_report "$gate" "일회용 postgres 동시성 슬롯(${max}개 · COLAB_PG_MAX_CONCURRENT)" \
        "${wait_s}초" "$(( $(date +%s) - deadline + wait_s ))초" \
        "슬롯 ${max}개가 모두 다른 게이트에 잡혀 있었다. 슬롯 디렉터리=$PG_SLOT_DIR"
      return "$PG_READINESS_EXIT"
    fi
    sleep 1
  done
}

pg_slot_release() {
  [ -n "$PG_SLOT_FD" ] || return 0
  eval "exec ${PG_SLOT_FD}>&-" 2>/dev/null
  PG_SLOT_FD=""
}

# ── 「준비됐다」의 뜻을 **실서버**로 좁힌다 ─────────────────────────────────
# 왜 있는가: `postgres:16-alpine` 의 엔트리포인트는 initdb 동안 **임시 서버**를 띄운다.
#   그 임시 서버도 「database system is ready to accept connections」를 찍고 `pg_isready` 에
#   응답한다. 곧바로 그것을 내리고(≈0.1초 뒤) **진짜 서버**를 띄운다. 종전 대기 루프는
#   임시 서버에서 break 했고, 뒤이은 확인 `pg_isready` 가 그 ~200ms 공백에 떨어져
#   60초 예산 중 **1초** 만에 red(준비) 를 냈다 — 실제로는 DB 가 곧 떴는데도.
#   (selftest 는 컨테이너 4개를 동시에 띄우므로 공백이 더 벌어진다.)
#
# 그래서 준비의 뜻을 **진짜 서버가 접속을 받는 상태**로 좁힌다:
#   ⑴ 로그에 엔트리포인트의 초기화 완료 표식이 있고 ⑵ 그 뒤 `pg_isready` 가 성공한다.
#   PGDATA 가 이미 초기화된 경우(여기서는 tmpfs 라 발생하지 않지만)는 initdb 단계 자체가
#   없으므로 임시 서버도 없다 — 초기화 표식 없이 접속 준비 로그만 있으면 그대로 준비로 센다.
#
# ⚠ 이것은 **대기 정밀화**다. 예산(60초)·판정·재시도 정책은 하나도 바뀌지 않는다.
#   상한을 넘기면 여전히 red(준비) 다.
PG_INIT_DONE_MARK='PostgreSQL init process complete; ready for start up'
PG_ACCEPT_MARK='database system is ready to accept connections'

pg_real_server_started() { # $1=컨테이너 → 0=진짜 서버가 떴다 / 1=아직
  local logs
  logs="$(docker logs "$1" 2>&1)" || return 1
  case "$logs" in
    *"$PG_INIT_DONE_MARK"*) return 0 ;;
  esac
  # 초기화 흔적이 하나도 없는데 접속 준비 로그가 있다 = 이미 초기화된 PGDATA(임시 서버 없음)
  case "$logs" in
    *"$PG_ACCEPT_MARK"*)
      printf '%s' "$logs" | grep -qE 'initdb|Success\. You can now start the database server' && return 1
      return 0 ;;
  esac
  return 1
}

pg_wait_ready() { # $1=컨테이너 $2=상한(초) → 0=준비 / 1=상한 초과
  local c="$1" limit="$2" i
  for (( i = 0; i < limit; i++ )); do
    if pg_real_server_started "$c" && docker exec "$c" pg_isready -U postgres -q >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

pg_ready_detail() { # $1=컨테이너 — 상한 초과 시 사유 문자열
  local c="$1" mark='초기화 완료 표식 없음(임시 서버 단계에서 멈춤)'
  pg_real_server_started "$c" && mark='초기화 완료 표식은 있으나 pg_isready 가 응답하지 않음'
  printf '컨테이너 상태=%s · %s · 호스트 %s · 마지막 로그: %s' \
    "$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo '(조회 실패)')" \
    "$mark" \
    "$(uptime | sed 's/.*load average/load average/')" \
    "$(docker logs --tail 3 "$c" 2>&1 | tr '\n' ' ' | cut -c1-200)"
}

pg_cleanup() {
  [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1
  PGC=""
  pg_slot_release
}

# $1 = 게이트 이름(메시지용). 성공하면 $PGC 가 컨테이너 이름이다.
pg_start() {
  local gate="$1"
  local t0; t0="$(pg_now)"
  if [ "${COLAB_PG_FORCE_UNAVAILABLE:-0}" = "1" ]; then
    pg_readiness_report "$gate" "일회용 postgres(주입된 부재 · COLAB_PG_FORCE_UNAVAILABLE=1)" \
      "대기 없음" "0초" "selftest 가 도커 부재를 주입했다."
    return "$PG_READINESS_EXIT"
  fi
  command -v docker >/dev/null 2>&1 || {
    pg_readiness_report "$gate" "docker 실행 파일" "대기 없음" "0초" \
      "docker 가 PATH 에 없다. CI 에서는 postgres 서비스 컨테이너를 띄우거나 docker 를 쓸 수 있게 한다."
    return "$PG_READINESS_EXIT"; }
  docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 || {
    pg_readiness_report "$gate" "이미지 $PG_IMAGE 확보(pull)" "상한 없음" "$(( $(pg_now) - t0 ))초" \
      "레지스트리/네트워크에서 이미지를 받지 못했다."
    return "$PG_READINESS_EXIT"; }

  pg_slot_acquire "$gate" || return "$PG_READINESS_EXIT"
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
      pg_readiness_report "$gate" "일회용 postgres 컨테이너 생성(docker run)" "대기 없음" \
        "$(( $(pg_now) - t0 ))초" "도커가 낸 말: ${runerr:-(출력 없음)}"
      PGC=""; return "$PG_READINESS_EXIT"; }

  local ready_limit="${COLAB_PG_READY_TIMEOUT:-60}" t1; t1="$(pg_now)"
  pg_wait_ready "$PGC" "$ready_limit" && return 0
  pg_readiness_report "$gate" "postgres 접속 준비(실서버 · pg_isready · 컨테이너 $PGC)" \
    "${ready_limit}초" "$(( $(pg_now) - t1 ))초" "$(pg_ready_detail "$PGC")"
  pg_cleanup
  return "$PG_READINESS_EXIT"
}

# psql 을 컨테이너 안에서 돌린다. $1=DB 이름, 나머지는 psql 인자.
pg_psql() { local db="$1"; shift; docker exec -i "$PGC" psql -U postgres -d "$db" -v ON_ERROR_STOP=1 "$@"; }

# 적용 실패가 **스키마 탓인지 서버 탓인지**를 가른다.
# 「적용되지 않는 스키마」(판정 red)와 「DB 가 쓸 수 있는 상태가 아니었다」(준비 red)는 다른 사실인데,
# 종전에는 둘 다 같은 문장으로 나왔다 — 부하에서 뜨는 간헐 red 를 스키마 결함으로 오인하게 만들던 자리다.
# 여기 나열한 것은 전부 **서버·접속 계열**이고, SQL 문법·제약 오류는 하나도 들어 있지 않다.
pg_is_readiness_error() { # $1=오류 문자열 → 0=준비 실패 / 1=판정 실패
  printf '%s' "$1" | grep -qiE \
    'could not connect|connection refused|server closed the connection|terminating connection|the database system is (starting up|shutting down|in recovery)|no route to host|could not translate host|connection to server .* failed|is the server running|Error response from daemon|is not running|No such container|EOF detected|server process was terminated'
}

# 호스트의 .sql 파일을 컨테이너 안 DB 에 적용한다. $1=DB $2=파일
# 실패하면 $PG_APPLY_ERR 에 **사유가 남는다** — 버리면 사후에 귀속할 수 없다.
PG_APPLY_ERR=""
pg_apply() {
  local db="$1" f="$2"
  PG_APPLY_ERR="$(docker exec "$PGC" createdb -U postgres "$db" 2>&1 >/dev/null)" || return 1
  PG_APPLY_ERR="$(docker exec -i "$PGC" psql -U postgres -d "$db" -q -v ON_ERROR_STOP=1 < "$f" 2>&1 >/dev/null)" || return 1
  PG_APPLY_ERR=""
  return 0
}
