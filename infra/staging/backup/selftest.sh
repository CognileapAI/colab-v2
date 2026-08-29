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

# F9 두 체인 중 **한쪽만** 백업된 상태를 성공으로 기록하지 않는다.
#    platform 은 실제로 떠지고 ai 는 없는 DB 를 가리킨다 → 부분 성공이므로 전체가 RED 여야 한다.
#    (살아 있는 staging 은 pg_dump 로 읽기만 한다. 산출물은 일회용 디렉터리에 떨어진다)
if command -v docker >/dev/null 2>&1 && docker inspect colab_v2_staging_pg >/dev/null 2>&1; then
  mkdir -p "$W/partial"
  cat > "$W/partial.env" <<CFG
COLAB_BACKUP_TARGET=postgres
COLAB_BACKUP_PG_CONTAINER=colab_v2_staging_pg
COLAB_BACKUP_PG_USER=postgres
COLAB_BACKUP_PROFILES="platform ai"
COLAB_BACKUP_DB_platform=colab_platform
COLAB_BACKUP_DB_ai=colab_ai_does_not_exist
COLAB_BACKUP_MIN_TABLES_ai=4
COLAB_BACKUP_MIN_ROWS_ai=1
COLAB_BACKUP_DIR=$W/partial
CFG
  expect_red "F9 두 체인 중 한쪽만 백업된 상태 (부분 성공 ≠ 성공)" \
    env COLAB_BACKUP_CONFIG="$W/partial.env" "$HERE/backup.sh"
else
  echo "──────── F9 건너뜀 — staging postgres 가 없다. 이 fixture 는 실행되지 않았다(증명 미완)"; BAD=$((BAD+1))
fi

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

# ══ 〈171〉-㉯ 조용한 기본값 스윕에서 나온 형제 결함 ═══════════════════════════
# F10 **프로파일 합격선 미선언 = RED.** 종전에는 전역 `COLAB_BACKUP_MIN_ROWS=1` 로 조용히
#     떨어져 「행 1건이면 통과」가 붙었다 — `volume_min_files` 의 조용한 `1` 과 같은 모양이다.
mkdir -p "$W/newprofile"
cat > "$W/newprofile.env" <<CFG
COLAB_BACKUP_TARGET=postgres
COLAB_BACKUP_PROFILES="brandnew"
COLAB_BACKUP_DB_brandnew=colab_brandnew
COLAB_BACKUP_DIR=$W/newprofile
CFG
RAN=$((RAN+1)); echo "──────── F10 합격선 미선언 프로파일 — 전역 기본값 1 로 떨어지지 않는다"
OUT10="$(env COLAB_BACKUP_CONFIG="$W/newprofile.env" \
           COLAB_BACKUP_MIN_TABLES="$(. "$HERE/lib.sh"; load_config; profile_min_tables brandnew)" \
           COLAB_BACKUP_MIN_ROWS="$(. "$HERE/lib.sh"; load_config; profile_min_rows brandnew)" \
           "$HERE/verify-artifact.sh" "$GOOD" 2>&1)"; RC10=$?
echo "$OUT10" | sed 's/^/    /'
if [ $RC10 -ne 0 ] && echo "$OUT10" | grep -q 'C0 합격선'; then
  echo "  → 기대대로 RED (exit $RC10) — 선언 없는 합격선을 기본값으로 메우지 않았다"
else
  echo "  → ✗ 합격선 없이 통과했다 — 조용한 기본값 1 회귀 (〈171〉-㉯)"; BAD=$((BAD+1))
fi

# F11 **선언된 프로파일은 코드가 쥔 값으로 돈다** — 홈 env 파일에 키가 없어도 190·45 다.
#     `〈170〉-㉮ ⑴`(「손으로 켠 GREEN 은 기구가 아니다」)을 원장 쪽에도 세운 것이다.
RAN=$((RAN+1)); echo "──────── F11 설정에 프로파일 합격선이 없어도 platform 190 · ai 45 로 돈다"
cat > "$W/nofloor.env" <<'CFG'
COLAB_BACKUP_TARGET=postgres
CFG
F11="$( COLAB_BACKUP_CONFIG="$W/nofloor.env"; export COLAB_BACKUP_CONFIG
        . "$HERE/lib.sh"; load_config
        printf '%s %s %s %s' "$(profile_min_rows platform)" "$(profile_min_tables platform)" \
                             "$(profile_min_rows ai)" "$(profile_min_tables ai)" )"
