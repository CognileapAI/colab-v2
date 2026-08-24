-- db/ai/seed/k2b_concept_graph_seed.sql — K2b 그래프 시드 **적재물** (SoT)
--
-- 내용 정본 = dev-package/sessions/K1b-ONTOLOGY-CONTENT.md §A(노드)·§B(엣지)
-- 판정      = Ted 2026-08-25 (PLAN-SoT §9) — F-4d ❌ · F-7 ❌ · F-10 ㈏ · F-12 ㈎ · 나머지 ✅
--
-- **기준은 여기 없다.** 기준은 db/ai/seed/k2b-graph-standard.tsv 이고 판정기는
-- db/ai/tools/k2b_graph_check.py 다. 기준을 적재물에서 생성하면 체크가 영원히 green 인 자동통과가 된다
-- (k2_ontology_seed.sql ↔ k2-coverage-standard.tsv 와 같은 규약).
--
-- 멱등하다 — ON CONFLICT … DO UPDATE. 두 번 돌아도 그래프가 두 벌이 되지 않는다.
-- 사람이 재적재할 때도 이 파일을 psql 로 그대로 돌린다.
--
-- 등급 표기 — 1 시드 사전 적재값 · 2 SEED-DATA 실데이터·원천 문서 · 3 실측 · 4 DataModel 값집합
--            · 5 기획 정본 어휘 · 6 도메인 상식(**Ted 승인이 있어야만 들어온다**)

BEGIN;

-- ══════════════════════════════════════════════════════════════════════════
-- 노드 49 — 방법 27 · 주제 4 · 지명 8 · 원천표기 10. **등급 ⑥ 은 0 건이다.**
-- ══════════════════════════════════════════════════════════════════════════
INSERT INTO d9_concept (concept_id, kind, label, source_grade, source_note, expandable) VALUES
-- ── 방법: 정본 인용 13 (d9_method_term 과 label 이 한 글자도 달라선 안 된다 — §E-3) ──
  ('m-grid-interp',  '방법', '격자 보간',              1, 'K1 시드 d9_method_term 적재값. 목업 E-04 Lv1 표기', true),
  ('m-qc',           '방법', '품질검사',                1, 'K1 시드 적재값. 넓은 말이라 상위가 될 수 없다 — 부모 금지 목록', false),
  ('m-basin-clip',   '방법', '유역 클리핑',            1, 'K1 시드 적재값. 목업 제품 카드 표기', true),
  ('m-basin-mean',   '방법', '유역 평균',              1, 'K1 시드 적재값', true),
  ('m-basin-agg',    '방법', '유역 집계',              1, 'K1 시드 적재값. F-7 이 ❌ 라 부모 금지 목록에 그대로 남는다', false),
  ('m-daily-mean',   '방법', '일 단위 평균',           1, 'K1 시드 적재값. DataModel §4.2 가공 방식 예시', true),
  ('m-basin-cut',    '방법', '유역 경계로 잘라냄',     1, 'K1 시드 적재값. DataModel §4.2', true),
  ('m-thresh-days',  '방법', '임계값 초과일 집계',     1, 'K1 시드 적재값', true),
  ('m-regrid',       '방법', '재격자화',                1, 'K1 시드 적재값. 목업 E-04 입력 도움말', true),
  ('m-bias-corr',    '방법', '편의 보정',              1, 'K1 시드 적재값', true),
  ('m-downscale',    '방법', '다운스케일',             1, 'K1 시드 적재값. 목업 E-04 0.25도에서 0.05도', true),
  ('m-preproc',      '방법', '전처리',                  1, 'K1 시드 적재값. Lv1 전체를 부르는 포괄어 — 부모 금지 목록', false),
  ('m-interp-mode',  '방법', '보간 방식(선형/최근접)', 1, 'K1 시드 적재값. 목업 E-04 AI 근거 문장', true),
-- ── 방법: 실데이터 어휘 12 + 영문 표기 2 ──
  ('m-nearest',      '방법', '최근린보간',             2, 'SEED-DATA §5.1 · 데이터셋 D-03 이름', true),
  ('m-nearest-en',   '방법', 'Nearest',                 2, 'SEED-DATA §5.1 이 같은 칸에 병기한 영문 표기. D-03 이름이 이 문자열을 쓴다', true),
  ('m-bilinear',     '방법', '이중선형보간',           2, 'SEED-DATA §5.1 · 데이터셋 D-04 이름', true),
  ('m-bilinear-en',  '방법', 'Bilinear',                2, 'SEED-DATA §5.1 병기 영문 표기. D-04 이름이 이 문자열을 쓴다', true),
  ('m-idw',          '방법', 'IDW',                     2, 'SEED-DATA §5.1 · 데이터셋 D-05 이름', true),
  ('m-cokriging',    '방법', 'Co-Kriging',              2, 'SEED-DATA §5.1·§4.1 (보조 변수 DEM) · 데이터셋 D-06 이름', true),
  ('m-regkriging',   '방법', 'Regression Kriging',      2, 'SEED-DATA §5.1 KWRA README §4', true),
  ('m-reproject',    '방법', 'LCC→WGS84 재투영',        2, 'SEED-DATA §5.1 · §4.2 식생·강우 사슬의 WGS84 변환', true),
  ('m-savgol',       '방법', 'Savitzky-Golay 필터',     2, 'SEED-DATA §5.1 (d=2, 23일창)', true),
  ('m-thinning',     '방법', 'source thinning',         2, 'SEED-DATA §5.1 KWRA README §8', true),
  ('m-unet',         '방법', 'U-Net 공간상세화',        2, 'SEED-DATA §4.2. 다운스케일과의 등식은 정본에 없어 엣지를 걸지 않는다', true),
  ('m-dqf',          '방법', 'DQF 마스킹',              2, 'SEED-DATA §5.1 식생 처리 문서', true),
  ('m-roi-crop',     '방법', 'ROI 크롭',                2, 'SEED-DATA §5.1. 유역이 아니라 사각 영역이라 유역 클리핑과 잇지 않는다', true),
  ('m-monthly-mean', '방법', '월평균',                  2, 'SEED-DATA §5.1 식생 처리 문서', true),
