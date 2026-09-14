#!/usr/bin/env bash
# prod(RDS) 부트스트랩 — staging `../staging/db-bootstrap.sh` 를 **원격 갈래**로 부르는 얇은 래퍼
# (`〈342〉-㉰` 의 dev 판과 같은 절차다. 다른 것은 이 파일이 사는 자리와, 그 자리가 가리키는 벌뿐).
#
# 절차는 staging 과 같다: ① roles(소유자 롤·DB 2) → ② 마이그레이션(up.sh 가 migrate-platform/ai 를 부른다)
# → ③ app-grants(앱 롤·ai 앱 롤) → verify. 스키마는 여기서 만들지 않는다 — alembic 체인이 정본이다.
#
# RDS 가 다른 점 — RDS 마스터는 `rds_superuser` 이지 진짜 슈퍼유저가 아니다:
#   · `CREATE DATABASE … OWNER colab_owner` 는 마스터가 colab_owner 의 멤버여야 한다 → roles 앞에 GRANT 한 번.
#   · `CREATE EXTENSION pg_trgm`(schema.sql·0006)은 소유자 롤로 가능한지 `[미확인 — G6 실측]`. 안 되면 마스터가
#     먼저 만든다(`IF NOT EXISTS` 라 체인이 무해하게 지나간다).
# 둘 다 이 래퍼의 `prep` 단계에 있다. 값(접속 문자열)은 파일로만 받고 출력하지 않는다.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
STAGING="$HERE/../staging/db-bootstrap.sh"
: "${COLAB_PG_MASTER_URL_FILE:?COLAB_PG_MASTER_URL_FILE 이 필요하다 — RDS 마스터 접속 문자열이 든 0600 파일}"
export COLAB_PG_MASTER_URL_FILE
STEP="${1:-}"

master_psql() { # $1=db, 나머지 = psql 인자
  local db="$1"; shift
  local url; url="$(cat "$COLAB_PG_MASTER_URL_FILE")"
  url="$(printf '%s' "$url" | sed -E "s#(://[^/]+)(/[^/?]*)?(\?.*)?\$#\1/$db\3#")"
  docker run --rm -i postgres:16-alpine psql -v ON_ERROR_STOP=1 "$url" "$@"
}

case "$STEP" in
prep)
  # 마스터 롤 이름은 URL 에서 읽는다 — 파일 밖으로 값을 내지 않는다.
  master="$(sed -E 's#^[a-z]+://([^:/@]+).*$#\1#' "$COLAB_PG_MASTER_URL_FILE")"
  master_psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='colab_owner'" | grep -q 1 \
    || { : "${COLAB_OWNER_PASSWORD:?COLAB_OWNER_PASSWORD 가 필요하다}"; \
         master_psql postgres -v owner_pw="$COLAB_OWNER_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE colab_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD %L', :'owner_pw')
\gexec
SQL
       }
  # RDS 멤버십 규칙 — 마스터가 소유자 롤의 멤버여야 OWNER 지정·소유권 이전이 된다(로컬 슈퍼유저에선 무해).
  master_psql postgres -c "GRANT colab_owner TO \"$master\";"
  echo "prep: ok (마스터 ∈ colab_owner)"
  ;;
roles|app-grants|verify)
  exec bash "$STAGING" "$STEP"
  ;;
