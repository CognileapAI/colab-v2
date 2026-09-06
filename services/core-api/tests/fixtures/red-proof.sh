#!/usr/bin/env bash
# red 증명 — **보호 장치를 하나씩 떼어 내고 그 테스트가 실제로 red 가 되는지** 본다.
#
# RLS 를 꺼도 통과하는 테스트 묶음은 아무 가치가 없다 (CLAUDE.md §4 「red 확인」).
# 여기서 하는 일은 게이트가 자기 fail-closed 를 red fixture 로 증명하는 것과 같은 성질이다.
#
# 각 회차는 ① DB 를 새로 만들고 ② 소유자 롤로 보호 장치를 훼손하고 ③ 해당 테스트를 돌려
# **red 가 나오면 성공**으로 센다. 훼손은 일회용 DB 안에서만 일어나고 `db/` 는 손대지 않는다.
#
# 사용:  CONTAINER=a2_pg tests/fixtures/red-proof.sh
set -uo pipefail

CONTAINER="${CONTAINER:-a2_pg}"
DB="${DB:-colab_platform}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_API="$(cd "$HERE/../.." && pwd)"
PY="$CORE_API/.venv/bin/python"

export COLAB_CORE_TEST_SUBJECTS_FILE="$HERE/subjects.json"

as_owner() { docker exec -i "$CONTAINER" psql -q -v ON_ERROR_STOP=1 -U colab_owner -d "$DB" -c "$1" >/dev/null; }

pass=0; fail=0
run_case() {   # $1 = 이름  $2 = 훼손 SQL  $3.. = pytest 대상
  local name="$1" mutation="$2"; shift 2
  export COLAB_CORE_TEST_DATABASE_URL="$(CONTAINER=$CONTAINER DB=$DB bash "$HERE/setup-db.sh")"
  if [ -n "$mutation" ]; then as_owner "$mutation" || { echo "  훼손 SQL 실패: $name"; fail=$((fail+1)); return; }; fi
  if (cd "$CORE_API" && "$PY" -m pytest -q "$@" >/tmp/a2_red.log 2>&1); then
    echo "✗ $name — 훼손했는데도 green 이다. 이 테스트는 오라클이 아니다."
    fail=$((fail+1))
  else
    echo "✓ $name — red (기대대로)"
    pass=$((pass+1))
  fi
}

echo "── ① cross-tenant 음성 4종 ──"
run_case "읽기 · 경계 조건 한 줄 누락" \
  "ALTER POLICY lab_boundary ON d3_dataset USING (true) WITH CHECK (true);" \
  tests/test_cross_tenant.py::test_read_never_returns_another_labs_rows \
  tests/test_cross_tenant.py::test_read_boundary_holds_at_the_http_layer

run_case "자식 · 자식 테이블에서만 경계 누락" \
  "ALTER POLICY lab_boundary ON d3_dataset_description USING (true) WITH CHECK (true);" \
  tests/test_cross_tenant.py::test_child_rows_of_another_labs_parent_are_invisible

run_case "미스코프 · 기본 거부를 기본 연구실로 바꿈" \
  "CREATE OR REPLACE FUNCTION current_lab_id() RETURNS char(26) LANGUAGE sql STABLE AS \$\$
     SELECT CASE WHEN current_setting('app.current_lab', true) ~ '^[0-9A-HJKMNP-TV-Z]{26}\$'
       THEN current_setting('app.current_lab', true)
       ELSE '0000000000000000000000000A' END::char(26) \$\$;" \
  tests/test_cross_tenant.py::test_a_connection_without_the_guc_sees_zero_rows

run_case "쓰기 · WITH CHECK 를 true 로" \
  "ALTER POLICY lab_boundary ON d6_project USING (lab_id = current_lab_id()) WITH CHECK (true);" \
  tests/test_cross_tenant.py::test_with_check_blocks_writing_into_another_lab

echo "── ② body_access 실효 2종 ──"
run_case "본체 음성 · 두 번째 층 제거" \
  "DROP POLICY body_access ON d3_file;" \
  tests/test_body_access.py::test_a_non_grantee_gets_zero_body_rows \
  tests/test_body_access.py::test_the_body_layer_holds_at_the_http_layer

run_case "본체 음성 · 만료 검사만 제거" \
  "ALTER POLICY body_access ON d3_file USING (
     COALESCE((SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
              (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)) = '열림'
     OR EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                 WHERE g.dataset_id = d3_file.dataset_id
                   AND g.grantee_account_id = current_account_id()));" \
  tests/test_body_access.py::test_an_expired_grant_is_the_same_as_no_grant

run_case "메타 양성 · 잠김을 메타까지 RLS 로 얹음 (P-13 회귀)" \
  "CREATE POLICY body_access ON d3_dataset AS RESTRICTIVE FOR ALL USING (
     COALESCE((SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_dataset.id),
              (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_dataset.lab_id)) = '열림');" \
  tests/test_body_access.py::test_locked_dataset_metadata_is_always_readable \
  tests/test_body_access.py::test_no_restrictive_policy_leaked_onto_the_metadata_tables \
  tests/test_body_access.py::test_locked_dataset_still_appears_in_the_catalog

echo "── ③ 전제 — 앱 롤이 우회 가능하면 위 전부가 거짓 green ──"
export COLAB_CORE_TEST_DATABASE_URL="$(CONTAINER=$CONTAINER DB=$DB bash "$HERE/setup-db.sh")"
IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER")"
COLAB_CORE_TEST_DATABASE_URL="postgresql+psycopg://postgres:a2pw@${IP}:5432/${DB}"
export COLAB_CORE_TEST_DATABASE_URL
if (cd "$CORE_API" && "$PY" -m pytest -q tests/test_cross_tenant.py tests/test_body_access.py >/tmp/a2_red.log 2>&1); then
  echo "✗ superuser 롤 — 음성 묶음이 superuser 로도 green 이다. 거짓 green 을 잡지 못한다."
  fail=$((fail+1))
else
  echo "✓ superuser 롤 — red (기대대로). 실패 수: $(grep -oE '[0-9]+ failed' /tmp/a2_red.log | head -1)"
  pass=$((pass+1))
fi

echo "── ④ 마무리: 훼손 없는 DB 에서 전부 green ──"
export COLAB_CORE_TEST_DATABASE_URL="$(CONTAINER=$CONTAINER DB=$DB bash "$HERE/setup-db.sh")"
if (cd "$CORE_API" && "$PY" -m pytest -q >/tmp/a2_green.log 2>&1); then
  echo "✓ 전체 green — $(tail -1 /tmp/a2_green.log)"; pass=$((pass+1))
else
  echo "✗ 전체 green 이 아니다"; tail -20 /tmp/a2_green.log; fail=$((fail+1))
fi

echo
echo "red 증명 $pass 성공 · $fail 실패"
[ "$fail" -eq 0 ]
