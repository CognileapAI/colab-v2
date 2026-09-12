DO $$ BEGIN
  IF to_regclass('account_admin.login_session') IS NULL THEN
    RAISE EXCEPTION 'login session table missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
     WHERE conrelid='account_admin.login_session'::regclass
       AND contype='u'
  ) THEN RAISE EXCEPTION 'revoke digest unique missing'; END IF;
  IF has_table_privilege('public', 'account_admin.login_session', 'SELECT') THEN
    RAISE EXCEPTION 'PUBLIC can read login sessions';
  END IF;
END $$;
