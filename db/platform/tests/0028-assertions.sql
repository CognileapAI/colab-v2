-- 0028 오라클 — 계정 상태 열이 서고, 기본값·NOT NULL·허용값이 **실제로** 걸려 있다.
-- 0026 판(이전 head)과 downgrade 판에서는 이 파일이 실패해야 한다 (`0028-drift.sh` 가 판정한다).
DO $$
DECLARE current_status text;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema='account_admin' AND table_name='login_credential'
       AND column_name='status' AND is_nullable='NO'
       AND column_default LIKE '%active%'
  ) THEN RAISE EXCEPTION 'login_credential.status 가 없거나 NOT NULL·기본값이 아니다'; END IF;

  -- 카탈로그만 보면 「CHECK 이 있다」까지다. 실제로 막는지는 넣어 봐야 안다.
  INSERT INTO d1_lab(id, name, opened_at)
    VALUES ('0000000000000000000000ST01', '상태 오라클 연구실', now());
  INSERT INTO d1_account(id, lab_id, name, email)
    VALUES ('0000000000000000000000ST02', '0000000000000000000000ST01',
            '상태 오라클', 'status@oracle.test');
  INSERT INTO account_admin.login_credential
    (account_id, login_name, kdf, salt, password_hash, n, r, p)
    VALUES ('0000000000000000000000ST02', 'status@oracle.test',
            'scrypt', 'salt', 'hash', 16384, 8, 1);

  SELECT status INTO current_status FROM account_admin.login_credential
   WHERE account_id='0000000000000000000000ST02';
  IF current_status IS DISTINCT FROM 'active' THEN
    RAISE EXCEPTION '새 자격의 기본 상태가 active 가 아니다: %', current_status;
  END IF;

  BEGIN
    UPDATE account_admin.login_credential SET status='삭제됨'
     WHERE account_id='0000000000000000000000ST02';
    RAISE EXCEPTION '허용값 밖의 상태가 저장됐다 — CHECK 이 없다';
  EXCEPTION WHEN check_violation THEN NULL;
  END;

  UPDATE account_admin.login_credential SET status='inactive'
   WHERE account_id='0000000000000000000000ST02';

  -- 자격은 계정 삭제에 딸려 간다(ON DELETE CASCADE). 연구실은 계정을 먼저 지워야 지워진다.
  DELETE FROM d1_account WHERE id='0000000000000000000000ST02';
  DELETE FROM d1_lab WHERE id='0000000000000000000000ST01';
END $$;
