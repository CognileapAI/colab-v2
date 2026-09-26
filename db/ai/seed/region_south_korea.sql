-- db/ai/seed/region_south_korea.sql — 남한 지명 1노드 · 포함 엣지 1 · 지명 별칭 2 (적재물)
--
-- 결정 = Ted 판정 2026-09-26 「자료 지역 확정」 1 축자
--   「㈎ 기상청 4건(seq 1·2·19·20)=남한, GK-2A(seq 6)=한반도, 남한⊂한반도 관계로 연결」
--   회차 기록 = dev-package/intent/2026-09-21-evidence-promotion.md 「판정 결과 — 2회차 지역(2026-09-26)」.
--
-- **왜 이것이 필요한가.** 정본 DATASETS.md 가 이번 판정으로 seq 1·2·19·20 에 「지역: 남한」,
-- seq 6 에 「지역: 한반도」를 적는다. 실무자 사례 6건(#1-3·#1-4·#2-3·#2-4·#2-6·#2-7)은
-- 「한반도」로 묻는다. 「한반도」 질의가 남한 자료에 닿으려면 그래프가 한반도 → 남한 한 홉을
-- 펴야 한다 — `d9_ontology.expand_by_graph` 는 `안에 있다` 의 dst(상위)에서 src(하위)로만 편다.
-- 그래서 엣지는 `남한 안에 있다 한반도`(src=남한 · dst=한반도)이고, 기존 E2-1
-- `충청권 안에 있다 한반도` 와 같은 방향이다.
--
-- **왜 기존 시드 파일에 덧붙이지 않는가.** 회차마다 제 적재물을 갖는 것이 이 체인의 규율이다
--   (`practitioner_lexicon.sql` · `practitioner_concept_nodes.sql` 머리말과 같은 이유).
--
-- 등급 — 노드 ② (실제 데이터셋 정본 `DATASETS.md` 의 지역 줄) · 엣지 ⑥ (도메인 상식 — Ted 확인).
--   ⑥ 엣지는 `db/ai/tools/k2b_graph_check.py::APPROVED_G6` 에 이 판정으로 한 줄 더한다.
--   ⛔ 노드는 등급 ⑥ 이 없다(`K1b §A`) — 이 파일의 노드도 ② 다.
--
-- 별칭 — `practitioner_lexicon.sql` 이 「남한」을 「정본 근거가 0건이라 넣지 않는다」고 닫았다.
--   이번 판정과 정본 지역 줄이 그 근거다. 「대한민국」은 정본 `01.level-data/03.drought/DATASETS.md`
--   seq 13·14 축자 「대한민국 내 기상관측소」의 표기이고 같은 영역의 다른 이름으로 「남한」에 잇는다.
--   「우리나라」·「South Korea」는 정본 근거가 여전히 0건이라 넣지 않는다.
--
-- **기준은 여기 없다.** 기준은 `db/ai/seed/k2b-graph-standard.tsv`(노드 55 · 엣지 21)와
-- `k2-coverage-standard.tsv`(지명 7)이고 둘 다 **손으로** 옮겨 적었다.
-- 멱등하다 — `ON CONFLICT … DO UPDATE`. 스키마 CHECK·컬럼 무변경이다.

BEGIN;

INSERT INTO d9_concept (concept_id, kind, label, source_grade, source_note, expandable) VALUES
  ('p-south-korea', '지명', '남한', 2,
   '정본 DATASETS.md seq 1·2·19·20 「지역: 남한 (Ted 확정 2026-09-26 · 기상청 관측망)」. Ted 판정 2026-09-26 — 자료 지역 확정 1', true)
ON CONFLICT (concept_id) DO UPDATE
  SET kind = EXCLUDED.kind,
      label = EXCLUDED.label,
      source_grade = EXCLUDED.source_grade,
      source_note = EXCLUDED.source_note,
      expandable = EXCLUDED.expandable;

INSERT INTO d9_concept_edge (src, relation, dst, source_grade, source_note) VALUES
  ('p-south-korea', '안에 있다', 'p-korea-peninsula', 6,
   'E2-2026-09-26. Ted 판정 2026-09-26 — 자료 지역 확정 1 축자 「남한⊂한반도 관계로 연결」. 방향 = src 하위 · dst 상위(E2-1 과 같다)')
ON CONFLICT (src, relation, dst) DO UPDATE
  SET source_grade = EXCLUDED.source_grade,
      source_note = EXCLUDED.source_note;

INSERT INTO d9_place_alias (alias, place_name, source_note) VALUES
  ('남한',     '남한', 'Ted 판정 2026-09-26 — 자료 지역 확정 1 · 정본 DATASETS.md seq 1·2·19·20 지역 줄 · 개념 노드 p-south-korea 등급 ②'),
  ('대한민국', '남한', 'Ted 판정 2026-09-26 — 자료 지역 확정 1 · 정본 01.level-data/03.drought/DATASETS.md seq 13·14 축자 「대한민국 내 기상관측소」')
ON CONFLICT (alias) DO UPDATE SET place_name = EXCLUDED.place_name, source_note = EXCLUDED.source_note;

COMMIT;
