"""0009 — 파일 관리: `d3_file.relative_path` · `d8_download.file_id` · 용량 합계 트리거 + 백필 1회 (〈339〉).

무엇
  ⑴ `d3_file.relative_path text NULL` — 폴더째 업로드의 `폴더/이름` 메타가 **등록 뒤에도** 남는다.
     `0008` 이 `d5_upload_file.relative_path` 로 접수 단계까지만 보존했고 「등록 후(d3) 표시는
     후속 결정」으로 열어 뒀다(`〈337〉-③`). 그 결정이 `PLAN-SoT §9 〈339〉-(나)`(파일 관리 회의
     2026-08-23)다 — 같은 모양·같은 CHECK 로 옮겨 적는다. 저장 키 규약(contracts/storage/layout.json)은
     여전히 손대지 않는다.
  ⑵ `d8_download.file_id ulid NULL` — NULL = 데이터셋 묶음 내려받기, 값 = 파일 단위 내려받기
     (`〈339〉-(다)`). **FK 를 걸지 않는다** — append-only 이력이라 파일이 지워져도 행은 남아야 한다.
     `[정본 무근거]` — 정본 §6.2 는 누가·어느 데이터셋·언제까지만 적고 파일 단위를 말하지 않는다.
  ⑶ `sync_dataset_total_size()` + `d3_file` 문장 트리거 3개 — `d3_dataset_autometa.total_size_bytes`
     를 **증분**으로 유지한다. `file_count`(`0002` ㊼) 와 **같은 표·같은 사건**을 다른 기구로
     움직이면 드리프트 유형이 둘이 된다 — 같은 기구(문장 단위 + 전이 테이블 + 증분)로 간다.
  ⑷ **백필 1회** — 기존 행의 `total_size_bytes` 를 `d3_file.size_bytes` 합계로 맞춘다.

⚠ 순수 additive 가 아니다 — 백필이 있다
  `0005`~`0008` 은 백필 없는 additive 였고 그래서 `NO FORCE RLS` 구간이 없었다. 이 판은
  **`0004` 이후 처음으로 그 창을 다시 연다**(`0002` ㊽ 패턴 그대로). 마이그레이션은 소유자
  롤(colab_owner · NOBYPASSRLS)로 돌고 FORCE RLS 아래에서는 소유자도 정책을 받는다 — 창 없이
  합계를 내면 `current_lab_id()` 가 NULL 이라 **모든 데이터셋이 0 으로 백필된다.** 그래서 실제로
  읽고 쓰는 두 표(`d3_file`·`d3_dataset_autometa`)만, 백필 한 구간 동안만 FORCE 를 내렸다가
  되올리고, 되올렸는지를 DB 에게 되묻는다. 정책을 고치거나 지우지 않고 어떤 롤에도 BYPASSRLS 를
  주지 않으며 같은 트랜잭션 안에서 원상복구된다.

`downgrade` — **정직하게**: 트리거 3·함수를 지우고 두 열을 DROP 한다. 되돌리면
`d3_file.relative_path` 값(폴더 구조)과 `d8_download.file_id` 값(파일 단위 이력)이 **사라진다.**
백필이 고쳐 놓은 `total_size_bytes` 값은 되돌리지 않는다 — 백필 전 값은 어디에도 남아 있지 않다.

Revision ID: 0009_file_management
Revises: 0008_s3_upload_transfer
"""
from __future__ import annotations

from alembic import op

revision = "0009_file_management"
down_revision = "0008_s3_upload_transfer"
branch_labels = None
depends_on = None


COLUMNS = r"""
-- ⑴ 0008 의 d5_upload_file.relative_path 와 같은 모양 · 같은 CHECK.
ALTER TABLE d3_file
  ADD COLUMN relative_path text
  CHECK (relative_path IS NULL OR length(relative_path) BETWEEN 1 AND 1024);

-- ⑵ FK 없음 — append-only 이력은 대상이 지워져도 남는다.
ALTER TABLE d8_download
  ADD COLUMN file_id ulid;
"""

