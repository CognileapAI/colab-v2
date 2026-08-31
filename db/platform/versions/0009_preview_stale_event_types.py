"""파이프라인 이벤트 종류에 D5 → D7 알림 3종을 더한다 — 12차 동결 해제

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0008 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 무엇을 바꾸나 (PLAN-SoT §9 〈253〉 · Ted RULING ㉗ · 12 차 동결 해제) ━━━━━━

`d5_pipeline_event.event_type` 의 CHECK 값 집합을 **7 종에서 10 종으로** 넓힌다.

    (신설) 'preview.backend-rerun'   -- 미리보기 뒷단 재실행
    (신설) 'preview.grid-changed'    -- 격자 변경
    (신설) 'preview.file-added'      -- 파일 추가

값의 정본은 계약(`contracts/events/envelope.json#/$defs/EventType`)이고, DB 는 그것을
**재선언하지 않고 옮겨 적는다**(⑲ 「확정 열거값은 DB 가 강제한다」 — 0004 의 주석 그대로).

━━ 왜 여는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`Y-1`(자동 무효화)의 **트리거 발신 배선**이 설 자리가 없었다(`03-HANDOFF §4 #55`).
받는 자리(viz-render 의 `TriggerPort`)는 서 있는데 보내는 쪽이 없었고, 우회로 둘이
막혀 있었다 — ⑴ D7 이 D5 의 표·outbox 를 직접 읽는 것은 **불변규칙 1** 위반이고
`db-boundary`·`import-boundary` 가 막는다 ⑵ 이벤트 계약은 종류 추가가 곧 계약 개정이다.
Ted 판정은 ⓐ **이벤트 계약을 확장한다** 였다 — 이 레포가 이미 사건 기반으로 서 있고,
자동 재생성은 본질적으로 「무엇이 바뀌었다」는 알림이기 때문이다.

━━ ⚠ 순수 가산이다 — 기존 값·행·제약을 하나도 건드리지 않는다 ━━━━━━━━━━━

  · 값 이행 **0 행**. 옛 7 종의 행은 그대로 유효하다
  · `d5_pipeline_event_source_matches_type` 은 **그대로 둔다**. 새 3 종의 발행자는
    pipeline-worker 이고, 그 CHECK 는 `(event_type = 'upload.accepted') = (source =
    'core-api')` 이라 새 종류에서 자연히 성립한다 — core-api 는 이 셋을 내지 않는다
  · 멱등 키 형태(`<타입>:<uploadId>`)와 그 CHECK·UNIQUE 도 **그대로**다
  · RLS 정책·인덱스 무변경

━━ ⚠ 되돌릴 수 없다 — 전진 전용이다 (〈168〉-㉲ · 0008 과 같은 자세) ━━━━━━━━

되돌리면 새 3 종으로 들어온 행이 **옛 CHECK 를 위반**하는데, 그 행에는 되짚을 옛 값이
없다(대응하는 옛 종류가 애초에 없어서 이 회차가 열렸다). 지우는 것은 이력 파괴이고
임의의 옛 값을 고르는 것은 마이그레이션이 값을 발명하는 것이다. 복구가 필요하면
**앞으로 가는 새 리비전**을 쓴다.

Revision ID: 0009_preview_stale_event_types
Revises: 0008_lineage_origin_labels
"""
from __future__ import annotations

from alembic import op

revision = "0009_preview_stale_event_types"
down_revision = "0008_lineage_origin_labels"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- 값 집합을 넓힌다. 이름은 0004 가 인라인 무명 CHECK 로 만든 것이라 postgres 규칙명이다.
ALTER TABLE d5_pipeline_event DROP CONSTRAINT d5_pipeline_event_event_type_check;

ALTER TABLE d5_pipeline_event
  ADD CONSTRAINT d5_pipeline_event_event_type_check
  CHECK (event_type IN (
    -- ① E-04 업로드 파이프라인 7 종 (core-api ↔ pipeline-worker)
    'upload.accepted', 'file.format-detected', 'file.header-parsed',
    'file.crs-normalized', 'preview.cog-built', 'upload.ready', 'upload.failed',
    -- ② D5 → D7 알림 3 종 (pipeline-worker → viz-render · 〈253〉 · 12 차 해제)
    --    「이미 선 미리보기의 재료가 바뀌었다」는 **사실**이고 명령이 아니다.
    'preview.backend-rerun', 'preview.grid-changed', 'preview.file-added'));

-- 넓어졌는지를 DB 에게 되묻는다. 관례가 아니라 기계가 지킨다 (0008 과 같은 방식).
DO $$
DECLARE
  ok boolean;
BEGIN
  SELECT pg_get_constraintdef(oid) LIKE '%preview.backend-rerun%'
     AND pg_get_constraintdef(oid) LIKE '%preview.grid-changed%'
     AND pg_get_constraintdef(oid) LIKE '%preview.file-added%'
    INTO ok
    FROM pg_constraint
   WHERE conname = 'd5_pipeline_event_event_type_check'
     AND conrelid = 'd5_pipeline_event'::regclass;
  IF ok IS NOT TRUE THEN
    RAISE EXCEPTION '0009: event_type CHECK 가 새 3 종을 받지 않는다 — 넓히지 못했다';
  END IF;
END $$;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """⚠ **전진 전용이다 — 되돌릴 수 없다** (`〈168〉-㉲`).

    새 3 종으로 들어온 행에는 되짚을 옛 값이 없다. 되돌림을 흉내 내면 그 행을 지우거나
    임의의 옛 값을 고르게 되고, 둘 다 마이그레이션이 할 일이 아니다.
    """
    raise RuntimeError(
        "0009_preview_stale_event_types 는 전진 전용이다 — 되돌리지 않는다. "
        "새 3 종으로 들어온 행에 대응하는 옛 값이 없다 (PLAN-SoT §9 〈253〉)."
    )
