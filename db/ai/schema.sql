-- db/ai/schema.sql — 지식·추론 선언 스키마 정본 (SoT)
--
-- 소유 도메인: D9 Ontology & Knowledge Graph · D10 AI Services
--
-- 범위 정본 = dev-package/ONTOLOGY-SCOPE.md (G8, Ted 승인 2026-08-23)
--             결정 기록 = dev-package/PLAN-SoT.md §9-㊸ · 규율 = §9-㊴-②
--
-- 이 체인이 아는 것은 **작은 사전 셋뿐**이다 (㊸-④-4).
--   ① d9_method_term    가공 방식 후보 어휘 — 제안 문장·자동완성용. 값을 닫지 않는다 (㊸-④-1 하이브리드)
--   ② d9_topic_synonym  주제 동의어 — 질의어 → 주제 4값 (㊸-④-2)
--   ③ d9_place_alias    지명 별칭 — 질의의 공간 축 인식용. **위계가 아니라 별칭만** (ONTOLOGY-SCOPE §2.4)
--
-- 여기에 **없는 것이 결정의 실물이다.**
--   · 그래프 구조·개념 유형 체계·관계 테이블 없음 (㊸-④-4: 정본이 준 값의 양이 그래프를 정당화하지 않는다)
--   · 관측소 명부 · 행정/유역 위계 · 좌표계 목록 · 기관 마스터 · 변수 사전 없음
--     (ONTOLOGY-SCOPE §③ 의 [정본 무근거] 10건 — 채우려면 기획 정본을 먼저 고친다)
--   · 가공 방식 enum 없음 — 저장·계약은 자유 문자열 그대로다. 이 표는 후보일 뿐이다
--
-- 이 체인이 지키는 것
--   · CLAUDE.md §3-3 — 이 체인은 기록 도메인(D1~D8)과 마이그레이션 체인이 분리된다.
--     체인 상태 테이블 이름이 다른 것이 그 분리의 실물이다.
--   · CLAUDE.md §3-2 — 여기에 계보 테이블을 두지 않는다. AI 는 제안만 하고,
--     사람이 확인한 것만 기록 쪽 체인으로 넘어간다. 제안 임시 저장소가 생기면 `ai_` 접두사를 쓴다.
--   · 여기에 D1~D8 테이블을 넣지 않는다. 넣으면 온톨로지 한 줄 추가가 기록 쪽 마이그레이션을 기다린다.
--   · 이 체인의 테이블은 기록 체인의 어떤 테이블도 FK 로 참조하지 않는다 — 애초에 다른 DB 다.
--
-- ID 정책: **자연키를 쓴다.** ULID 를 쓰지 않는 이유는 셋이다 —
--   ⑴ 이 표들은 사전이고, 사전의 정체성은 어휘 그 자체다 (같은 어휘가 두 번 들어오면 그것이 중복이다)
--   ⑵ 이 표의 행을 밖에서 id 로 가리키는 곳이 없다 — 소비자는 D10 하나이고, 오가는 값은 문자열이다
--   ⑶ K2 시드 적재가 어휘 기준으로 멱등해진다 (ON CONFLICT (term) …)
--   contracts/schemas/common.json 의 Ulid 는 여전히 정규 ID 타입 정본이다 (CLAUDE.md §3-6).
--   여기서 그 타입을 쓰지 않는 것이지, 다른 ID 타입을 새로 만드는 것이 아니다.
--
-- RLS: 세 표 전부 **연구실 공통 지식**이라 테넌트별로 갈리지 않는다 (DOMAINS.md D9 · 아래 각 표의 근거).
--   그래서 lab_id 컬럼이 하나도 없고, RLS 를 걸지 않는다.
--   면제는 **접두사가 아니라 이름 하나씩** gates/config/rls-allowlist.toml 에 적는다 —
--   테이블이 생길 때마다 사람이 판단을 한 번 내리게 하려는 것이다.

-- ════════════════════════════════════════════════════════════════════════════
-- 1. D9 — 가공 방식 후보 어휘 (ONTOLOGY-SCOPE §2.6 · ㊸-④-1)
-- ════════════════════════════════════════════════════════════════════════════

