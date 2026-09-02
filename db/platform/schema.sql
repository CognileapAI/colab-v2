-- db/platform/schema.sql — 플랫폼 선언 스키마 정본 (SoT)
--
-- 소유 도메인: D1 Identity&Lab · D2 Access&Policy · D3 Catalog · D4 Lineage · D5 Ingestion&Pipeline
--              · D6 Project · D8 Insight(공통 기록)
-- D5 는 `0004`(P2-db) 이 더했다 — §4-b. D7 Visualization 은 P3 에서 더한다 (저장 형태의 정본이 아직 없다).
--
-- 근거
--   정본  에픽/E-00_공통_기반/documents/DataModel_공통_기반.md v1.8  (§2 §3 §4.1 §4.2 §4.3 §5 §6)
--   기준표 dev-package/DATAMODEL-BASELINE.md §1 (전 행) · §3 (소급 위험 11건)
--   규칙  CLAUDE.md §3-1 §3-5 §3-6 · PLAN-SoT §9-⑲ ⑳ ㉖ ㉗ ㉘ · PERMISSION-PRINCIPLES P-13 P-24 P-29 P-30 P-32 P-34
--
-- 이 파일이 지키는 것 (틀리면 뒤가 전부 소급된다 — DATAMODEL-BASELINE §3)
--   · 데이터셋 : 파일 = 1 : N (본체 1건 이상 + 기준 격자 **0~2건** — `〈58〉`·`〈66〉`, `0004`)
--   · 계보는 데이터셋 사이에만 — 파일에는 계보가 없다. 부모 여럿, 가공 방식은 관계에 부착
--   · 소유자(빈 값 불가) 와 올린 사람(불변) 은 별개 기록
--   · 가공 단계 Lv · 계보 상태는 컬럼이 아니다 — 계산한다 (⑳). 이 파일에 그 두 컬럼이 없는 것이 그 강제다
--   · 프로젝트 연결 N:N + 활용 의미 문장은 연결마다
--   · 다시 올리기(버전) 자리 없음
--   · 활동 기록은 바꾼 일만 — 열람 기록 테이블이 없다
--   · 삭제는 묘비 — 행을 지우지 않는다
--   · 확정 열거값은 전부 CHECK 로 DB 가 강제한다 (⑲)

-- ════════════════════════════════════════════════════════════════════════════
-- 0. 공통 커널 — 정규 ID 타입과 스코프 커널
-- ════════════════════════════════════════════════════════════════════════════