account-admin)
  # 계정 관리(백오피스) 전용 롤 `colab_account_admin` — 앱 롤과 자격을 공유하지 않는다.
  #
  # ⛔ **staging 갈래(`exec bash "$STAGING" account-admin`)로 부르지 않는다.** 그 갈래는
  #    `services/core-api/ops/account-admin-role.sql` 을 통째로 먹이는데, 그 파일의
  #      SELECT format('ALTER ROLE %I NOSUPERUSER … PASSWORD %L', …) \gexec
  #    한 문장이 **RDS 에서 구조적으로 성립하지 않는다** —
  #      ERROR: permission denied to alter role
  #      DETAIL: Only roles with the SUPERUSER attribute may change the SUPERUSER attribute.
  #    PostgreSQL 은 `SUPERUSER`/`NOSUPERUSER` 를 **명시하면 값이 같아도** superuser 를 요구하고,
  #    RDS 마스터는 `rds_superuser` 일 뿐 superuser 가 아니다(dev 실측 `rolsuper=f · rolcreaterole=t`).
  #    파일이 `\set ON_ERROR_STOP on` 이라 그 한 문장에서 멈추면 **뒤의 REVOKE·GRANT 가 한 줄도 안 돈다.**
  #
  # ⭑ **dev 가 실제로 통과한 절차를 그대로 옮긴다**(`dev-package/reports/r-login-backoffice/task5/deploy-2.md §2-③`):
  #    1차는 **파일 그대로** 먹인다. `permission denied to alter role` 로 죽으면
  #    **그 한 문장만** 빼고 2차를 먹인다. ⛔ 검사는 하나도 빼지 않는다 —
  #    파일 꼬리의 자기 점검(`rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR NOT rolbypassrls`
  #    → 예외)이 ALTER 가 세우려던 속성을 그대로 판정한다. 빠지는 것은 **같은 값으로의 비밀번호 재설정**
  #    하나이고, 그것은 롤 생성문(`CREATE ROLE … PASSWORD`)이 이미 세운다.
  #    ⚠ 2차도 실패하면 여기서 멈춘다(fail-closed). 「걸리는 검사가 없다」는 자리다 —
  #      `deploy_doctor` ⑨ 는 `colab_app`·`colab_owner` 속성만 보고 롤 권한 대조는 어디에도 없다.
  : "${COLAB_ACCOUNT_ADMIN_PASSWORD:?COLAB_ACCOUNT_ADMIN_PASSWORD 가 필요하다}"
  case "$COLAB_ACCOUNT_ADMIN_PASSWORD" in
    (*[!A-Za-z0-9_-]*) echo "COLAB_ACCOUNT_ADMIN_PASSWORD 는 base64url 문자만 허용한다" >&2; exit 1 ;;
  esac
  ADMIN_SQL="$REPO/services/core-api/ops/account-admin-role.sql"
  [ -r "$ADMIN_SQL" ] || { echo "롤 SQL 이 없다: services/core-api/ops/account-admin-role.sql" >&2; exit 2; }
  admin_feed() { # $1=sql 본문 → psql. 값(비밀번호)은 표준입력으로만 간다.
    { printf '\\set admin_password %s\n' "$COLAB_ACCOUNT_ADMIN_PASSWORD"; printf '%s\n' "$1"; } \
      | master_psql colab_platform -v admin=colab_account_admin
  }
  FULL="$(cat "$ADMIN_SQL")"
  if OUT1="$(admin_feed "$FULL" 2>&1)"; then
    echo "account admin role: ok (파일 그대로)"
  else
    case "$OUT1" in
      *"permission denied to alter role"*)
        echo "account admin role: ALTER ROLE … NOSUPERUSER 가 RDS 에서 거절됐다 — 그 한 문장만 빼고 재적용한다"
        echo "  (근거 dev-package/reports/r-login-backoffice/task5/deploy-2.md §2-③ · 검사는 빼지 않는다)"
        # `SELECT format('ALTER ROLE %I NOSUPERUSER …` 부터 바로 다음 `\gexec` 까지만 제거한다.
        TRIMMED="$(printf '%s\n' "$FULL" | awk '
          /^SELECT format\(.ALTER ROLE %I NOSUPERUSER/ { skip=1; next }
          skip && /^\\gexec$/                          { skip=0; next }
          skip                                          { next }
          { print }')"
        # 뺀 것이 정확히 그 한 덩어리인지 값으로 확인한다 — awk 가 헛돌면 여기서 멈춘다.
        REMOVED=$(( $(printf '%s\n' "$FULL" | wc -l) - $(printf '%s\n' "$TRIMMED" | wc -l) ))
        [ "$REMOVED" -eq 3 ] || { echo "제거된 줄 수가 3 이 아니다: $REMOVED — 파일이 바뀌었다. 손으로 본다" >&2; exit 3; }
        printf '%s\n' "$TRIMMED" | grep -q 'rolsuper OR rolcreatedb' \
          || { echo "꼬리 자기 점검이 사라졌다 — 검사를 줄이는 적용은 하지 않는다" >&2; exit 3; }
        admin_feed "$TRIMMED"
        echo "account admin role: ok (ALTER 한 문장 제외 · 꼬리 자기 점검 통과 · 운영자 등기 자동 변경 없음)"
        ;;
      *) printf '%s\n' "$OUT1" >&2; exit 3 ;;
    esac
  fi
  ;;
operator)
  # 운영자 권한 묶음 두 개(`colab_operator_reporter`·`colab_operator_exporter`) ＋ 실행 로그인 하나.
  #
  # 권한 묶음은 `NOLOGIN` 이고 `ALTER ROLE … NOSUPERUSER` 가 없다 — RDS 에서 파일 그대로 돈다
  # (`CREATE ROLE … NOSUPERUSER` 는 마스터가 할 수 있다. 막히는 것은 **ALTER** 뿐이다).
  # 실행 로그인은 파일 밖에서 만든다 — 그 파일의 머리 주석이 그렇게 정한다
  # (「grant exactly one to a dedicated NOBYPASSRLS runtime login outside this file」).
  # ⛔ 한 로그인에 두 묶음을 함께 주지 않는다. 지금 세우는 것은 **exporter** 하나다.
  : "${COLAB_OPERATOR_PASSWORD:?COLAB_OPERATOR_PASSWORD 가 필요하다 — 운영자 실행 로그인 비밀번호}"
  case "$COLAB_OPERATOR_PASSWORD" in
    (*[!A-Za-z0-9_-]*) echo "COLAB_OPERATOR_PASSWORD 는 base64url 문자만 허용한다" >&2; exit 1 ;;
  esac
  OPERATOR_SQL="$REPO/services/core-api/ops/operator-roles.sql"
  [ -r "$OPERATOR_SQL" ] || { echo "롤 SQL 이 없다: services/core-api/ops/operator-roles.sql" >&2; exit 2; }
  master_psql colab_platform < "$OPERATOR_SQL" >/dev/null
  master_psql colab_platform -v operator_pw="$COLAB_OPERATOR_PASSWORD" <<'SQL' >/dev/null
