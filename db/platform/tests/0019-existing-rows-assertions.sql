-- 0019 「기존 행」 오라클 — 0018 상태에 심은 두 행 위에 델타를 적용한 뒤 잰다.
--
-- ⭑ **동작으로 잰다** — 색인식을 grep 하지 않고 「그 낱말로 잡히는가」를 묻는다.
-- ⭑ **대조군이 있어야 오라클이다** — `netcdf`·변수명은 **종전에도 잡히던 것**이고 여기서
--    red 가 나면 이 회차가 회귀를 낸 것이다. `nc`·`evapotranspiration` 은 **종전에 안
--    잡히던 것**이고 여기서 green 이 나야 이 회차가 실제로 무엇을 했다는 뜻이다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0019 기존 행 오라클 실패 — %', msg; END $$;

CREATE FUNCTION _t_hits(ds text, word text) RETURNS boolean LANGUAGE sql STABLE AS $$
  SELECT coalesce((SELECT a.search_vector @@ to_tsquery('simple', word)
                     FROM d3_dataset_autometa a WHERE a.dataset_id = ds), false)
$$;

SET app.current_lab = '0000000000000000000000000T';

-- ⓪ 재료가 실재하는가. **빈 집합 통과를 막는다** — 두 행이 없으면 아래 전부가 공짜 green 이다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset_autometa
   WHERE dataset_id IN ('000000000000000000000DSM1A', '000000000000000000000DSM2A');
  IF n <> 2 THEN PERFORM _t_fail(format('재료가 %s 행이다 (기대 2)', n)); END IF;
END $$;

-- ① **`nc` 로 잡힌다** — R-A 이월 1건(PRD-21)이 여기서 닫힌다.
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM1A', 'nc') THEN
    PERFORM _t_fail('기존 행이 `nc` 로 안 잡힌다 — 색인 재정의가 전 행에 안 미쳤다');
  END IF;
END $$;

-- ② **`netcdf` 는 종전과 같이 잡힌다**(회귀 대조군).
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM1A', 'netcdf') THEN
    PERFORM _t_fail('`netcdf` 가 안 잡힌다 — format 을 잃었다 (회귀)');
  END IF;
END $$;

-- ③ **이관된 변수명이 종전과 같이 잡힌다**(회귀 대조군).
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM1A', 'precipitation') THEN
    PERFORM _t_fail('이관된 변수명이 안 잡힌다 — 회귀다');
  END IF;
END $$;

-- ④ **행 표에만 있던 변수명이 처음으로 잡힌다** — `0016` 이 남긴 잔여 위험이 닫혔다.
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM2A', 'evapotranspiration') THEN
    PERFORM _t_fail('행 표에만 있던 변수명이 안 잡힌다 — 배열 백필이 안 돌았다');
  END IF;
END $$;

-- ⑤ 분류 미러가 **전수** 백필됐다 (NULL 인 행은 NULL 그대로 — 지어내지 않는다).
DO $$
DECLARE bad bigint;
BEGIN
  SELECT count(*) INTO bad
    FROM d3_dataset_autometa a JOIN d3_dataset_description dd ON dd.dataset_id = a.dataset_id
   WHERE a.category_mirror IS DISTINCT FROM dd.category;
  IF bad <> 0 THEN PERFORM _t_fail(format('분류 미러가 원천과 다른 행 %s 건', bad)); END IF;
  IF NOT _t_hits('000000000000000000000DSM1A', '수문') THEN
    PERFORM _t_fail('분류로 안 잡힌다 — 미러가 색인에 안 물렸다');
  END IF;
END $$;

-- ⑥ 변수 미러가 **행 표와 같다** (전수).
DO $$
DECLARE bad bigint;
BEGIN
  SELECT count(*) INTO bad FROM d3_dataset_autometa a
   WHERE a.variables IS DISTINCT FROM coalesce(
           (SELECT array_agg(v.name ORDER BY v.ordinal)
              FROM d3_dataset_variable v WHERE v.dataset_id = a.dataset_id), '{}'::text[]);
  IF bad <> 0 THEN PERFORM _t_fail(format('변수 미러가 행 표와 다른 행 %s 건', bad)); END IF;
END $$;

-- ⑦ **새 행도 트리거로 따라온다** — 백필만 하고 트리거를 안 세우면 여기서 red 다.
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name) VALUES
  ('000000000000000000000DSM2A', '0000000000000000000000000T', 2, 'sublimation');
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM2A', 'sublimation') THEN
    PERFORM _t_fail('새로 넣은 변수 행이 색인에 안 들어온다 — 미러 트리거가 없다');
  END IF;
END $$;

DELETE FROM d3_dataset_variable
 WHERE dataset_id = '000000000000000000000DSM2A' AND ordinal = 2;
DO $$
BEGIN
  IF _t_hits('000000000000000000000DSM2A', 'sublimation') THEN
    PERFORM _t_fail('지운 변수 행이 아직 색인에 있다 — 미러가 지우기를 안 따라간다');
  END IF;
END $$;

ROLLBACK;