-- 삼중자 검색 확장 (`0006` · `PLAN-SoT §9-〈89〉-㉰`). **이미지에 있는 것만 건다** —
-- `postgres:16-alpine` 의 `pg_available_extensions` 에 `pg_trgm` 1.6 이 있다(실측).
-- `pgvector` 는 같은 질의에서 0행이라 걸지 않았고, 그 판정은 `0005` 서두에 그대로 남아 있다.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 정규 ID. 값 정본은 contracts/schemas/common.json#/$defs/Ulid 하나뿐이고(CLAUDE.md §3-6),
-- 여기서는 그 정본을 DB 층으로 옮겨 적는다 — 도메인 하나로 선언해 타입 드리프트를 원천 차단한다
-- (v1 의 #1 함정: users.id 를 String(20/30/36) 으로 제각각 선언 — DATAMODEL-BASELINE §3-⑩).
CREATE DOMAIN ulid AS char(26)
  CONSTRAINT ulid_crockford_base32 CHECK (VALUE ~ '^[0-9A-HJKMNP-TV-Z]{26}$');

-- 스코프 커널. GUC 를 정규식으로 검증하고 어긋나면 NULL 을 돌려준다 →
-- 모든 경계 정책이 `lab_id = NULL` = false 가 되어 **기본 거부**로 닫힌다.
-- GUC 를 세팅하지 않은 접속은 아무 행도 보지 못한다 (DATAMODEL-BASELINE §4 — v1 에서 물려받은 기법).
CREATE FUNCTION current_lab_id() RETURNS char(26)
  LANGUAGE sql STABLE
  AS $$
    SELECT CASE
      WHEN current_setting('app.current_lab', true) ~ '^[0-9A-HJKMNP-TV-Z]{26}$'
      THEN current_setting('app.current_lab', true)
      ELSE NULL
    END::char(26)
  $$;

CREATE FUNCTION current_account_id() RETURNS char(26)
  LANGUAGE sql STABLE
  AS $$
    SELECT CASE
      WHEN current_setting('app.current_account', true) ~ '^[0-9A-HJKMNP-TV-Z]{26}$'
      THEN current_setting('app.current_account', true)
      ELSE NULL
    END::char(26)
  $$;

-- 불변 기록용 트리거 2종. "고칠 수 있는 감사 기록은 감사 기록이 아니다" (㉘).
CREATE FUNCTION deny_update_delete() RETURNS trigger
  LANGUAGE plpgsql
  AS $$
  BEGIN
    RAISE EXCEPTION 'append-only 기록이다 — 수정·삭제 경로를 만들지 않는다 (PLAN-SoT 9-28)';
  END;
  $$;

-- 올린 사람은 승계해도 바뀌지 않는다 (정본 §4.1 · P-30).
CREATE FUNCTION deny_uploader_change() RETURNS trigger
  LANGUAGE plpgsql
  AS $$
  BEGIN
    IF NEW.uploader_account_id IS DISTINCT FROM OLD.uploader_account_id THEN
      RAISE EXCEPTION '올린 사람은 바뀌지 않는다 (DataModel 4.1 · P-30)';
    END IF;
    RETURN NEW;
  END;
  $$;

-- ════════════════════════════════════════════════════════════════════════════
-- 1. D1 Identity & Lab — 테넌트 루트 (정본 §2 §3)
-- ════════════════════════════════════════════════════════════════════════════

-- 연구실 = 모든 것의 경계. **자기 자신이 경계이므로 RLS 를 걸지 않는다**
-- (gates/config/rls-allowlist.toml 의 유일한 도메인 면제).
CREATE TABLE d1_lab (
  id          ulid        PRIMARY KEY,
  name        text        NOT NULL CHECK (length(btrim(name)) > 0),
  opened_at   timestamptz NOT NULL,          -- 정본 §2 `개설일`
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- 연구실 정보 — "연구실을 정의하는 유일한 자리" (정본 §2). 연구실 1:1.
-- `데이터 공개 범위` 는 **기본값 한 값**이고 데이터셋이 따로 정했으면 그쪽이 이긴다 (P-27 · ㉗).
CREATE TABLE d1_lab_profile (
  lab_id                  ulid        PRIMARY KEY REFERENCES d1_lab(id),
  university              text,
  department              text,
  principal_investigator  text,
  research_field          text,
  introduction            text,                       -- 한 줄 소개
  default_visibility      text        NOT NULL DEFAULT '열림'
                          CHECK (default_visibility IN ('열림', '잠김')),
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

-- 계정 (정본 §3). 역할·권한 스위치는 D2 가 소유한다 — 여기 두지 않는다.
CREATE TABLE d1_account (
  id          ulid        PRIMARY KEY,
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  name        text        NOT NULL CHECK (length(btrim(name)) > 0),
  email       text        NOT NULL CHECK (length(btrim(email)) > 0),
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (lab_id, email)
);
CREATE INDEX d1_account_lab_idx ON d1_account (lab_id);

-- ════════════════════════════════════════════════════════════════════════════
-- 2. D2 Access & Policy (정본 §3 §4.1 · PERMISSION-PRINCIPLES · ㉖ ㉗ ㉘)
--    규칙 본체(누가 무엇을 할 수 있는가)는 P6 다. 여기는 **저장 자리**뿐이다.
-- ════════════════════════════════════════════════════════════════════════════

-- 역할 2값 (P-2). 계정 1:1.
CREATE TABLE d2_member_role (
  account_id  ulid        PRIMARY KEY REFERENCES d1_account(id),
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  role        text        NOT NULL CHECK (role IN ('교수', '연구원')),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d2_member_role_lab_idx ON d2_member_role (lab_id);

-- 권한 스위치 정확히 4종 (P-3). 스위치 하나 = 한 행 — 다섯 번째 열이 생기지 않는다.
-- 기본값은 스위치 성격을 따른다 (P-4): 앞의 둘 켜짐, 위임 성격 둘 꺼짐.
-- 교수는 네 스위치가 항상 켜진 것으로 **취급한다**(P-5) — 저장이 아니라 판정이라 컬럼을 두지 않는다.
CREATE TABLE d2_permission_switch (
  account_id  ulid        NOT NULL REFERENCES d1_account(id),
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  switch      text        NOT NULL
              CHECK (switch IN ('업로드·편집', '프로젝트 생성', '승인 위임', '연구실 설정')),
  enabled     boolean     NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (account_id, switch)
);
CREATE INDEX d2_permission_switch_lab_idx ON d2_permission_switch (lab_id);

-- 권한 변경 이력 — append-only, **스위치 하나당 한 줄** (㉘ · P-33).
-- 확인 모달 한 번에 세 칸이 바뀌면 세 줄이 남는다. v2 에 조회 화면은 두지 않는다.
CREATE TABLE d2_permission_change (
  id                ulid        PRIMARY KEY,
  lab_id            ulid        NOT NULL REFERENCES d1_lab(id),
  changed_at        timestamptz NOT NULL DEFAULT now(),   -- 언제
  actor_account_id  ulid        NOT NULL REFERENCES d1_account(id),  -- 누가(저장한 사람)
  target_account_id ulid        NOT NULL REFERENCES d1_account(id),  -- 대상
  switch            text        NOT NULL
                    CHECK (switch IN ('업로드·편집', '프로젝트 생성', '승인 위임', '연구실 설정')),
  direction         text        NOT NULL CHECK (direction IN ('켬', '끔'))
);
CREATE INDEX d2_permission_change_lab_idx ON d2_permission_change (lab_id, changed_at DESC);
CREATE TRIGGER d2_permission_change_append_only
  BEFORE UPDATE OR DELETE ON d2_permission_change
  FOR EACH ROW EXECUTE FUNCTION deny_update_delete();

-- 접근 상태 (정본 §4.1 · ㉗). 데이터셋 1:1.
-- state 가 NULL 이면 "따로 정하지 않음" → 연구실 `데이터 공개 범위` 기본값이 적용된다.
-- 값이 있으면 데이터셋 쪽이 이긴다 (P-27).
-- dataset_id 는 **bare 컬럼이다** — D2 가 D3 테이블을 직접 FK 하지 않는다 (CLAUDE.md §3-1).
CREATE TABLE d2_dataset_access (
  dataset_id  ulid        PRIMARY KEY,
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  state       text        CHECK (state IN ('열림', '잠김')),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d2_dataset_access_lab_idx ON d2_dataset_access (lab_id);

-- 볼 수 있는 사람 목록 — 잠김일 때만 쓰인다. 줄마다 만료일 = 승인일 + 6개월 (P-24 · P-25).
-- 승인 단위는 데이터 한 건이다 — 사람 단위·연구실 단위 일괄 승인 자리를 만들지 않는다.
CREATE TABLE d2_dataset_access_grant (
  id                   ulid        PRIMARY KEY,
  lab_id               ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id           ulid        NOT NULL,
  grantee_account_id   ulid        NOT NULL REFERENCES d1_account(id),
  approver_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  approved_at          timestamptz NOT NULL DEFAULT now(),
  expires_at           timestamptz NOT NULL,
  CHECK (expires_at > approved_at),
  UNIQUE (dataset_id, grantee_account_id, approved_at)
);
CREATE INDEX d2_dataset_access_grant_lookup_idx
  ON d2_dataset_access_grant (dataset_id, grantee_account_id, expires_at);
CREATE INDEX d2_dataset_access_grant_lab_idx ON d2_dataset_access_grant (lab_id);

-- ── 승인 처리 두 갈래의 **요청** 표 2종 (WU-P6 · 정본 §7.1 §7.2) ──────────────
--
-- 왜 요청과 결과를 가르나. 아래 두 표는 승인 **전후의 상태**이고, `d2_dataset_access_grant`
-- (허용 목록) 과 `d2_verified` (배지) 는 승인 **결과**다. 결과 표에 '검토 대기'·'거절됨' 을
-- 앉히면 잠금 판정(`d3_file` 의 `body_access` RESTRICTIVE) 과 배지 판정이 **상태 문자열에
-- 의존**하게 된다. 정본 §7.1·§7.2 는 요청의 전이와 결과의 수명(만료·취소)을 **다른 축**으로
-- 적었고, 표를 가르는 것이 그 축을 지키는 방법이다.
--
-- dataset_id 는 두 표 다 **bare 컬럼이다** — D2 가 D3 테이블을 직접 FK 하지 않는다 (CLAUDE.md §3-1).

-- 접근 요청 — 잠긴 데이터를 볼 권한을 여는 요청 (정본 §7.2).
-- 처리하는 사람은 **교수 + `승인 위임` 연구원**이다 (정본 §1.2 §6). 소유자가 아니다.
CREATE TABLE d2_dataset_access_request (
  id                    ulid        PRIMARY KEY,
  lab_id                ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id            ulid        NOT NULL,
  requester_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  -- 요청 사유는 0~300자 **선택**이다 (정본 §5). 빈 문자열은 없음과 같으므로 받지 않는다.
  reason                text        CHECK (reason IS NULL OR
                                           (length(reason) BETWEEN 1 AND 300)),
  requested_at          timestamptz NOT NULL DEFAULT now(),
  -- 상태 3값은 정본 §7.2 전이표 그대로다. **「만료됨」은 여기 없다** — 만료는 허용 줄의
  -- `expires_at` 이 말하고(P-25), 요청 자체는 승인된 채로 남는다. 여기에 넣으면 만료를
  -- 지우러 다니는 배치가 필요해지고, 그 배치가 없으면 값이 거짓말을 한다.
  state                 text        NOT NULL DEFAULT '검토 대기'
                                    CHECK (state IN ('검토 대기', '승인됨', '거절됨')),
  decided_by_account_id ulid        REFERENCES d1_account(id),
  decided_at            timestamptz,
  -- 거절 사유는 1~300자 **필수**이고 요청자에게 그대로 전달된다 (정본 §5 · P-26).
  rejection_reason      text        CHECK (rejection_reason IS NULL OR
                                           (length(rejection_reason) BETWEEN 1 AND 300)),
  CHECK ((decided_by_account_id IS NULL) = (decided_at IS NULL)),
  CHECK ((state = '검토 대기') = (decided_at IS NULL)),
  -- 거절이면 사유가 반드시 있고, 거절이 아니면 사유가 없다. 「사유 없이 거절」은
  -- 화면이 막기 전에 DB 가 막는다 (정본 §9 첫 줄).
  CHECK ((state = '거절됨') = (rejection_reason IS NOT NULL))
);
-- **한 사람이 한 데이터셋에 검토 대기를 둘 이상 만들 수 없다** (정본 §9 「이미 검토 대기 중」).
-- 부분 유니크라 처리가 끝난 뒤에는 다시 요청할 수 있다 (§7.2 「재요청 가능」).
CREATE UNIQUE INDEX d2_dataset_access_request_pending_key
  ON d2_dataset_access_request (dataset_id, requester_account_id)
  WHERE state = '검토 대기';
-- 할 일 함은 **오래된 순**으로 내려간다 — 방치를 막기 위해서다 (정본 §1.3-1).
CREATE INDEX d2_dataset_access_request_pending_idx
  ON d2_dataset_access_request (lab_id, requested_at)
  WHERE state = '검토 대기';
CREATE INDEX d2_dataset_access_request_lab_idx ON d2_dataset_access_request (lab_id);

-- Verified 승인 요청 — 올린 사람·소유자가 상세 헤더에서 직접 누른다 (정본 §1.2 §7.1).
-- **자동으로 검토 대기에 들어가지 않는다.** 처리하는 사람은 **교수만**이고 위임되지 않는다
-- (정본 §1.2 「Verified 는 위임 불가」 · P-22).
CREATE TABLE d2_verification_request (
  id                    ulid        PRIMARY KEY,
  lab_id                ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id            ulid        NOT NULL,
  requester_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  requested_at          timestamptz NOT NULL DEFAULT now(),
  -- **거절이 없다** — 정본 §1.2 축자 「거절 ｜ 없음 (승인 / 미승인)」. 접근 요청 표와
  -- 상태 집합이 다른 것은 실수가 아니라 그 조항이다. 두 표를 하나로 합치면 이 차이가 사라진다.
  state                 text        NOT NULL DEFAULT '검토 대기'
                                    CHECK (state IN ('검토 대기', '승인됨')),
  decided_by_account_id ulid        REFERENCES d1_account(id),
  decided_at            timestamptz,
  CHECK ((decided_by_account_id IS NULL) = (decided_at IS NULL)),
  CHECK ((state = '검토 대기') = (decided_at IS NULL))
);
-- **데이터셋당 검토 대기는 하나다** (계약 `requestVerification` 409 「이미 검토 대기이거나
-- 이미 승인된 데이터다」). 접근 요청과 달리 사람이 열쇠에 안 들어간다 — 대기가 붙는 대상이
-- 데이터셋이고, 처리자도 교수 하나이기 때문이다.
CREATE UNIQUE INDEX d2_verification_request_pending_key
  ON d2_verification_request (dataset_id)
  WHERE state = '검토 대기';
CREATE INDEX d2_verification_request_pending_idx
  ON d2_verification_request (lab_id, requested_at)
  WHERE state = '검토 대기';
CREATE INDEX d2_verification_request_lab_idx ON d2_verification_request (lab_id);

-- Verified 기록 (정본 §4.1). 데이터셋 1:1. 배지 1종.
-- 취소하면 취소한 사람·취소 시각·사유도 남는다 — 데이터와 계보는 남고 배지만 사라진다.
CREATE TABLE d2_verified (
  dataset_id            ulid        PRIMARY KEY,
  lab_id                ulid        NOT NULL REFERENCES d1_lab(id),
  verified              boolean     NOT NULL DEFAULT false,
  approver_account_id   ulid        REFERENCES d1_account(id),
  approved_at           timestamptz,
  cancelled_by_account_id ulid      REFERENCES d1_account(id),
  cancelled_at          timestamptz,
  cancellation_reason   text        CHECK (cancellation_reason IS NULL OR length(cancellation_reason) <= 120),
  CHECK ((approver_account_id IS NULL) = (approved_at IS NULL)),
  CHECK ((cancelled_by_account_id IS NULL) = (cancelled_at IS NULL)),
  CHECK (NOT verified OR approved_at IS NOT NULL)
);
CREATE INDEX d2_verified_lab_idx ON d2_verified (lab_id);

-- ════════════════════════════════════════════════════════════════════════════
-- 3. D3 Catalog (정본 §4.1 §4.3)
-- ════════════════════════════════════════════════════════════════════════════

-- 검색어 결합기 — `text[]` **전용**이다 (`0005`). 다른 타입 배열에 쓰지 않는다.
-- 생성 열은 IMMUTABLE 식만 받는데 `array_to_string` 은 `anyarray` 라 STABLE 이다
-- (원소 출력 함수가 GUC 를 읽을 수 있다 — `timestamptz` 는 DateStyle 을 읽는다).
-- 원소 타입을 `text` 로 못 박으면 그 사유가 사라진다 — `textout` 은 IMMUTABLE 이다.
CREATE FUNCTION d3_search_join(arr text[]) RETURNS text
  LANGUAGE sql IMMUTABLE PARALLEL SAFE
  AS $$ SELECT array_to_string(coalesce(arr, '{}'::text[]), ' ') $$;

-- 데이터셋. **가공 단계 Lv 컬럼도 계보 상태 컬럼도 여기 없다** — 둘 다 파생값이다 (⑳).
-- 다시 올리기(버전) 자리도 없다 (정본 §8).
CREATE TABLE d3_dataset (
  id                     ulid        PRIMARY KEY,
  lab_id                 ulid        NOT NULL REFERENCES d1_lab(id),
  owner_account_id       ulid        NOT NULL REFERENCES d1_account(id),   -- 빈 값 불가 (P-29)
  uploader_account_id    ulid        NOT NULL REFERENCES d1_account(id),   -- 불변 (P-30, 아래 트리거)
  source_label           text,        -- 원천 표기. 계보 그래프의 점선 노드가 이 값이다 (정본 §4.1)
  -- 레코드 시점 3종. `기간`(자동 정보)과 축이 다르다 — 이 셋은 기록의 시간이다 (정본 §4.1).
  uploaded_at            timestamptz NOT NULL DEFAULT now(),
  last_modified_at       timestamptz NOT NULL DEFAULT now(),
  lineage_confirmed_at   timestamptz,
  -- 삭제 기록(묘비). 행을 지우지 않는다 — 지운 데이터가 부모였다면 자식의 출처가 끊긴다 (정본 §4.1).
  deleted_at             timestamptz,
  deleted_by_account_id  ulid        REFERENCES d1_account(id),
  -- 조각 수. **메타다** (㊼). `d3_file` 을 세지 않는다 — `body_access` RESTRICTIVE 아래서 본체 테이블을 세면
  -- 잠긴 데이터셋이 0 을 내고, 계약 `DatasetRow.fileCount`(required · minimum 1)를 표현할 수단이 사라진다.
  -- 드러나는 것은 **개수 하나뿐**이고 이름·종류·본체는 그대로 잠긴다. 유지는 `d3_file` 의 트리거가 한다.
  file_count             integer     NOT NULL DEFAULT 0 CHECK (file_count >= 0),
  CHECK ((deleted_at IS NULL) = (deleted_by_account_id IS NULL)),
  -- 검색 색인 (`0005` · 〈72〉 — 매칭·순위는 tsvector 가 정한다).
  -- `ts_config` 는 `'simple'` 이고 이 값은 **`[정본 무근거]`** 다 — 소문자화·구두점 분리뿐,
  -- 한국어 형태소 분석이 없다(이미지의 `pg_ts_config` 29종에 한국어가 없다 — 실측).
  search_vector tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(source_label, '')), 'B')
  ) STORED,
  -- ── `0007` 이 더한 셋. **여기 순서는 임의가 아니다** ──────────────────────────
  -- `ALTER TABLE ADD COLUMN` 은 열을 **뒤에** 붙인다. 선언이 이 순서와 다르면
  -- schema-diff 가 red 를 낸다 — 실제로 그렇게 잡혔다.
  -- 가공 단계 — **사람이 고른 값만 담는다** (`0007` · `PLAN-SoT §9 〈140〉`).
  -- ⚠ **계산 결과를 여기 넣지 않는다.** `⑳` 이 「저장 필드를 두지 않는다」고 한 것이 막으려던
  -- 위험은 `DATAMODEL-BASELINE:166` 이 적은 그것이다 — 「Lv 를 손으로 고치는 칸으로 두면
  -- 계보를 고쳐도 Lv 가 안 따라가 둘이 갈라진다」. **낡는 것은 계산 결과지 사람의 의도가 아니다.**
  -- `NULL` = 계보에서 파생하라 · 값 있음 = 사람이 골랐으니 자동 보정이 덮지 않는다 (`POL-020` 예외).
  processing_level_user_set smallint,
  CONSTRAINT d3_dataset_processing_level_user_set_range CHECK (
    processing_level_user_set IS NULL OR processing_level_user_set BETWEEN 0 AND 2),
  -- 대표 조각 — 상세 진입 시 미리보기에 그려지는 조각 (결정 2-4).
  -- **`NULL` 이 「자동」이다** — 파일명 오름차순 자연 정렬의 첫 조각(결정 2-8)을 그때그때 고른다.
  -- 값이 있으면 사람이 지정한 것이라 **렌더 결과가 바뀌어도 따라 움직이지 않는다.**
  -- 별도 플래그를 두지 않는 이유가 이것이다 — `NULL` 하나로 두 상태가 다 표현된다.
  -- ⚠ FK 는 여기 못 붙인다 — `d3_file` 이 아직 선언되기 전이다(그쪽이 이 표를 참조한다).
  --    제약은 `d3_file` 선언 뒤에 `ALTER TABLE` 로 붙인다. 순서가 곧 이유다.
  representative_file_id ulid,
  -- 원천 표기의 정규화값 (결정 2-10). **원문(`source_label`)을 지우지 않고 병기한다** —
  -- 원문이 남아야 나중에 정규화 규칙이 바뀌어도 복구된다.
  -- 근거: 원천은 **계보 그래프의 뿌리 노드**라 `ERA5`/`era5`/`ECMWF ERA5` 가 각각 노드가 되면
  -- 「ERA5 를 쓴 데이터셋 전부」에 답할 수 없고 그래프 상단이 통째로 갈라진다.
  source_label_normalized text
);
CREATE INDEX d3_dataset_lab_idx ON d3_dataset (lab_id);
CREATE INDEX d3_dataset_search_idx ON d3_dataset USING gin (search_vector);
CREATE INDEX d3_dataset_owner_idx ON d3_dataset (owner_account_id);
-- 자동완성이 훑는 자리 (`listDatasetFieldSuggestions` · 결정 2-10).
-- **연구실을 앞에 둔다** — 경계 없는 접두 스캔이 되지 않게 한다.
CREATE INDEX d3_dataset_source_label_normalized_idx
  ON d3_dataset (lab_id, source_label_normalized)
  WHERE source_label_normalized IS NOT NULL;
CREATE TRIGGER d3_dataset_uploader_immutable
  BEFORE UPDATE ON d3_dataset
  FOR EACH ROW EXECUTE FUNCTION deny_uploader_change();

-- 사람이 적는 정보 — 이름 · 주제 · 설명 (정본 §4.1). 데이터셋 1:1.
-- 목록·상세가 쓰는 이름이 이 `name` 이다. 조각 하나를 대표로 세우지 않는다 (§4.3).
CREATE TABLE d3_dataset_description (
  dataset_id  ulid        PRIMARY KEY REFERENCES d3_dataset(id),
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  name        text        NOT NULL CHECK (length(btrim(name)) > 0),
  -- 주제 = **확정 열거값 10번째** (⑲ · 〈55〉). 4값은 `㊸-④-2`(`P04 §5`) 가 못 박았다.
  -- **nullable 을 유지한다** — 강제하는 것은 「값이 있다면 넷 중 하나」이지 「반드시 있다」가 아니다.
  -- 아직 분류하지 않은 상태가 표현되어야 하고, 4값이 담지 못하는 실데이터(`D-11`·`D-12`)는 NULL 로 남는다.
  topic       text        CHECK (topic IS NULL OR topic IN ('강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC')),
  summary     text,
  updated_at  timestamptz NOT NULL DEFAULT now(),
  -- 사람이 적은 말. **이름이 가장 무겁다** — 검색 순위가 여기서 갈린다 (`0005`).
  search_vector tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(name, '')),    'A') ||
    setweight(to_tsvector('simple', coalesce(topic, '')),   'B') ||
    setweight(to_tsvector('simple', coalesce(summary, '')), 'C')
  ) STORED
);
CREATE INDEX d3_dataset_description_lab_idx ON d3_dataset_description (lab_id);
CREATE INDEX d3_dataset_description_search_idx
  ON d3_dataset_description USING gin (search_vector);
