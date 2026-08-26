#!/usr/bin/env bash
# staging 부분 재시드 실행기 — D3/D4/D5 한정.
#
# 판정 근거 = 2026-08-26 Ted ③ (`dev-package/sessions/S2-BLOCKER-INVESTIGATION.md` §2.6).
# 순서 = ⓪ 백업 신선도 확인 → ① 충돌 검사 → ② 고아 계수(전) → ③ 적재 → ④ 계수 대조.
# 실패 시 재시도하지 않는다. 백업 복원 후 정지가 규약이다(`S2-EXEC-PLAN.md` §8-0).
#
# 이 스크립트는 DELETE·TRUNCATE·DDL 을 실행하지 않는다. SQL 은 INSERT 전용이다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PG="${COLAB_STAGING_PG_CONTAINER:-colab_v2_staging_pg}"
DB="${COLAB_STAGING_PG_DB:-colab_platform}"
USR="${COLAB_STAGING_PG_USER:-postgres}"

q() { docker exec -i "$PG" psql -U "$USR" -d "$DB" -At -c "$1"; }
die() { echo "RED — $*" >&2; exit 1; }

TARGETS="d3_dataset d3_dataset_description d3_dataset_autometa d3_file d4_lineage_edge d5_upload d5_upload_file d5_pipeline_event"

ORPHAN_SQL="
select 'd6_project_dataset', count(*) from d6_project_dataset x where not exists (select 1 from d3_dataset d where d.id = x.dataset_id)
union all select 'd2_dataset_access', count(*) from d2_dataset_access x where not exists (select 1 from d3_dataset d where d.id = x.dataset_id)
union all select 'd2_verified', count(*) from d2_verified x where not exists (select 1 from d3_dataset d where d.id = x.dataset_id)
union all select 'd8_download', count(*) from d8_download x where not exists (select 1 from d3_dataset d where d.id = x.dataset_id)
order by 1;"

echo "── ⓪ 백업 신선도"
"$HERE/backup/latest-check.sh" || die "직전 백업 확인 실패 — 재시드하지 않는다"

echo "── ① 충돌 검사 (대상 8표는 0행이어야 한다)"
CONFLICT=0
for t in $TARGETS; do
  n="$(q "select count(*) from $t;")" || die "계수 조회 실패: $t"
  echo "   $t = $n"
  [ "$n" = "0" ] || CONFLICT=1
done
[ "$CONFLICT" = "0" ] || die "대상 표에 행이 있다 — 중복 적재 위험. 정지."

echo "── ② 고아 계수 (전)"
q "$ORPHAN_SQL" | tee /tmp/colab-orphan-before.txt

echo "── ③ 적재"
docker exec -i "$PG" psql -U "$USR" -d "$DB" -v ON_ERROR_STOP=1 -f - < "$HERE/reseed-fixture-d345.sql" \
  || die '적재 실패 — 재시도 금지. 백업 복원 후 정지 (backup/verify-restore.sh 참조).'

echo "── ④ 계수 대조 (후)"
for t in $TARGETS; do printf '   %s = %s\n' "$t" "$(q "select count(*) from $t;")"; done
echo "── 고아 계수 (후)"
q "$ORPHAN_SQL" | tee /tmp/colab-orphan-after.txt

echo "── 고아 해소 대조"
diff -y /tmp/colab-orphan-before.txt /tmp/colab-orphan-after.txt || true
echo "GREEN — 재시드 완료"
