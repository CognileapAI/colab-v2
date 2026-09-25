\set ON_ERROR_STOP on
BEGIN;
-- `:reconciled_expected` = 1 이면 봉합된 상태를, 0 이면 봉합 전(구 체인) 상태를 기대한다.
-- 세 갈래만 기대값으로 흔들리고, 정책의 형태(RESTRICTIVE · FOR ALL)와 나머지 세 갈래는
-- **두 상태 모두 불변**이어야 한다 — 봉합이 정책을 다시 만들면 여기서 잡힌다.
SELECT set_config('test.reconciled_expected', :'reconciled_expected', true);
DO $$
DECLARE
  expected boolean := current_setting('test.reconciled_expected')::integer = 1;
  has_fn boolean;
  account_nullable boolean;
  session_nullable boolean;
  qual text;
  chk text;
  is_permissive boolean;
  policy_cmd "char";
BEGIN
  -- ① 관리자 판정 함수 — 서명·언어·휘발성까지 본다. 이름만 같고 속성이 다르면 schema-diff 가 red 다.
  -- 인자 형은 `proargtypes` 로 본다. `pg_get_function_identity_arguments` 는 길이 수식(26)을
  -- 떼고 내므로 `char(26)` 과 `text` 를 가르는 근거가 되지 못한다.
  SELECT EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
      JOIN pg_language l ON l.oid = p.prolang
    WHERE n.nspname = 'public'
      AND p.proname = 'is_dataset_manager'
      AND p.pronargs = 1
      AND p.proargtypes[0] = 'pg_catalog.bpchar'::regtype
      AND p.prorettype = 'pg_catalog.bool'::regtype
      AND l.lanname = 'sql'
      AND p.provolatile = 's'
  ) INTO has_fn;
  IF has_fn <> expected THEN
    RAISE EXCEPTION 'is_dataset_manager(char(26)) STABLE sql: 기대 %, 실측 %', expected, has_fn;
  END IF;

  -- ② 소속 없는 운영자 — lab_id 두 자리의 NOT NULL 이 풀려 있는가.
  SELECT NOT attnotnull INTO account_nullable
    FROM pg_attribute
   WHERE attrelid = 'public.d1_account'::regclass AND attname = 'lab_id' AND NOT attisdropped;
  IF account_nullable IS NULL THEN RAISE EXCEPTION 'd1_account.lab_id 열이 없다'; END IF;
  IF account_nullable <> expected THEN
    RAISE EXCEPTION 'd1_account.lab_id nullable: 기대 %, 실측 %', expected, account_nullable;
  END IF;

  SELECT NOT attnotnull INTO session_nullable
    FROM pg_attribute
   WHERE attrelid = 'account_admin.login_session'::regclass AND attname = 'lab_id' AND NOT attisdropped;
  IF session_nullable IS NULL THEN RAISE EXCEPTION 'account_admin.login_session.lab_id 열이 없다'; END IF;
  IF session_nullable <> expected THEN
    RAISE EXCEPTION 'account_admin.login_session.lab_id nullable: 기대 %, 실측 %', expected, session_nullable;
  END IF;

  -- ③ 파일 본체 정책 — 관리자 갈래만 기대값을 따르고 형태와 나머지 갈래는 불변이다.
  SELECT pg_get_expr(polqual, polrelid), pg_get_expr(polwithcheck, polrelid), polpermissive, polcmd
    INTO qual, chk, is_permissive, policy_cmd
    FROM pg_policy
   WHERE polrelid = 'public.d3_file'::regclass AND polname = 'body_access';
  IF qual IS NULL THEN RAISE EXCEPTION 'd3_file 의 body_access 정책이 없다'; END IF;

  IF is_permissive THEN RAISE EXCEPTION 'body_access 가 RESTRICTIVE 가 아니다'; END IF;
  IF policy_cmd <> '*' THEN RAISE EXCEPTION 'body_access 가 FOR ALL 이 아니다 (polcmd=%)', policy_cmd; END IF;
  IF chk IS NULL THEN RAISE EXCEPTION 'body_access 에 WITH CHECK 가 없다'; END IF;

  IF (qual LIKE '%is_dataset_manager%') <> expected THEN
    RAISE EXCEPTION 'body_access USING 관리자 갈래: 기대 %, 실측 %', expected, qual LIKE '%is_dataset_manager%';
  END IF;
  IF (chk LIKE '%is_dataset_manager%') <> expected THEN
    RAISE EXCEPTION 'body_access WITH CHECK 관리자 갈래: 기대 %, 실측 %', expected, chk LIKE '%is_dataset_manager%';
  END IF;

  IF qual NOT LIKE '%owner_account_id%' OR chk NOT LIKE '%owner_account_id%' THEN
    RAISE EXCEPTION 'body_access 에서 소유자 갈래가 사라졌다';
  END IF;
  IF qual NOT LIKE '%d2_dataset_access_grant%' OR chk NOT LIKE '%d2_dataset_access_grant%' THEN
    RAISE EXCEPTION 'body_access 에서 허용 줄 갈래가 사라졌다';
  END IF;
  IF qual NOT LIKE '%열림%' OR chk NOT LIKE '%열림%' THEN
    RAISE EXCEPTION 'body_access 에서 열림 갈래가 사라졌다';
  END IF;
END $$;
ROLLBACK;