-- 이름의 **삼중자 색인** (`0006` · `PLAN-SoT §9-〈89〉`). `tsvector` 가 한 건도 못 잡은
-- 질의에만 도는 보조 팔이다 — `ts_config='simple'` 이 형태소를 안 자르므로 접두 질의로도
-- 못 넘는 자리(질의가 색인된 낱말보다 **긴** 경우)가 남고, 그 자리를 유사도가 받는다.
-- **순위는 여전히 `tsvector` 가 낸다** — 유사도는 세 번째 정렬 키다 (`〈89〉-㉮③`).
CREATE INDEX d3_dataset_description_name_trgm_idx
  ON d3_dataset_description USING gin (name gin_trgm_ops);

-- 자동으로 읽은 정보 (정본 §4.1). **파일에서 자동** — 사람이 타이핑하지 않는다.
-- 본체가 여럿이면 §4.3 합치는 규칙의 **결과**를 담는다
-- (포맷·변수·좌표계·격자는 모든 조각이 같아야 하고, 기간은 합집합, 용량은 합계).
CREATE TABLE d3_dataset_autometa (
  dataset_id        ulid        PRIMARY KEY REFERENCES d3_dataset(id),
  lab_id            ulid        NOT NULL REFERENCES d1_lab(id),
  format            text,
  variables         text[]      NOT NULL DEFAULT '{}',
  period_start      timestamptz,
  period_end        timestamptz,
  crs               text,
  grid              text,
  total_size_bytes  bigint      CHECK (total_size_bytes IS NULL OR total_size_bytes >= 0),
  bundle_file_name  text,       -- 묶음 이름(조각에서 시각 부분을 뺀 파일명). 조각 이름이 아니다 (§4.3)
  updated_at        timestamptz NOT NULL DEFAULT now(),
  CHECK (period_start IS NULL OR period_end IS NULL OR period_start <= period_end),
  -- 파일에서 자동으로 읽은 말 (`0005`). 변수명·포맷이 좌표계·격자·묶음 이름보다 앞선다.
  -- 배열은 `d3_search_join` 을 지난다 — `array_to_tsvector` 는 대소문자를 그대로 둬서
  -- `to_tsquery` 와 영영 안 만난다(실측). 있는데 절대 안 맞는 색인이 될 뻔했다.
  search_vector tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple',
      coalesce(format, '') || ' ' || d3_search_join(variables)), 'B') ||
    setweight(to_tsvector('simple',
      coalesce(crs, '') || ' ' || coalesce(grid, '') || ' ' ||
      coalesce(bundle_file_name, '')), 'C')
  ) STORED
);
CREATE INDEX d3_dataset_autometa_lab_idx ON d3_dataset_autometa (lab_id);
CREATE INDEX d3_dataset_autometa_search_idx
  ON d3_dataset_autometa USING gin (search_vector);

