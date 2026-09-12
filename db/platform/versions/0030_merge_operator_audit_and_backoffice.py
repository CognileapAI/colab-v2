"""두 갈래를 합친다 — 운영자 감사·내보내기 ↔ 백오피스 계정 상태·운영자 읽기 스코프

**스키마를 한 글자도 바꾸지 않는다.** 이 리비전이 하는 일은 갈라진 두 head 를 하나로
잇는 것뿐이고, `upgrade` 는 비어 있다.

━━ 왜 생겼나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

백오피스 레인(`lane/backoffice-2`)을 새 `main` 위로 올리면서 생긴 자리다. 두 갈래가
**같은 `0026_login_sessions` 위에 각자 얹혔다**(`CLAUDE.md §10-5` — 한 라운드 = 한 체인
구간, 형제가 생기면 `00NN_merge` ＋ 두 순서 drift 오라클 의무).

    … ─ 0026_login_sessions ─┬─ 0027_operator_audit ─────────────────────────┐
                             └─ 0028_account_status ─ 0029_operator_read_policy ┴─ (이 리비전)

  · `0027_operator_audit` = `main` 갈래. `d{2,3,6}_operator_audit` 3표 ＋
    `d{2,3,5,6,8}_operator_export` 5표 ＋ append-only 트리거 ＋ pending 인덱스 ＋ RLS.
  · `0028_account_status` · `0029_operator_read_policy` = 백오피스 갈래.
    `d1_account.status` 열 ＋ 테넌트 표 31개의 `operator_read`(FOR SELECT · PERMISSIVE).

⚠ **레인 쪽 번호만 다시 붙였다.** `0027_operator_audit` 은 이미 `main` 에 있는 id 라
그대로 두고, 아직 어디에도 적용되지 않은 레인 쪽을 `0027_account_status` →
`0028_account_status`, `0028_operator_read_policy` → `0029_operator_read_policy` 로
옮겼다. alembic 의 위치는 파일 이름이 아니라 **리비전 id** 이고, id 는 한 번 배포되면
사실이다.

━━ 무엇을 확인했나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 갈래가 **같은 대상을 건드리지 않는다.**

  · `main` 갈래가 만든 이름 = `d2_operator_audit` · `d3_operator_audit` ·
    `d6_operator_audit` · `d2_operator_export` · `d3_operator_export` ·
    `d5_operator_export` · `d6_operator_export` · `d8_operator_export`
    ＋ 그 트리거·인덱스·`lab_boundary` 정책.
  · 백오피스 갈래가 만진 이름 = `d1_account.status` · 함수 `is_operator_read()`
    ＋ **기존** 테넌트 표 31개 위의 `operator_read` 정책.
  ⟹ 교집합 **0**. 어느 쪽을 먼저 올려도 결과가 같다. **순수 병합이다.**

⭑ `0029_operator_read_policy` 의 표 목록은 **정적 열거**다. 그래서 `main` 갈래가 새로
만든 감사·내보내기 8표에는 `operator_read` 가 붙지 않는다 — 그것이 두 순서가 수렴하는
이유이기도 하다(동적 열거였다면 순서가 결과를 바꿨다). 운영자 읽기 스코프를 그 8표까지
넓힐지는 **이 리비전이 정하지 않는다** — 넓히려면 새 회차이고, 그 표들은 지금
`lab_boundary` 만으로 닫혀 있다.

선언 정본은 `db/platform/schema.sql` 이다 — 이 리비전이 차분을 만들지 않으므로 그 정본은
**두 갈래의 합집합** 그대로다. 어긋나면 `schema-diff` 가 red 를 낸다.
두 순서 수렴은 `db/platform/tests/0030-drift.sh` 가 실제 DB 두 벌로 판정한다.
"""
from __future__ import annotations

#: ⚠ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
#: `0030_merge_audit_and_backoffice` = 31자.
revision = "0030_merge_audit_and_backoffice"
down_revision = ("0027_operator_audit", "0029_operator_read_policy")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """**빈 채로 둔다.** 스키마 변경이 여기 들어오면 그것은 머지가 아니라 새 회차다."""


def downgrade() -> None:
    """머지를 되돌리면 head 가 다시 둘이 된다 — 그 상태를 만들 이유가 없다."""
    raise RuntimeError(
        "0030_merge_audit_and_backoffice 는 되돌리지 않는다 — "
        "되돌리면 head 가 둘로 갈라진다."
    )
