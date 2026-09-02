#!/usr/bin/env bash
# dev(RDS) 부트스트랩 — staging `../staging/db-bootstrap.sh` 를 **원격 갈래**로 부르는 얇은 래퍼 (`〈178〉-㉰`).
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
  echo "사용: db-bootstrap.sh {prep|roles|extensions|app-grants|backup-role|verify}" >&2
  echo "  순서: prep → roles → [extensions] → 마이그레이션 → app-grants → backup-role → verify" >&2
  exit 2 ;;
esac