-- 파일 — 데이터셋 1:N. 종류는 둘뿐이고 기준 격자 파일은 데이터셋당 **0~2건**
-- (위도·경도 한 쌍이 실물이다 — `〈58〉`. 결합축 파일이면 1건으로 둘 다 선다 — `〈66〉`).
-- **파일에는 계보가 없다.** 계보는 데이터셋 사이에만 있다 (§4.2·§4.3).
-- 파일 **본체 테이블**이므로 경계 정책 위에 본체 정책이 하나 더 걸린다 (㉖ ③ · P-34).
--
-- 축은 **텍스트 단일값이 아니라 두 불리언**이다 (`〈66〉` — `0004`).
--   실물 16건 중 2건이 한 파일에 `lat`·`lon` 을 다 담는다. 단일값 모델은 그 파일을
--   「축을 못 갈라서」가 아니라 **「둘 다 갈려서」** 표현하지 못한다.
--   제3값(결합축이라는 세 번째 enum)은 **「위도 1건 + 결합축 1건」을 못 막아** 탈락했다.
--   **행 : 파일 = 1 : 1 을 유지한다** — 행을 축으로 쪼개면 같은 `storage_key` 가 두 행에 들어간다.
CREATE TABLE d3_file (
  id           ulid        PRIMARY KEY,
  lab_id       ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id   ulid        NOT NULL REFERENCES d3_dataset(id),
  kind         text        NOT NULL CHECK (kind IN ('본체', '기준 격자 파일')),
  file_name    text        NOT NULL CHECK (length(btrim(file_name)) > 0),
  size_bytes   bigint      CHECK (size_bytes IS NULL OR size_bytes >= 0),
  storage_key  text        NOT NULL CHECK (length(btrim(storage_key)) > 0),
  created_at   timestamptz NOT NULL DEFAULT now(),
  carries_lat  boolean     NOT NULL DEFAULT false,
  carries_lon  boolean     NOT NULL DEFAULT false,
  -- 폴더째 업로드에서 온 파일의 `폴더/이름` 상대 경로 (0009 · 〈278〉-(나)). 낱개 파일은 NULL.
  -- 접수 원장 `d5_upload_file.relative_path`(0008 · 〈276〉-③)를 등록 전환 때 **그대로** 승계한다 —
  -- 저장 키에는 넣지 않는다. 키 규약(contracts/storage/layout.json)은 세 배포 단위의 공유
  -- 정본이라 여기 메타로만 보존한다. **맨 뒤에 선언한다** — `ALTER TABLE ADD COLUMN` 은
  -- 열을 뒤에 붙이고 선언 순서가 다르면 schema-diff 가 red 를 낸다 (d3_dataset 의 0007 주석).
  relative_path text        CHECK (relative_path IS NULL
                                   OR length(relative_path) BETWEEN 1 AND 1024),
  -- **양쪽 반쪽을 다 건다.** 축 없는 격자 파일도, 축 붙은 본체도 만들지 않는다 —
  -- 한쪽만 걸면 「열을 뒀는데 안 채우면 그만」이 된다 (DATA-REFERENCE §1).
  CONSTRAINT d3_file_grid_carries_an_axis
    CHECK (kind <> '기준 격자 파일' OR carries_lat OR carries_lon),
  CONSTRAINT d3_file_body_carries_no_axis
    CHECK (kind <> '본체' OR (NOT carries_lat AND NOT carries_lon))
);
CREATE INDEX d3_file_dataset_idx ON d3_file (dataset_id);
CREATE INDEX d3_file_lab_idx ON d3_file (lab_id);
-- 유일성은 **축 원소마다 1건**이다. 개수만 2로 늘리면 위도 파일이 둘 들어가고 시스템이
-- 둘을 구분하지 못한다 — 개수 제약은 「몇 개냐」만 답하고 「무엇이냐」는 안 답한다.
-- 결합축 파일은 두 인덱스에 **동시에** 걸리므로 「위도1 + 결합1」도 여기서 막힌다.
-- 본체 1건 이상은 행 제약으로 표현할 수 없다 — 마지막 본체를 지우는 것을 막는 일은
-- 애플리케이션·묘비 규칙의 몫이다.
CREATE UNIQUE INDEX d3_file_one_lat_grid_per_dataset
  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일' AND carries_lat;
CREATE UNIQUE INDEX d3_file_one_lon_grid_per_dataset
  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일' AND carries_lon;

-- 대표 조각의 FK (`0007` · 결정 2-4). `d3_dataset` 선언 시점에는 이 표가 없어 여기서 붙인다.
--   · `ON DELETE SET NULL` — 대표로 지정한 조각이 사라지면 **자동으로 되돌아간다.**
--     그 자리를 비워 두면 상세가 없는 조각을 그리려 하고, 막으면 조각을 못 지운다.
--   · 다른 데이터셋의 조각을 대표로 지정하는 것은 **FK 로 못 막는다**(같은 표라서).
--     그 검사는 애플리케이션의 몫이고, 음성 시험이 지킨다.
ALTER TABLE d3_dataset
  ADD CONSTRAINT d3_dataset_representative_file_fk
  FOREIGN KEY (representative_file_id) REFERENCES d3_file(id) ON DELETE SET NULL;

