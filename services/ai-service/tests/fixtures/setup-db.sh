#!/usr/bin/env bash
# ai-service 시험용 일회용 DB (`db/ai` 체인) 를 만든다. **포트를 하나도 공개하지 않는다** — 컨테이너 IP 로만 붙는다.
#
# 규약은 `services/core-api/tests/fixtures/setup-db.sh` 와 같다. 다른 것은 체인(ai)뿐이다.
#   ① 소유자 롤이 db/ai/schema.sql 을 적용한다              (앱 롤은 DDL 을 갖지 않는다)
#   ② db/ai/seed 의 시드 둘을 소유자 롤로 적재한다           (K2 사전 22행 · K2b 그래프 노드 49·엣지 19)
#   ③ 앱 롤(colab_ai_app) 을 만든다 — **SELECT 뿐이다.** 정본은 infra/staging/db-bootstrap.sh 의
#      `app-grants` 이고 마지막 검사는 그것과 같은 fail-closed 다. D10 은 기록하지 않는다 (CLAUDE.md §3-2).
#
# ⚠ 이 체인의 앱 롤은 `colab_app` 이 아니다. 한 자격증명이 두 체인을 다 여는 순간을 만들지 않는다.
# ⚠ 값(비밀번호·접속 문자열)은 마지막 한 줄 말고 아무 데도 남기지 않는다.
#
# 사용:  CONTAINER=ai_pg APP_PASSWORD=<임시> tests/fixtures/setup-db.sh
set -euo pipefail

CONTAINER="${CONTAINER:-ai_pg}"
DB="${DB:-colab_ai}"
OWNER="${OWNER:-colab_owner}"
APP="${APP:-colab_ai_app}"
APP_PASSWORD="${APP_PASSWORD:-aiapp}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_SERVICE="$(cd "$HERE/../.." && pwd)"
REPO="$(cd "$AI_SERVICE/../.." && pwd)"

psql_su() { docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U postgres -d "$DB" "$@"; }
psql_owner() { docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$OWNER" -d "$DB" "$@"; }

# ① 소유자 롤 · 스키마
psql_su -q -c "SET client_min_messages=warning; DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null 2>&1
psql_su -c "DO \$\$BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='${OWNER}') THEN CREATE ROLE ${OWNER} LOGIN NOSUPERUSER NOBYPASSRLS; END IF; END\$\$;" >/dev/null
psql_su -c "ALTER SCHEMA public OWNER TO ${OWNER}; GRANT ALL ON SCHEMA public TO ${OWNER};" >/dev/null
psql_owner < "$REPO/db/ai/schema.sql" >/dev/null

# ② 시드 — 소유자 롤로 넣는다. 시험이 세는 수(22 · 49 · 19)의 출처가 여기다.
psql_owner < "$REPO/db/ai/seed/k2_ontology_seed.sql" >/dev/null
psql_owner < "$REPO/db/ai/seed/k2b_concept_graph_seed.sql" >/dev/null

# ③ 앱 롤 — SELECT 뿐. 쓰기 권한이 하나라도 붙으면 여기서 죽는다.
psql_su -v app="$APP" -v owner="$OWNER" -v app_password="$APP_PASSWORD" <<'SQL' >/dev/null
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD %L', :'app', :'app_password')
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app')
\gexec
SELECT format('ALTER ROLE %I PASSWORD %L', :'app', :'app_password')
\gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'app')
\gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'app')
\gexec
SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA public TO %I', :'app')
\gexec
SELECT format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT SELECT ON TABLES TO %I', :'owner', :'app')
\gexec
-- fail-closed: SELECT 밖 권한이 한 건이라도 있으면 \gexec 가 그 자리에서 예외를 던진다.
--   깨끗하면 행이 0 이라 \gexec 는 아무것도 실행하지 않는다.
SELECT format('DO $chk$ BEGIN RAISE EXCEPTION %L; END $chk$', :'app' || ' 에 SELECT 밖 권한이 있다')
  FROM information_schema.role_table_grants
 WHERE grantee = :'app' AND privilege_type <> 'SELECT'
 LIMIT 1
\gexec
SQL

IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER")"
echo "postgresql+psycopg://${APP}:${APP_PASSWORD}@${IP}:5432/${DB}"
