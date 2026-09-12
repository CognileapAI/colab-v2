DO $$ BEGIN
  IF to_regclass('account_admin.login_credential') IS NULL THEN
    RAISE EXCEPTION 'login credential table missing';
  END IF;
  IF to_regclass('account_admin.service_operator') IS NULL THEN
    RAISE EXCEPTION 'service operator table missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
     WHERE conrelid='account_admin.login_credential'::regclass AND contype='u'
  ) THEN RAISE EXCEPTION 'login name unique missing'; END IF;
END $$;
