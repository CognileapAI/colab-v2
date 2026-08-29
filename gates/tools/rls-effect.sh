#!/usr/bin/env bash
# rls-effect 게이트 (WU-D3b) — **RLS 가 실제로 막는지**를 엔진에 물어 판정한다.
#
# rls-coverage 는 「정책이 걸려 있는가」를 본다. 그것만으로는 부족하다 —
# 조건이 `USING (true)` 인 정책도 걸려 있기는 하다. 이 게이트는 한 걸음 더 가서
# **행이 실제로 안 보이는지**를 본다. WORK-UNITS D3b 의 오라클 셋이 그대로 판정이다.
#
#   ① 본체 음성  — 허용자 아님 · 만료됨 두 경우, 잠긴 데이터셋의 파일 본체가 **DB 층에서 0행**
#   ② 메타 양성  — 잠긴 데이터셋의 **메타는 반드시 조회된다** (P-13 회귀 방지)
#   ③ cross-tenant — 남의 연구실 행은 어떤 테이블에서도 0행 · GUC 없는 접속도 0행
#
# 재료는 A2 가 남긴 것을 그대로 쓴다 (services/core-api/tests/fixtures/seed.sql ·
# services/core-api/ops/app-role.sql · db/platform/schema.sql). 게이트가 자기 시드를
# 따로 들면 시드가 두 벌이 되어 갈라진다 — 정본은 하나다.
#
# **가장 무너지기 쉬운 자리: 접속 롤.**
#   superuser 나 테이블 소유자로 붙으면 FORCE RLS 가 무력해지고 위 셋이 전부 거짓 green 이 된다.
#   실측(P0-rls-proof §②)으로 같은 묶음을 superuser 로 돌리면 13 failed 였다. 즉 롤이 틀리면
#   게이트는 «아무것도 증명하지 못한 채» green 을 낼 수 있다. 그래서 이 게이트는 판정 전에
#   접속 롤의 성질을 **직접 확인하고, 틀리면 red 를 낸다.** 조용한 통과는 없다 (CLAUDE.md §4).
#
# 원칙 (CLAUDE.md §4): 도커가 없거나 재료가 없으면 **red**. skip 없음.
#
# 환경변수
#   COLAB_PG_IMAGE               기본 postgres:16-alpine
#   COLAB_PG_FORCE_UNAVAILABLE=1 selftest 전용 — 도커 부재 주입
#   COLAB_RLS_EFFECT_SCHEMA      선언 스키마 (기본 db/platform/schema.sql)
#   COLAB_RLS_EFFECT_APPROLE     앱 롤 부트스트랩 (기본 services/core-api/ops/app-role.sql)
#   COLAB_RLS_EFFECT_SEED        시드 (기본 services/core-api/tests/fixtures/seed.sql)
#   COLAB_RLS_EFFECT_MUTATION    selftest 전용 — 소유자로 적용할 **훼손 SQL**(red fixture)
#   COLAB_RLS_EFFECT_ROLE        판정에 쓸 접속 롤 (기본 colab_app). selftest 가 틀린 롤을 주입한다
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCHEMA="${COLAB_RLS_EFFECT_SCHEMA:-$REPO_ROOT/db/platform/schema.sql}"
APPROLE="${COLAB_RLS_EFFECT_APPROLE:-$REPO_ROOT/services/core-api/ops/app-role.sql}"
SEED="${COLAB_RLS_EFFECT_SEED:-$REPO_ROOT/services/core-api/tests/fixtures/seed.sql}"
MUTATION="${COLAB_RLS_EFFECT_MUTATION:-}"
APP_ROLE="${COLAB_RLS_EFFECT_ROLE:-colab_app}"
OWNER="colab_owner"
DB="rlseffect"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"

red() { echo "::error::rls-effect red — $*"; exit 1; }

