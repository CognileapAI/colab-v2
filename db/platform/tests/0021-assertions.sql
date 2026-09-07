-- 0021 되돌림 오라클 — **옮긴 행이 정확히 NULL 로 돌아왔는가**.
--
-- 되돌림 축자 (`R-C-1-contract-db.md §2` WU-C7 되돌림) — 「`지정 공개`→`잠김` 역이관
-- (값 소실 0)」. 이 행들의 연구실 기본값이 `잠김` 이라 **NULL 이 곧 `잠김`** 이고,
-- `0017` 이 남긴 원래 값이 정확히 NULL 이었다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0021 되돌림 오라클 실패 — %', msg; END $$;

DO $$
DECLARE s text;
BEGIN
  SELECT state INTO s FROM d2_dataset_access WHERE dataset_id = '00000000000000000000000DS1';
  IF s IS NOT NULL THEN
    PERFORM _t_fail(format('DS1 이 %L 다 (기대 NULL) — 되돌림이 원래 값으로 안 갔다', s));
  END IF;
END $$;

-- 나머지 둘은 **애초에 안 옮겼으니 그대로**다.
DO $$
DECLARE s2 text; s3 text;
BEGIN
  SELECT state INTO s2 FROM d2_dataset_access WHERE dataset_id = '00000000000000000000000DS2';
  SELECT state INTO s3 FROM d2_dataset_access WHERE dataset_id = '00000000000000000000000DS3';
  IF s2 IS NOT NULL THEN PERFORM _t_fail(format('DS2 가 %L 다 (기대 NULL)', s2)); END IF;
  IF s3 IS DISTINCT FROM '잠김' THEN PERFORM _t_fail(format('DS3 가 %L 다 (기대 잠김)', s3)); END IF;
END $$;

-- **값 소실 0** — grant 줄은 한 줄도 안 사라졌다(되돌림이 허용 목록을 건드리지 않는다).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access_grant WHERE expires_at > now();
  IF n <> 2 THEN PERFORM _t_fail(format('유효 grant 가 %s 건이다 (기대 2) — 되돌림이 허용 목록을 건드렸다', n)); END IF;
END $$;

ROLLBACK;
