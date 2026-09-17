\set ON_ERROR_STOP on
BEGIN;
SELECT set_config('test.manager_expected', :'manager_expected', true);
SELECT set_config('app.current_lab', '0000000000000000000000000A', true);
SELECT set_config('app.current_account', '000000000000000000000000A1', true);
DO $$
DECLARE n integer; expected integer := current_setting('test.manager_expected')::integer;
BEGIN
  IF (SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user)
     OR EXISTS(SELECT 1 FROM pg_tables WHERE schemaname='public' AND tableowner=current_user) THEN
    RAISE EXCEPTION 'oracle role bypasses RLS';
  END IF;
  IF EXISTS(SELECT 1 FROM d3_file WHERE dataset_id='0000000000000000000000DSA2') THEN
    RAISE EXCEPTION 'ordinary researcher can access private body';
  END IF;
  IF (SELECT count(*) FROM d3_dataset WHERE id='0000000000000000000000DSA2') <> 1 THEN
    RAISE EXCEPTION 'private dataset metadata disappeared';
  END IF;
  PERFORM set_config('app.current_account','00000000000000000000000AP1',true);
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id='0000000000000000000000DSA2';
  IF n <> expected THEN RAISE EXCEPTION 'professor private read: expected %, got %',expected,n; END IF;
  UPDATE d3_file SET file_name=file_name WHERE dataset_id='0000000000000000000000DSA2';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> expected THEN RAISE EXCEPTION 'professor private write: expected %, got %',expected,n; END IF;
  PERFORM set_config('app.current_account','00000000000000000000000BP1',true);
  IF EXISTS(SELECT 1 FROM d3_file WHERE dataset_id='0000000000000000000000DSA2') THEN
    RAISE EXCEPTION 'foreign professor can access private body';
  END IF;
  PERFORM set_config('app.operator_manage','on',true);
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id='0000000000000000000000DSA2';
  IF n <> expected THEN RAISE EXCEPTION 'system administrator private read: expected %, got %',expected,n; END IF;
  UPDATE d3_file SET file_name=file_name WHERE dataset_id='0000000000000000000000DSA2';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> expected THEN RAISE EXCEPTION 'system administrator private write: expected %, got %',expected,n; END IF;
  IF EXISTS(SELECT 1 FROM d3_file WHERE lab_id <> current_lab_id()) THEN
    RAISE EXCEPTION 'manager exception bypassed target lab boundary';
  END IF;
END $$;
ROLLBACK;
