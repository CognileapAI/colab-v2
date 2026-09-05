-- 0013 백필 오라클 — **기존 행의 `file_extension` 이 파일명과 일치하는가** (PRD-21 수용 기준 ④).
--
-- `0013-backfill-seed.sql` 이 0011 상태의 DB 에 심은 네 장면 위에서 돈다.
-- 백필 없이 열만 세운 DB 에서는 반드시 실패한다 — 그것이 이 파일이 오라클인 이유다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0013 백필 오라클 실패 — %', msg; END $$;

-- ⑴ 네 행의 값이 파일명과 **일치한다**. 조각이 둘이어도 데이터셋당 1값이다 (`P-5`).
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('0000000000000000000000DST1', 'nc'),
      ('0000000000000000000000DST2', 'hdf'),
      ('0000000000000000000000DST3', NULL),
      ('0000000000000000000000DST4', 'nc')) AS v(id, want)
  LOOP
    IF (SELECT file_extension FROM d3_dataset_autometa WHERE dataset_id = r.id)
       IS DISTINCT FROM r.want THEN
      PERFORM _t_fail(format('%s 의 확장자가 %L 다 — 기대 %L',
        r.id,
        (SELECT file_extension FROM d3_dataset_autometa WHERE dataset_id = r.id),
        r.want));
    END IF;
  END LOOP;
END $$;

-- ⑵ **대소문자를 접는다** — `A.NC` 는 `nc` 다 (PRD-32 · 화면 규칙과 어긋나지 않는다).
--   ⑴ 의 DST4 가 이미 그것을 재고, 여기서는 「접히지 않은 값이 어디에도 없다」를 전수로 센다.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset_autometa
   WHERE file_extension IS NOT NULL AND file_extension <> lower(file_extension);
  IF n > 0 THEN PERFORM _t_fail(format('소문자로 접히지 않은 확장자가 %s 건이다', n)); END IF;
END $$;

-- ⑶ **격자 파일이 값을 정하지 않는다.** DST4 의 `grid.tif` 가 이겼다면 `tif` 가 들어 있다.
DO $$
BEGIN
  IF (SELECT file_extension FROM d3_dataset_autometa
       WHERE dataset_id = '0000000000000000000000DST4') = 'tif' THEN
    PERFORM _t_fail('기준 격자 파일의 확장자가 데이터셋의 값을 덮었다 — 조각(본체)만 세야 한다');
  END IF;
END $$;

-- ⑷ 판별 결과(`format`)를 **지우지도 덮지도 않았다** — 퇴행 표시의 재료이자 되돌림 경로다.
DO $$
DECLARE f text;
BEGIN
  SELECT format INTO f FROM d3_dataset_autometa
   WHERE dataset_id = '0000000000000000000000DST3';
  IF f IS DISTINCT FROM 'NetCDF-4' THEN
    PERFORM _t_fail(format('확장자를 못 뽑은 행의 format 이 %L 로 바뀌었다 — 퇴행 표시가 사라진다', f));
  END IF;
END $$;

ROLLBACK;
