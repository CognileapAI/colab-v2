"""P0 — 플랫폼 초기 스키마 (D1 D2 D3 D4 D6 + 공통 기록)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 그 정본을 **그대로** 재현한다 —
두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.
autogenerate 로 만들지 않았다. 선언과 절차를 사람이 같은 커밋에서 맞춘다.

Revision ID: 0001_p0_platform
Revises:
"""
from __future__ import annotations

from alembic import op

revision = "0001_p0_platform"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = r"""
-- db/platform/schema.sql — 플랫폼 선언 스키마 정본 (SoT)
--
-- 소유 도메인: D1 Identity&Lab · D2 Access&Policy · D3 Catalog · D4 Lineage · D6 Project · D8 Insight(공통 기록)
-- D5 Ingestion · D7 Visualization 은 P2·P3 에서 이 파일에 더한다 (저장 형태의 정본이 아직 없다).
--
-- 근거
--   정본  에픽/E-00_공통_기반/documents/DataModel_공통_기반.md v1.8  (§2 §3 §4.1 §4.2 §4.3 §5 §6)
--   기준표 dev-package/DATAMODEL-BASELINE.md §1 (전 행) · §3 (소급 위험 11건)
--   규칙  CLAUDE.md §3-1 §3-5 §3-6 · PLAN-SoT §9-⑲ ⑳ ㉖ ㉗ ㉘ · PERMISSION-PRINCIPLES P-13 P-24 P-29 P-30 P-32 P-34
--
-- 이 파일이 지키는 것 (틀리면 뒤가 전부 소급된다 — DATAMODEL-BASELINE §3)
--   · 데이터셋 : 파일 = 1 : N (본체 1건 이상 + 기준 격자 0~1건)
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
  CHECK ((deleted_at IS NULL) = (deleted_by_account_id IS NULL))
);
CREATE INDEX d3_dataset_lab_idx ON d3_dataset (lab_id);
CREATE INDEX d3_dataset_owner_idx ON d3_dataset (owner_account_id);
CREATE TRIGGER d3_dataset_uploader_immutable
  BEFORE UPDATE ON d3_dataset
  FOR EACH ROW EXECUTE FUNCTION deny_uploader_change();

-- 사람이 적는 정보 — 이름 · 주제 · 설명 (정본 §4.1). 데이터셋 1:1.
-- 목록·상세가 쓰는 이름이 이 `name` 이다. 조각 하나를 대표로 세우지 않는다 (§4.3).
CREATE TABLE d3_dataset_description (
  dataset_id  ulid        PRIMARY KEY REFERENCES d3_dataset(id),
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  name        text        NOT NULL CHECK (length(btrim(name)) > 0),
  topic       text,
  summary     text,
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d3_dataset_description_lab_idx ON d3_dataset_description (lab_id);

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
  CHECK (period_start IS NULL OR period_end IS NULL OR period_start <= period_end)
);
CREATE INDEX d3_dataset_autometa_lab_idx ON d3_dataset_autometa (lab_id);

-- 파일 — 데이터셋 1:N. 종류는 둘뿐이고 기준 격자 파일은 데이터셋당 0~1건 (정본 §4.3).
-- **파일에는 계보가 없다.** 계보는 데이터셋 사이에만 있다 (§4.2·§4.3).
-- 파일 **본체 테이블**이므로 경계 정책 위에 본체 정책이 하나 더 걸린다 (㉖ ③ · P-34).
CREATE TABLE d3_file (
  id           ulid        PRIMARY KEY,
  lab_id       ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id   ulid        NOT NULL REFERENCES d3_dataset(id),
  kind         text        NOT NULL CHECK (kind IN ('본체', '기준 격자 파일')),
  file_name    text        NOT NULL CHECK (length(btrim(file_name)) > 0),
  size_bytes   bigint      CHECK (size_bytes IS NULL OR size_bytes >= 0),
  storage_key  text        NOT NULL CHECK (length(btrim(storage_key)) > 0),
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d3_file_dataset_idx ON d3_file (dataset_id);
CREATE INDEX d3_file_lab_idx ON d3_file (lab_id);
-- 기준 격자 파일은 데이터셋당 최대 1건 (§4.3). 본체 1건 이상은 행 제약으로 표현할 수 없다 —
-- 마지막 본체를 지우는 것을 막는 일은 애플리케이션·묘비 규칙의 몫이다.
CREATE UNIQUE INDEX d3_file_one_reference_grid_per_dataset
  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일';

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
                         CHECK (origin IN ('AI 제안을 사람이 확인', '사람이 직접 연결')),
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
  downloaded_at  timestamptz NOT NULL DEFAULT now()
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
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS d8_download CASCADE")
    op.execute("DROP TABLE IF EXISTS d8_activity CASCADE")
    op.execute("DROP TABLE IF EXISTS d6_project_dataset CASCADE")
    op.execute("DROP TABLE IF EXISTS d6_project CASCADE")
    op.execute("DROP TABLE IF EXISTS d4_lineage_unknown CASCADE")
    op.execute("DROP TABLE IF EXISTS d4_lineage_edge CASCADE")
    op.execute("DROP TABLE IF EXISTS d3_file CASCADE")
    op.execute("DROP TABLE IF EXISTS d3_dataset_autometa CASCADE")
    op.execute("DROP TABLE IF EXISTS d3_dataset_description CASCADE")
    op.execute("DROP TABLE IF EXISTS d3_dataset CASCADE")
    op.execute("DROP TABLE IF EXISTS d2_verified CASCADE")
    op.execute("DROP TABLE IF EXISTS d2_dataset_access_grant CASCADE")
    op.execute("DROP TABLE IF EXISTS d2_dataset_access CASCADE")
    op.execute("DROP TABLE IF EXISTS d2_permission_change CASCADE")
    op.execute("DROP TABLE IF EXISTS d2_permission_switch CASCADE")
    op.execute("DROP TABLE IF EXISTS d2_member_role CASCADE")
    op.execute("DROP TABLE IF EXISTS d1_account CASCADE")
    op.execute("DROP TABLE IF EXISTS d1_lab_profile CASCADE")
    op.execute("DROP TABLE IF EXISTS d1_lab CASCADE")
    op.execute("DROP FUNCTION IF EXISTS deny_uploader_change()")
    op.execute("DROP FUNCTION IF EXISTS deny_update_delete()")
    op.execute("DROP FUNCTION IF EXISTS current_account_id()")
    op.execute("DROP FUNCTION IF EXISTS current_lab_id()")
    op.execute("DROP DOMAIN IF EXISTS ulid")