# ── 재료 확인 — 없는 것을 «검사할 게 없다»로 세지 않는다 ─────────────────────
MISSING=()
for f in "$SCHEMA" "$APPROLE" "$SEED"; do
  [ -f "$f" ] || MISSING+=("${f#"$REPO_ROOT"/}")
done
if [ "${#MISSING[@]}" -gt 0 ]; then
  red "판정 재료가 없다. 대상 0건은 통과가 아니다 (CLAUDE.md §4).
   없는 것:
$(printf '     - %s\n' "${MISSING[@]}")"
fi

# ── 일회용 postgres — 포트를 하나도 publish 하지 않는다 ──────────────────────
# 이 호스트에는 staging(colab_v2_staging_*)이 돈다. 이름·포트가 겹칠 여지를 만들지 않는다.
# 동시성 한도·슬롯은 `_pg.sh` 의 것을 **그대로 쓴다** — 두 벌로 두면 한쪽이 언젠가 관대해진다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_pg.sh"

PGC=""
cleanup() { [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1; [ -n "${TMP:-}" ] && rm -rf "$TMP"; pg_slot_release; }
trap cleanup EXIT INT TERM

if [ "${COLAB_PG_FORCE_UNAVAILABLE:-0}" = "1" ]; then
  red "일회용 postgres 를 띄울 수 없다(주입된 부재). 검사를 못 한 것은 통과가 아니다."
fi
command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 게이트를 DB 없이 green 으로 세지 않는다."
docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 \
  || red "이미지 $PG_IMAGE 를 확보하지 못했다(네트워크/레지스트리). skip 아님."

pg_slot_acquire rls-effect || exit 1

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" rls-effect-XXXXXX)"
PGC="b3_rlseffect_$$_${RANDOM}"
RUNERR="$(docker run -d --rm --name "$PGC" \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$PG_IMAGE" 2>&1 >/dev/null)" || { PGC=""; red "일회용 postgres 컨테이너를 띄우지 못했다.
   도커가 낸 말: ${RUNERR:-(출력 없음)}"; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || red "postgres 가 60초 안에 뜨지 않았다.
   컨테이너 상태: $(docker inspect -f '{{.State.Status}}' "$PGC" 2>/dev/null || echo '(조회 실패)') · 호스트 부하: $(uptime | sed 's/.*load average/load average/')
   마지막 로그: $(docker logs --tail 3 "$PGC" 2>&1 | tr '\n' ' ' | cut -c1-300)
   ⚠ 이것은 **red 다.** 못 돈 검사를 통과로 세지 않는다. 동시성 한도는 COLAB_PG_MAX_CONCURRENT 로 선언된다."

su_psql()  { docker exec -i "$PGC" psql -v ON_ERROR_STOP=1 -U postgres  -d "$DB" "$@"; }
own_psql() { docker exec -i "$PGC" psql -v ON_ERROR_STOP=1 -U "$OWNER"  -d "$DB" "$@"; }
app_psql() { docker exec -i "$PGC" psql -v ON_ERROR_STOP=1 -U "$APP_ROLE" -d "$DB" "$@"; }

# ── 구성 — A2 의 setup-db.sh 와 같은 순서. 소유자가 DDL, superuser 가 시드 ────
docker exec "$PGC" createdb -U postgres "$DB" >/dev/null 2>&1 || red "DB 를 만들지 못했다."
su_psql -q -c "CREATE ROLE $OWNER LOGIN NOSUPERUSER NOBYPASSRLS;" >/dev/null 2>&1 \
  || red "소유자 롤을 만들지 못했다."
su_psql -q -c "ALTER SCHEMA public OWNER TO $OWNER; GRANT ALL ON SCHEMA public TO $OWNER;" >/dev/null 2>&1 \
  || red "public 스키마 소유권을 넘기지 못했다."
