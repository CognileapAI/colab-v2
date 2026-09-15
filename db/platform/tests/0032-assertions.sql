DO $$ BEGIN
  IF (SELECT is_nullable FROM information_schema.columns
       WHERE table_schema='public' AND table_name='d1_account' AND column_name='lab_id') <> 'YES' THEN
    RAISE EXCEPTION 'd1_account.lab_id must be nullable';
  END IF;
  IF (SELECT is_nullable FROM information_schema.columns
       WHERE table_schema='account_admin' AND table_name='login_session' AND column_name='lab_id') <> 'YES' THEN
    RAISE EXCEPTION 'login_session.lab_id must be nullable';
  END IF;
END $$;
INSERT INTO d1_account(id,lab_id,name,email)
VALUES ('00000000000000000000000N32',NULL,'무소속 관리자','labless-0032@example.com');
INSERT INTO account_admin.service_operator(account_id)
VALUES ('00000000000000000000000N32');
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM d2_member_role WHERE account_id='00000000000000000000000N32') THEN
    RAISE EXCEPTION 'labless operator must not receive a member role';
  END IF;
END $$;