-- 조각 수 유지 (㊼). **다시 세지 않고 증분으로 더한다.**
--   · 다시 세면 세는 주체가 `body_access` 를 받아 잠긴 데이터셋에 0 을 써 넣는다 — 고치려던 결함을 트리거가 재현한다
--   · 문장 단위 + 전이 테이블: 전이 테이블은 RLS 로 걸러지지 않는다(실제로 영향받은 행 그대로).
--     한 문장이 조각 수백 개를 넣어도 `d3_dataset` UPDATE 는 한 번이다
--   · `UPDATE ... SET file_count = file_count + n` 은 행 잠금을 잡는다 — 동시 삽입도 어긋나지 않는다
--   · 갱신된 행 수가 기대와 다르면 **예외로 멈춘다.** 경계 정책이 UPDATE 를 0행으로 막는 순간
--     조용히 드리프트가 생기는데, 조용한 드리프트가 비정규화의 유일한 위험이다
CREATE FUNCTION sync_dataset_file_count() RETURNS trigger
  LANGUAGE plpgsql
  AS $$
  DECLARE
    ids     char(26)[];
    deltas  bigint[];
    touched bigint;
  BEGIN
    IF TG_OP = 'INSERT' THEN
      SELECT array_agg(g.dataset_id), array_agg(g.n) INTO ids, deltas
        FROM (SELECT dataset_id, count(*)::bigint AS n FROM new_files GROUP BY dataset_id) g;
    ELSIF TG_OP = 'DELETE' THEN
      SELECT array_agg(g.dataset_id), array_agg(-g.n) INTO ids, deltas
        FROM (SELECT dataset_id, count(*)::bigint AS n FROM old_files GROUP BY dataset_id) g;
    ELSE
      SELECT array_agg(g.dataset_id), array_agg(g.n) INTO ids, deltas
        FROM (
          SELECT dataset_id, sum(d)::bigint AS n
            FROM (SELECT dataset_id, 1 AS d FROM new_files
                  UNION ALL
                  SELECT dataset_id, -1 AS d FROM old_files) s
           GROUP BY dataset_id HAVING sum(d) <> 0
        ) g;
    END IF;

    IF ids IS NULL THEN
      RETURN NULL;
    END IF;

    WITH applied AS (
      UPDATE d3_dataset t
         SET file_count = t.file_count + u.n
        FROM unnest(ids, deltas) AS u(dataset_id, n)
       WHERE t.id = u.dataset_id
      RETURNING 1
    )
    SELECT count(*) INTO touched FROM applied;

    IF touched <> array_length(ids, 1) THEN
      RAISE EXCEPTION '조각 수를 유지하지 못했다 — d3_dataset % 건 중 % 건만 갱신됐다 (PLAN-SoT 9-47)',
        array_length(ids, 1), touched;
    END IF;
    RETURN NULL;
  END;
  $$;

CREATE TRIGGER d3_file_count_insert
  AFTER INSERT ON d3_file
  REFERENCING NEW TABLE AS new_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_file_count();

CREATE TRIGGER d3_file_count_delete
  AFTER DELETE ON d3_file
  REFERENCING OLD TABLE AS old_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_file_count();

-- 조각이 다른 데이터셋으로 옮겨 가는 경우. 열 목록(`UPDATE OF dataset_id`)을 붙이지 않는다 —
-- postgres 는 열 목록과 전이 테이블을 함께 못 쓴다. 옮김이 아닌 UPDATE 는 증분이 0 이라 저절로 빠진다.
CREATE TRIGGER d3_file_count_move
  AFTER UPDATE ON d3_file
  REFERENCING OLD TABLE AS old_files NEW TABLE AS new_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_file_count();

-- 용량 합계 유지 (`0009` · 〈278〉). `d3_dataset_autometa.total_size_bytes` 를 위의
-- `sync_dataset_file_count` 와 **같은 기구**로 움직인다 — `file_count` 와 같은 표·같은 사건을
-- 다른 기구로 움직이면 드리프트 유형이 둘이 된다.
--   · **다시 세지 않고 증분으로 더한다** — 다시 세면 `body_access` 아래서 잠긴 데이터셋이 0 이 된다
--   · 문장 단위 + 전이 테이블 — 전이 테이블은 RLS 로 걸러지지 않는다
--   · `size_bytes` NULL 인 조각은 0 으로 센다 — 합계가 NULL 로 물들지 않는다
--   · UPDATE 는 `size_bytes` 변경·데이터셋 이동일 때만 뜻이 있다. `UPDATE OF size_bytes` 는
--     전이 테이블과 함께 못 쓰므로 함수 안에서 차분을 내고, 차분 0 인 데이터셋은 저절로 빠진다
--   · `file_count` 와 다른 점 하나 — 갱신 행 수를 검사하지 않는다. autometa 행은 데이터셋마다
--     반드시 있는 것이 아니라(등록 전환이 따로 세운다) 없는 데이터셋은 건너뛴다
--   · ⚠ 이 열에 값을 **손으로 넣지 않는다.** 시드·등록 전환이 합계를 직접 쓰고 조각도 넣으면
--     두 번 센다 — `file_count` 와 같은 규율이다 (seed.sql 의 file_count 주석)
CREATE FUNCTION sync_dataset_total_size() RETURNS trigger
  LANGUAGE plpgsql
  AS $$
  DECLARE
    ids     char(26)[];
    deltas  bigint[];
  BEGIN
    IF TG_OP = 'INSERT' THEN
      SELECT array_agg(g.dataset_id), array_agg(g.n) INTO ids, deltas
        FROM (SELECT dataset_id, sum(COALESCE(size_bytes, 0))::bigint AS n
                FROM new_files GROUP BY dataset_id
              HAVING sum(COALESCE(size_bytes, 0)) <> 0) g;
    ELSIF TG_OP = 'DELETE' THEN
      SELECT array_agg(g.dataset_id), array_agg(-g.n) INTO ids, deltas
        FROM (SELECT dataset_id, sum(COALESCE(size_bytes, 0))::bigint AS n
                FROM old_files GROUP BY dataset_id
              HAVING sum(COALESCE(size_bytes, 0)) <> 0) g;
    ELSE
      SELECT array_agg(g.dataset_id), array_agg(g.n) INTO ids, deltas
        FROM (
          SELECT dataset_id, sum(d)::bigint AS n
            FROM (SELECT dataset_id,  COALESCE(size_bytes, 0) AS d FROM new_files
                  UNION ALL
                  SELECT dataset_id, -COALESCE(size_bytes, 0) AS d FROM old_files) s
           GROUP BY dataset_id HAVING sum(d) <> 0
        ) g;
    END IF;

    IF ids IS NULL THEN
      RETURN NULL;
    END IF;

    UPDATE d3_dataset_autometa t
       SET total_size_bytes = COALESCE(t.total_size_bytes, 0) + u.n
      FROM unnest(ids, deltas) AS u(dataset_id, n)
     WHERE t.dataset_id = u.dataset_id;
    RETURN NULL;
  END;
  $$;

CREATE TRIGGER d3_file_total_size_insert
  AFTER INSERT ON d3_file
  REFERENCING NEW TABLE AS new_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_total_size();

CREATE TRIGGER d3_file_total_size_delete
  AFTER DELETE ON d3_file
  REFERENCING OLD TABLE AS old_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_total_size();

CREATE TRIGGER d3_file_total_size_update
  AFTER UPDATE ON d3_file
  REFERENCING OLD TABLE AS old_files NEW TABLE AS new_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_total_size();

-- ════════════════════════════════════════════════════════════════════════════
-- 4. D4 Lineage (정본 §4.2)
-- ════════════════════════════════════════════════════════════════════════════

