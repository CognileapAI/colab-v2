"""Reconcile the manager access objects that re-parenting let an applied chain skip.

Revision ID: 0042_reconcile_admin_access
Revises: 0041_lineage_dependencies

⭑ **⟨2026-09-18⟩ 이 리비전은 새 내용을 선언하지 않는다 — 이미 선언된 것을 다시 세운다.**
  `0032_private_owner_access` 는 리비전 id 를 그대로 둔 채 부모가 `0031_search_evidence`
  에서 `0033_admin_body_access` 로 바뀌었다. 구 체인
  (`0031 → 0032_private_owner_access → 0033_search_changes → …`)을 이미 적용한 DB 는
  `alembic_version_platform` 에 **자기 head 하나만** 들고 있다. 알렘빅은 그 head 이전을 전부
  적용됐다고 보므로, 재부모화로 체인 앞쪽에 끼어든 `0032_labless_operator` 와
  `0033_admin_body_access` 를 **한 번도 돌리지 않는다.** 그 결과 선언
  `db/platform/schema.sql` 과 세 자리가 갈린다:
    ① `is_dataset_manager(char(26))` 부재
    ② `d1_account.lab_id` · `account_admin.login_session.lab_id` 가 NOT NULL 로 남음
    ③ `d3_file` 의 `body_access` 에 관리자 갈래 부재
  이미 남의 DB 에서 돈 리비전의 내용을 고치는 것은 계약 파괴이므로, head 위에 **멱등한**
  리비전을 하나 더 얹어 세 자리를 맞춘다. 새 체인으로 올라온 DB 에서는 세 문장 전부
  결과를 바꾸지 않는다.

  ⚠ 순서가 고정이다 — 정책이 함수를 부르므로 함수가 **먼저** 있어야 한다.
"""
from alembic import op

revision = "0042_reconcile_admin_access"
down_revision = "0041_lineage_dependencies"
branch_labels = None
depends_on = None

#: `0033_admin_body_access` 가 세운 것과 **같은 본문·같은 서명·같은 휘발성**이다.
#: 한 글자라도 다르면 pg_dump 가 다른 줄을 내고 schema-diff 가 red 를 낸다.
_FUNCTION = """
CREATE OR REPLACE FUNCTION is_dataset_manager(target_lab char(26)) RETURNS boolean
LANGUAGE sql STABLE AS $$
  SELECT COALESCE(current_setting('app.operator_manage', true), '') = 'on' OR EXISTS (
    SELECT 1 FROM d2_member_role r WHERE r.account_id = current_account_id()
      AND r.lab_id = target_lab AND r.role = '교수'
  )
$$;
"""

#: `0032_labless_operator` 와 같다. 이미 풀린 DB 에서는 아무것도 바뀌지 않는다.
_DROP_NOT_NULL = """
ALTER TABLE d1_account ALTER COLUMN lab_id DROP NOT NULL;
ALTER TABLE account_admin.login_session ALTER COLUMN lab_id DROP NOT NULL;
"""

#: 관리자(교수·시스템) · 열림 · 소유자 · 유효한 허용 줄 — `0032_private_owner_access` 의 네 갈래 그대로다.
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

#: ALTER 는 `AS RESTRICTIVE` · `FOR ALL` 을 그대로 둔다 — 정책을 다시 만들지 않는다.
#: DROP/CREATE 로 바꾸면 그 틈에 RESTRICTIVE 가 사라져 본체가 열린 채로 남을 수 있다.
_ALTER_POLICY = (f"ALTER POLICY body_access ON d3_file\n"
                 f"  USING ({_PREDICATE_WITH_OWNER}  )\n"
                 f"  WITH CHECK ({_PREDICATE_WITH_OWNER}  );\n")


def upgrade() -> None:
    op.execute(_FUNCTION)
    op.execute(_DROP_NOT_NULL)
    op.execute(_ALTER_POLICY)


def downgrade() -> None:
    # 되돌리지 않는다. 이 리비전이 도는 DB 는 두 가지인데 — 구 체인을 적용해 세 자리가 비어
    # 있던 DB 와, 새 체인으로 이미 맞춰져 있던 DB — `alembic_version_platform` 만으로는 둘을
    # 구분할 수 없다. 되돌리면 후자에서 `0033_admin_body_access` 가 세운 관리자 갈래와
    # `0032_labless_operator` 가 푼 NOT NULL 을 **자기 리비전이 아닌데도** 깨뜨린다.
    # 구 상태가 필요하면 해당 리비전의 downgrade 를 명시로 고른다.
    pass
