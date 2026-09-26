-- 0012 오라클 — `0012_region_south_korea` 가 **무엇을 넣었는가**를 SQL 로 잰다.
--
-- 이 파일은 `0012-drift.sh` 의 ㈎(head 판)에서 **통과**하고 ㈏(0011 판)·㈐(downgrade 판)에서
-- **실패해야** 한다 (`0010-assertions.sql` 과 같은 규율).

\set ON_ERROR_STOP on

DO $$
DECLARE
  n int;
BEGIN
  -- ① 남한 지명 노드가 등급 ② 로 있다. 노드에는 등급 ⑥ 이 없다(K1b §A).
  SELECT count(*) INTO n FROM d9_concept
   WHERE (concept_id, kind, label, source_grade, expandable) IN (('p-south-korea', '지명', '남한', 2, true));
  IF n <> 1 THEN
    RAISE EXCEPTION '0012 오라클 ① — 남한 지명 노드(p-south-korea · 등급 ②)가 없다';
  END IF;

  -- ② 엣지 방향 — src=남한(하위) · dst=한반도(상위). 확장은 dst→src 로만 가므로 이 방향이어야
  --    「한반도」 질의가 남한을 데려온다. 거꾸로 적히면 「남한」 질의가 한반도로 **올라간다**.
  SELECT count(*) INTO n FROM d9_concept_edge
   WHERE src = 'p-south-korea' AND relation = '안에 있다' AND dst = 'p-korea-peninsula' AND source_grade = 6;
  IF n <> 1 THEN
    RAISE EXCEPTION '0012 오라클 ② — 「남한 안에 있다 한반도」(등급 ⑥)가 없다';
  END IF;
  SELECT count(*) INTO n FROM d9_concept_edge
   WHERE src = 'p-korea-peninsula' AND dst = 'p-south-korea';
  IF n <> 0 THEN
    RAISE EXCEPTION '0012 오라클 ② — 한반도→남한 역방향 엣지가 %행 있다', n;
  END IF;

  -- ③ 한반도의 직계 하위(`안에 있다`)는 2 — 충청권 · 남한. 팬아웃 상한 6 안이다.
  SELECT count(*) INTO n FROM d9_concept_edge WHERE relation = '안에 있다' AND dst = 'p-korea-peninsula';
  IF n <> 2 THEN
    RAISE EXCEPTION '0012 오라클 ③ — 한반도의 안에 있다 하위가 2 가 아니라 %다', n;
  END IF;

  -- ④ 별칭 2행 — 남한·대한민국 → 남한.
  SELECT count(*) INTO n FROM d9_place_alias
   WHERE (alias, place_name) IN (('남한', '남한'), ('대한민국', '남한'));
  IF n <> 2 THEN
    RAISE EXCEPTION '0012 오라클 ④ — 지명 별칭 남한·대한민국 중 %건만 있다', n;
  END IF;

  -- ⑤ 총계 — 노드 55 · 엣지 21 · 등급 ⑥ 엣지 9 (기준 TSV 와 같은 수).
  SELECT count(*) INTO n FROM d9_concept;
  IF n <> 55 THEN
    RAISE EXCEPTION '0012 오라클 ⑤ — 개념 노드가 55 가 아니라 %다', n;
  END IF;
  SELECT count(*) INTO n FROM d9_concept_edge;
  IF n <> 21 THEN
    RAISE EXCEPTION '0012 오라클 ⑤ — 개념 엣지가 21 이 아니라 %다', n;
  END IF;
  SELECT count(*) INTO n FROM d9_concept_edge WHERE source_grade = 6;
  IF n <> 9 THEN
    RAISE EXCEPTION '0012 오라클 ⑤ — 등급 ⑥ 엣지가 9 가 아니라 %다', n;
  END IF;
  SELECT count(*) INTO n FROM d9_concept WHERE source_grade = 6;
  IF n <> 0 THEN
    RAISE EXCEPTION '0012 오라클 ⑤ — 등급 ⑥ 노드가 %건 생겼다', n;
  END IF;

  -- ⑥ 관계값은 3값 그대로다.
  SELECT count(*) INTO n FROM d9_concept_edge
   WHERE relation NOT IN ('같은 말이다', '~의 한 가지다', '안에 있다');
  IF n <> 0 THEN
    RAISE EXCEPTION '0012 오라클 ⑥ — CHECK 3값 밖의 relation 이 %행 있다', n;
  END IF;
END $$;
