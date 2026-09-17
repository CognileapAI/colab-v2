\set ON_ERROR_STOP on
BEGIN;
SELECT set_config('test.owner_expected', :'owner_expected', true);
SELECT set_config('app.current_lab', '0000000000000000000000000A', true);
DO $$
DECLARE n integer; expected integer := current_setting('test.owner_expected')::integer;
BEGIN
  -- 판정 롤이 RLS 를 우회하면 이 오라클은 아무것도 재지 않는다 (0033 오라클과 같은 규율).
  IF (SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user)
     OR EXISTS(SELECT 1 FROM pg_tables WHERE schemaname='public' AND tableowner=current_user) THEN
    RAISE EXCEPTION 'oracle role bypasses RLS';
  END IF;

  -- ⑴ **재는 것** — 관리자가 아닌 소유자(연구원 A1)가 자기 「나만 보기」 본체를 읽는가.
  --    0033 에서는 0행, `0032_private_owner_access` 뒤에는 1행이어야 한다.
  PERFORM set_config('app.current_account','000000000000000000000000A1',true);
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id='0000000000000000000000DSX1';
  IF n <> expected THEN
    RAISE EXCEPTION 'private owner read: expected %, got %',expected,n;
  END IF;
  UPDATE d3_file SET file_name=file_name WHERE dataset_id='0000000000000000000000DSX1';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> expected THEN
    RAISE EXCEPTION 'private owner write: expected %, got %',expected,n;
  END IF;

  -- ⑵ **음성 대조** — 소유 갈래는 소유자에게만 열린다. 같은 연구실이라는 이유로는 안 열린다.
  --    A1 은 교수 소유 DSA2 의 소유자도, 관리자도, 허용 대상도 아니다 → 두 상태 모두 0행.
  IF EXISTS(SELECT 1 FROM d3_file WHERE dataset_id='0000000000000000000000DSA2') THEN
    RAISE EXCEPTION 'ordinary researcher can access another owner private body';
  END IF;

  -- ⑶ **불변 대조** — 관리자 갈래(`0033_admin_body_access`)가 이 회차에 죽지 않았는가.
  --    교수는 소유자가 아니어도 자기 연구실 비공개 본체를 본다 → 두 상태 모두 1행.
  PERFORM set_config('app.current_account','00000000000000000000000AP1',true);
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id='0000000000000000000000DSX1';
  IF n <> 1 THEN
    RAISE EXCEPTION 'manager branch lost: professor private read got %',n;
  END IF;

  -- ⑷ **경계** — 다른 연구실 교수에게는 어느 상태에서도 열리지 않는다.
  PERFORM set_config('app.current_account','00000000000000000000000BP1',true);
  IF EXISTS(SELECT 1 FROM d3_file WHERE dataset_id='0000000000000000000000DSX1') THEN
    RAISE EXCEPTION 'foreign professor can access private body';
  END IF;

  -- ⑸ **소유 갈래가 연구실 경계를 열지 않는다** — 관리 권한을 켜도 대상 연구실 밖은 그대로다.
  PERFORM set_config('app.operator_manage','on',true);
  IF EXISTS(SELECT 1 FROM d3_file WHERE lab_id <> current_lab_id()) THEN
    RAISE EXCEPTION 'owner branch bypassed target lab boundary';
  END IF;
END $$;
ROLLBACK;