-- ── 주제 4 (끝점이 되는 엣지가 0 행이다 — 질의어→주제는 d9_topic_synonym 의 일이다) ──
  ('t-precip',       '주제', '강우·강수',              1, 'd9_topic_synonym CHECK 4값 · P04 §5 고정 목록', true),
  ('t-veg',          '주제', '식생·NDVI',              1, '상동', true),
  ('t-dem',          '주제', '지형·DEM',               1, '상동', true),
  ('t-lulc',         '주제', '토지피복·LULC',          1, '상동', true),
-- ── 지명 8 ──
  ('p-nakdong',        '지명', '낙동강 유역',          1, 'K1 시드 d9_place_alias 적재값 · 목업 E-02', true),
  ('p-han-upper',      '지명', '한강 상류',            1, 'K1 시드 적재값 · 목업 제품 카드', true),
  ('p-geum-estuary',   '지명', '금강 하굿둑',          1, 'K1 시드 적재값', true),
  ('p-han',            '지명', '한강 유역',            1, 'K1 시드 적재값 · 목업 제품 카드', true),
  ('p-chungcheong',    '지명', '충청권',                2, 'SEED-DATA §5.3 KWRA README(한글). 좌표 126.70~127.96E, 36.08~37.36N', true),
  ('p-chungcheong-en', '지명', 'southern Gyeonggi and Chungcheong regions', 2, 'SEED-DATA §5.3 KWRA docx(영문) — 같은 영역의 다른 이름', true),
  ('p-korea-peninsula','지명', '한반도',                2, 'SEED-DATA §5.3 한반도 전역 852x1200 격자 · 데이터셋 D-01 이름', true),
  ('p-korea-en',       '지명', 'Korea',                 2, 'SEED-DATA §5.3 폴더명', true),
-- ── 원천표기 10 (엔티티가 아니라 표기 문자열이다 — 속성도 데이터셋 참조도 없다) ──
  ('s-gk2a-hyphen', '원천표기', 'GK-2A',               2, 'SEED-DATA §5.4 GK-2A(천리안위성2A호)', true),
  ('s-gk2a',        '원천표기', 'GK2A',                 5, 'DataModel §4.1 원천 표기 예시', true),
  ('s-gk2a-ko',     '원천표기', '천리안위성2A호',       2, 'SEED-DATA §5.4', true),
  ('s-nmsc',        '원천표기', 'NMSC',                 2, 'SEED-DATA §5.4 NMSC(국가기상위성센터)', true),
  ('s-nmsc-ko',     '원천표기', '국가기상위성센터',     5, 'DataModel §4.1 · 목업 E-03 계보 원천', true),
  ('s-kma-hub',     '원천표기', '기상청 API허브',       2, 'SEED-DATA §5.4 — D-07·D-08·D-15 의 원천 표기 후보', true),
  ('s-modis',       '원천표기', 'MODIS MOD15A2H',       2, 'SEED-DATA §5.4·§0-F-2 — D-13', true),
  ('s-hls',         '원천표기', 'HLS S30',              2, 'SEED-DATA §5.4·§0-F-3 — D-14', true),
  ('s-kwra',        '원천표기', 'KWRA',                 2, 'SEED-DATA §5.4 한국수자원학회(KWRA)', true),
  ('s-kwra-ko',     '원천표기', '한국수자원학회',       2, '상동', true)
ON CONFLICT (concept_id) DO UPDATE
  SET kind = EXCLUDED.kind,
      label = EXCLUDED.label,
      source_grade = EXCLUDED.source_grade,
      source_note = EXCLUDED.source_note,
      expandable = EXCLUDED.expandable;

