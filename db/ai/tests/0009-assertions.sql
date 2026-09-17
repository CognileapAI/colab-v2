-- 0009 오라클 — `0009_practitioner_lexicon` 이 **무엇을 넣었는가**를 SQL 로 잰다.
--
-- 이 파일은 `0009-drift.sh` 의 ㈎(head 판)에서 **통과**하고 ㈏(0008 판)·㈐(downgrade 판)에서
-- **실패해야** 한다. 한 판에서만 통과하는 것이 오라클이 이 회차를 잰다는 증거다 —
-- 세 판 모두에서 통과하면 이 파일은 아무 말도 하지 않는 것이다
-- (`db/platform/tests/0031-drift.sh` ㈏ 와 같은 규율).

\set ON_ERROR_STOP on

DO $$
DECLARE
  syns text[] := ARRAY['강수량','강수','강우','강우량','강수자료',
                       '강우관측','집중호우','호우','precipitation'];
  aliases text[] := ARRAY['한반도','Korea','충청권',
                          'southern Gyeonggi and Chungcheong regions'];
  n int;
BEGIN
  -- ① 주제 동의어 9행이 **전부** 있고 **전부** 「강우·강수」다.
  SELECT count(*) INTO n FROM d9_topic_synonym
   WHERE synonym = ANY (syns) AND topic = '강우·강수';
  IF n <> 9 THEN
    RAISE EXCEPTION '0009 오라클 ① — 주제 동의어 9행 중 %건만 「강우·강수」로 있다', n;
  END IF;

  -- ② 그 9행의 `category` 는 NULL 이다. 분류 축 5값은 주제 축과 다른 축이고
  --    이번 판정은 주제만 말했다 — 값이 채워졌다면 그것은 지어낸 분류다.
  SELECT count(*) INTO n FROM d9_topic_synonym
   WHERE synonym = ANY (syns) AND category IS NOT NULL;
  IF n <> 0 THEN
    RAISE EXCEPTION '0009 오라클 ② — 새 동의어 %건에 분류가 채워졌다 (정본 무근거)', n;
  END IF;

  -- ③ 지명 별칭 4행이 있고, 별칭 둘은 **자기 자신이 아닌** 표기로 간다.
  SELECT count(*) INTO n FROM d9_place_alias WHERE alias = ANY (aliases);
  IF n <> 4 THEN
    RAISE EXCEPTION '0009 오라클 ③ — 지명 별칭 4행 중 %건만 있다', n;
  END IF;
  IF (SELECT place_name FROM d9_place_alias WHERE alias = 'Korea') IS DISTINCT FROM '한반도' THEN
    RAISE EXCEPTION '0009 오라클 ③ — Korea 가 「한반도」로 가지 않는다';
  END IF;
  IF (SELECT place_name FROM d9_place_alias
        WHERE alias = 'southern Gyeonggi and Chungcheong regions') IS DISTINCT FROM '충청권' THEN
    RAISE EXCEPTION '0009 오라클 ③ — 영문 표기가 「충청권」으로 가지 않는다';
  END IF;

  -- ④ 기존 행을 지우지 않았다. `0006` 까지의 동의어 18행과 K2 지명 4행이 그대로 산다.
  SELECT count(*) INTO n FROM d9_topic_synonym;
  IF n < 27 THEN
    RAISE EXCEPTION '0009 오라클 ④ — 동의어가 %행뿐이다 (18 + 9 = 27 이상이어야 한다)', n;
  END IF;
  SELECT count(*) INTO n FROM d9_place_alias WHERE alias = place_name AND alias IN
    ('낙동강 유역','한강 상류','금강 하굿둑','한강 유역');
  IF n <> 4 THEN
    RAISE EXCEPTION '0009 오라클 ④ — K2 지명 4행 중 %건만 남았다', n;
  END IF;

  -- ⑤ ⛔ **개념 그래프를 만지지 않았다** (결정 4·5 보류).
  --    노드·엣지가 늘었다면 보류 판정이 조용히 깨진 것이다.
  SELECT count(*) INTO n FROM d9_concept;
  IF n <> 49 THEN
    RAISE EXCEPTION '0009 오라클 ⑤ — 개념 노드가 49 가 아니라 %다 (결정 4·5 는 보류다)', n;
  END IF;
  SELECT count(*) INTO n FROM d9_concept_edge;
  IF n <> 19 THEN
    RAISE EXCEPTION '0009 오라클 ⑤ — 개념 엣지가 19 가 아니라 %다 (결정 4·5 는 보류다)', n;
  END IF;

  -- ⑥ 출처가 비어 있지 않다. 「Ted 판정」 문면이 13행 전부에 남는다.
  SELECT count(*) INTO n FROM d9_topic_synonym
   WHERE synonym = ANY (syns) AND source_note LIKE 'Ted 판정 2026-09-18%';
  IF n <> 9 THEN
    RAISE EXCEPTION '0009 오라클 ⑥ — 판정 문면이 붙은 동의어가 %건뿐이다', n;
  END IF;
END $$;
