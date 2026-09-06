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

# ── 이 스크립트가 필요로 하는 설정 키 — **여기가 정본이다** ──────────────────
# `preflight.sh` 가 이 목록을 물어서 빌드 전에 검사한다. 목록을 프리플라이트 쪽에
# 베껴 두면 언젠가 어긋나고, 어긋난 순간 프리플라이트는 「검사했다」면서 아무것도
# 지키지 않는다. 그래서 **필요로 하는 쪽이 자기 목록을 말한다.**
# 값은 절대 출력하지 않는다 — 나가는 것은 이름뿐이다.
DB_BOOTSTRAP_REQUIRED_ENV=(COLAB_OWNER_PASSWORD COLAB_APP_PASSWORD COLAB_AI_APP_PASSWORD)
if [ "$STEP" = required-env ]; then
  printf '%s\n' "${DB_BOOTSTRAP_REQUIRED_ENV[@]}"; exit 0
fi

: "${COLAB_OWNER_PASSWORD:?COLAB_OWNER_PASSWORD 가 필요하다}"
: "${COLAB_APP_PASSWORD:?COLAB_APP_PASSWORD 가 필요하다}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

# ── 접속 경로 두 갈래 (`PLAN-SoT §9 〈342〉-㉰`).
#   기본(미설정) = 현행 그대로 — staging 의 postgres **컨테이너** 안에서 슈퍼유저로.
#   `COLAB_PG_MASTER_URL_FILE` 이 있으면 = 그 파일의 마스터 접속 문자열로 **원격 DB(RDS)** 에 —
#   일회용 `postgres:16-alpine` 컨테이너의 psql 이 붙는다(버전 16 일치). 값은 파일에서만 읽고 출력하지 않는다.
#   호출 규약은 둘 다 `su_psql -d <db> [psql 인자…]` 다 — 원격 갈래는 `-d` 를 URL 의 데이터베이스 자리로 옮긴다.
MASTER_URL_FILE="${COLAB_PG_MASTER_URL_FILE:-}"
_url_for_db() { # $1=db → 마스터 URL 의 경로(데이터베이스) 자리를 $1 로 바꾼다
  local url; url="$(cat "$MASTER_URL_FILE")"
  printf '%s' "$url" | sed -E "s#(://[^/]+)(/[^/?]*)?(\?.*)?\$#\1/$1\3#"
}
su_psql() {
  if [ -n "$MASTER_URL_FILE" ]; then
    [ "${1:-}" = "-d" ] || { echo "su_psql: 원격 갈래는 -d <db> 로 시작해야 한다" >&2; return 2; }
    local db="$2"; shift 2
    docker run --rm -i postgres:16-alpine psql -v ON_ERROR_STOP=1 "$(_url_for_db "$db")" "$@"
  else
    docker exec -i -e PGPASSWORD_UNUSED=1 "$PG" psql -v ON_ERROR_STOP=1 -U postgres "$@"
  fi
}

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
  # `su_psql` 을 거친다 — 원격 갈래(RDS)에서도 같은 파일을 같은 롤로 먹인다(`〈342〉`-㉰: 이 줄이 직접 exec 였다).
  su_psql -d colab_platform \
    -v owner=colab_owner -v app=colab_app -v app_password="$COLAB_APP_PASSWORD" \
    < "$REPO/services/core-api/ops/app-role.sql" >/dev/null
  # ── ai-service 의 접속 주체. **`colab_app` 이 아니다.**
  #    `colab_app` 은 core-api 배포 단위 하나의 것이고, 그 롤에 colab_ai 접속을 붙이면
  #    한 자격증명이 두 체인을 다 여는 순간이 생긴다 — `db-boundary` 가 파일로 막는 것을
  #    자격증명이 뒤에서 뚫는 모양이다. 그리고 **SELECT 뿐이다**: 이 단위는 사전을 읽기만 한다
  #    (`colab_ai/app/main.py` — 쓰기 호출이 0건). D10 은 기록하지 않는다 (CLAUDE.md §3-2).
  : "${COLAB_AI_APP_PASSWORD:?COLAB_AI_APP_PASSWORD 가 필요하다}"
  su_psql -d colab_ai -v ai_pw="$COLAB_AI_APP_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE colab_ai_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD %L', :'ai_pw')
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='colab_ai_app')
\gexec
SELECT format('ALTER ROLE colab_ai_app PASSWORD %L', :'ai_pw')
\gexec
GRANT CONNECT ON DATABASE colab_ai TO colab_ai_app;
GRANT USAGE ON SCHEMA public TO colab_ai_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO colab_ai_app;
ALTER DEFAULT PRIVILEGES FOR ROLE colab_owner IN SCHEMA public GRANT SELECT ON TABLES TO colab_ai_app;
-- fail-closed: 쓰기 권한이 하나라도 붙어 있으면 여기서 죽는다.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM information_schema.role_table_grants
   WHERE grantee='colab_ai_app' AND privilege_type <> 'SELECT';
  IF n > 0 THEN RAISE EXCEPTION 'colab_ai_app 에 SELECT 밖 권한이 % 건 있다', n; END IF;
END $$;
SQL
  echo "app role grants: ok (colab_app@platform · colab_ai_app@ai · SELECT only)"
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
  echo "사용: db-bootstrap.sh {roles|app-grants|verify|required-env}" >&2; exit 2 ;;
esac
