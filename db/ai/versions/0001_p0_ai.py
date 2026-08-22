"""P0 — 지식·추론 체인의 초기 리비전 (테이블 없음)

이 체인은 기록 도메인과 **마이그레이션 체인이 분리된다** (CLAUDE.md §3-3).
지금 만드는 것은 체인 그 자체뿐이다 — 온톨로지 형태는 G8·K1 이 정한다.
빈 리비전을 두는 이유: 체인이 존재한다는 사실과 아직 테이블이 없다는 사실은 다른 사실이고,
게이트는 둘을 구분해야 한다. 리비전이 0건이면 "분리를 증명할 체인 자체가 없다"가 된다.

Revision ID: 0001_p0_ai
Revises:
"""
from __future__ import annotations

revision = "0001_p0_ai"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """테이블을 만들지 않는다. 체인 상태 테이블은 alembic 이 만든다."""


def downgrade() -> None:
    """되돌릴 것이 없다."""
