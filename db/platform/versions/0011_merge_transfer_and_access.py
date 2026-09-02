"""두 갈래를 합친다 — 업로드 전송·파일 관리 ↔ 미리보기 사건·승인 처리

**스키마를 한 글자도 바꾸지 않는다.** 이 리비전이 하는 일은 갈라진 두 head 를 하나로
잇는 것뿐이고, `upgrade`·`downgrade` 는 비어 있다.

━━ 왜 생겼나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 레인이 `0007_p2_human_written_meta` 위에서 **동시에** 갈라졌고, 각자 자기 갈래에서
번호를 이어 붙였다 — 그래서 파일 이름의 `0008`·`0009` 가 양쪽에 하나씩 있다.

    0007 ─┬─ 0008_s3_upload_transfer ─── 0009_file_management ────────────┐
          └─ 0008_lineage_origin_labels ─ 0009_preview_stale_event_types ─┴─ 0010_p6_access_request
                                                                              (여기서 이 리비전이 둘을 잇는다)

**이름을 다시 붙이지 않은 이유가 있다.** 한쪽 리비전 id 를 바꾸면 그 값이 이미 찍혀 있는
데이터베이스가 **자기 위치를 잃는다** — dev 는 `0009_file_management` 로 스탬프돼 있다.
alembic 의 위치는 파일 이름이 아니라 **리비전 id** 이고, id 는 한 번 배포되면 사실이다.
파일 이름의 번호가 겹치는 것은 보기에 거슬릴 뿐 동작에 영향이 없다.

`migration-single-head` 게이트가 이 상태를 red 로 내고 **머지 리비전으로 합치라**고
직접 말한다(`db/README.md` — 두 체인 각각 single-head 강제). 이 파일이 그 집행이다.

━━ 무엇을 확인했나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 갈래가 **같은 대상을 건드리지 않는다** — 겹치는 표·열·인덱스·정책이 없다.
  · 이쪽 갈래: `d5_upload_transfer*`(전송 원장) · `d3_file.relative_path` · `d8_download.file_id`
  · 저쪽 갈래: 계보 출처 레이블 · 미리보기 낡음 사건 타입 · `d2_*_request`(승인 처리)
겹쳤다면 여기서 합칠 수 없고 **한쪽을 다시 써야 했다.** 겹치지 않아서 순수 병합이 됐다.

선언 정본은 `db/platform/schema.sql` 이다 — 이 리비전이 차분을 만들지 않으므로 그 정본은
두 갈래의 합집합 그대로다. 어긋나면 `schema-diff` 가 red 를 낸다.
"""
from __future__ import annotations

#: ⚠ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
#: 처음 쓴 `0011_merge_upload_transfer_and_access`(36자)는 upgrade 마지막 UPDATE 에서
#: `StringDataRightTruncation` 으로 죽었다. `schema-diff` 게이트가 그것을 잡았다.
revision = "0011_merge_transfer_and_access"
down_revision = ("0009_file_management", "0010_p6_access_request")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """**빈 채로 둔다.** 스키마 변경이 여기 들어오면 그것은 머지가 아니라 새 회차다."""


def downgrade() -> None:
    """머지를 되돌리면 head 가 다시 둘이 된다 — 그 상태를 만들 이유가 없다.

    앞의 두 리비전이 전부 전진 전용(`〈168〉-㉲`)이라 어차피 그 아래로는 못 간다.
    """
    raise RuntimeError(
        "0011_merge_transfer_and_access 는 되돌리지 않는다 — "
        "되돌리면 head 가 둘로 갈라지고, 아래 두 갈래는 전진 전용이라 더 내려가지도 못한다."
    )
