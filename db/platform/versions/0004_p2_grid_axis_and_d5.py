"""P2 — 기준 격자 축 전환(두 불리언) + D5 업로드 원장

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0003 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ ⑴ 기준 격자 축 (PLAN-SoT §9-〈66〉 · sessions/P2.md §2-22-a) ━━━━━━━━━━━━

`〈58〉-㉠` 은 `grid_axis text` **단일값** + `UNIQUE(dataset_id, grid_axis)` 를 세웠고
`P2.md §2-22` 가 그대로 적혀 있었다. **그 전제가 실측으로 깨졌다** — 실물 16건 중 2건이
한 파일에 `lat`·`lon` 을 다 담는다(sessions/P2-W0-1-measurement.md). 단일값 모델은 그 파일을
「축을 못 갈라서」가 아니라 **「둘 다 갈려서」** 표현하지 못한다.

그래서 `carries_lat boolean` · `carries_lon boolean` **두 열**이다. 제3값(결합축이라는
세 번째 enum 값)이 탈락한 이유는 하나다 — **「위도 1건 + 결합축 1건」을 못 막는다.**
개수 제약이 「몇 개냐」만 답하고 「무엇이냐」는 안 답하는 것과 같은 실패다
(DATA-REFERENCE §1). 두 불리언은 **축 원소마다 부분 유니크 인덱스**를 걸 수 있어
「위도 2건」도 「위도1+결합1」도 함께 막으면서 **행 : 파일 = 1 : 1 을 유지**하고
**계약을 한 글자도 고치지 않는다**(`UploadFileRef`·`DatasetFile`·`FileKind` 무변경).

**시급성은 열 이름 논쟁이 아니라 여기 있다** — 현행 `d3_file_one_reference_grid_per_dataset`
는 `(dataset_id) WHERE kind='기준 격자 파일'` 이라 **데이터셋당 격자 1건**만 허용한다.
`〈58〉` 이 확정한 「위도·경도 한 쌍이 실물」은 정의상 2건이므로, 이 인덱스가 걸린 채로는
**실물 16건 중 `.npy` 쌍을 쓰는 14건이 두 번째 파일에서 반드시 실패한다**
(sessions/P2-W0-R1-code-usage.md §2.5).

**CHECK 는 양쪽 반쪽을 다 건다** — 축 없는 격자 파일도, 축 붙은 본체도 만들지 않는다.
한쪽만 걸면 「열을 뒀는데 안 채우면 그만」이 된다(DATA-REFERENCE §1).

`〈63〉-ⓒ`(축 판별 실패는 그 파일만 막고 등록은 막지 않는다)와 충돌하지 않는다 —
**축을 못 정한 파일은 행을 만들지 않고 거절**하므로 축이 빈 행이 생길 자리가 없다(`〈66〉` 유권해석).

━━ ⑵ D5 업로드 원장 (P2-EXEC §4 W1 ⑵ · 〈63〉-㉱ · 〈64〉 / P2.md §2-27) ━━━━━

「등록 전에는 아무것도 저장되지 않는다」의 **대상은 D3 카탈로그**다(`〈64〉-ⓐ`).
`d5_*` 는 그 진술의 대상이 아니라 **D5 소유의 처리 중 상태**이고(`ⓑ`), 어느 사용자 읽기
경로에도 비치지 않으며 만료되면 reaper 가 지운다(`ⓒ`). 원장이 없으면 `getUploadStatus`
가 읽을 자리가 사라져 이벤트 ②~⑦ 이 갈 곳을 잃는다.

`core-api` 는 이 표들을 직접 만지지 않는다 — `ports/ingestion.py`(P2-api 소관) 를 지난다
(`〈63〉-㉱`). 이 마이그레이션은 **표만** 세운다.

세 표 전부 `lab_id` + RLS ENABLE + FORCE + `lab_boundary`. 면제 0건이다.
`body_access` 를 걸지 않는 이유는 `gates/config/rls-allowlist.toml` 주석에 남겼다 —
조용히 빼지 않는다(K1 선례).

━━ ⚠ 선행 실측이 이 파일 안에 있다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`P2-EXEC §4 W1 ⑴-1` 은 「`d3_file WHERE kind='기준 격자 파일'` 현재 행 수를 세고,
0 이 아니면 축을 채울 근거가 없으므로 멈춘다」고 못 박았다. **그 판정을 사람의 절차가
아니라 마이그레이션이 직접 한다** — 적용 대상 DB 를 미리 다 볼 수 없기 때문이다.
기존 격자 행이 하나라도 있으면 여기서 예외로 멈춘다. 축을 추측해 채우지 않는다(M-4).

Revision ID: 0004_p2_grid_axis_and_d5
Revises: 0003_p1_topic_check
"""
from __future__ import annotations