-- ══════════════════════════════════════════════════════════════════════════
-- 엣지 19 — 같은 말이다 11 · ~의 한 가지다 7 · 안에 있다 1
--
-- **여기 없는 것이 판정의 실물이다.**
--   · Co-Kriging → 재격자화 (F-4d ❌) — 보조 변수를 쓰는 지구통계 기법을 재격자화의 한 가지로
--     묶는 것이 옳은지 초안 스스로 확신하지 못했다. 그래서 §D-2 의 개선은 4건이 아니라 **3건**이다
--   · 유역 평균 → 유역 집계 (F-7 ❌) — 유역 집계가 부모 금지 목록에 남는 것과 충돌했다. 목록이 이겼다
--   · 한강 상류 ⊂ 한강 유역 (F-8 은 ✅ 였으나 F-10 ㈏ 가 「E2 는 1행만」으로 닫았다). 오늘 0 건이다
--   · ECMWF ≡ 유럽중기예보센터 (F-12 ㈎) — 15 데이터셋에 그 원천이 0 건이라 결과를 안 바꾼다
-- ══════════════════════════════════════════════════════════════════════════
INSERT INTO d9_concept_edge (src, relation, dst, source_grade, source_note) VALUES
-- ── E1 같은 말이다 11 (대칭 — src < dst 정규형 한 행) ──
  ('m-nearest',       '같은 말이다', 'm-nearest-en',       2, 'E1-1. SEED-DATA §5.1 이 한 칸에 최근린보간 (Nearest) 로 적었다'),
  ('m-bilinear',      '같은 말이다', 'm-bilinear-en',      2, 'E1-2. SEED-DATA §5.1 이중선형보간 (Bilinear)'),
  ('m-cokriging',     '같은 말이다', 'm-regkriging',       6, 'E1-3. Ted ✅ F-1 (2026-08-25). SEED-DATA §5.1 의 빗금 나열을 등식으로 읽는다'),
  ('m-dqf',           '같은 말이다', 'm-qc',               2, 'E1-4. SEED-DATA §5.1 이 DQF 마스킹 / 품질검사(QC) 대응을 명시했다'),
  ('m-basin-clip',    '같은 말이다', 'm-basin-cut',        6, 'E1-5. Ted ✅ F-2 (2026-08-25). 같은 동작의 두 정본 어휘'),
  ('p-chungcheong',   '같은 말이다', 'p-chungcheong-en',   2, 'E1-6. SEED-DATA §5.3 이 원천 대조로 같은 영역에 이름이 둘임을 확정했다'),
  ('p-korea-en',      '같은 말이다', 'p-korea-peninsula',  6, 'E1-7. Ted ✅ F-3 (2026-08-25). README 한반도 = 폴더명 Korea'),
  ('s-gk2a',          '같은 말이다', 's-gk2a-hyphen',      5, 'E1-8. 실측 2026-08-25 — to_tsvector(simple, GK-2A) = {gk-2a, gk, 2a} 로 gk2a 와 만나지 않는다. 이 엣지가 D-01~D-06 6건을 좌우한다'),
  ('s-gk2a-hyphen',   '같은 말이다', 's-gk2a-ko',          2, 'E1-9. SEED-DATA §5.4 가 한 표기 안에 병기했다'),
  ('s-nmsc',          '같은 말이다', 's-nmsc-ko',          2, 'E1-10. SEED-DATA §5.4 · DataModel §4.1'),
  ('s-kwra',          '같은 말이다', 's-kwra-ko',          2, 'E1-11. SEED-DATA §5.4 한국수자원학회(KWRA)'),
-- ── E5 ~의 한 가지다 7 (src=하위 → dst=상위 · 확장은 하향 전용) ──
  ('m-nearest',       '~의 한 가지다', 'm-regrid',         6, 'E5-1. Ted ✅ F-4a (2026-08-25). 재격자화 질의가 D-03 을 잡는다'),
  ('m-bilinear',      '~의 한 가지다', 'm-regrid',         6, 'E5-2. Ted ✅ F-4b (2026-08-25). D-04'),
  ('m-idw',           '~의 한 가지다', 'm-regrid',         6, 'E5-3. Ted ✅ F-4c (2026-08-25). D-05'),
  ('m-nearest',       '~의 한 가지다', 'm-interp-mode',    5, 'E5-5. 정본 어휘가 글자로 최근접을 담고 있다 (목업 E-04 AI 근거)'),
  ('m-bilinear',      '~의 한 가지다', 'm-interp-mode',    5, 'E5-6. 상동 — 선형'),
  ('m-grid-interp',   '~의 한 가지다', 'm-regrid',         6, 'E5-7. Ted ✅ F-5 (2026-08-25). 동의어가 아니라 하위로 확정'),
  ('m-downscale',     '~의 한 가지다', 'm-regrid',         6, 'E5-8. Ted ✅ F-6 (2026-08-25). 목업 E-04 의 해상도 변화 읽기'),
-- ── E2 안에 있다 1 (Ted F-10 ㈏ — 실측 좌표가 받치는 한 행만) ──
  ('p-chungcheong',   '안에 있다',   'p-korea-peninsula',  3, 'E2-1. SEED-DATA §5.3 실측 좌표가 D-01 한반도 852x1200 격자 범위 안이다')
ON CONFLICT (src, relation, dst) DO UPDATE
  SET source_grade = EXCLUDED.source_grade,
      source_note = EXCLUDED.source_note;

COMMIT;
