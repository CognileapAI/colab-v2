"""LV-1 — 사람이 고른 가공 단계를 담던 열을 없앤다 (레벨은 언제나 계보에서 나온다)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0010 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 지우는가 (PLAN-SoT §9 〈194〉 · 2026-08-29 Ted) ━━━━━━━━━━━━━━━━━━━━━

「**레벨은 언제나 계보에서 나온다 — 사람이 직접 정하지 못한다 … 예외 없음**」.
`0007` 이 이 열을 세운 근거는 `POL-020` 의 **예외**(사람이 고른 값은 자동 보정이
덮지 않는다)였고, 〈194〉 가 그 예외 자체를 없앴다. 근거가 사라진 저장 자리는
남겨 두면 **다음 회차가 그것을 보고 경로를 되살린다** — 그래서 막지 않고 지운다.

계약(`DatasetCreate`·`DatasetUpdate` 의 `processingLevel`)·수용 경로·`user_set`
분기가 같은 회차에 함께 사라진다. **응답의 `processingLevel` 과 목록 질의 조건은
그대로 있다** — 파생값이지만 조건으로는 걸 수 있고, 쓰기 바디에만 없다.

━━ 이행 대상 (착수 시점 재계수 · CLAUDE.md §6 「조건문이 아니라 목록으로」) ━━

⭑ **2026-09-02 실측** — staging `d3_dataset` 전체 **13행** · `processing_level_user_set`
비-NULL **0건**(읽기 전용 조회). ⟹ **화면 값이 바뀌는 행이 하나도 없다.**
2026-08-29 값(전체 12 · 비-NULL 0)에서 전체 수만 늘었고 비-NULL 은 그대로 0 이다.
값을 옮길 대상이 0건이므로 백필도 목록 고정도 필요 없고, 이 리비전은 **DROP 뿐**이다.
⚠ 비-NULL 이 있었다면 이 리비전은 그 목록을 먼저 고정한 뒤에야 돌 수 있었다.

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 `0007` 이 세운 그대로 **열과 CHECK 를 되살린다** — 문장은 `0007` 의
UPGRADE ⑴ 과 같다. 되살아나는 값은 전량 `NULL` 이고, 그것이 정확히 지우기 직전의
상태다(비-NULL 0건). **되돌려도 잃는 값이 없는 회차다.**

Revision ID: 0011_lv1_drop_level_user_set
Revises: 0010_p6_access_request
"""
from __future__ import annotations

from alembic import op

revision = "0011_lv1_drop_level_user_set"
down_revision = "0010_p6_access_request"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- CHECK 를 먼저 떨어뜨린다 — 열을 지우면 따라 사라지지만, 순서를 적어 두는 편이
-- 되돌림(0007 UPGRADE ⑴)과 정확히 거울이 된다.
ALTER TABLE d3_dataset
  DROP CONSTRAINT IF EXISTS d3_dataset_processing_level_user_set_range;

ALTER TABLE d3_dataset
  DROP COLUMN IF EXISTS processing_level_user_set;
"""

DOWNGRADE = r"""
-- 0007 UPGRADE ⑴ 그대로. ⚠ 열 순서는 되살아나지 않는다 — ADD COLUMN 은 뒤에 붙는다.
ALTER TABLE d3_dataset
  ADD COLUMN processing_level_user_set smallint;

ALTER TABLE d3_dataset
  ADD CONSTRAINT d3_dataset_processing_level_user_set_range
  CHECK (processing_level_user_set IS NULL
         OR processing_level_user_set BETWEEN 0 AND 2);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """열과 CHECK 를 되살린다. 되살아나는 값은 전량 `NULL` — 지우기 직전과 같다."""
    op.execute(DOWNGRADE)