-- **값을 닫는 표가 아니다.** 가공 방식은 정본이 자유 문장으로 못 박았고(`P04 §5` 1~120자,
-- `DM §4.2` "어떻게 만들었는지 한 줄"), 계약(`ProcessingMethodSuggestion.methodText`)과
-- 기록 쪽 저장 형태가 이미 그렇게 동결돼 있다. 이 표는 K3 제안 문장 생성과
-- 업로드 화면 자동완성 **후보**로만 읽힌다 — 사람은 언제든 목록에 없는 문장을 쓴다.
--
-- 연구실별로 갈리지 않는 이유: 여기 들어오는 값의 출처는 기획 정본 인용뿐이고(K2 시드),
-- 사람이 고쳐 쓴 문장은 이 표로 **되돌아오지 않는다** (ONTOLOGY-SCOPE §2.6-⑷ — 학습 루프를 1차에 만들지 않는다).
-- 즉 이 표에는 연구실 데이터가 한 줄도 들어올 수 없다.
CREATE TABLE d9_method_term (
  -- 어휘 그 자체가 키다. 길이 상한은 정본의 가공 방식 한 줄 상한과 같게 둔다 (`P04 §5` 1~120자).
  term         text        PRIMARY KEY
               CHECK (btrim(term) = term AND length(term) BETWEEN 1 AND 120),
  -- 이 어휘가 정본 어디서 왔는가. **비울 수 없다** — [정본 무근거] 어휘가 조용히 섞이는 것을 막는다
  -- (PLAN-SoT §9-㊴-② · DOMAINS §7 규칙 4).
  source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
  created_at   timestamptz NOT NULL DEFAULT now()
);

-- 동의어 그룹을 만들지 않는다. `재격자화 ≡ 리샘플` 같은 동일성 판정은 정본이 답하지 않았고
-- (ONTOLOGY-SCOPE §③-2 · §⑤-1), 판정 컬럼을 두면 그 자리를 누군가 발명으로 채우게 된다.

-- ════════════════════════════════════════════════════════════════════════════
-- 2. D9 — 주제 동의어 (ONTOLOGY-SCOPE §2.2 · ㊸-④-2)
-- ════════════════════════════════════════════════════════════════════════════