if [ "$F11" = "190 20 45 4" ]; then
  echo "  → 기대대로: platform 190/20 · ai 45/4 (값이 코드에 있다)"
else
  echo "  → ✗ 합격선이 코드에 없다: [$F11]"; BAD=$((BAD+1))
fi

# ══ 검사 대상 0건을 성공으로 읽지 않는다 (요약줄 정본 `verdict`) ══════════════
# 결함: `verdict` 은 FAILED 만 봤다. 통과도 실패도 SKIP 도 **하나도 없는** 상태 —
#   즉 검사가 한 건도 돌지 않은 상태 — 가 「GREEN (SKIP 0 — 모든 항목이 실제로 돌았다)」로
#   찍혔다. 이것이 `CLAUDE.md §4` 의 green-by-skip 그 자체다. 세 상태로 가른다:
#     ⓐ 검사 대상 있음(PASSED>0) → 검사한다        ⓑ 명시 면제(SKIP 만) → 건수를 드러낸 채 통과
#     ⓒ 아무것도 선언·발견되지 않음(0/0/0)        → **RED**
_vd() { ( FAILED=0; SKIPPED=0; PASSED=0; . "$HERE/lib.sh"; "$@" >/dev/null 2>&1; verdict "결과" ); }

RAN=$((RAN+1)); echo "──────── F12 검사 대상 0건 (통과·실패·SKIP 전부 0) — 성공으로 찍히지 않는다"
OUT12="$(_vd true)"; RC12=$?
echo "$OUT12" | sed 's/^/    /'
if [ $RC12 -ne 0 ]; then
  echo "  → 기대대로 RED — 검사 0건을 통과로 세지 않았다"
else
  echo "  → ✗ 검사 0건인데 GREEN 이 나왔다 (green-by-skip)"; BAD=$((BAD+1))
fi

RAN=$((RAN+1)); echo "──────── F12-b 명시 면제만 있는 상태 — 통과하되 SKIP 건수를 요약줄에 드러낸다"
OUT12B="$( ( FAILED=0; SKIPPED=0; PASSED=0; . "$HERE/lib.sh"; skip_ack "면제 항목" >/dev/null; verdict "결과" ) )"; RC12B=$?
echo "$OUT12B" | sed 's/^/    /'
if [ $RC12B -eq 0 ] && echo "$OUT12B" | grep -q 'SKIP 1건' && echo "$OUT12B" | grep -q '검사 0건'; then
  echo "  → 기대대로 GREEN — 건너뛴 건수와 「검사 0건」이 요약줄에 남았다"
else
  echo "  → ✗ 명시 면제의 건수·검사 0건 사실이 요약줄에 드러나지 않았다"; BAD=$((BAD+1))
fi

RAN=$((RAN+1)); echo "──────── F12-c 대조군 — 실제로 통과 항목이 있으면 GREEN 이다"
OUT12C="$( ( FAILED=0; SKIPPED=0; PASSED=0; . "$HERE/lib.sh"; pass "항목1" >/dev/null; verdict "결과" ) )"; RC12C=$?
echo "$OUT12C" | sed 's/^/    /'
if [ $RC12C -eq 0 ] && echo "$OUT12C" | grep -q '통과 1건'; then
  echo "  → 기대대로 GREEN — 검사기가 무조건 red 를 내는 것이 아니다"
else
  echo "  → ✗ 통과 항목이 있는데 GREEN 이 아니다 (또는 통과 건수가 요약줄에 없다)"; BAD=$((BAD+1))
fi

