-- 앱 DB 롤 부트스트랩 — **`db/` 에 두지 않는다.**
--
-- 왜 여기인가
--   `db/platform` 은 **선언 스키마 ↔ 적용 DB 의 일치**를 증명하는 체인이다(schema-diff 게이트).
--   롤·GRANT 는 데이터베이스가 아니라 **클러스터** 단위 객체라 그 diff 의 대상이 아니고,
--   여기에 넣으면 배포 환경 값(비밀번호)이 스키마 정본에 섞인다.
--   `infra/` 가 아니라 `services/core-api/ops/` 인 이유는 이 롤이 **이 배포 단위 하나의 접속 주체**라서다.
--
-- 무엇을 막는가 (NIGHT-20260823 §3)
--   · NOBYPASSRLS — BYPASSRLS 롤로 접속하면 모든 경계 정책이 통째로 무시되고,
--                   cross-tenant 음성 테스트가 **거짓 green** 이 된다.
--   · 비소유자   — 소유자는 ENABLE 만 된 RLS 를 건너뛴다. schema.sql 이 FORCE 까지 켜 뒀지만,
--                  접속 주체와 소유자를 갈라 두면 그 실수의 여지 자체가 없어진다.
--   · NOSUPERUSER · NOCREATEDB · NOCREATEROLE · CREATE 권한 회수
--                — 앱이 스키마를 바꾸는 경로를 두지 않는다. 마이그레이션은 소유자 롤로 돈다.
--
-- 사용
--   psql -v owner=colab_owner -v app=colab_app -v app_password=... \
--        -f services/core-api/ops/app-role.sql
--
-- psql 변수는 달러 인용 블록 안에서 치환되지 않는다 — 그래서 DO 블록 대신 \gexec 를 쓴다.

\set ON_ERROR_STOP on

-- 1) 소유자 롤 — 테이블을 소유하고 마이그레이션을 돌린다.
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOBYPASSRLS', :'owner')
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'owner')
\gexec

-- 2) 앱 롤 — core-api 가 이걸로만 접속한다.
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD %L',
              :'app', :'app_password')
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app')
\gexec

-- 3) 읽고 쓰기만 — DDL 은 없다.
GRANT USAGE ON SCHEMA public TO :"app";
REVOKE CREATE ON SCHEMA public FROM :"app";
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"app";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app";

-- 4) 마지막 확인 — 위 성질이 하나라도 깨졌으면 여기서 멈춘다. 조용히 통과시키지 않는다.
SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''앱 롤이 superuser 이거나 BYPASSRLS 다 — 경계 증명이 거짓 green 이 된다.''; END $check$'
  FROM pg_roles WHERE rolname = :'app' AND (rolsuper OR rolbypassrls)
\gexec

SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''앱 롤이 테이블 소유자다 — 소유자와 접속 주체를 갈라 둔다.''; END $check$'
  FROM pg_tables t JOIN pg_roles r ON r.rolname = t.tableowner
 WHERE t.schemaname = 'public' AND r.rolname = :'app'
 LIMIT 1
\gexec