-- 주제 **값 자체는 이 도메인의 것이 아니다** — 사람이 고정 목록에서 고르고 카탈로그가 저장한다.
-- D9 가 갖는 것은 `질의어 → 주제 4값` 매핑뿐이다 (ONTOLOGY-SCOPE §2.2-⑶).
-- 정본이 든 유일한 증거: "'강우데이터'는 강수 주제로 일치" (목업 E-02).
--
-- 4값을 여기에도 CHECK 로 적는 이유: 체인이 분리돼 있어 카탈로그 쪽 목록을 FK 로 참조할 수 없다
-- (CLAUDE.md §3-3). 두 곳이 각각 **같은 정본**(`P04 §5`)을 옮겨 적는 것이고,
-- 목업의 `유출·수문` 은 예시라 반영하지 않는다는 Ted 판정(㊸-④-2)이 이 CHECK 로 굳는다.
--
-- 연구실별로 갈리지 않는 이유: 주제 고정 목록 자체가 "연구실이 항목을 추가할 수 없다 —
-- 항목 추가는 운영팀이 한다"(`P04 §5`)로 못 박힌 전역 값이다. 그 위에 다는 동의어도 전역이다.
CREATE TABLE d9_topic_synonym (
  -- 질의어가 키다. 한 질의어는 한 주제로만 간다 — 정본의 유일한 예가 1:1 이고,
  -- 다의어 처리 규칙은 정본에 없다([정본 무근거]). 규칙이 없는 채로 1:N 을 열면
  -- "어느 주제를 고를 것인가"를 구현이 발명하게 된다.
  synonym      text        PRIMARY KEY
               CHECK (btrim(synonym) = synonym AND length(synonym) BETWEEN 1 AND 120),
  topic        text        NOT NULL
               CHECK (topic IN ('강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC')),
  source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d9_topic_synonym_topic_idx ON d9_topic_synonym (topic);

-- ════════════════════════════════════════════════════════════════════════════
-- 3. D9 — 지명 별칭 (ONTOLOGY-SCOPE §2.4 · ㊸-④-3)
-- ════════════════════════════════════════════════════════════════════════════

-- **별칭만이다. 위계가 아니다.** 정본은 `낙동강 유역`·`한강 상류`·`금강 하굿둑`·`소유역` 을
-- 이름으로만 쓰고 포함 관계를 정의한 곳이 없다 (ONTOLOGY-SCOPE §2.4-⑵).
-- 그래서 부모 컬럼도, 유역 코드도, 좌표도 두지 않는다 — 두면 정본에 없는 위계를 발명하게 된다.
-- 검색의 공간 축은 정본상 문자열 일치로 설명된다: "'낙동강 유역'은 공간" (목업 E-02).
--
-- 연구실별로 갈리지 않는 이유: 여기 들어오는 이름은 정본이 쓴 지명이다. 연구실이 자기 데이터셋에
-- 붙인 이름은 카탈로그 쪽 데이터셋 이름·설명에 남고 이 표로 오지 않는다 (ONTOLOGY-SCOPE §2.4-⑷).
CREATE TABLE d9_place_alias (
  -- 별칭이 키다 (`낙동강` · `낙동강유역` …). 한 별칭은 한 정본 표기로만 간다 — 위와 같은 이유.
  alias        text        PRIMARY KEY
               CHECK (btrim(alias) = alias AND length(alias) BETWEEN 1 AND 120),
  -- 정본이 쓴 표기 (`낙동강 유역` 등). 별칭 = 표기인 행(자기 자신)도 들어올 수 있다.
  place_name   text        NOT NULL
               CHECK (btrim(place_name) = place_name AND length(place_name) BETWEEN 1 AND 120),
  source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d9_place_alias_place_idx ON d9_place_alias (place_name);

-- ════════════════════════════════════════════════════════════════════════════
-- 4. D9 — 개념 노드 (WU-K1b · Ted 판정 2026-08-25 · PLAN-SoT §9)
--    내용 정본 = dev-package/sessions/K1b-ONTOLOGY-CONTENT.md §A·§E-1
-- ════════════════════════════════════════════════════════════════════════════

-- **위 세 표를 흡수하지 않는다** (§E-3 · Ted F-13 ㈎).
--   · 세 표는 `질의어 → 값` 조회(사전)이고 이 두 표는 `질의어 → term set` 확장(그래프)이다. 역할이 다르다
--   · 합치면 K2 의 완료 오라클(k2-coverage-standard.tsv)과 0002·0003 이 통째로 흔들린다
-- **여기에 「데이터셋에 대한 사실」은 한 줄도 들어오지 않는다.** kind 4값이 그것을 스키마로 못 박은 것이다 —
-- `데이터셋`·`프로젝트`·`변수`·`좌표계`가 이 목록에 **없는 것**이 CLAUDE.md §3-2 의 실물이다.
-- 이 표에도 lab_id 가 없다 — 연구실 공통 지식이라 테넌트로 갈리지 않는다 (0002 서두와 같은 근거).
CREATE TABLE d9_concept (
  -- **대리키다.** 세 시드 표는 어휘 자체가 PK(자연키)라 표기를 고치면 참조가 끊긴다.
  -- 그래프에서는 그 성질이 치명적이라(엣지가 통째로 죽는다) 여기서만 안정 키를 쓴다 (§E-1).
  concept_id   text        PRIMARY KEY
               CHECK (concept_id ~ '^[a-z0-9]+(-[a-z0-9]+)*$'
                      AND length(concept_id) BETWEEN 1 AND 60),
  kind         text        NOT NULL
               CHECK (kind IN ('방법', '주제', '지명', '원천표기')),
  -- 정본 한국어 표기. 세 시드 표의 CHECK 와 같은 모양이다.
  label        text        NOT NULL
               CHECK (btrim(label) = label AND length(label) BETWEEN 1 AND 120),
  -- **출처 등급이 DB 까지 살아남는다** (§E-2). ⑥ = 도메인 상식 = Ted 승인이 있어야 하는 행이고,
  -- 완료 오라클(db/ai/tools/k2b_graph_check.py)이 이 열 하나로 승인 목록과 대조한다.
  source_grade smallint    NOT NULL CHECK (source_grade BETWEEN 1 AND 6),
  source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
  -- §D-6 경계 4 「부모 금지 목록」. false 면 `~의 한 가지다` 의 **도착**이 될 수 없다.
  -- `전처리`·`품질검사`·`유역 집계` 처럼 넓은 말이 상위가 되면 확장이 15건 중 12건을 부르고
  -- 「근거 한 줄」이 아무 말도 아닌 문장이 된다 (〈72〉-㉮).
  expandable   boolean     NOT NULL DEFAULT true,
  created_at   timestamptz NOT NULL DEFAULT now(),
  -- 같은 종류 안에 같은 표기가 둘일 수 없다.
  UNIQUE (kind, label)
);
CREATE INDEX d9_concept_kind_idx ON d9_concept (kind);
CREATE INDEX d9_concept_grade_idx ON d9_concept (source_grade);

-- ════════════════════════════════════════════════════════════════════════════
-- 5. D9 — 개념 엣지 (WU-K1b · K1b-ONTOLOGY-CONTENT.md §B·§C·§E-2)
-- ════════════════════════════════════════════════════════════════════════════

-- 관계는 **셋뿐**이다. 정본이 안 쓴 어휘(`subClassOf`·`skos:broader`)를 들여오지 않는다.
--   · `같은 말이다`   대칭 — 저장은 한 방향 한 행, 조회에서 양쪽으로 편다
--   · `~의 한 가지다` 방향 — src=하위 → dst=상위. **확장은 dst→src(하향)로만** 간다 (§D-6 경계 1)
--   · `안에 있다`     방향 — 공간 포함. Ted F-10 ㈏ 로 시드는 1행뿐이다
-- **가중치·점수·확신도 열이 없다.** CLAUDE.md §3 AI 응답 규격 「숫자·퍼센트 필드 없음」 ·
-- 순위는 tsvector 가 정한다(〈72〉-㉮). 순위가 두 곳에서 정해지면 평가셋으로 회귀를 못 잡는다.
CREATE TABLE d9_concept_edge (
  -- 같은 체인 안의 FK 다. 금지된 것은 기록 체인(D1~D8)으로 넘어가는 FK 이고(CLAUDE.md §3-1),
  -- 애초에 다른 DB 라 걸 수도 없다.
  --
  -- ⚠ **여기 산문에 기록 체인의 경로 문자열을 적지 않는다.** `ai-no-lineage-write` ⑨ 는
  --   db/ai 파일 안에서 그 경로가 **글자로 나타나는 것만으로** red 를 낸다 — 주석인지 코드인지
  --   구분하지 않는다. 게이트가 맞다(정규식이 산문과 코드를 가를 방법이 없고, 가르려 들면
  --   진짜 참조를 놓칠 문이 생긴다). 같은 실수가 이 레포에서 두 번 났다 —
  --   S1-search-infra 레인이 한 번, K1b 가 한 번. **고칠 것은 게이트가 아니라 문장이다.**
  src          text        NOT NULL REFERENCES d9_concept (concept_id),
  relation     text        NOT NULL
               CHECK (relation IN ('같은 말이다', '~의 한 가지다', '안에 있다')),
  dst          text        NOT NULL REFERENCES d9_concept (concept_id),
  source_grade smallint    NOT NULL CHECK (source_grade BETWEEN 1 AND 6),
  source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
  created_at   timestamptz NOT NULL DEFAULT now(),
  -- 재적재가 멱등해진다 (세 시드 표의 ON CONFLICT DO UPDATE 규약을 그대로 승계).
  PRIMARY KEY (src, relation, dst),
  CONSTRAINT d9_concept_edge_no_self CHECK (src <> dst),
  -- 대칭 관계는 **정규형 한 행**만 둔다. 같은 쌍이 순서만 바꿔 두 번 들어오면
  -- 「한쪽만 지우는 사고」가 나고 확장이 조용히 반쪽이 된다 (§E-2).
  CONSTRAINT d9_concept_edge_sym_normalized
               CHECK (relation <> '같은 말이다' OR src < dst)
);
-- 확장은 상위(dst)에서 하위(src)를 찾는다 — 그 방향의 조회를 색인이 받친다.
CREATE INDEX d9_concept_edge_dst_idx ON d9_concept_edge (relation, dst);

-- 여기 **CHECK 로 못 넣는 것 셋**이 있고, 그것들은 완료 오라클(k2b_graph_check.py)이 본다.
--   ① 양끝의 kind 규약 — `안에 있다`=지명·지명, `~의 한 가지다`=방법·방법 (상대 행을 CHECK 가 못 본다)
--   ② expandable=false 인 노드가 `~의 한 가지다` 의 dst 가 되는 것 (두 표를 걸친 조건)
--   ③ 팬아웃 상한 6 (집계 조건)
-- 트리거를 쓰지 않는 이유 = 세 시드 표에 트리거가 하나도 없고, d9 표는 **선언만으로 읽히는 것**이 규약이다.

-- ════════════════════════════════════════════════════════════════════════════
-- 6. 마이그레이션 체인 상태 테이블
--    alembic 이 만드는 것과 **같은 형태**를 여기 선언해 둔다 — 그래야 선언 = 적용이 성립한다.
--    이름이 다른 체인과 다른 것이 체인 분리의 실물이다 (CLAUDE.md §3-3).
-- ════════════════════════════════════════════════════════════════════════════

CREATE TABLE alembic_version_ai (
  version_num character varying(32) NOT NULL,
  CONSTRAINT alembic_version_ai_pkc PRIMARY KEY (version_num)
);