-- 계보 관계. 관계 하나 = "자식 ← 부모" 한 쌍. **한 자식에 부모가 여럿일 수 있다.**
-- 가공 방식은 **관계에 붙는다** — 화살표 라벨이 되는 값이라서다 (소급 위험 §3-②).
-- **사람이 확인한 관계만 저장한다** — `제안` 상태 값이 없는 것이 D10→D4 쓰기 경로 부재의 저장 형태 쪽 표현이다
-- (CLAUDE.md §3-2 · 소급 위험 §3-⑦). 확인 기록은 NOT NULL 이다.
CREATE TABLE d4_lineage_edge (
  id                     ulid        PRIMARY KEY,
  lab_id                 ulid        NOT NULL REFERENCES d1_lab(id),
  child_dataset_id       ulid        NOT NULL REFERENCES d3_dataset(id),
  parent_dataset_id      ulid        NOT NULL REFERENCES d3_dataset(id),
  parent_role            text        NOT NULL DEFAULT '주입력'
                         CHECK (parent_role IN ('주입력', '보조입력')),
  method                 text,       -- 가공 방식 한 줄. 자유 문장 — 정본이 열거값을 주지 않았다
  origin                 text        NOT NULL
                         -- 뜻: ai = AI 가 제안하고 **사람이 확인**한 것(「AI 가 만든 것」이 아니다 —
                         -- AI 는 계보를 쓰지 않는다, CLAUDE.md §3-2) · manual = 사람이 손으로 이은 것 ·
                         -- processed = 가공으로 자동 생성된 것(생산 경로는 아직 없다 — 값만 열려 있다).
                         -- 근거: PLAN-SoT §9 〈198〉·〈205〉 (10 차 동결 해제).
                         CHECK (origin IN ('ai', 'manual', 'processed')),
  confirmed_by_account_id ulid       NOT NULL REFERENCES d1_account(id),
  confirmed_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (child_dataset_id <> parent_dataset_id),
  UNIQUE (child_dataset_id, parent_dataset_id)
);
CREATE INDEX d4_lineage_edge_child_idx ON d4_lineage_edge (child_dataset_id);
CREATE INDEX d4_lineage_edge_parent_idx ON d4_lineage_edge (parent_dataset_id);
CREATE INDEX d4_lineage_edge_lab_idx ON d4_lineage_edge (lab_id);

-- 기록 없음 표시 (정본 §4.2). 부모를 모르는 채 등록한 표시이고, 관계가 붙으면 지운다.
-- 근거 없는 추측을 사실처럼 기록하지 않기 위한 자리다.
CREATE TABLE d4_lineage_unknown (
  dataset_id      ulid        PRIMARY KEY REFERENCES d3_dataset(id),
  lab_id          ulid        NOT NULL REFERENCES d1_lab(id),
  marked_at       timestamptz NOT NULL DEFAULT now(),
  marked_by_account_id ulid   NOT NULL REFERENCES d1_account(id)
);
CREATE INDEX d4_lineage_unknown_lab_idx ON d4_lineage_unknown (lab_id);

-- ════════════════════════════════════════════════════════════════════════════
-- 4-b. D5 Ingestion & Pipeline — 등록 **전** 임시 원장 (`0004` · `〈63〉-㉱` · `〈64〉`)
--
--   「등록 전에는 아무것도 저장되지 않는다」의 **대상은 D3 카탈로그**다 (`〈64〉-ⓐ` · P2.md §2-27).
--   이 세 표는 그 진술의 대상이 아니라 **D5 소유의 처리 중 상태**이고(`ⓑ`),
--   어느 사용자 읽기 경로(카탈로그·계보·검색)에도 비치지 않으며 만료되면 reaper 가 지운다(`ⓒ`).
--   원장이 없으면 `getUploadStatus` 가 읽을 자리가 사라져 이벤트 ②~⑦ 이 갈 곳을 잃는다.
--
--   **`core-api` 는 이 표들을 직접 만지지 않는다** — `ports/ingestion.py` 를 지난다
--   (`〈63〉-㉱` · 불변규칙 1). 여기에는 D3·D4·D6 를 가리키는 FK 가 **하나도 없다.**
-- ════════════════════════════════════════════════════════════════════════════

-- 업로드 1건 — 등록 전 임시 세계의 집계 루트. `uploadId` 는 이벤트 봉투의 것과 같은 값이다.
CREATE TABLE d5_upload (
  id                   ulid        PRIMARY KEY,
  lab_id               ulid        NOT NULL REFERENCES d1_lab(id),
  uploader_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  created_at           timestamptz NOT NULL DEFAULT now(),
  -- 수명. **값은 정본이 안 줬다** — 계약이 발행자에게 열어 뒀고(`NB-2`), 여기서 DEFAULT 를
  -- 발명하지 않는다. 넣는 쪽이 명시한다.
  expires_at           timestamptz NOT NULL,
  -- 이벤트 ②~⑦ 의 **결과**를 담는 자리. 새 사실을 만들지 않는다 (`UploadStatus` 와 1:1).
  ready                boolean     NOT NULL DEFAULT false,
  renderable           boolean,            -- 아직 모르면 NULL (계약도 3값이다)
  metadata_complete    boolean,            -- 상동
  failed_at            timestamptz,
  failure_class        text CHECK (failure_class IS NULL OR failure_class IN ('재시도 가능', '영구')),
  failure_reason       text CHECK (failure_reason IS NULL OR failure_reason IN (
                         '업로드 중단', '형식 인식 실패', '헤더 인식 실패', '조각이 서로 다름',
                         '좌표계 변환 실패', '미리보기 준비 실패', '시간 초과', '내부 오류')),
  -- 등록 전환 시각. **`datasetId` 를 두지 않는다** — D5 가 D3 를 직접 가리키면 불변규칙 1 위반이다.
  -- 「이미 전환됐다(409)」 판정에 필요한 것은 여부이지 대상이 아니다.
  registered_at        timestamptz,
  CHECK (expires_at > created_at),
  -- 실패는 세 값이 함께 선다. 하나만 채워진 반쪽 실패를 만들지 않는다.
  CHECK ((failed_at IS NULL) = (failure_reason IS NULL)
         AND (failed_at IS NULL) = (failure_class IS NULL))
);
CREATE INDEX d5_upload_lab_idx ON d5_upload (lab_id);
-- reaper 가 만료분을 훑는 자리 (`〈64〉-ⓒ`).
CREATE INDEX d5_upload_expiry_idx ON d5_upload (expires_at);

-- 업로드 안의 파일 N건.
-- **PK 가 업로드가 발급한 `fileId` ULID 다** — 등록 시 `d3_file.id` 로 **그대로** 간다.
-- 변환 지점이 없다는 것이 `NB-A`(fileId 동일성)의 저장 형태 쪽 표현이다.
CREATE TABLE d5_upload_file (
  id               ulid        PRIMARY KEY,
  lab_id           ulid        NOT NULL REFERENCES d1_lab(id),
  upload_id        ulid        NOT NULL REFERENCES d5_upload(id) ON DELETE CASCADE,
  kind             text        NOT NULL CHECK (kind IN ('본체', '기준 격자 파일')),
  file_name        text        NOT NULL CHECK (length(btrim(file_name)) > 0
                                               AND length(file_name) <= 255),
  byte_size        bigint      CHECK (byte_size IS NULL OR byte_size >= 0),
  storage_key      text        NOT NULL CHECK (length(btrim(storage_key)) > 0),
  -- D3 와 **같은 두 열 · 같은 두 CHECK.** 원장이 먼저 막지 않으면 등록 전환 때 뒤늦게 터진다.
  carries_lat      boolean     NOT NULL DEFAULT false,
  carries_lon      boolean     NOT NULL DEFAULT false,
  -- 파이프라인이 매직바이트로 판정한 포맷 (`file.format-detected`). 확장자가 아니다.
  detected_format  text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  -- 폴더째 업로드에서 온 파일의 `폴더/이름` 상대 경로 (0008 · 〈276〉). 낱개 파일은 NULL.
  -- 저장 키에는 넣지 않는다 — 키 규약(contracts/storage/layout.json)은 세 배포 단위의
  -- 공유 정본이라 여기 메타로만 보존한다. 등록 후(d3) 표시는 `0009` 의 `d3_file.relative_path`.
  -- `created_at` **뒤에** 선언한다 — 0008 은 `ALTER TABLE ADD COLUMN` 이라 열이 맨 뒤에 붙고,
  -- 선언 순서가 다르면 schema-diff 가 red 를 낸다 (d3_dataset 의 0007 주석과 같은 이유).
  relative_path    text        CHECK (relative_path IS NULL
                                      OR length(relative_path) BETWEEN 1 AND 1024),
  CONSTRAINT d5_upload_file_grid_carries_an_axis
    CHECK (kind <> '기준 격자 파일' OR carries_lat OR carries_lon),
  CONSTRAINT d5_upload_file_body_carries_no_axis
    CHECK (kind <> '본체' OR (NOT carries_lat AND NOT carries_lon))
);
CREATE INDEX d5_upload_file_upload_idx ON d5_upload_file (upload_id);
CREATE INDEX d5_upload_file_lab_idx ON d5_upload_file (lab_id);
-- D3 와 같은 유일성을 원장에서도 건다 — 업로드 하나 안에 같은 축이 둘 있으면 등록은
-- 반드시 실패한다. 그 실패를 등록 시점이 아니라 **접수 시점에** 낸다.
CREATE UNIQUE INDEX d5_upload_file_one_lat_grid_per_upload
  ON d5_upload_file (upload_id) WHERE kind = '기준 격자 파일' AND carries_lat;
CREATE UNIQUE INDEX d5_upload_file_one_lon_grid_per_upload
  ON d5_upload_file (upload_id) WHERE kind = '기준 격자 파일' AND carries_lon;

