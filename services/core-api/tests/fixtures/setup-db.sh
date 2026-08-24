#!/usr/bin/env bash
# 음성·양성 증명용 일회용 DB 를 만든다. **포트를 하나도 공개하지 않는다** — 컨테이너 IP 로만 붙는다.
#
#   ① 소유자 롤이 db/platform/schema.sql 을 적용한다        (앱 롤은 DDL 을 갖지 않는다)
#   ② ops/app-role.sql 이 앱 롤(NOBYPASSRLS·비소유자)을 만든다
#   ③ superuser 가 시드를 넣는다 — FORCE RLS 아래에서는 소유자도 정책을 받아 두 연구실을 한 번에 못 심는다
#
# 사용:  CONTAINER=a2_pg DB=colab_platform tests/fixtures/setup-db.sh
set -euo pipefail

CONTAINER="${CONTAINER:-a2_pg}"
DB="${DB:-colab_platform}"
OWNER="${OWNER:-colab_owner}"
APP="${APP:-colab_app}"
APP_PASSWORD="${APP_PASSWORD:-a2app}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_API="$(cd "$HERE/../.." && pwd)"
REPO="$(cd "$CORE_API/../.." && pwd)"

psql_su() { docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U postgres -d "$DB" "$@"; }

# ① 소유자 롤 · 스키마
psql_su -q -c "SET client_min_messages=warning; DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null 2>&1
psql_su -c "DO \$\$BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='${OWNER}') THEN CREATE ROLE ${OWNER} LOGIN NOSUPERUSER NOBYPASSRLS; END IF; END\$\$;" >/dev/null
psql_su -c "ALTER SCHEMA public OWNER TO ${OWNER}; GRANT ALL ON SCHEMA public TO ${OWNER};" >/dev/null
# 선언 스키마가 `CREATE EXTENSION pg_trgm` 을 담고 있다 (`0006` · `〈89〉-㉰`). trusted 확장이라
# superuser 는 필요 없지만 **DB 에 대한 CREATE 권한**은 필요하다 — 스키마 소유권만으로는 안 된다.
psql_su -c "GRANT CREATE ON DATABASE ${DB} TO ${OWNER};" >/dev/null
docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$OWNER" -d "$DB" < "$REPO/db/platform/schema.sql" >/dev/null

# ② 앱 롤
docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U postgres -d "$DB" \
  -v owner="$OWNER" -v app="$APP" -v app_password="$APP_PASSWORD" < "$CORE_API/ops/app-role.sql" >/dev/null

# ③ 시드
psql_su < "$HERE/seed.sql" >/dev/null

IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER")"
echo "postgresql+psycopg://${APP}:${APP_PASSWORD}@${IP}:5432/${DB}"
