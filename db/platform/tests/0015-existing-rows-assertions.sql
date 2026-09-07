-- 0015 「기존 행」 오라클 — **적재된 데이터 위에서 무엇이 일어났는가**.
--
-- 수용 기준 축자 (R-B-1-db.md §2 WU-B1) —
--   「Given 마이그레이션 적용, When `SELECT topic, category FROM d3_dataset_description`,
--    Then 전 행이 `category IS NULL` 이고 `topic` 값은 그대로다.」
--
-- ⭑ 이 오라클은 **「채웠다」가 아니라 「안 채웠다」를 잰다**. 0013 의 백필 오라클과 반대
--    방향이고, 그래서 대조군도 반대다 — `0015-drift.sh` ㈑-b 가 **백필을 흉내 낸 DB** 를
--    만들어 이 오라클이 거기서 red 를 내는지를 본다(오라클이 오라클임의 증명).
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0015 기존 행 오라클 실패 — %', msg; END $$;

-- ⑴ **전 행 `category IS NULL`** — 자동 매핑이 없다 (미결-3 ⓐ).
DO $$
DECLARE n bigint; sample text;
BEGIN
  SELECT count(*), min(category) INTO n, sample
    FROM d3_dataset_description WHERE category IS NOT NULL;
  IF n > 0 THEN
    PERFORM _t_fail(format('category 가 채워진 기존 행이 %s 건이다 (예: %L) — backfill 을 돌렸다',
                           n, sample));
  END IF;
END $$;

-- ⑵ **전 행 `data_type IS NULL`** — 대응 관계가 존재하지 않는 신규 축이다 (PRD-02).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset_description WHERE data_type IS NOT NULL;
  IF n > 0 THEN
    PERFORM _t_fail(format('data_type 이 채워진 기존 행이 %s 건이다 — 자동 매핑을 만들었다', n));
  END IF;
END $$;

-- ⑶ **전 행 `processing_level_user_set IS NULL`** — 파생값을 사람 값 자리에 복사하면
--    두 값의 구분이 영구히 사라진다 (PRD-03 축자 「일괄 backfill 을 하지 않는다」).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset WHERE processing_level_user_set IS NOT NULL;
  IF n > 0 THEN
    PERFORM _t_fail(format('processing_level_user_set 이 채워진 기존 행이 %s 건이다 — '
                           '파생값을 복사했다(두 값의 구분이 사라진다)', n));
  END IF;
END $$;

-- ⑷ **`topic` 값이 그대로다** — 6값이 하나도 안 사라지고 하나도 안 바뀌었다.
--    이 열이 이관 대조 근거이자 되돌림 경로다 (§3-㉴).
DO $$
DECLARE got text; want text := '가뭄,강우·강수,식생·NDVI,지형·DEM,토지피복·LULC,파일 포맷 예제';
BEGIN
  SELECT string_agg(topic, ',' ORDER BY topic) INTO got
    FROM d3_dataset_description WHERE topic IS NOT NULL;
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('topic 집합이 %L 다 (기대 %L) — 분류를 세우면서 주제를 건드렸다',
                           got, want));
  END IF;
END $$;

-- ⑸ 행이 **한 건도 사라지지 않았다**. 열을 더하는 마이그레이션이 행을 지울 이유가 없다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset_description;
  IF n <> 7 THEN
    PERFORM _t_fail(format('기존 행이 %s 건 남았다 (심은 것은 7건) — 마이그레이션이 행을 건드렸다', n));
  END IF;
END $$;

ROLLBACK;
