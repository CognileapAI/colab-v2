"""두 갈래를 합친다 — `LV-1` 가공 단계 열 제거 ↔ 업로드 전송·파일 관리 머지

**스키마를 한 글자도 바꾸지 않는다.** 이 리비전이 하는 일은 갈라진 두 head 를 하나로
잇는 것뿐이고, `upgrade`·`downgrade` 는 비어 있다.

━━ 왜 생겼나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**창 8-a 의 PR #1 병합**(`〈336〉`-㉴)이 만든 자리다. `0011_merge_transfer_and_access` 는
PR #1 쪽에서 자기 갈래를 `0010_p6_access_request` 에 이미 합쳤다. 그런데 `main` 쪽은
그 뒤 **같은 `0010` 위에 `0011_lv1_drop_level_user_set` 을 얹었다**(`LV-1` · `〈194〉`).
그래서 병합 트리에서 `0010` 위에 형제가 둘이 되고 head 가 둘이 됐다.

    … ─ 0010_p6_access_request ─┬─ 0011_lv1_drop_level_user_set ──────┐
                                └─ 0011_merge_transfer_and_access ────┴─ (여기서 이 리비전이 둘을 잇는다)
                                   (그 아래로 0009_file_management 갈래가 붙어 있다)

⚠ **번호를 다시 붙이지 않는다.** 앞선 머지 리비전이 적어 둔 이유가 그대로 산다 —
alembic 의 위치는 파일 이름이 아니라 **리비전 id** 이고, id 는 한 번 배포되면 사실이다.
**dev 는 `0009_file_management` 로 스탬프돼 있었고** 병합 뒤 head 는 이 리비전이다.

━━ 무엇을 확인했나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 갈래가 **같은 대상을 건드리지 않는다** — 겹치는 표·열·인덱스·정책이 없다.
  · `0011_lv1_drop_level_user_set` = `d3_dataset.level_user_set` **열 제거** 하나
    (사람이 가공 단계를 직접 고르는 경로를 쓰기 바디에서 걷은 회차 · `〈194〉`).
  · `0011_merge_transfer_and_access` = **빈 머지**다. 그 아래 두 갈래가 만진 것은
    `d5_upload_transfer*`(전송 원장) · `d3_file.relative_path` · `d8_download.file_id` ·
    계보 출처 레이블 · 미리보기 낡음 사건 타입 · `d2_*_request`(승인 처리).
  ⟹ `d3_dataset` 의 그 열을 두 번째 갈래가 읽지도 쓰지도 않는다. **순수 병합이다.**
  겹쳤다면 여기서 합칠 수 없고 한쪽을 다시 써야 했다.

선언 정본은 `db/platform/schema.sql` 이다 — 이 리비전이 차분을 만들지 않으므로 그 정본은
두 갈래의 합집합 그대로다. 어긋나면 `schema-diff` 가 red 를 낸다.
"""
from __future__ import annotations

#: ⚠ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
#: `0012_merge_lv1_and_transfer` = 27자.
revision = "0012_merge_lv1_and_transfer"
down_revision = ("0011_lv1_drop_level_user_set", "0011_merge_transfer_and_access")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """**빈 채로 둔다.** 스키마 변경이 여기 들어오면 그것은 머지가 아니라 새 회차다."""


def downgrade() -> None:
    """머지를 되돌리면 head 가 다시 둘이 된다 — 그 상태를 만들 이유가 없다.

    아래 갈래가 전부 전진 전용(`〈168〉-㉲`)이라 어차피 그 아래로는 못 간다.
    """
    raise RuntimeError(
        "0012_merge_lv1_and_transfer 는 되돌리지 않는다 — "
        "되돌리면 head 가 둘로 갈라지고, 아래 갈래는 전진 전용이라 더 내려가지도 못한다."
    )