# ═══════════════════════════════════════════════════════════════════════════
# F13 스케줄 설치가 **남의 crontab 항목을 지우지 않는다**
#
# 왜 있는가: `crontab -l 2>/dev/null` 은 「크론탭이 없다」와 「crontab 명령이 실패했다」를
#   **같은 빈 출력**으로 만든다. 그 빈 출력을 그대로 `crontab -` 에 밀어 넣으면 배포 블록을
#   포함한 기존 항목이 통째로 사라진 채 「설치됨」이 찍힌다. 배포 쪽에서 이미 고친 모양이고,
#   백업 쪽에 같은 것이 남아 있었다.
# 어떻게 증명하나: **가짜 crontab** 을 물려(COLAB_CRONTAB_BIN) 실제 crontab 을 한 줄도
#   건드리지 않고 파괴 경로를 재현한다. 실물 crontab 은 이 픽스처에서 읽지도 쓰지도 않는다.
IS="$HERE/install-schedule.sh"
FAKE_DIR="$W/fakecron"; mkdir -p "$FAKE_DIR"
cat > "$FAKE_DIR/crontab" <<'FAKE'
#!/usr/bin/env bash
# 가짜 crontab. 실물을 대신해 픽스처 안에서만 산다.
#   FAKE_CRON_STORE   현재 크론탭 내용을 담은 파일
#   FAKE_CRON_MODE    ok | none(크론탭 없음) | fail(명령 실패)
set -uo pipefail
STORE="$FAKE_CRON_STORE"
case "${1:-}" in
  -l)
    case "${FAKE_CRON_MODE:-ok}" in
      # 「없음」은 **쓰기 전까지만** 없음이다. 설치가 실제로 걸었으면 그 뒤로는 읽힌다 —
      # 이걸 흉내내지 않으면 픽스처가 스크립트 대신 자기 거짓말을 재는 꼴이 된다.
      none) if [ -s "$STORE" ]; then cat "$STORE"; else echo "no crontab for tester" >&2; exit 1; fi ;;
      fail) echo "crontab: cannot open /var/spool/cron/tester: Permission denied" >&2; exit 1 ;;
      *)    cat "$STORE" ;;
    esac ;;
  -)  cat > "$STORE" ;;
  *)  cat "$1" > "$STORE" ;;
esac
FAKE
chmod +x "$FAKE_DIR/crontab"

SIBLING='# >>> colab-v2-staging-deploy >>>
MAILTO=""
*/5 * * * * /opt/colab/watch.sh >> /tmp/p.log 2>&1
# <<< colab-v2-staging-deploy <<<
0 6 * * * /opt/other/nightly.sh'

# ⚠ **실물 crontab 에 절대 닿지 않는다** — 두 겹으로 막는다.
#   ⓐ COLAB_CRONTAB_BIN 으로 명시 주입 ⓑ PATH 앞에 가짜를 놓아, 스크립트가 주입을 무시하고
#      맨 `crontab` 을 불러도 가짜가 받는다. ⓐ 만으로는 스크립트가 주입을 안 읽는 판에서
#      픽스처가 **실물 crontab 을 갈아엎는다** — 실제로 한 번 일어났다.
run_is() { # $1=모드 $2..=install-schedule 인자 — 가짜 crontab 으로만 돈다
  local mode="$1"; shift
  env PATH="$FAKE_DIR:$PATH" COLAB_CRONTAB_BIN="$FAKE_DIR/crontab" FAKE_CRON_STORE="$W/cronstore" \
      FAKE_CRON_MODE="$mode" COLAB_BACKUP_STATE_DIR="$W/state" "$IS" "$@" 2>&1
}

RAN=$((RAN+1)); echo "──────── F13-0 픽스처가 실물 crontab 에 닿지 않는다 (주입이 실제로 먹는지 먼저 증명)"
printf 'SENTINEL-DO-NOT-TOUCH\n' > "$W/cronstore"
run_is ok show >/dev/null 2>&1
if grep -q 'SENTINEL-DO-NOT-TOUCH' "$W/cronstore"; then
  echo "  → 기대대로 — 가짜 저장소만 읽었다. 아래 파괴 픽스처를 돌려도 된다"
else
  echo "  → ✗ 주입이 먹지 않는다. **아래 픽스처는 실물 crontab 을 건드린다** — 중단한다"; BAD=$((BAD+1))
  echo "셀프테스트 RED — crontab 주입 미동작"; exit 1
fi

RAN=$((RAN+1)); echo "──────── F13-a crontab 읽기 실패 시 설치를 **거부한다** (형제 블록이 살아남는다)"
printf '%s
' "$SIBLING" > "$W/cronstore"
OUT13A="$(run_is fail install)"; RC13A=$?
echo "$OUT13A" | sed 's/^/    /'
SURVIVED="$(grep -c 'nightly.sh' "$W/cronstore" || true)"
if [ $RC13A -ne 0 ] && [ "$SURVIVED" -ge 1 ] && grep -q 'colab-v2-staging-deploy' "$W/cronstore"; then
  echo "  → 기대대로 RED — 쓰지 않았고 형제 블록·남의 줄이 그대로다"
