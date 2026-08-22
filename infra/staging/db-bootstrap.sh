#!/usr/bin/env bash
# staging postgres 부트스트랩 — 롤과 데이터베이스만 만든다. **스키마는 만들지 않는다.**
#
# 스키마 정본은 db/{platform,ai}/schema.sql 이고 그것을 적용하는 절차는 alembic 체인이다.
# 여기서 CREATE TABLE 을 하면 정본이 둘이 되고 schema-diff 게이트가 보는 대상이 흐려진다.
#
# 순서가 중요하다:
#   ① 롤 · 데이터베이스 (이 스크립트, 1단계)
#   ② 체인별 마이그레이션 — **소유자 롤**로 (deploy.sh 가 migrate-platform / migrate-ai 를 부른다)
#   ③ 앱 롤 GRANT (이 스크립트, 2단계) — 테이블이 생긴 뒤라야 GRANT ON ALL TABLES 가 의미를 갖는다
#
# 비밀은 환경변수로만 들어온다. 값을 출력하지 않는다.
set -euo pipefail

PG="${PG_CONTAINER:-colab_v2_staging_pg}"
STEP="${1:-}"
: "${COLAB_OWNER_PASSWORD:?COLAB_OWNER_PASSWORD 가 필요하다}"
: "${COLAB_APP_PASSWORD:?COLAB_APP_PASSWORD 가 필요하다}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

su_psql() { docker exec -i -e PGPASSWORD_UNUSED=1 "$PG" psql -v ON_ERROR_STOP=1 -U postgres "$@"; }

case "$STEP" in
roles)
  # 소유자 롤 — 테이블을 소유하고 마이그레이션을 돌린다. NOBYPASSRLS 는 여기서도 지킨다.
  su_psql -d postgres -v owner_pw="$COLAB_OWNER_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE colab_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD %L', :'owner_pw')
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='colab_owner')
\gexec
SELECT format('ALTER ROLE colab_owner PASSWORD %L', :'owner_pw')
\gexec
SQL
  # 두 체인 = 두 데이터베이스. 한 DB 안의 두 스키마로 합치지 않는다 (CLAUDE.md §3-3).
  for db in colab_platform colab_ai; do
    su_psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1 \
      || su_psql -d postgres -c "CREATE DATABASE $db OWNER colab_owner"
    su_psql -d "$db" -c "ALTER SCHEMA public OWNER TO colab_owner; REVOKE CREATE ON SCHEMA public FROM PUBLIC;"
  done
  echo "roles/databases: ok"
  ;;
app-grants)
  # 앱 롤 — core-api 의 유일한 접속 주체. 정본은 services/core-api/ops/app-role.sql 이다.
  # 여기서 다시 쓰지 않고 그 파일을 그대로 먹인다 (마지막 두 검사가 fail-closed 다).
  # colab_ai 에는 만들지 않는다 — 이 롤은 core-api 배포 단위 하나의 접속 주체다.
  docker exec -i "$PG" psql -v ON_ERROR_STOP=1 -U postgres -d colab_platform \
    -v owner=colab_owner -v app=colab_app -v app_password="$COLAB_APP_PASSWORD" \
    < "$REPO/services/core-api/ops/app-role.sql" >/dev/null
  echo "app role grants: ok"
  ;;
verify)
  # 경계가 staging 에서도 살아 있는지 — 값으로 확인한다.
  echo "== 앱 롤 속성 (rolsuper·rolbypassrls 는 f 여야 한다)"
  su_psql -d colab_platform -c \
    "SELECT rolname, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname IN ('colab_app','colab_owner') ORDER BY 1;"
  echo "== 테이블 소유자 분포 (colab_app 소유가 0 이어야 한다)"
  su_psql -d colab_platform -c \
    "SELECT tableowner, count(*) FROM pg_tables WHERE schemaname='public' GROUP BY 1 ORDER BY 1;"
  echo "== FORCE RLS 켜진 테이블 수"
  su_psql -d colab_platform -c \
    "SELECT count(*) FILTER (WHERE relrowsecurity) AS rls_enabled, count(*) FILTER (WHERE relforcerowsecurity) AS rls_forced, count(*) AS tables FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r';"
  echo "== 체인 분리 (두 데이터베이스가 각자의 version_table 을 갖는다)"
  su_psql -d colab_platform -c "SELECT 'platform' AS chain, version_num FROM alembic_version_platform;"
  su_psql -d colab_ai       -c "SELECT 'ai' AS chain, version_num FROM alembic_version_ai;"
  ;;
*)
  echo "사용: db-bootstrap.sh {roles|app-grants|verify}" >&2; exit 2 ;;
esac