TRIGGERS = r"""
-- 용량 합계 유지 (〈339〉). `sync_dataset_file_count`(㊼) 를 본뜬다 —
--   · **다시 세지 않고 증분으로 더한다.** 다시 세면 세는 주체가 `body_access` 를 받아
--     잠긴 데이터셋에 0 을 써 넣는다
--   · 문장 단위 + 전이 테이블: 전이 테이블은 RLS 로 걸러지지 않는다. 한 문장이 조각 수백 개를
--     넣어도 `d3_dataset_autometa` UPDATE 는 한 번이다
--   · `size_bytes` 가 NULL 인 조각은 0 으로 센다 — 합계 열이 NULL 로 물드는 것을 막는다
--   · UPDATE 는 `size_bytes` 가 바뀌거나 조각이 다른 데이터셋으로 옮겨 갈 때만 의미가 있다.
--     `UPDATE OF size_bytes` 는 전이 테이블과 함께 못 쓰므로(0002 와 같은 제약) 함수 안에서
--     차분을 내고, 차분이 0 인 데이터셋은 저절로 빠진다
--   · `file_count` 와 **다른 점 하나** — 갱신된 행 수를 검사하지 않는다. autometa 행은
--     데이터셋마다 반드시 있는 것이 아니라(등록 전환이 따로 세운다) 없는 데이터셋은 건너뛴다.
--     `file_count` 는 `d3_dataset` 행이 반드시 있어 0행 갱신 = 경계 사고였지만 여기서는 아니다
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
"""

# 백필. **읽을 수 없는 것을 세야 하는 자리다** — 0002 ㊽ 그대로.
#   소유자 롤은 FORCE RLS 아래에서 정책을 받으므로 그냥 합계를 내면 잠긴 데이터셋이 0 으로
#   백필된다(고치려던 결함을 마이그레이션이 재현한다). 실제로 읽는 표(d3_file)와 쓰는 표
#   (d3_dataset_autometa)만, 이 구간 동안만 FORCE 를 내렸다가 되올리고 DB 에게 되묻는다.
BACKFILL = r"""
ALTER TABLE d3_file             NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_autometa NO FORCE ROW LEVEL SECURITY;

-- 선행 실측 — 몇 행이 합계와 달랐는지 로그에 남긴다. 판정이 아니라 기록이다.
DO $$
DECLARE
  total_rows bigint;
  stale_rows bigint;
BEGIN
  SELECT count(*),
         count(*) FILTER (WHERE a.total_size_bytes IS DISTINCT FROM
           (SELECT COALESCE(sum(f.size_bytes), 0) FROM d3_file f WHERE f.dataset_id = a.dataset_id))
    INTO total_rows, stale_rows
    FROM d3_dataset_autometa a;
  RAISE NOTICE '[0009 백필] d3_dataset_autometa % 행 중 % 행의 total_size_bytes 가 d3_file 합계와 달랐다 → 합계로 맞춘다',
    total_rows, stale_rows;
END
$$;

UPDATE d3_dataset_autometa a
   SET total_size_bytes = (SELECT COALESCE(sum(f.size_bytes), 0)
                             FROM d3_file f WHERE f.dataset_id = a.dataset_id);

ALTER TABLE d3_file             FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_autometa FORCE ROW LEVEL SECURITY;

-- 되올렸는지 DB 에게 되묻는다. 관례가 아니라 기계가 지킨다.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
     WHERE relname IN ('d3_file', 'd3_dataset_autometa')
       AND relnamespace = 'public'::regnamespace
       AND NOT relforcerowsecurity
  ) THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 — 마이그레이션을 되돌린다';
  END IF;
END
$$;
"""

DOWNGRADE = r"""
DROP TRIGGER d3_file_total_size_update ON d3_file;
DROP TRIGGER d3_file_total_size_delete ON d3_file;
DROP TRIGGER d3_file_total_size_insert ON d3_file;
DROP FUNCTION sync_dataset_total_size();
ALTER TABLE d3_file     DROP COLUMN relative_path;
ALTER TABLE d8_download DROP COLUMN file_id;
"""


def upgrade() -> None:
    op.execute(COLUMNS)
    op.execute(TRIGGERS)
    op.execute(BACKFILL)


def downgrade() -> None:
    op.execute(DOWNGRADE)
