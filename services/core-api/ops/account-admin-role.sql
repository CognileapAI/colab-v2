-- Stage 3 계정 관리자 접속 롤. 일반 앱 롤과 자격을 공유하지 않는다.
-- 사용:
-- psql -v admin=colab_account_admin -v admin_password=... -f services/core-api/ops/account-admin-role.sql
\set ON_ERROR_STOP on
SELECT format(
  'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT BYPASSRLS PASSWORD %L',
  :'admin', :'admin_password')
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'admin')
\gexec
-- 기존 동명 롤이 다른 롤을 SET ROLE 할 수 있거나 객체 소유자면 권한을 줄여도 좁은 롤이 아니다.
SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''계정 관리자 롤에 기존 role membership이 있다''; END $check$'
 WHERE EXISTS (
   SELECT 1 FROM pg_auth_members m
   JOIN pg_roles r ON r.oid=m.member
   WHERE r.rolname=:'admin')
\gexec
SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''계정 관리자 롤이 현재 DB 객체를 소유한다''; END $check$'
 WHERE EXISTS (
   SELECT 1 FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner WHERE r.rolname=:'admin'
   UNION ALL
   SELECT 1 FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner WHERE r.rolname=:'admin')
\gexec
SELECT format('ALTER ROLE %I NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT BYPASSRLS PASSWORD %L',
              :'admin', :'admin_password')
\gexec
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM :"admin";
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA account_admin FROM :"admin";
REVOKE ALL ON SCHEMA public, account_admin FROM :"admin";
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'admin')
\gexec
GRANT USAGE ON SCHEMA public, account_admin TO :"admin";
REVOKE CREATE ON SCHEMA public, account_admin FROM :"admin";
GRANT SELECT ON d1_lab, d1_account TO :"admin";
-- 계정 목록의 **역할 열**이 `d2_member_role` 를 읽는다. 발급만 하던 시절에는 INSERT 뿐이었다.
GRANT SELECT ON d2_member_role TO :"admin";
GRANT INSERT ON d1_account, d2_member_role TO :"admin";
GRANT SELECT, INSERT, UPDATE ON account_admin.login_credential TO :"admin";
-- 운영자 지정·해제(백오피스)가 이 표에 쓴다. UPDATE 는 주지 않는다 — 행은 있거나 없거나다.
GRANT SELECT, INSERT, DELETE ON account_admin.service_operator TO :"admin";
GRANT SELECT, INSERT, UPDATE ON account_admin.login_session TO :"admin";

SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''계정 관리자 롤이 superuser다''; END $check$'
  FROM pg_roles WHERE rolname=:'admin'
   AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR NOT rolbypassrls)
\gexec