# 선언 스키마가 `CREATE EXTENSION pg_trgm` 을 담고 있다 (`0006` · `〈89〉-㉰`). trusted 확장이라
# superuser 는 필요 없지만 **DB 에 대한 CREATE 권한**은 필요하다 — public 스키마 소유권만으로는
# 안 된다. 소유자는 여전히 NOSUPERUSER·NOBYPASSRLS 이므로 이 게이트가 재는 성질은 그대로다.
su_psql -q -c "GRANT CREATE ON DATABASE $DB TO $OWNER;" >/dev/null 2>&1 \
  || red "소유자에게 DB CREATE 권한을 주지 못했다 — 확장을 담은 선언 스키마가 적용되지 않는다."
own_psql -q < "$SCHEMA" >"$TMP/err" 2>&1 \
  || red "선언 스키마를 적용하지 못했다. 적용되지 않는 스키마는 검사할 수 없다:
$(sed 's/^/     /' "$TMP/err")"
su_psql -q -v owner="$OWNER" -v app=colab_app -v app_password=gateapp < "$APPROLE" >"$TMP/err" 2>&1 \
  || red "앱 롤 부트스트랩이 실패했다:
$(sed 's/^/     /' "$TMP/err")"
su_psql -q < "$SEED" >"$TMP/err" 2>&1 \
  || red "시드를 넣지 못했다:
$(sed 's/^/     /' "$TMP/err")"

# ── red fixture 훼손 (selftest 전용) — 일회용 DB 안에서만 일어난다 ──────────
# superuser 로 적용한다. 훼손은 「누가 그럴 수 있는가」를 묻는 자리가 아니라 **보호 장치를 뗀 상태**를
# 만드는 자리다. 롤 속성 훼손(BYPASSRLS·소유자 이전)은 소유자 롤 권한으로는 아예 만들 수 없다.
if [ -n "$MUTATION" ]; then
  su_psql -q -c "$MUTATION" >"$TMP/err" 2>&1 \
    || red "주입된 훼손 SQL 자체가 실패했다(픽스처 결함이지 판정이 아니다):
$(sed 's/^/     /' "$TMP/err")"
  echo "# [selftest] 보호 장치를 훼손한 상태로 판정한다"
fi

# ═════ 0. 접속 롤 성질 — 여기서 틀리면 아래 판정 전부가 거짓 green 이다 ═════
ROLE_FACTS="$(su_psql -At -F'|' -c "
  SELECT r.rolname, r.rolsuper, r.rolbypassrls,
         (SELECT count(*) FROM pg_tables t WHERE t.schemaname='public' AND t.tableowner = r.rolname)
    FROM pg_roles r WHERE r.rolname = '$APP_ROLE';" 2>/dev/null)"
[ -n "$ROLE_FACTS" ] || red "판정 롤 '$APP_ROLE' 이 존재하지 않는다."
IFS='|' read -r R_NAME R_SUPER R_BYPASS R_OWNED <<< "$ROLE_FACTS"
if [ "$R_SUPER" = "t" ] || [ "$R_BYPASS" = "t" ] || [ "$R_OWNED" != "0" ]; then
  red "판정 롤 '$R_NAME' 이 RLS 를 우회한다 — rolsuper=$R_SUPER · rolbypassrls=$R_BYPASS · public 소유 테이블 ${R_OWNED}개.
   이 롤로 낸 green 은 **아무것도 증명하지 않는다.** 실측(P0-rls-proof §②)으로 같은 판정을 superuser 로 돌리면
   음성이 전부 무너진다. 그래서 틀린 롤은 조용한 통과가 아니라 red 다 (CLAUDE.md §4)."
fi
echo "# 판정 롤 $R_NAME — rolsuper=f · rolbypassrls=f · public 소유 테이블 0개 (우회 불가)"