from alembic import op

revision = "0004_p2_grid_axis_and_d5"
down_revision = "0003_p1_topic_check"
branch_labels = None
depends_on = None

# ── 선행 실측 + 정지 ─────────────────────────────────────────────────────────
# 0002 백필·0003 사전조회와 **같은 방식**으로 이 한 구간만 FORCE 를 내린다.
# 그냥 세면 FORCE RLS 아래에서 소유자 롤도 정책을 받아 **위반 행이 있어도 0 건으로 보이고**,
# 「없다」고 조용히 거짓말한다. ① 정책을 고치거나 지우지 않고 ② 어떤 롤에도 BYPASSRLS 를
# 주지 않으며 ③ 같은 트랜잭션 안에서 원상복구되고 ④ 복구 여부를 DB 에게 되묻는다.
PRECOUNT = r"""
ALTER TABLE d3_file NO FORCE ROW LEVEL SECURITY;

DO $$
DECLARE
  grid_rows bigint;
BEGIN
  SELECT count(*) INTO grid_rows FROM d3_file WHERE kind = '기준 격자 파일';

  RAISE NOTICE '[0004 선행 실측] d3_file WHERE kind=기준 격자 파일 → % 행', grid_rows;

  IF grid_rows > 0 THEN
    RAISE EXCEPTION '기존 기준 격자 파일이 % 행 있다 — 축(carries_lat·carries_lon)을 채울 근거가 없다. '
                    '사람이 각 행의 축을 실측으로 정한 뒤 다시 적용한다 (P2-EXEC 4 W1 1-1 · DATA-REFERENCE M-4)',
                    grid_rows;
  END IF;
END
$$;

ALTER TABLE d3_file FORCE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
     WHERE relname = 'd3_file'
       AND relnamespace = 'public'::regnamespace
       AND NOT relforcerowsecurity
  ) THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 — 마이그레이션을 되돌린다';
  END IF;
END
$$;
"""

# ── ⑴ 축 두 열 + CHECK 2종 + 유일성 이전 ────────────────────────────────────
GRID_AXIS = r"""
ALTER TABLE d3_file
  ADD COLUMN carries_lat boolean NOT NULL DEFAULT false,
  ADD COLUMN carries_lon boolean NOT NULL DEFAULT false;

-- ㈎ 기준 격자 파일 → 둘 중 최소 하나는 true. 축이 빈 격자 파일을 만들지 않는다.
ALTER TABLE d3_file
  ADD CONSTRAINT d3_file_grid_carries_an_axis
  CHECK (kind <> '기준 격자 파일' OR carries_lat OR carries_lon);

-- ㈏ 본체 → 둘 다 false. **반쪽만 걸면 축 붙은 본체가 들어온다.**
ALTER TABLE d3_file
  ADD CONSTRAINT d3_file_body_carries_no_axis
  CHECK (kind <> '본체' OR (NOT carries_lat AND NOT carries_lon));

-- 옛 인덱스를 걷는다 (schema.sql:289-290 · 0001_p0_platform.py:301-302 — cat -n 으로 확인했다).
-- 이것이 오늘 실물 `.npy` 쌍의 두 번째 파일을 막고 있는 자리다.
DROP INDEX d3_file_one_reference_grid_per_dataset;

-- 새 유일성 — **축 원소마다 1건.** 개수만 2로 늘리면 위도 파일이 둘 들어간다.
-- 결합축 파일은 두 인덱스에 동시에 걸리므로 「위도1 + 결합1」도 여기서 막힌다.
CREATE UNIQUE INDEX d3_file_one_lat_grid_per_dataset
  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일' AND carries_lat;
CREATE UNIQUE INDEX d3_file_one_lon_grid_per_dataset
  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일' AND carries_lon;
"""

