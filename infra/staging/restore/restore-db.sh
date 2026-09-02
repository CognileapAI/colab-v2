#!/usr/bin/env bash
# 원장 하나를 제자리 복원한다 (`R1-RESTORE-DRAFT §4.3`).
#
# ⚠⚠ **비가역이다.** `DROP SCHEMA public CASCADE` 는 되돌릴 수 없다. 되돌릴 재료는
#     `§4.0 P7` 에서 뜬 「복원 직전 백업」 하나뿐이다. 그것 없이 이 스크립트를 돌리지 않는다.
#
# 그래서 문을 셋 세운다 — 셋 다 통과해야 한 글자라도 쓴다:
#   ① `--yes-drop-schema` 를 손으로 붙였다        (오타로 실행되지 않는다)
#   ② `COLAB_RESTORE_PRE_BACKUP` 이 실재하는 파일을 가리킨다  (되돌림의 되돌림 재료)
#   ③ 대상 DB 에 **앱 커넥션이 0** 이다             (`§4.1` — 먼저 비운다)
#
# 사용: restore-db.sh --db <DB> --owner <소유자롤> --dump <덤프.sql.gz> --yes-drop-schema
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../backup/lib.sh"
load_config
: "${COLAB_STAGING_PG_CONTAINER:=colab_v2_staging_pg}"

DB=""; OWNER=""; DUMP=""; CONFIRM=0
while [ $# -gt 0 ]; do
  case "$1" in
    --db) DB="${2:?}"; shift 2 ;;
    --owner) OWNER="${2:?}"; shift 2 ;;
    --dump) DUMP="${2:?}"; shift 2 ;;
    --yes-drop-schema) CONFIRM=1; shift ;;
    *) die "모르는 인자: $1" ;;
  esac
done
[ -n "$DB" ] && [ -n "$OWNER" ] && [ -n "$DUMP" ] || die "사용: restore-db.sh --db <DB> --owner <롤> --dump <덤프.sql.gz> --yes-drop-schema"
[ -f "$DUMP" ] || die "덤프를 찾지 못했다"

# ── 문 ① ────────────────────────────────────────────────────────────────────
[ "$CONFIRM" -eq 1 ] || die "--yes-drop-schema 가 없다. 이 스크립트는 스키마를 통째로 지운다 — 실수로 돌아가지 않게 둔다"

# ── 문 ② ────────────────────────────────────────────────────────────────────
[ -n "${COLAB_RESTORE_PRE_BACKUP:-}" ] && [ -f "$COLAB_RESTORE_PRE_BACKUP" ] \
  || die "COLAB_RESTORE_PRE_BACKUP 이 실재하는 파일을 가리켜야 한다 — 되돌림의 되돌림 재료가 없으면 시작하지 않는다"

# ── 산출물 재확인 — 사고 복원이라 신선도는 뺀다.
# ⭑ **합격선은 프로파일의 것을 쓴다** (`〈286〉`). 종전에는 전역 `COLAB_BACKUP_MIN_TABLES`(20 ·
#   platform 형상)를 그대로 넘겨, 표 6개가 정상인 `ai` 원장이 **구조적 거짓 RED** 로 거부됐다
#   (`sessions/WINDOW-20260903-D3.md §4.2`). 형제 호출 둘은 이미 프로파일 합격선을 쓴다 —
#   `backup/latest-check.sh` · `backup/restore-rehearsal.sh`. 여기만 빠져 있었다.
# ⚠ 이것은 **검사 범위를 줄인 것이 아니다** — 각 프로파일의 실측 합격선으로 **갈아 끼운** 것이고,
#   진짜 잘린 덤프는 여전히 RED 다(`selftest-restore.sh` SR16·SR17 이 두 방향을 못 박는다).
PROFILE="$(profile_for_db "$DB")"
[ "$PROFILE" != "미해결" ] \
  || die "DB '$DB' 에 대응하는 백업 프로파일이 없다 — 합격선을 전역 기본값으로 메우지 않는다 (COLAB_BACKUP_PROFILES · COLAB_BACKUP_DB_<프로파일> 확인)"
log "합격선 프로파일 = $PROFILE (테이블 $(profile_min_tables "$PROFILE") · 행 $(profile_min_rows "$PROFILE"))"
COLAB_BACKUP_MIN_TABLES="$(profile_min_tables "$PROFILE")" \
COLAB_BACKUP_MIN_ROWS="$(profile_min_rows "$PROFILE")" \
  "$HERE/../backup/verify-artifact.sh" "$DUMP" --skip-age || die "덤프가 RED 다. 적재하지 않는다"

# ── 문 ③ 잔여 커넥션 ─────────────────────────────────────────────────────────
# `§4.1` — 서비스가 커넥션을 쥔 채로는 되돌릴 수 없다. `DROP SCHEMA` 가 막히거나,
# 반쯤 적재된 상태에 앱이 쓰기를 얹는다. **여기서는 세기만 하고 끊지 않는다** —
# 커넥션을 끊는 것은 정지 절차(§4.1)의 일이고, 이 스크립트가 그것을 대신하면
# 「정지 안 했는데 돌아가는 복원」이 관행이 된다.
LEFT="$(docker exec "$COLAB_STAGING_PG_CONTAINER" psql -U "$OWNER" -d "$DB" -At \
  -c "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB' AND pid<>pg_backend_pid()" 2>/dev/null)"
[ "${LEFT:-x}" = "0" ] || die "$DB 에 남은 커넥션 ${LEFT:-측정실패}건 — 먼저 §4.1 정지 순서를 돈다"

log "① $DB 의 public 스키마를 비운다 (소유자 롤 $OWNER)"
docker exec -i "$COLAB_STAGING_PG_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$OWNER" -d "$DB" \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null \
  || die "스키마 교체 실패 — 여기서 멈춘다. 반쯤 지워진 상태에 적재를 얹지 않는다"

log "② 덤프를 적재한다 (ON_ERROR_STOP=1)"
# ⚠ `ON_ERROR_STOP=1` 이 없으면 **절반만 적재된 DB 가 exit 0 으로 끝난다**(`IS3 §3` F8).
if ! gunzip -c "$DUMP" | docker exec -i "$COLAB_STAGING_PG_CONTAINER" \
      psql -q -v ON_ERROR_STOP=1 -U "$OWNER" -d "$DB" >/dev/null; then
  die "적재 실패. **성공으로 기록하지 않는다.** 다음 수는 §4.7(되돌림의 되돌림)이다"
fi

log "$DB 적재 완료 — **아직 성공이 아니다.** verify-restored.sh 로 내용을 센다"
exit 0