-- 프리사인드 전송 원장 (0008 · 〈277〉 동결 해제 8차) — 저장 모드 s3 에서만 쓰인다.
-- **전송이 완결되기 전의 상태**만 담는다: 완결(complete)되는 순간 같은 ULID 로
-- `d5_upload` 가 서고(upload.accepted 발행), 이후는 기존 원장의 세계다.
-- 격자 파일도 여기엔 행이 선다 — 축 CHECK 가 없는 전송 전용 표라서다. `d5_upload_file`
-- 의 격자 행은 여전히 워커가 축을 정한 뒤 세운다 (`〈79〉`).
-- 파트의 정본은 S3 ListParts 다 — 파트 번호·크기를 여기 저장하지 않는다.
CREATE TABLE d5_upload_transfer (
  id                   ulid        PRIMARY KEY,          -- 완결 시 d5_upload.id 로 승계
  lab_id               ulid        NOT NULL REFERENCES d1_lab(id),
  uploader_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  source_label         text        NOT NULL CHECK (length(source_label) <= 255),
  created_at           timestamptz NOT NULL DEFAULT now(),
  expires_at           timestamptz NOT NULL,             -- 이어올리기 창 — 수명 밖은 정리 대상
  completed_at         timestamptz,                      -- 완결 = d5_upload 로 승계된 시각
  CONSTRAINT d5_upload_transfer_expiry_after_birth CHECK (expires_at > created_at)
);
CREATE INDEX d5_upload_transfer_lab_idx ON d5_upload_transfer (lab_id);
-- 미완료 배너·지연 정리가 훑는 자리.
CREATE INDEX d5_upload_transfer_open_idx ON d5_upload_transfer (expires_at)
  WHERE completed_at IS NULL;

CREATE TABLE d5_upload_transfer_file (
  id             ulid        PRIMARY KEY,                -- 완결 시 d5_upload_file.id 로 승계 (NB-A)
  lab_id         ulid        NOT NULL REFERENCES d1_lab(id),
  transfer_id    ulid        NOT NULL REFERENCES d5_upload_transfer(id) ON DELETE CASCADE,
  kind           text        NOT NULL CHECK (kind IN ('본체', '기준 격자 파일')),
  file_name      text        NOT NULL CHECK (length(btrim(file_name)) > 0
                                             AND length(file_name) <= 255),
  relative_path  text        CHECK (relative_path IS NULL
                                    OR length(relative_path) BETWEEN 1 AND 1024),
  byte_size      bigint      NOT NULL CHECK (byte_size >= 0),
  storage_key    text        NOT NULL CHECK (length(btrim(storage_key)) > 0),
  -- 멀티파트일 때만: 파트 크기와 S3 가 발급한 멀티파트 UploadId. 단일 PUT 은 둘 다 NULL.
  part_size      bigint      CHECK (part_size IS NULL OR part_size > 0),
  transfer_ref   text,
  -- 서버가 S3 실측(ListParts·HeadObject)으로 확인한 결과만 기록한다 — 자기 보고를 믿지 않는다.
  outcome        text        NOT NULL DEFAULT '대기' CHECK (outcome IN ('대기', '올라감', '실패')),
  created_at     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT d5_upload_transfer_file_ref_only_for_multipart
    CHECK (transfer_ref IS NULL OR part_size IS NOT NULL)
);
CREATE INDEX d5_upload_transfer_file_transfer_idx ON d5_upload_transfer_file (transfer_id);
CREATE INDEX d5_upload_transfer_file_lab_idx ON d5_upload_transfer_file (lab_id);

-- 파이프라인 이벤트 / outbox. 열 구성의 정본은 `contracts/events/envelope.json` 의 봉투다 —
-- 여기서 값 집합을 **재선언하지 않고 옮겨 적는다** (⑲ 「확정 열거값은 DB 가 강제한다」).
CREATE TABLE d5_pipeline_event (
  id                  ulid        PRIMARY KEY,          -- = eventId (전달의 정체성)
  lab_id              ulid        NOT NULL REFERENCES d1_lab(id),
  actor_account_id    ulid        NOT NULL REFERENCES d1_account(id),
  -- **파일 단위 이벤트가 없다.** 7종 페이로드 전부가 업로드 단위이고, 파일을 가리킬 때도
  -- `fileIds` 배열을 페이로드에 싣는다 (core-pipeline.json — CrsNormalized·CogBuilt).
  -- 그래서 `file_id` 열을 두지 않는다. 그리고 그것이 멱등 키가 `<타입>:<uploadId>` 만으로
  -- 충돌 없이 성립하는 이유다 — 타입 하나당 업로드 하나당 이벤트 하나.
  upload_id           ulid        NOT NULL REFERENCES d5_upload(id) ON DELETE CASCADE,
  -- ⭑ ⟨증보 2026-08-31 · 12 차 동결 해제 · `PLAN-SoT §9 〈253〉`⟩ **10 종이다** ／ 이전 7 종.
  --   ① 앞의 7 = E-04 업로드 파이프라인(core-api ↔ pipeline-worker) — 업로드 하나의 **진행**
  --   ② 뒤의 3 = D5 → D7 알림(pipeline-worker → viz-render) — 「이미 선 미리보기의 재료가
  --      바뀌었다」는 **사실**. `Y-1` 의 트리거 발신이 여기 실린다. 무엇을 지울지는 D7 이 정한다.
  event_type          text        NOT NULL CHECK (event_type IN (
                        'upload.accepted', 'file.format-detected', 'file.header-parsed',
                        'file.crs-normalized', 'preview.cog-built', 'upload.ready', 'upload.failed',
                        'preview.backend-rerun', 'preview.grid-changed', 'preview.file-added')),
  schema_version      text        NOT NULL CHECK (schema_version ~ '^[0-9]+\.[0-9]+$'),
  source              text        NOT NULL CHECK (source IN ('core-api', 'pipeline-worker')),
  occurred_at         timestamptz NOT NULL DEFAULT now(),
  -- **작업의 정체성.** `<이벤트 타입>:<uploadId>` 로 결정론적으로 만든다 — 발행자가 난수를
  -- 쓰지 않으므로 outbox 행이 다시 만들어져도 같은 키가 나온다 (envelope.json `IdempotencyKey`).
  idempotency_key     text        NOT NULL CHECK (
                        idempotency_key ~ '^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*:[0-9A-HJKMNP-TV-Z]{26}$'),
  attempt             integer     NOT NULL DEFAULT 1 CHECK (attempt >= 1),
  max_attempts        integer     NOT NULL DEFAULT 5 CHECK (max_attempts >= 1),
  first_published_at  timestamptz,        -- 미발행 = NULL. 릴레이가 채운다
  published_at        timestamptz,
  dead_lettered       boolean     NOT NULL DEFAULT false,
  payload             jsonb       NOT NULL,
  -- `upload.accepted` **만** core-api 가 낸다 — 봉투가 타입마다 `source` 를 const 로 못박았다.
  -- 산문으로만 있던 그 규칙을 DB 가 강제한다.
  -- ⚠ 새 3 종(`preview.*`)은 pipeline-worker 가 내므로 이 CHECK 를 **고칠 필요가 없다** —
  --    core-api 가 그 셋을 내려 하면 여기서 걸린다.
  CONSTRAINT d5_pipeline_event_source_matches_type
    CHECK ((event_type = 'upload.accepted') = (source = 'core-api')),
  -- **재전달 멱등의 DB 층 뿌리.** S2 완료 판정이 요구하고 PoC 에 선례가 없다 (P2.md §10-(나)).
  CONSTRAINT d5_pipeline_event_idempotency_key_unique UNIQUE (idempotency_key)
);
CREATE INDEX d5_pipeline_event_upload_idx ON d5_pipeline_event (upload_id, occurred_at);
CREATE INDEX d5_pipeline_event_lab_idx ON d5_pipeline_event (lab_id);
-- 릴레이가 집는 자리 — 아직 안 나간 것만.
CREATE INDEX d5_pipeline_event_unpublished_idx
  ON d5_pipeline_event (occurred_at) WHERE published_at IS NULL;

-- ════════════════════════════════════════════════════════════════════════════
-- 5. D6 Project (정본 §5)
-- ════════════════════════════════════════════════════════════════════════════

