"""P2 — 사람이 고치는 값 셋: 가공 단계 · 대표 조각 · 원천 표기 정규화

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0006 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 이것이 필요한가 (PLAN-SoT §9 〈140〉 · 결정 2-4 · 2-10) ━━━━━━━━━━━━━━

**지금 v2 에는 「고치는 길」이 거의 없다.** 올린 뒤 고칠 수 있는 것이 이름·주제·요약
셋뿐이고 `deleteDataset` 도 501 이라 지울 수도 없다. **되돌릴 수 없는 제품은 사람이
조심하느라 안 쓰게 된다** — 「졸업하면 데이터가 사라진다」를 막겠다는 목적과 어긋난다.
Ted 판정 ㈏(2026-08-27)가 「올리고 고친다」를 한 벌로 열었고, 이 리비전이 그 저장이다.

━━ ⚠ 적재된 데이터 위에서 도는 첫 스키마 변경이다 ━━━━━━━━━━━━━━━━━━━━━

staging 에 데이터셋 12 · 파일 123(본체) · 계보 간선 6 이 이미 있다.

**그래서 셋 다 additive 로만 짰다** — 열 추가와 제약 추가뿐이고 **기존 값을 읽지도
고치지도 않는다.** 백필이 없으므로 `0002`·`0004` 가 필요로 했던 `NO FORCE RLS` 구간
(`㊽`)도 **여기엔 없다.** 완화를 안 쓰는 것이 가장 싼 안전이다.

**전량 `NULL` 로 들어간다. 12건의 화면 값이 하나도 바뀌지 않는다.**
  · `processing_level_user_set` = NULL → Lv 는 종전대로 계보에서 파생한다
  · `representative_file_id`    = NULL → 대표 조각은 종전대로 자동으로 고른다
  · `source_label_normalized`   = NULL → 원문(`source_label`)이 그대로 정본이다

━━ 왜 「사람이 고른 값」만 저장하는가 (〈140〉-㉯) ━━━━━━━━━━━━━━━━━━━━━━

`⑳` 과 `common.json#ProcessingLevel` 이 **「파생값 — 저장 필드·편집 칸을 두지 않는다」**
고 못 박았다. 그 규칙이 막으려던 위험은 `DATAMODEL-BASELINE:166` 이 적은 그것이다 —
「Lv 를 손으로 고치는 칸으로 두면 **계보를 고쳐도 Lv 가 안 따라가 둘이 갈라진다**」.

**낡는 것은 계산 결과지 사람의 의도가 아니다.** 「나는 이걸 Lv1 로 본다」는 계보가
바뀌어도 유효하다. 그래서 **계산 결과는 절대 저장하지 않고** 사람이 손댄 것만 담는다 —
`⑳` 을 깨는 것이 아니라 정확히 지키면서 정본(`VAL-005`·`POL-020`·`TC-W-001`)을 만족시킨다.

**`NULL` 하나로 두 상태를 표현한다.** 별도의 「사람이 골랐나」 플래그를 두지 않는다 —
두 열이 어긋날 자리를 만들지 않는 편이 낫고, 대표 조각도 같은 모양이다(결정 2-4).

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 **열을 지운다 — 사람이 고른 값이 사라진다.** 데이터 손실이므로
`0004` 와 달리 재적용은 막히지 않지만, **되돌리면 사람의 선택이 안 돌아온다.**
(`0004` 는 `d5_upload*` 를 DROP 해 사실상 단방향이다 — 그것과 다른 종류의 손실이다.)

Revision ID: 0007_p2_human_written_meta
Revises: 0006_s1_trgm_matching
"""
from __future__ import annotations

from alembic import op

revision = "0007_p2_human_written_meta"
down_revision = "0006_s1_trgm_matching"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ⑴ 가공 단계 — 사람이 고른 값만. NULL 이면 계보에서 파생한다 (〈140〉).
ALTER TABLE d3_dataset
  ADD COLUMN processing_level_user_set smallint;

-- 상한은 정본이 준 값이다 — `VAL-005`(Lv0·Lv1·Lv2) · `POL-020`(상한 Lv2).
-- 「Lv3 은 존재할 수 없는 값이다」(재검토 판정). 응답 층(`〈133〉`)과 **같은 상한**을
-- DB 에도 건다 — 코드만 지키면 다른 경로가 생겼을 때 조용히 3 이 들어온다.
ALTER TABLE d3_dataset
  ADD CONSTRAINT d3_dataset_processing_level_user_set_range
  CHECK (processing_level_user_set IS NULL
         OR processing_level_user_set BETWEEN 0 AND 2);

-- ⑵ 대표 조각 — NULL 이 「자동」이다 (결정 2-4 · 정렬 기준은 결정 2-8).
ALTER TABLE d3_dataset
  ADD COLUMN representative_file_id ulid;

-- `ON DELETE SET NULL` — 대표로 지정한 조각이 사라지면 **자동으로 되돌아간다.**
-- 비워 두면 상세가 없는 조각을 그리려 하고, 막으면 조각을 못 지운다.
-- ⚠ **다른 데이터셋의 조각을 가리키는 것은 FK 가 못 막는다**(같은 표다).
--    그 검사는 애플리케이션의 몫이고 음성 시험이 지킨다.
ALTER TABLE d3_dataset
  ADD CONSTRAINT d3_dataset_representative_file_fk
  FOREIGN KEY (representative_file_id) REFERENCES d3_file(id) ON DELETE SET NULL;

-- ⑶ 원천 표기 정규화값 — 원문을 지우지 않고 **병기한다** (결정 2-10).
-- 원문이 남아야 나중에 정규화 규칙이 바뀌어도 복구된다.
ALTER TABLE d3_dataset
  ADD COLUMN source_label_normalized text;

-- 자동완성이 훑는 자리다 (`listDatasetFieldSuggestions`). 연구실 경계가 먼저 걸리므로
-- 랩을 앞에 둔다 — 경계 없는 접두 스캔이 되지 않게 한다.
CREATE INDEX d3_dataset_source_label_normalized_idx
  ON d3_dataset (lab_id, source_label_normalized)
  WHERE source_label_normalized IS NOT NULL;
"""

DOWNGRADE = r"""
DROP INDEX IF EXISTS d3_dataset_source_label_normalized_idx;
ALTER TABLE d3_dataset DROP CONSTRAINT IF EXISTS d3_dataset_representative_file_fk;
ALTER TABLE d3_dataset DROP CONSTRAINT IF EXISTS d3_dataset_processing_level_user_set_range;
ALTER TABLE d3_dataset DROP COLUMN IF EXISTS source_label_normalized;
ALTER TABLE d3_dataset DROP COLUMN IF EXISTS representative_file_id;
ALTER TABLE d3_dataset DROP COLUMN IF EXISTS processing_level_user_set;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """⚠ **사람이 고른 값이 사라진다.** 열을 지우므로 되돌림은 데이터 손실이다."""
    op.execute(DOWNGRADE)
