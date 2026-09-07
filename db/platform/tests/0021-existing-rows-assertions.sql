-- 0021 기존 행 오라클 — **픽스처 3종 중 첫 것만 옮긴다**.
--
-- 수용 기준 축자 (`R-C-1-contract-db.md §2` WU-C7) — 「`0021` 픽스처 3종
-- (NULL∧잠김∧grant / NULL∧열림 / 잠김∧grant0) 중 **첫 것만** `지정 공개`」 ＋
-- 「`state='잠김'` ∧ 유효 grant ≥1 행 **어느 시점에도 0건**」.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0021 기존 행 오라클 실패 — %', msg; END $$;

CREATE FUNCTION _t_state(ds text) RETURNS text LANGUAGE sql STABLE AS $$
  SELECT state FROM d2_dataset_access WHERE dataset_id = ds
$$;

-- ㈎ NULL ∧ 연구실 기본 `잠김` ∧ 유효 grant ≥1 → **지정 공개**
DO $$
BEGIN
  IF _t_state('00000000000000000000000DS1') IS DISTINCT FROM '지정 공개' THEN
    PERFORM _t_fail(format('㈎ DS1 이 %L 다 (기대 지정 공개) — 빈틈이 안 닫혔다',
                           _t_state('00000000000000000000000DS1')));
  END IF;
END $$;

-- ㈏ NULL ∧ 연구실 기본 `열림` → **NULL 그대로**. 기본값이 넓으면 빈틈이 아니다.
DO $$
BEGIN
  IF _t_state('00000000000000000000000DS2') IS NOT NULL THEN
    PERFORM _t_fail(format('㈏ DS2 가 %L 다 (기대 NULL) — 연구실 기본값을 안 갈랐다',
                           _t_state('00000000000000000000000DS2')));
  END IF;
END $$;

-- ㈐ 명시 `잠김` ∧ 유효 grant 0건 → **잠김 그대로**. NULL 행만 대상이다.
DO $$
BEGIN
  IF _t_state('00000000000000000000000DS3') IS DISTINCT FROM '잠김' THEN
    PERFORM _t_fail(format('㈐ DS3 가 %L 다 (기대 잠김) — 명시값을 건드렸다',
                           _t_state('00000000000000000000000DS3')));
  END IF;
END $$;

-- 옮긴 행이 **정확히 하나**다 — 「이동 행 수 1」이 수용 기준의 숫자다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access WHERE state = '지정 공개';
  IF n <> 1 THEN PERFORM _t_fail(format('지정 공개 행이 %s 건이다 (기대 1)', n)); END IF;
END $$;

-- 불변식 — `잠김` ∧ 유효 grant ≥1 은 **0건**이다 (R-B 경계 증명 유지).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access a
   WHERE a.state = '잠김'
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());
  IF n <> 0 THEN PERFORM _t_fail(format('잠김 ∧ 유효 grant ≥1 인 행이 %s 건이다 (기대 0)', n)); END IF;
END $$;

-- ⛔ **행이 늘거나 줄지 않았다** — 없는 상태 행을 지어내지 않는다(판정 20 「상태 행 NULL」).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access;
  IF n <> 3 THEN PERFORM _t_fail(format('상태 행이 %s 건이다 (기대 3) — 행을 지어냈거나 지웠다', n)); END IF;
END $$;

ROLLBACK;