CREATE TABLE d6_project (
  id            ulid        PRIMARY KEY,
  lab_id        ulid        NOT NULL REFERENCES d1_lab(id),
  type          text        NOT NULL CHECK (type IN ('국가과제', '논문')),
  name          text        NOT NULL CHECK (length(btrim(name)) > 0),
  description   text,
  period_start  date,
  period_end    date,
  link_url      text,       -- 논문·공고 주소. 받아 적고 링크로만 보여준다
  status        text        NOT NULL DEFAULT '진행 중' CHECK (status IN ('진행 중', '닫힘')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  CHECK (period_start IS NULL OR period_end IS NULL OR period_start <= period_end)
);
CREATE INDEX d6_project_lab_idx ON d6_project (lab_id);

-- 데이터셋 연결 — **N:N** (정본 §5 · 소급 위험 §3-⑥).
-- 활용 의미 문장은 **연결마다 따로** 적는다. 데이터셋에 붙이면 과제별 쓰임이 뭉개진다.
-- dataset_id 는 bare 컬럼이다 — D6 가 D3 테이블을 직접 FK 하지 않는다 (CLAUDE.md §3-1).
CREATE TABLE d6_project_dataset (
  id          ulid        PRIMARY KEY,
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  project_id  ulid        NOT NULL REFERENCES d6_project(id),
  dataset_id  ulid        NOT NULL,
  usage_note  text,       -- 활용 의미 문장. 역할 태그는 P1(B-04)
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, dataset_id)
);
CREATE INDEX d6_project_dataset_dataset_idx ON d6_project_dataset (dataset_id);
CREATE INDEX d6_project_dataset_lab_idx ON d6_project_dataset (lab_id);

-- ════════════════════════════════════════════════════════════════════════════
-- 6. 공통 기록 — D8 Insight (정본 §6)
-- ════════════════════════════════════════════════════════════════════════════

-- 활동 기록 — **바꾼 일만** 쌓는다 (정본 §6.1).
-- **열람 기록 테이블이 없는 것이 "열람은 서버에 남기지 않는다"의 저장 형태 쪽 표현이다.**
-- action 에 CHECK 를 걸지 않는다 — 정본 §6.1 은 다섯을 **예시로 열거**할 뿐 값 집합으로 닫지 않았고,
-- contracts/seams/fe-core.yaml 의 Activity.action 도 같은 근거로 문자열이다. 없는 값 집합을 DB 가 발명하지 않는다.
CREATE TABLE d8_activity (
  id                ulid        PRIMARY KEY,
  lab_id            ulid        NOT NULL REFERENCES d1_lab(id),
  actor_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  action            text        NOT NULL CHECK (length(btrim(action)) > 0),
  target_kind       text        NOT NULL CHECK (target_kind IN ('데이터셋', '프로젝트')),
  target_id         ulid        NOT NULL,
  occurred_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d8_activity_lab_idx ON d8_activity (lab_id, occurred_at DESC);
CREATE TRIGGER d8_activity_append_only
  BEFORE UPDATE OR DELETE ON d8_activity
  FOR EACH ROW EXECUTE FUNCTION deny_update_delete();

-- 다운로드 이력 — 쌓기만 하고 1차 화면에 쓰지 않는다 (정본 §6.2).
CREATE TABLE d8_download (
  id             ulid        PRIMARY KEY,
  lab_id         ulid        NOT NULL REFERENCES d1_lab(id),
  account_id     ulid        NOT NULL REFERENCES d1_account(id),
  dataset_id     ulid        NOT NULL,
  downloaded_at  timestamptz NOT NULL DEFAULT now(),
  -- 파일 단위 내려받기 (`0009` · 〈278〉-(다)). NULL = 데이터셋 묶음, 값 = 그 파일 하나.
  -- **FK 없음** — append-only 이력은 파일이 지워져도 남는다. `[정본 무근거]` — 정본 §6.2 는
  -- 누가·어느 데이터셋·언제까지만 적는다. `dataset_id` 와 같은 bare 컬럼이다 (D8 → D3 직접 FK 금지).
  file_id        ulid
);
CREATE INDEX d8_download_lab_idx ON d8_download (lab_id, downloaded_at DESC);
CREATE TRIGGER d8_download_append_only
  BEFORE UPDATE OR DELETE ON d8_download
  FOR EACH ROW EXECUTE FUNCTION deny_update_delete();

-- ════════════════════════════════════════════════════════════════════════════
-- 7. RLS — 잠금은 두 층이다 (PLAN-SoT §9-㉖ · PERMISSION-PRINCIPLES P-34)
--
--   ① 연구실 경계          → 모든 테넌트 테이블에 `lab_boundary` (ENABLE + FORCE)
--   ② 파일 본체            → `d3_file` 에 `body_access` 를 **RESTRICTIVE** 로 하나 더
--   ③ 데이터셋 메타        → 경계 정책만. 잠겼다고 행이 사라지면 안 된다 (P-13)
--
--   FORCE 까지 켜는 이유: ENABLE 만이면 테이블 소유자로 접속했을 때 정책이 통째로 무시된다.
--   RESTRICTIVE 인 이유: PERMISSIVE 정책은 서로 **OR** 로 합쳐진다 — 본체 정책을 permissive 로 걸면
--   경계를 넘은 행이 본체 조건만 맞아도 보이게 되어 두 층이 아니라 한 층이 된다.
-- ════════════════════════════════════════════════════════════════════════════

ALTER TABLE d1_lab_profile          ENABLE ROW LEVEL SECURITY;
ALTER TABLE d1_lab_profile          FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d1_lab_profile FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d1_account              ENABLE ROW LEVEL SECURITY;
ALTER TABLE d1_account              FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d1_account FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_member_role          ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_member_role          FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_member_role FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_permission_switch    ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_permission_switch    FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_permission_switch FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_permission_change    ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_permission_change    FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_permission_change FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_dataset_access       ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access       FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_dataset_access FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_dataset_access_grant ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_grant FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_dataset_access_grant FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_dataset_access_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_request FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_dataset_access_request FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_verification_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_verification_request FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_verification_request FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d2_verified             ENABLE ROW LEVEL SECURITY;
ALTER TABLE d2_verified             FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d2_verified FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

-- 데이터셋 메타 3종 — **경계 정책만.** 잠긴 데이터도 이름·요약까지 보이고
-- 그 자리가 `접근 요청` 버튼이 된다 (P-13). 여기에 본체 정책을 걸면 E-06 승인 흐름이 죽는다.
ALTER TABLE d3_dataset              ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset              FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_dataset FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d3_dataset_description  ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_description  FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_dataset_description FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d3_dataset_autometa     ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_autometa     FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_dataset_autometa FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

-- 파일 **본체** — 두 층이 여기서 겹친다.
ALTER TABLE d3_file                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_file                 FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_file FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());
-- 허용자 목록 + 만료일. 데이터셋이 값을 정했으면 그쪽이, 아니면 연구실 기본값이 적용된다 (P-27 · ㉗).
-- 만료된 줄은 조건에서 저절로 빠진다 — 만료를 애플리케이션이 지우러 다니지 않아도 DB 가 거부한다 (P-25).
CREATE POLICY body_access ON d3_file AS RESTRICTIVE FOR ALL
  USING (
    COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
  )
  WITH CHECK (
    COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
  );

-- D5 임시 원장 3종 — **경계 정책만.** `body_access` 는 걸 수 없다(걸 대상이 없다):
-- 그 정책은 `d2_dataset_access`·`d1_lab_profile` 을 `dataset_id` 로 조회하는데, 등록 전
-- 업로드에는 **데이터셋이 아직 없다**(`〈64〉-ⓓ` — `upload.ready` 에 `datasetId` 가 없다).
-- 「올린 사람 말고는 못 본다」는 Port·앱 층이 지킨다 — 근거는 rls-allowlist.toml 주석에 남겼다.
ALTER TABLE d5_upload               ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload               FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_upload_file          ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload_file          FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload_file FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_pipeline_event       ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_pipeline_event       FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_pipeline_event FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_upload_transfer      ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload_transfer      FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload_transfer FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_upload_transfer_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload_transfer_file FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload_transfer_file FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d4_lineage_edge         ENABLE ROW LEVEL SECURITY;
ALTER TABLE d4_lineage_edge         FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d4_lineage_edge FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d4_lineage_unknown      ENABLE ROW LEVEL SECURITY;
ALTER TABLE d4_lineage_unknown      FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d4_lineage_unknown FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d6_project              ENABLE ROW LEVEL SECURITY;
ALTER TABLE d6_project              FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d6_project FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d6_project_dataset      ENABLE ROW LEVEL SECURITY;
ALTER TABLE d6_project_dataset      FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d6_project_dataset FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d8_activity             ENABLE ROW LEVEL SECURITY;
ALTER TABLE d8_activity             FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d8_activity FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d8_download             ENABLE ROW LEVEL SECURITY;
ALTER TABLE d8_download             FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d8_download FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

-- ════════════════════════════════════════════════════════════════════════════
-- 8. 마이그레이션 체인 상태 테이블
--    alembic 이 만드는 것과 **같은 형태**를 여기 선언해 둔다 — 그래야 선언 = 적용이 성립한다.
--    이름이 다른 체인과 다른 것이 체인 분리의 실물이다 (CLAUDE.md §3-3).
-- ════════════════════════════════════════════════════════════════════════════

CREATE TABLE alembic_version_platform (
  version_num character varying(32) NOT NULL,
  CONSTRAINT alembic_version_platform_pkc PRIMARY KEY (version_num)
);