else
  echo "  → ✗ 읽기 실패인데 exit $RC13A 로 진행했다(또는 기존 항목이 사라졌다). 파괴 경로가 열려 있다"; BAD=$((BAD+1))
fi

RAN=$((RAN+1)); echo "──────── F13-b 「크론탭 없음」은 실패가 아니다 — 설치되고, 설치 뒤 읽어서 확인한다"
: > "$W/cronstore"
OUT13B="$(run_is none install)"; RC13B=$?
# 설치 뒤에는 저장소에 내용이 생겼으니 이후 읽기는 ok 모드로 확인한다
echo "$OUT13B" | sed 's/^/    /'
if [ $RC13B -eq 0 ] && grep -q 'colab-v2-staging-backup' "$W/cronstore"; then
  echo "  → 기대대로 GREEN — 없던 크론탭에 블록이 실제로 걸렸다"
else
  echo "  → ✗ 「크론탭 없음」을 실패로 다뤘거나 블록이 걸리지 않았다 (exit $RC13B)"; BAD=$((BAD+1))
fi

RAN=$((RAN+1)); echo "──────── F13-c 설치가 형제 블록(배포)과 남의 줄을 **보존한다**"
printf '%s
' "$SIBLING" > "$W/cronstore"
OUT13C="$(run_is ok install)"; RC13C=$?
echo "$OUT13C" | sed 's/^/    /'
if [ $RC13C -eq 0 ] \
   && grep -q 'colab-v2-staging-deploy' "$W/cronstore" \
   && grep -q 'nightly.sh' "$W/cronstore" \
   && grep -q 'colab-v2-staging-backup' "$W/cronstore"; then
  echo "  → 기대대로 GREEN — 형제 블록·남의 줄·새 블록이 함께 있다"
else
  echo "  → ✗ 설치가 남의 항목을 삼켰다 (exit $RC13C)"; BAD=$((BAD+1))
fi

RAN=$((RAN+1)); echo "──────── F13-d 「설치했다」≠「걸려 있다」 — 써도 안 걸리면 RED 다"
printf '%s
' "$SIBLING" > "$W/cronstore"
cat > "$FAKE_DIR/crontab.swallow" <<'FAKE2'
#!/usr/bin/env bash
# 쓰기를 **삼키는** 가짜 crontab — exit 0 을 내지만 저장하지 않는다.
set -uo pipefail
case "${1:-}" in
  -l) cat "$FAKE_CRON_STORE" ;;
  -)  cat > /dev/null ;;
  *)  : ;;
esac
FAKE2
chmod +x "$FAKE_DIR/crontab.swallow"
OUT13D="$(env PATH="$FAKE_DIR:$PATH" COLAB_CRONTAB_BIN="$FAKE_DIR/crontab.swallow" FAKE_CRON_STORE="$W/cronstore" \
   COLAB_BACKUP_STATE_DIR="$W/state" "$IS" install 2>&1)"; RC13D=$?
echo "$OUT13D" | sed 's/^/    /'
if [ $RC13D -ne 0 ]; then
  echo "  → 기대대로 RED — 붙인 뒤 읽어서 「안 걸렸다」를 잡았다"
else
  echo "  → ✗ 쓰기가 삼켜졌는데 「설치됨」을 냈다. 설치 후 재확인이 없다"; BAD=$((BAD+1))
fi

RAN=$((RAN+1)); echo "──────── F13-e remove 도 읽기 실패에서 **쓰지 않는다**"
printf '%s
' "$SIBLING" > "$W/cronstore"
OUT13E="$(run_is fail remove)"; RC13E=$?
echo "$OUT13E" | sed 's/^/    /'
if [ $RC13E -ne 0 ] && grep -q 'nightly.sh' "$W/cronstore"; then
  echo "  → 기대대로 RED — 지우지 않았고 남의 줄이 그대로다"
else
  echo "  → ✗ 읽기 실패인데 remove 가 crontab 을 덮었다 (exit $RC13E)"; BAD=$((BAD+1))
fi

echo
if [ "$BAD" -eq 0 ]; then
  echo "셀프테스트 GREEN — fixture $RAN 건 전부 기대대로 RED"
  exit 0
else
  echo "셀프테스트 RED — $BAD 건이 fail-closed 가 아니다"
  exit 1
fi