SELECT 'CREATE ROLE colab_operator_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS'
 WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='colab_operator_runtime')
\gexec
SELECT format('ALTER ROLE colab_operator_runtime PASSWORD %L', :'operator_pw')
\gexec
GRANT CONNECT ON DATABASE colab_platform TO colab_operator_runtime;
GRANT colab_operator_exporter TO colab_operator_runtime;
DO $check$
BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname='colab_operator_runtime'
             AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls)) THEN
    RAISE EXCEPTION '운영자 실행 로그인에 넓은 속성이 있다';
  END IF;
  IF EXISTS (SELECT FROM pg_auth_members m
             JOIN pg_roles g ON g.oid=m.roleid
             JOIN pg_roles r ON r.oid=m.member
             WHERE r.rolname='colab_operator_runtime'
               AND g.rolname <> 'colab_operator_exporter') THEN
    RAISE EXCEPTION '운영자 실행 로그인이 exporter 밖의 롤을 물고 있다';
  END IF;
END $check$;
SQL
  echo "operator: ok (권한 묶음 2 · 실행 로그인 1 = exporter 만)"
  ;;
backup-role)
  # ⚠ **연구실 경계를 우회하는 유일한 롤이다.** 사용자 판정 2026-08-31 (진행 파일 결정 기록).
  #
  # 왜 필요한가 — RLS 가 **FORCE** 라 테이블 소유자(`colab_owner`)도 정책에 걸리고,
  # `current_lab_id()` 는 경계가 없으면 NULL 을 돌려주므로 `lab_id = NULL` 이 영영 거짓이다.
  # 그래서 **어떤 롤도 전수를 못 읽는다** — RDS 마스터조차 `rolbypassrls=f` 다(실측).
  # 백업은 본질적으로 전수를 읽어야 하므로, 그 예외를 **이름 붙은 롤 하나로 드러내 놓고** 만든다.
  # 숨은 우회로를 두는 것보다 낫다.
  #
  # 경계는 이렇게 좁힌다:
  #   · `pg_read_all_data` **읽기 전용** — INSERT·UPDATE·DELETE·DDL 이 없다
  #   · `NOSUPERUSER NOCREATEDB NOCREATEROLE` · `NOINHERIT` 아님(미리 정의된 롤을 써야 하므로)
  #   · **앱은 이 롤을 절대 쓰지 않는다** — compose 어디에도 없고, 자격은 EC2 의 root 전용 0600 파일뿐
  #   · 자격 파일이 새면 **연구실 경계가 통째로 뚫린다** — 그래서 앱 시크릿과 같은 자리에 두되 root 소유다
  : "${COLAB_BACKUP_PASSWORD:?COLAB_BACKUP_PASSWORD 가 필요하다}"
  master_psql postgres -v backup_pw="$COLAB_BACKUP_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE colab_backup LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS PASSWORD %L', :'backup_pw')
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='colab_backup')
\gexec
SELECT format('ALTER ROLE colab_backup BYPASSRLS PASSWORD %L', :'backup_pw')
\gexec
GRANT pg_read_all_data TO colab_backup;
SQL
  for db in colab_platform colab_ai; do
    master_psql "$db" -c "GRANT CONNECT ON DATABASE $db TO colab_backup;"
  done
  echo "backup-role: ok (읽기 전용 + BYPASSRLS · 앱은 쓰지 않는다)"
  ;;
extensions)
  # `[미확인 — G6 실측]` 소유자 롤이 CREATE EXTENSION 을 못 하면 여기서 마스터가 만든다. 체인은 IF NOT EXISTS 로 지나간다.
  for db in colab_platform colab_ai; do
    master_psql "$db" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
  done
  echo "extensions: ok"
  ;;
*)
  echo "사용: db-bootstrap.sh {prep|roles|extensions|app-grants|account-admin|operator|backup-role|verify}" >&2
  echo "  순서: prep → roles → [extensions] → 마이그레이션 → app-grants → account-admin → operator → backup-role → verify" >&2
  echo "  ⚠ account-admin·operator 는 **마이그레이션 뒤**다 — 표가 생긴 뒤라야 GRANT 가 의미를 갖는다" >&2
  echo "    (account-admin 은 0025 이후 · operator 는 0027 이후)" >&2
  exit 2 ;;
esac
