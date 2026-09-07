-- 0017 「기존 행」 오라클 — **적재된 데이터 위에서 매핑이 무엇을 했는가**.
--
-- 수용 기준 축자 (`R-B-1-db.md §2` WU-B4) 셋을 여기서 잰다 —
--   ㈎ 「Given 마이그레이션 적용, When 유효 grant 를 가진 잠김 데이터셋 조회, Then 상태가
--      `지정 공개` 이고 그 사람의 접근이 종전과 같다(**양성·음성 둘 다**).」
--   ㈏ 「Given 어느 시점이든, When `state='잠김'` 인 데이터셋의 유효 grant 를 셈, Then 0건.」
--   ㈐ 「Given 연구실 밖 계정, When 어느 상태의 데이터셋이든 조회, Then 보이지 않는다.」
--
-- ⭑ 이 오라클은 「넓혔다」와 **「유효 grant 유무로 갈라 옮겼다」**를 가른다. 대조군
--    (`0017-drift.sh` ㈑-b)은 만료된 grant 를 유효로 바꿔 놓은 DB 이고, 거기서 red 가
--    나야 이 오라클이 오라클이다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0017 기존 행 오라클 실패 — %', msg; END $$;

-- 정책이 FORCE 라 소유자 세션도 스코프가 필요하다.
SET app.current_lab = '0000000000000000000000000T';

-- ⑴ **네 갈래가 각자의 값으로 간다.** 이 한 줄이 매핑표 전체다.
DO $$
DECLARE got text;
        want text := 'DSC1A:지정 공개,DSC2A:잠김,DSC3A:열림';
BEGIN
  SELECT string_agg(right(dataset_id, 5) || ':' || state, ',' ORDER BY dataset_id) INTO got
    FROM d2_dataset_access;
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('매핑 결과가 %L 다 (기대 %L) — 잠김 ∧ 유효 grant ≥1 만 지정 공개로 간다',
                           coalesce(got, '(0건)'), want));
  END IF;
END $$;

-- ⑵ **NULL→NULL** — 상태 행이 없던 데이터셋에 행을 지어내지 않는다(연구실 기본값 경로).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access
   WHERE dataset_id = '000000000000000000000DSC4A';
  IF n <> 0 THEN
    PERFORM _t_fail(format('상태 행이 없던 데이터셋에 %s 건이 생겼다 — NULL 이 값으로 굳었다', n));
  END IF;
END $$;

-- ⑶ **불변식** — `잠김` ∧ 유효 grant ≥1 인 행이 0건이다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n
    FROM d2_dataset_access a
   WHERE a.state = '잠김'
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());
  IF n <> 0 THEN
    PERFORM _t_fail(format('잠김 ∧ 유효 grant ≥1 인 행이 %s 건이다 — 매핑이 그 자리를 안 옮겼다', n));
  END IF;
END $$;

-- ⑷ **허용 줄을 건드리지 않았다** — 매핑은 상태만 옮긴다. 두 줄이 그대로 있다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access_grant;
  IF n <> 2 THEN
    PERFORM _t_fail(format('허용 줄이 %s 건이다 (기대 2) — 매핑이 grant 를 만졌다', n));
  END IF;
END $$;

-- ⑸ **접근이 종전과 같다 — 양성·음성 둘 다.** 비소유자 롤로 잰다(superuser 는 RLS 를
--    언제나 우회하므로 그 롤의 「보인다·안 보인다」는 오라클이 아니다).
CREATE ROLE t_app2 NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT USAGE ON SCHEMA public TO t_app2;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO t_app2;
SET ROLE t_app2;
SET app.current_lab = '0000000000000000000000000T';
SET app.current_account = '00000000000000000000000TR1';

DO $$
DECLARE yes bigint; no bigint;
BEGIN
  -- 양성 — 유효 grant 를 가진 사람은 `지정 공개` 가 된 뒤에도 본체가 보인다.
  SELECT count(*) INTO yes FROM d3_file WHERE dataset_id = '000000000000000000000DSC1A';
  IF yes <> 1 THEN
    PERFORM _t_fail(format('허용자에게 DSC1 의 본체가 %s 행이다 (기대 1) — 매핑이 접근을 바꿨다', yes));
  END IF;
  -- 음성 — 만료된 줄뿐인 데이터셋은 종전대로 안 보인다.
  SELECT count(*) INTO no FROM d3_file WHERE dataset_id = '000000000000000000000DSC2A';
  IF no <> 0 THEN
    PERFORM _t_fail(format('만료된 허용 줄뿐인 DSC2 의 본체가 %s 행 보인다 — 매핑이 경계를 열었다', no));
  END IF;
END $$;

-- ⑹ **cross-tenant 음성** — 연구실 밖 스코프에서는 어느 상태든 0건이다(RLS 무개방).
SET app.current_lab = '0000000000000000000000000B';
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access;
  IF n <> 0 THEN
    PERFORM _t_fail(format('연구실 밖 스코프에서 상태 행이 %s 건 보인다 — 3값이 경계를 열었다', n));
  END IF;
END $$;

RESET ROLE;
ROLLBACK;
