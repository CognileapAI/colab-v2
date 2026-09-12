-- migration owner만 실행한다. 교수/연구실 관리자에서 서비스 운영자로 자동 승격하지 않는다.
-- 사용: psql -v account_id=000... -f services/core-api/ops/provision-service-operator.sql
\set ON_ERROR_STOP on
INSERT INTO account_admin.service_operator(account_id)
SELECT id FROM d1_account WHERE id=:'account_id'
ON CONFLICT (account_id) DO NOTHING;
SELECT 'DO $check$ BEGIN RAISE EXCEPTION ''지정한 계정이 없어 운영자를 등록하지 못했다''; END $check$'
 WHERE NOT EXISTS (
   SELECT 1 FROM account_admin.service_operator WHERE account_id=:'account_id')
\gexec
