"""운영자의 전 연구실 읽기 정책을 `d3_search_evidence` 에도 건다.

Revision ID: 0044_evidence_operator_read
Revises: 0043_variable_missing_rate

⭑ **⟨2026-09-25⟩ 왜** (`dev-package/intent/2026-09-25-operator-search-scope.md` §설계트리 Q7 ·
  사용자 승인). 검토된 검색 근거 표는 `0031_search_evidence` 에서 섰고, 그때 `0029` 의
  `operator_read` 목록에 함께 오르지 않았다. 그래서 무소속 시스템 관리자(`app.current_lab` 이 빈 값)
  에게는 이 표가 **0행**이고, 조건 검색의 후보와 AI 경로의 근거 대조가 전부 비었다.

  정책은 `0029` 와 **글자까지 같은 모양**이다 — `FOR SELECT` · PERMISSIVE · `is_operator_read()`.
  PERMISSIVE 는 OR 로 합쳐지므로 읽기만 넓어지고, INSERT·UPDATE·DELETE 는 `lab_boundary` 의
  USING·WITH CHECK 을 그대로 통과해야 한다. RESTRICTIVE `body_access`(같은 연구실의 `d3_file`
  행이 보여야 한다)도 그대로 AND 로 걸린다 — 본체 접근 규칙은 새로 만들지 않는다(Q4).

  비운영자 규칙은 바뀌지 않는다 — 스위치(`app.operator_read`)는 커널이 인증된 시스템 관리자에게만
  켠다(`services/core-api/src/colab_core/kernel/scope.py`). 표 구조 변경·새 grant 없음.
"""
from alembic import op

revision = "0044_evidence_operator_read"
down_revision = "0043_variable_missing_rate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE POLICY operator_read ON d3_search_evidence "
               "FOR SELECT USING (is_operator_read());")


def downgrade() -> None:
    op.execute("DROP POLICY operator_read ON d3_search_evidence;")