# ═════ 1~3. 오라클 셋 — 앱 롤로 붙어 엔진에 직접 묻는다 ══════════════════════
cat > "$TMP/oracle.sql" <<'SQL'
\set ON_ERROR_STOP on
\set LAB_A    '0000000000000000000000000A'
\set LAB_B    '0000000000000000000000000B'
\set A_PROF   '00000000000000000000000AP1'
\set A_RES    '000000000000000000000000A1'
\set B_PROF   '00000000000000000000000BP1'
\set DS_A1    '0000000000000000000000DSA1'
\set DS_A2    '0000000000000000000000DSA2'
\set DS_B1    '0000000000000000000000DSB1'

-- 접속 주체가 정말 그 롤인지 한 번 더 (docker exec -U 가 무시되는 사고 방지).
DO $$ BEGIN
  IF current_user = 'postgres' OR (SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user) THEN
    RAISE EXCEPTION '[롤] 판정 세션이 우회 롤(%)이다.', current_user;
  END IF;
END $$;

-- ═══ ① 본체 음성 — 허용자 아님 · 만료됨 ══════════════════════════════════════
BEGIN;
SELECT set_config('app.current_lab',     :'LAB_A',  true);
SELECT set_config('app.current_account', :'A_PROF', true);

DO $$
DECLARE n int;
BEGIN
  -- ⓐ 허용자 목록에 없는 사람 → 잠긴 데이터셋(DSA2)의 본체 0행.
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id = '0000000000000000000000DSA2';
  IF n <> 0 THEN RAISE EXCEPTION '[①-ⓐ] 허용자가 아닌데 잠긴 데이터셋 본체가 %행 보인다.', n; END IF;
  -- 대조 — 열린 데이터셋은 그대로 보인다. 그래야 위의 0 이 «원래 0» 이 아님이 증명된다.
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id = '0000000000000000000000DSA1';
  IF n <> 2 THEN RAISE EXCEPTION '[①-대조] 열린 데이터셋 본체가 %행 (2 여야 한다) — 정책이 과하게 닫혔다.', n; END IF;
END $$;
ROLLBACK;

BEGIN;
SELECT set_config('app.current_lab',     :'LAB_A', true);
SELECT set_config('app.current_account', :'A_RES', true);

DO $$
DECLARE n int;
BEGIN
  -- ⓑ 만료된 허용 줄은 없는 것과 같다 (P-25). 애플리케이션이 만료를 지우러 다니지 않아도 DB 가 거부한다.
  INSERT INTO d2_dataset_access_grant
    (id, lab_id, dataset_id, grantee_account_id, approver_account_id, approved_at, expires_at)
  VALUES ('0000000000000000000000GRN1', '0000000000000000000000000A', '0000000000000000000000DSA2',
          '000000000000000000000000A1', '00000000000000000000000AP1',
          '2025-01-01T00:00:00Z', '2025-07-01T00:00:00Z');
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id = '0000000000000000000000DSA2';
  IF n <> 0 THEN RAISE EXCEPTION '[①-ⓑ] 만료된 허용 줄이 본체를 열었다 (%행).', n; END IF;

  -- 대조 — 유효한 줄을 하나 더 넣으면 1행. 이 대조가 없으면 위의 0 은 아무 말도 하지 않는다.
  INSERT INTO d2_dataset_access_grant
    (id, lab_id, dataset_id, grantee_account_id, approver_account_id, approved_at, expires_at)
  VALUES ('0000000000000000000000GRN2', '0000000000000000000000000A', '0000000000000000000000DSA2',
          '000000000000000000000000A1', '00000000000000000000000AP1',
          '2026-08-01T00:00:00Z', '2027-02-01T00:00:00Z');
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id = '0000000000000000000000DSA2';
  IF n <> 1 THEN RAISE EXCEPTION '[①-대조] 유효한 허용 줄인데 본체가 %행 (1 이어야 한다).', n; END IF;

  -- 허용은 **사람마다** 다르다 — 같은 트랜잭션에서 주체만 바꾸면 다시 0.
  PERFORM set_config('app.current_account', '00000000000000000000000AP1', true);
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id = '0000000000000000000000DSA2';
  IF n <> 0 THEN RAISE EXCEPTION '[①-ⓑ] 남의 허용 줄로 다른 사람이 본체를 봤다 (%행).', n; END IF;
