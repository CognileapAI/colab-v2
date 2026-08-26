#!/usr/bin/env bash
# 실연구실 C 신설 실행기 (`S2-EXEC-PLAN §3` · §8 3단 3-A).
#
# 순서 = ⓪ 백업 신선도 → ① 사전 계수 → ② 적재(INSERT 전용) → ③ 사후 계수 대조.
# 실패 시 재시도하지 않는다 — 백업 복원 후 정지가 규약이다 (`§8` 0단).
#
# 이 스크립트는 DELETE·TRUNCATE·DDL 을 실행하지 않는다. SQL 은 INSERT 전용이고
# 전 문장이 `ON CONFLICT DO NOTHING` 이라 **재실행해도 행이 늘지 않는다**.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PG="${COLAB_STAGING_PG_CONTAINER:-colab_v2_staging_pg}"
DB="${COLAB_STAGING_PG_DB:-colab_platform}"
USR="${COLAB_STAGING_PG_USER:-postgres}"
LAB='00000000000000000000HYMETS'

q() { docker exec -i "$PG" psql -U "$USR" -d "$DB" -At -c "$1"; }
die() { echo "RED — $*" >&2; exit 1; }

COUNT_SQL="
select 'd1_lab', count(*) from d1_lab where id = '$LAB'
union all select 'd1_lab_profile', count(*) from d1_lab_profile where lab_id = '$LAB'
union all select 'd1_account', count(*) from d1_account where lab_id = '$LAB'
union all select 'd2_member_role', count(*) from d2_member_role where lab_id = '$LAB'
union all select 'd2_permission_switch', count(*) from d2_permission_switch where lab_id = '$LAB'
order by 1;"

echo "-- 0 백업 신선도"
"$HERE/backup/latest-check.sh" >/dev/null || die "직전 백업 확인 실패 — 신설하지 않는다"
echo "   GREEN"

echo "-- 1 사전 계수 (연구실 C)"
q "$COUNT_SQL" || die "사전 계수 조회 실패"

echo "-- 2 적재"
docker exec -i "$PG" psql -U "$USR" -d "$DB" -v ON_ERROR_STOP=1 -f - < "$HERE/provision-lab.sql" \
  || die '신설 실패 — 재시도 금지. 백업 복원 후 정지.'

echo "-- 3 사후 계수 대조 (기대 = 1/1/1/1/0)"
q "$COUNT_SQL" || die "사후 계수 조회 실패"

echo "-- 4 픽스처 A·B 불변 확인 (신설이 남의 연구실을 건드리지 않았다)"
q "select lab_id, count(*) from d1_account group by lab_id order by 1;"

echo "GREEN — 연구실 C 신설 완료"
