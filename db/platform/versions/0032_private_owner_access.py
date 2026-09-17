"""Allow private dataset owners through the file body policy.

Revision ID: 0032_private_owner_access
Revises: 0033_admin_body_access

⭑ **⟨2026-09-18 develop 동기화⟩ 이 리비전은 `0031_search_evidence` 가 아니라
  `0033_admin_body_access` 뒤에 선다.** 두 브랜치가 각자 `0031` 위에 `0032` 를 얹어 head 가
  둘이 됐고, 둘 다 **같은 `body_access` 정책**을 다시 썼다. 병합 리비전으로 합치면 두 정책 중
  나중에 도는 쪽이 앞의 갈래를 지운다 — 그래서 체인을 한 줄로 펴고, 여기서 관리자 갈래
  (`is_dataset_manager`)를 **보존한 채** 소유자 갈래를 덧붙인다.
  리비전 식별자는 바꾸지 않는다 — 회차 기록·시험이 이 이름으로 이 리비전을 가리킨다.
"""
from alembic import op

revision = "0032_private_owner_access"
down_revision = "0033_admin_body_access"
branch_labels = None
depends_on = None

#: 관리자(교수·시스템) · 열림 · 소유자 · 유효한 허용 줄 — 네 갈래다.
_PREDICATE_WITH_OWNER = """
    is_dataset_manager(d3_file.lab_id)
    OR COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d3_dataset owner_dataset
      WHERE owner_dataset.id = d3_file.dataset_id
        AND owner_dataset.lab_id = current_lab_id()
        AND owner_dataset.owner_account_id = current_account_id()
    )
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
"""

#: `0033_admin_body_access` 가 세운 상태 — 소유자 갈래만 없다.
_PREDICATE_WITHOUT_OWNER = """
    is_dataset_manager(d3_file.lab_id)
    OR COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
"""


def _alter(predicate: str) -> str:
    # ALTER 는 `AS RESTRICTIVE` · `FOR ALL` 을 그대로 둔다 — 정책을 다시 만들지 않는다.
    return (f"ALTER POLICY body_access ON d3_file\n"
            f"  USING ({predicate}  )\n"
            f"  WITH CHECK ({predicate}  );\n")


def upgrade() -> None:
    op.execute(_alter(_PREDICATE_WITH_OWNER))


def downgrade() -> None:
    op.execute(_alter(_PREDICATE_WITHOUT_OWNER))