END $$;
ROLLBACK;
\echo '# ① 본체 음성 — 허용자 아님 0행 · 만료됨 0행 (유효 줄 대조 1행)'

-- ═══ ② 메타 양성 — 잠겨도 메타는 보인다 (P-13) ══════════════════════════════
BEGIN;
SELECT set_config('app.current_lab',     :'LAB_A',  true);
SELECT set_config('app.current_account', :'A_PROF', true);

DO $$
DECLARE n int; s text;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset WHERE id = '0000000000000000000000DSA2';
  IF n <> 1 THEN RAISE EXCEPTION '[②] 잠긴 데이터셋이 목록에서 사라졌다 — E-06 접근 요청 흐름이 죽는다 (P-13).'; END IF;
  SELECT name INTO s FROM d3_dataset_description WHERE dataset_id = '0000000000000000000000DSA2';
  IF s IS NULL OR s = '' THEN RAISE EXCEPTION '[②] 잠긴 데이터셋의 이름이 사라졌다 (P-13).'; END IF;
  SELECT count(*) INTO n FROM d3_dataset_autometa WHERE dataset_id = '0000000000000000000000DSA2';
  IF n <> 1 THEN RAISE EXCEPTION '[②] 잠긴 데이터셋의 자동메타가 사라졌다.'; END IF;
  SELECT state INTO s FROM d2_dataset_access WHERE dataset_id = '0000000000000000000000DSA2';
  IF s <> '잠김' THEN RAISE EXCEPTION '[②] 접근 상태를 읽지 못했다 (%).', s; END IF;
  SELECT count(*) INTO n FROM d2_verified WHERE dataset_id = '0000000000000000000000DSA2';
  IF n <> 1 THEN RAISE EXCEPTION '[②] 잠긴 데이터셋의 Verified 상태가 사라졌다.'; END IF;
  SELECT count(*) INTO n FROM d4_lineage_edge WHERE child_dataset_id = '0000000000000000000000DSA2';
  IF n <> 1 THEN RAISE EXCEPTION '[②] 잠긴 데이터의 계보까지 사라졌다.'; END IF;
END $$;
ROLLBACK;

-- 행 개수만 보는 판정은 시드가 마침 열려 있으면 통과해 버린다. 정책 목록 자체를 오라클로 삼는다 —
-- 메타 3표에는 lab_boundary(PERMISSIVE) **하나뿐**, 본체 표만 두 층이고 둘째 층은 RESTRICTIVE.
DO $$
DECLARE t text; got text;
BEGIN
  FOREACH t IN ARRAY ARRAY['d3_dataset','d3_dataset_description','d3_dataset_autometa'] LOOP
    SELECT string_agg(policyname || ':' || permissive, ',' ORDER BY policyname) INTO got
      FROM pg_policies WHERE schemaname='public' AND tablename = t;
    IF got IS DISTINCT FROM 'lab_boundary:PERMISSIVE' THEN
      RAISE EXCEPTION '[②-구조] % 에 정책이 더 붙었다(%) — 잠긴 데이터가 목록에서 사라진다 (P-13·P-34).', t, got;
    END IF;
  END LOOP;
  SELECT string_agg(policyname || ':' || permissive, ',' ORDER BY policyname) INTO got
    FROM pg_policies WHERE schemaname='public' AND tablename = 'd3_file';
  IF got IS DISTINCT FROM 'body_access:RESTRICTIVE,lab_boundary:PERMISSIVE' THEN
    RAISE EXCEPTION '[②-구조] d3_file 의 두 층이 무너졌다(%). PERMISSIVE 로 바뀌면 OR 로 합쳐져 한 층이 된다.', got;
  END IF;
