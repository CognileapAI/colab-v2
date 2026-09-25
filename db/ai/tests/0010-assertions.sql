-- 0010 오라클 — `0010_practitioner_concept` 이 **무엇을 넣었는가**를 SQL 로 잰다.
--
-- 이 파일은 `0010-drift.sh` 의 ㈎(head 판)에서 **통과**하고 ㈏(0009 판)·㈐(downgrade 판)에서
-- **실패해야** 한다. 한 판에서만 통과하는 것이 오라클이 이 회차를 잰다는 증거다 —
-- 세 판 모두에서 통과하면 이 파일은 아무 말도 하지 않는 것이다
-- (`0009-drift.sh` ㈏ · `db/platform/tests/0031-drift.sh` ㈏ 와 같은 규율).

\set ON_ERROR_STOP on

DO $$
DECLARE
  n int;
  g int;
BEGIN
  -- ① 원천표기 3노드가 등급 ⑤ 로 있고 label 이 정본 인용 그대로다.
  SELECT count(*) INTO n FROM d9_concept
   WHERE (concept_id, kind, label, source_grade, expandable) IN (
     ('s-era5',     '원천표기', 'ERA5',             5, true),
     ('s-ecmwf',    '원천표기', 'ECMWF',            5, true),
     ('s-ecmwf-ko', '원천표기', '유럽중기예보센터', 5, true));
  IF n <> 3 THEN
    RAISE EXCEPTION '0010 오라클 ① — 원천표기 3노드 중 %건만 기준대로 있다 (결정 4)', n;
  END IF;

  -- ② 주제 2노드가 등급 ① 로 있고 label 이 `d9_topic_synonym.topic` 값과 한 글자도 다르지 않다.
  SELECT count(*) INTO n FROM d9_concept
   WHERE (concept_id, kind, label, source_grade, expandable) IN (
     ('t-drought',    '주제', '가뭄',           1, true),
     ('t-fileformat', '주제', '파일 포맷 예제', 1, true));
  IF n <> 2 THEN
    RAISE EXCEPTION '0010 오라클 ② — 주제 2노드 중 %건만 기준대로 있다 (결정 5)', n;
  END IF;

  -- ③ 주제 노드 집합 = 동의어 사전의 주제 값 집합. **비대칭을 없앤 것이 이 회차의 내용이다.**
  SELECT count(*) INTO n FROM (
    SELECT label FROM d9_concept WHERE kind = '주제'
    EXCEPT SELECT topic FROM d9_topic_synonym) x;
  SELECT count(*) INTO g FROM (
    SELECT topic FROM d9_topic_synonym
    EXCEPT SELECT label FROM d9_concept WHERE kind = '주제') y;
  IF n <> 0 OR g <> 0 THEN
    RAISE EXCEPTION '0010 오라클 ③ — 주제 노드와 동의어 사전 주제가 갈렸다 (노드만 %건 · 사전만 %건)', n, g;
  END IF;

  -- ④ 엣지 1행. 등급 ⑤ 다 — ⑥ 이면 APPROVED_G6 승인 목록이 필요했을 것이다.
  SELECT count(*) INTO n FROM d9_concept_edge
   WHERE src = 's-ecmwf' AND relation = '같은 말이다' AND dst = 's-ecmwf-ko' AND source_grade = 5;
  IF n <> 1 THEN
    RAISE EXCEPTION '0010 오라클 ④ — E1-12(s-ecmwf ≡ s-ecmwf-ko, 등급 ⑤)가 없다';
  END IF;

  -- ⑤ 총계 — 노드 54 · 엣지 20. 기준 TSV(`k2b-graph-standard.tsv`)와 같은 수다.
  SELECT count(*) INTO n FROM d9_concept;
  IF n <> 54 THEN
    RAISE EXCEPTION '0010 오라클 ⑤ — 개념 노드가 54 가 아니라 %다', n;
  END IF;
  SELECT count(*) INTO n FROM d9_concept_edge;
  IF n <> 20 THEN
    RAISE EXCEPTION '0010 오라클 ⑤ — 개념 엣지가 20 이 아니라 %다', n;
  END IF;

  -- ⑥ ⛔ **등급 ⑥ 노드는 0 건이다** (`K1b §A`). 이 회차가 그 규약을 깨지 않는다.
  SELECT count(*) INTO n FROM d9_concept WHERE source_grade = 6;
  IF n <> 0 THEN
    RAISE EXCEPTION '0010 오라클 ⑥ — 등급 ⑥ 노드가 %건 생겼다 (노드에는 ⑥ 이 없다)', n;
  END IF;
  -- 등급 ⑥ 엣지도 8행 그대로다 — 새 엣지는 ⑤ 라 승인 목록이 흔들리지 않는다.
  SELECT count(*) INTO n FROM d9_concept_edge WHERE source_grade = 6;
  IF n <> 8 THEN
    RAISE EXCEPTION '0010 오라클 ⑥ — 등급 ⑥ 엣지가 8 이 아니라 %다 (APPROVED_G6 가 흔들렸다)', n;
  END IF;

  -- ⑦ ⚠ **`s-era5` 에 닿는 엣지는 0행이다.** ECMWF→ERA5 를 적을 관계값 「~이 제공한다」는
  --    결정 8 이 닫아 두었다. 여기가 통과해야 「ERA5 질의는 그래프로 안 넓혀진다」가 사실로
  --    남고, 오라클 `practitioner-lexical.json` LEX-15 의 blocked 가 근거를 갖는다.
  SELECT count(*) INTO n FROM d9_concept_edge WHERE src = 's-era5' OR dst = 's-era5';
  IF n <> 0 THEN
    RAISE EXCEPTION '0010 오라클 ⑦ — s-era5 에 엣지가 %행 붙었다. 결정 8 은 relation CHECK 를 열지 않았다', n;
  END IF;

  -- ⑧ 관계값은 3값 그대로다. 새 값이 들어오면 스키마 CHECK 가 열린 것이다.
  SELECT count(*) INTO n FROM d9_concept_edge
   WHERE relation NOT IN ('같은 말이다', '~의 한 가지다', '안에 있다');
  IF n <> 0 THEN
    RAISE EXCEPTION '0010 오라클 ⑧ — CHECK 3값 밖의 relation 이 %행 있다', n;
  END IF;

  -- ⑨ 기존 행을 지우지 않았다. `0009` 까지의 어휘(동의어 27 · 별칭 8)가 그대로 산다.
  SELECT count(*) INTO n FROM d9_topic_synonym;
  IF n < 27 THEN
    RAISE EXCEPTION '0010 오라클 ⑨ — 동의어가 %행뿐이다 (0009 뒤 27행 이상이어야 한다)', n;
  END IF;
  SELECT count(*) INTO n FROM d9_place_alias;
  IF n < 8 THEN
    RAISE EXCEPTION '0010 오라클 ⑨ — 지명 별칭이 %행뿐이다 (0009 뒤 8행 이상이어야 한다)', n;
  END IF;
END $$;