# ── ⑵ D5 업로드 원장 3표 ────────────────────────────────────────────────────
D5 = r"""
-- 업로드 1건 — 등록 전 임시 세계의 집계 루트. `uploadId` 는 이벤트 봉투의 것과 같은 값이다.
CREATE TABLE d5_upload (
  id                   ulid        PRIMARY KEY,
  lab_id               ulid        NOT NULL REFERENCES d1_lab(id),
  uploader_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  created_at           timestamptz NOT NULL DEFAULT now(),
  -- 수명. **값은 정본이 안 줬다** — 계약이 발행자에게 열어 뒀고(`NB-2`), 여기서 DEFAULT 를
  -- 발명하지 않는다. 넣는 쪽이 명시한다 (P2-EXEC §7 「정본이 값을 주지 않으면 만들지 않는다」).
  expires_at           timestamptz NOT NULL,
  -- 이벤트 ②~⑦ 의 **결과**를 담는 자리. 새 사실을 만들지 않는다 (UploadStatus 와 1:1).
  ready                boolean     NOT NULL DEFAULT false,
  renderable           boolean,            -- 아직 모르면 NULL (계약도 3값이다)
  metadata_complete    boolean,            -- 상동
  failed_at            timestamptz,
  failure_class        text CHECK (failure_class IS NULL OR failure_class IN ('재시도 가능', '영구')),
  failure_reason       text CHECK (failure_reason IS NULL OR failure_reason IN (
                         '업로드 중단', '형식 인식 실패', '헤더 인식 실패', '조각이 서로 다름',
                         '좌표계 변환 실패', '미리보기 준비 실패', '시간 초과', '내부 오류')),
  -- 등록 전환 시각. **datasetId 를 두지 않는다** — D5 가 D3 를 직접 가리키면 불변규칙 1 위반이다.
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
-- 변환 지점이 없다는 것이 `NB-A`(fileId 동일성, Ted 승인 2026-08-23)의 저장 형태 쪽 표현이다.
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
  CONSTRAINT d5_upload_file_grid_carries_an_axis
    CHECK (kind <> '기준 격자 파일' OR carries_lat OR carries_lon),
  CONSTRAINT d5_upload_file_body_carries_no_axis
    CHECK (kind <> '본체' OR (NOT carries_lat AND NOT carries_lon))
);
CREATE INDEX d5_upload_file_upload_idx ON d5_upload_file (upload_id);
CREATE INDEX d5_upload_file_lab_idx ON d5_upload_file (lab_id);
-- D3 와 같은 유일성을 원장에서도 건다 — 업로드 하나 안에 같은 축이 둘 있으면
-- 등록은 반드시 실패한다. 그 실패를 등록 시점이 아니라 **접수 시점에** 낸다.
CREATE UNIQUE INDEX d5_upload_file_one_lat_grid_per_upload
  ON d5_upload_file (upload_id) WHERE kind = '기준 격자 파일' AND carries_lat;
CREATE UNIQUE INDEX d5_upload_file_one_lon_grid_per_upload
  ON d5_upload_file (upload_id) WHERE kind = '기준 격자 파일' AND carries_lon;

-- 파이프라인 이벤트 / outbox. 열 구성의 정본은 contracts/events/envelope.json 의 봉투다 —
-- 여기서 값 집합을 **재선언하지 않고 옮겨 적는다**(⑲ 「확정 열거값은 DB 가 강제한다」).
CREATE TABLE d5_pipeline_event (
  id                  ulid        PRIMARY KEY,          -- = eventId (전달의 정체성)
  lab_id              ulid        NOT NULL REFERENCES d1_lab(id),
  actor_account_id    ulid        NOT NULL REFERENCES d1_account(id),
  -- **파일 단위 이벤트가 없다.** 7종 페이로드 전부가 업로드 단위이고, 파일을 가리킬 때도
  -- `fileIds` 배열을 페이로드에 싣는다 (core-pipeline.json — CrsNormalized·CogBuilt).
  -- 그래서 `file_id` 열을 두지 않는다. 그리고 그것이 멱등 키가 `<타입>:<uploadId>` 만으로
  -- 충돌 없이 성립하는 이유다 — 타입 하나당 업로드 하나당 이벤트 하나.
  upload_id           ulid        NOT NULL REFERENCES d5_upload(id) ON DELETE CASCADE,
  event_type          text        NOT NULL CHECK (event_type IN (
                        'upload.accepted', 'file.format-detected', 'file.header-parsed',
                        'file.crs-normalized', 'preview.cog-built', 'upload.ready', 'upload.failed')),
  schema_version      text        NOT NULL CHECK (schema_version ~ '^[0-9]+\.[0-9]+$'),
  source              text        NOT NULL CHECK (source IN ('core-api', 'pipeline-worker')),
  occurred_at         timestamptz NOT NULL DEFAULT now(),
  -- **작업의 정체성.** `<이벤트 타입>:<uploadId>` 로 결정론적으로 만든다 — 발행자가 난수를
  -- 쓰지 않으므로 outbox 행이 다시 만들어져도 같은 키가 나온다 (envelope.json IdempotencyKey).
  idempotency_key     text        NOT NULL CHECK (
                        idempotency_key ~ '^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*:[0-9A-HJKMNP-TV-Z]{26}$'),
  attempt             integer     NOT NULL DEFAULT 1 CHECK (attempt >= 1),
  max_attempts        integer     NOT NULL DEFAULT 5 CHECK (max_attempts >= 1),
  first_published_at  timestamptz,        -- 미발행 = NULL. 릴레이가 채운다
  published_at        timestamptz,
  dead_lettered       boolean     NOT NULL DEFAULT false,
  payload             jsonb       NOT NULL,
  -- `upload.accepted` **만** core-api 가 낸다 — 봉투가 타입마다 source 를 const 로 못박았다.
  -- 산문으로만 있던 그 규칙을 DB 가 강제한다.
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
"""

