-- db/ai/seed/practitioner_concept_nodes.sql — 개념 그래프 6행 (적재물)
--
-- 결정 = Ted 판정 2026-09-18 · intent/2026-09-18-practitioner-cases-ontology.md 결정 4·5.
--   결정 4(원천표기 ERA5·ECMWF·유럽중기예보센터) 축자 「없어도 앞으로 추가될거니까 넣자」
--     — 2026-08-25 `F-12 ㈎`(「뺀다」)의 **재개봉**이다. 그때의 기각 사유는
--       `K1b-ONTOLOGY-CONTENT.md:346` 축자 「15 데이터셋에 ECMWF·ERA5 원천이 0 건」이었고,
--       이번 판정이 그 사유 대신 **앞으로 들어올 자료**를 근거로 세웠다. 재개봉 기록은
--       intent 「확인」 절에 있다 — 이 파일이 판정을 새로 만들지 않는다.
--   결정 5(주제 노드 4→6) 축자 「가뭄 파일포멧 예제 넣자. 데이터가 들어오면 검색이 되어야 한다」
--     — 사전(`d9_topic_synonym`)은 `0006_topic_vocab_six` 로 이미 6값인데 그래프만 4개였다.
--       그 **비대칭**을 없앤다. 새 주제 값을 발명하는 것이 아니다.
--
-- **왜 `k2b_concept_graph_seed.sql` 에 덧붙이지 않는가.**
--   그 파일은 `0005` 가 실행하는 적재물이고 회차마다 제 적재물을 갖는 것이 이 체인의 규율이다
--   (`topic_synonym_six.sql` · `practitioner_lexicon.sql` 과 같은 이유). 그래야 어느 리비전이
--   무엇을 넣었는지가 파일 하나로 읽힌다.
--
-- **기준은 여기 없다.** 기준은 `db/ai/seed/k2b-graph-standard.tsv`(노드 54 · 엣지 20)이고
-- 판정기는 `db/ai/tools/k2b_graph_check.py` 다. 둘 다 **손으로** 옮겨 적었다 — 기준을
-- 적재물에서 생성하면 체크가 영원히 green 인 자동통과가 된다.
--
-- 멱등하다 — `ON CONFLICT … DO UPDATE`. 스키마 CHECK·컬럼 무변경이다.
-- 등급 표기 — 5 기획 정본 어휘 · 1 시드 사전에 이미 적재된 값. **등급 6 은 이 파일에 0 건이다.**

BEGIN;

-- ══════════════════════════════════════════════════════════════════════════
-- 노드 +5 → 54 (방법 27 · 주제 6 · 지명 8 · 원천표기 13). 등급 6 은 그대로 0 건이다.
--
-- 원천표기 3 은 **엔티티가 아니라 표기 문자열**이다 (`K1b §A.4` 머리말 · `DM §4.1`
-- 「원천은 연구실 데이터셋이 아니라 표기로 남긴다」). 속성도 데이터셋 참조도 없다.
-- ══════════════════════════════════════════════════════════════════════════
INSERT INTO d9_concept (concept_id, kind, label, source_grade, source_note, expandable) VALUES
  ('s-era5',     '원천표기', 'ERA5',   5,
   'ONTOLOGY-SCOPE.md §2.7-⑴ 축자 「ECMWF (ERA5)」. Ted 판정 2026-09-18 결정 4(F-12 ㈎ 재개봉) — 「없어도 앞으로 추가될거니까 넣자」', true),
  ('s-ecmwf',    '원천표기', 'ECMWF',  5,
   'ONTOLOGY-SCOPE.md §2.7-⑴ 축자 「ECMWF (ERA5)」 · 목업 E-02·E-03. Ted 판정 2026-09-18 결정 4', true),
  ('s-ecmwf-ko', '원천표기', '유럽중기예보센터', 5,
   'ONTOLOGY-SCOPE.md §2.7-⑴ 축자 「유럽중기예보센터 재분석 강수를 격자 보간·품질검사한 자료」(목업 E-03). Ted 판정 2026-09-18 결정 4', true),
-- ── 주제 +2 → 6. label 은 `d9_topic_synonym.topic` CHECK 6값과 **한 글자도 달라선 안 된다** ──
  ('t-drought',    '주제', '가뭄',          1,
   'd9_topic_synonym CHECK 6값 (0006_topic_vocab_six · Ted 판정 2026-09-06 창 9) 에 이미 있는 값. Ted 판정 2026-09-18 결정 5 — 「가뭄 파일포멧 예제 넣자. 데이터가 들어오면 검색이 되어야 한다」', true),
  ('t-fileformat', '주제', '파일 포맷 예제', 1,
   '상동 — 사전은 6값인데 그래프만 4개이던 비대칭을 없앤다. 새 주제 값을 만드는 것이 아니다', true)
ON CONFLICT (concept_id) DO UPDATE
  SET kind = EXCLUDED.kind,
      label = EXCLUDED.label,
      source_grade = EXCLUDED.source_grade,
      source_note = EXCLUDED.source_note,
      expandable = EXCLUDED.expandable;

-- ══════════════════════════════════════════════════════════════════════════
-- 엣지 +1 → 20 (같은 말이다 12 · ~의 한 가지다 7 · 안에 있다 1)
--
-- **여기 없는 것** — `ECMWF → ERA5`. 그것을 적을 관계값은 `~이 제공한다` 이고
-- 결정 8 이 `relation` CHECK 3값을 그대로 두기로 닫았다. 그래서 `s-era5` 는 **엣지가 없는
-- 노드**이고, 「ERA5」 질의는 이 회차 뒤에도 그래프로 넓혀지지 않는다
-- (오라클 `practitioner-lexical.json` LEX-15 가 그 상태를 blocked 로 적어 둔다).
-- 주제 노드 둘도 끝점이 되는 엣지가 **0 행**이다 — `K1b §A.2` 축자 「질의어→주제 매핑은 이미
-- d9_topic_synonym 이 하는 일이고, 같은 사실을 두 곳에 두면 어긋났을 때 판정할 수 없다」.
-- ══════════════════════════════════════════════════════════════════════════
INSERT INTO d9_concept_edge (src, relation, dst, source_grade, source_note) VALUES
  ('s-ecmwf', '같은 말이다', 's-ecmwf-ko', 5,
   'E1-12. ONTOLOGY-SCOPE.md §2.7-⑴ 이 「ECMWF (ERA5)」와 「유럽중기예보센터 …」를 같은 전수 목록에 둔다. 정규형 src < dst 를 지킨다(s-ecmwf < s-ecmwf-ko). Ted 판정 2026-09-18 결정 4 = F-12 ㈎ 재개봉')
ON CONFLICT (src, relation, dst) DO UPDATE
  SET source_grade = EXCLUDED.source_grade,
      source_note = EXCLUDED.source_note;

COMMIT;