END $$;
\echo '# ② 메타 양성 — 잠긴 데이터셋의 이름·주제·자동메타·접근상태·Verified·계보 전부 조회됨'

-- ═══ ③ cross-tenant — 남의 연구실은 어떤 표에서도 0행 ════════════════════════
BEGIN;
SELECT set_config('app.current_lab',     :'LAB_A',  true);
SELECT set_config('app.current_account', :'A_PROF', true);

DO $$
DECLARE r record; n int; scanned int := 0;
BEGIN
  -- 표 목록을 손으로 적지 않는다. lab_id 를 가진 **모든** 표를 훑는다 —
  -- 새 표가 생겨도 이 판정은 자동으로 늘어난다.
  FOR r IN SELECT c.relname FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
            JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='lab_id' AND a.attnum>0
           WHERE c.relkind='r' AND ns.nspname='public' ORDER BY c.relname
  LOOP
    EXECUTE format('SELECT count(*) FROM public.%I WHERE lab_id <> current_lab_id()', r.relname) INTO n;
    IF n <> 0 THEN RAISE EXCEPTION '[③] %: 남의 연구실 행이 %건 보인다.', r.relname, n; END IF;
    scanned := scanned + 1;
  END LOOP;
  IF scanned < 10 THEN
    RAISE EXCEPTION '[③] lab_id 를 가진 표가 %개뿐이다 — 훑을 대상이 없으면 통과가 아니다.', scanned;
  END IF;

  -- ID 를 알고 있어도 마찬가지다 (열거 실패가 아니라 경계다).
  SELECT count(*) INTO n FROM d3_dataset WHERE id = '0000000000000000000000DSB1';
  IF n <> 0 THEN RAISE EXCEPTION '[③] 남의 데이터셋을 ID 로 직접 집어 봤다.'; END IF;
  -- 대조 — 자기 연구실은 보인다.
  SELECT count(*) INTO n FROM d3_dataset;
  IF n <> 2 THEN RAISE EXCEPTION '[③-대조] 자기 연구실 데이터셋이 %건 (2 여야 한다).', n; END IF;
  RAISE NOTICE '# ③ lab_id 보유 표 %개 전수 — 남의 연구실 0행', scanned;
END $$;
ROLLBACK;

-- GUC 를 세팅하지 않은 접속은 한 행도 못 본다 (기본 거부).
BEGIN;
DO $$
DECLARE n int;
BEGIN
  IF current_lab_id() IS NOT NULL THEN
    RAISE EXCEPTION '[③-미스코프] GUC 가 없는데 current_lab_id() 가 값을 냈다 (%) — 기본값을 주면 미스코프가 전체 열람이 된다.', current_lab_id();
  END IF;
  SELECT count(*) INTO n FROM d3_dataset;
  IF n <> 0 THEN RAISE EXCEPTION '[③-미스코프] GUC 없는 접속이 %행을 봤다.', n; END IF;
END $$;
ROLLBACK;

-- 반대편에서도 같다 — B 로 붙으면 B 것만.
BEGIN;
SELECT set_config('app.current_lab',     :'LAB_B',  true);
SELECT set_config('app.current_account', :'B_PROF', true);
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset;
  IF n <> 1 THEN RAISE EXCEPTION '[③-반대편] B 연구실이 %건을 봤다 (1 이어야 한다).', n; END IF;
END $$;
ROLLBACK;
\echo '# ③ cross-tenant — 전수 0행 · ID 직접 지정 0행 · 미스코프 0행 · 반대편 1행'
SQL

if app_psql -q < "$TMP/oracle.sql" >"$TMP/out" 2>&1; then
  grep -E '^(#|NOTICE)' "$TMP/out" | sed 's/^NOTICE:  //'
  echo "rls-effect green — 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다. 판정 롤은 우회 불가."
  exit 0
fi
red "경계가 실제로는 막지 못한다:
$(sed 's/^/     /' "$TMP/out")"
