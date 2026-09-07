-- 0018 「기존 행」 오라클 — **적재된 데이터 위에서 무엇이 일어났는가**.
--
-- 수용 기준·PRD-19 축자 — 「두 컬럼 전 행 NULL. 필수 검사가 없으므로 기존 행의 수정이
-- 막히지 않는다.」 · 「파생 Lv≥1 이면서 `source_label` 에 값이 있는 행은 그 값을 지우지
-- 않고 계속 보인다. 재선택을 요구하지 않는다.」
--
-- ⭑ 이 오라클은 **「채웠다」가 아니라 「안 채웠다」를 잰다**(`0015` 와 같은 방향).
--    그래서 대조군도 같은 방향이다 — `0018-drift.sh` ㈑-b 가 **백필을 흉내 낸 DB** 를
--    만들어 이 오라클이 거기서 red 를 내는지를 본다(오라클이 오라클임의 증명).
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0018 기존 행 오라클 실패 — %', msg; END $$;

-- ⑴ **전 행 `source_url IS NULL`** — `source_label` 은 출처의 **이름**이지 주소가 아니다.
--    옮겨 담으면 그 순간 거짓 주소가 기존 행에 박힌다.
DO $$
DECLARE n bigint; sample text;
BEGIN
  SELECT count(*), min(source_url) INTO n, sample
    FROM d3_dataset WHERE source_url IS NOT NULL;
  IF n > 0 THEN
    PERFORM _t_fail(format('source_url 이 채워진 기존 행이 %s 건이다 (예: %L) — backfill 을 돌렸다',
                           n, sample));
  END IF;
END $$;

-- ⑵ **전 행 `source_downloaded_on IS NULL`** — 내려받은 날은 어디에도 기록돼 있지 않다.
--    `uploaded_at` 을 옮겨 적으면 「올린 날」과 「받은 날」이 영구히 뒤섞인다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset WHERE source_downloaded_on IS NOT NULL;
  IF n > 0 THEN
    PERFORM _t_fail(format('source_downloaded_on 이 채워진 기존 행이 %s 건이다 — '
                           '올린 날을 받은 날로 옮겨 적었다', n));
  END IF;
END $$;

-- ⑶ **`source_label` 값이 그대로다** — 하나도 안 사라지고 하나도 안 바뀌었다 (미결-11 ⓐ).
DO $$
DECLARE got text; want text := 'ECMWF ERA5,NASA MODIS,기상청 GK2A';
BEGIN
  SELECT string_agg(source_label, ',' ORDER BY source_label) INTO got
    FROM d3_dataset WHERE source_label IS NOT NULL;
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('source_label 집합이 %L 다 (기대 %L) — 두 칸을 세우면서 원천 표기를 건드렸다',
                           got, want));
  END IF;
END $$;

-- ⑷ **기존 행의 수정이 막히지 않는다** — 필수 검사가 없다(PRD-19 「기존 데이터」 축자).
--    두 칸이 빈 채로 이름을 고치는 것이 이 회차 뒤에도 성립해야 한다.
DO $$
BEGIN
  UPDATE d3_dataset_description SET name = '이름만 고친다'
   WHERE dataset_id = '000000000000000000000DST1A';
  UPDATE d3_dataset SET source_label = 'ECMWF ERA5 (수정)'
   WHERE id = '000000000000000000000DST1A';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('두 칸이 빈 기존 행의 수정이 막혔다 — 필수 검사를 세웠다');
END $$;

-- ⑸ 행이 **한 건도 사라지지 않았다**. 열을 더하는 마이그레이션이 행을 지울 이유가 없다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset;
  IF n <> 5 THEN
    PERFORM _t_fail(format('기존 행이 %s 건 남았다 (심은 것은 5건) — 마이그레이션이 행을 건드렸다', n));
  END IF;
END $$;

ROLLBACK;