D5_RLS = r"""
ALTER TABLE d5_upload            ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload            FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_upload_file       ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload_file       FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload_file FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_pipeline_event    ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_pipeline_event    FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_pipeline_event FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());
"""

DOWN = r"""
DROP TABLE IF EXISTS d5_pipeline_event;
DROP TABLE IF EXISTS d5_upload_file;
DROP TABLE IF EXISTS d5_upload;

DROP INDEX IF EXISTS d3_file_one_lon_grid_per_dataset;
DROP INDEX IF EXISTS d3_file_one_lat_grid_per_dataset;

-- 옛 인덱스를 **되살린다.** 지우기만 하면 downgrade 가 아니라 반쪽 복구다.
-- 되돌린 뒤의 스키마가 0003 과 같아야 한다 (db/platform/tests/0004-drift.sh ㈐ 가 pg_dump 로 대조한다).
CREATE UNIQUE INDEX d3_file_one_reference_grid_per_dataset
  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일';

ALTER TABLE d3_file DROP CONSTRAINT IF EXISTS d3_file_body_carries_no_axis;
ALTER TABLE d3_file DROP CONSTRAINT IF EXISTS d3_file_grid_carries_an_axis;
ALTER TABLE d3_file DROP COLUMN IF EXISTS carries_lon;
ALTER TABLE d3_file DROP COLUMN IF EXISTS carries_lat;
"""


def upgrade() -> None:
    op.execute(PRECOUNT)
    op.execute(GRID_AXIS)
    op.execute(D5)
    op.execute(D5_RLS)


def downgrade() -> None:
    op.execute(DOWN)
