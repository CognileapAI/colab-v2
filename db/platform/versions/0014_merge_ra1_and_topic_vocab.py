"""두 갈래를 합친다 — R-A 확장자·관측 간격·기간 단위 ↔ 창 8-b 주제 어휘 6값

**스키마를 한 글자도 바꾸지 않는다.** 이 리비전이 하는 일은 갈라진 두 head 를 하나로
잇는 것뿐이고, `upgrade`·`downgrade` 는 비어 있다.

━━ 왜 생겼나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**창 8-b 레인을 새 `main` 위로 올리면서**(`〈367〉`) 생긴 자리다. 두 갈래가 **같은
`0012_merge_lv1_and_transfer` 위에 각자 얹혔다.**

    … ─ 0012_merge_lv1_and_transfer ─┬─ 0013_ra1_ext_interval_period ──┐
                                     └─ 0013_topic_vocab_six ──────────┴─ (이 리비전이 둘을 잇는다)

  · `0013_ra1_ext_interval_period` = R-A 회차(계약 동결 해제 **19차** · `〈346〉`).
    `d3_dataset_autometa.file_extension` ＋ `period_granularity` ＋
    `d3_dataset_description.observation_interval_{value,unit}` 신설.
  · `0013_topic_vocab_six` = 창 8-b 회차(**20차** · `〈359〉`).
    `d3_dataset_description_topic_check` 를 4값 → **6값**으로 다시 건다.

⚠ **번호를 다시 붙이지 않는다 — `0013_topic_vocab_six` 는 이미 dev 에 적용된 id 다.**
alembic 의 위치는 파일 이름이 아니라 **리비전 id** 이고, id 는 한 번 배포되면 사실이다.
**dev 의 `alembic_version_platform` 은 지금 `0013_topic_vocab_six` 로 스탬프돼 있다**
(`〈362〉` 재적재 시점). ⟹ 다음 dev 배포가 받는 것은 **`0013_ra1_ext_interval_period`
＋ 이 리비전** 둘이다. 그 순서로 올라가면 head 는 이 리비전 하나가 된다.

━━ 무엇을 확인했나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 갈래가 **같은 대상을 건드리지 않는다.** 둘 다 `d3_dataset_description` 을 만지지만
**만지는 이름이 갈린다** — 겹치는 표·열·인덱스·제약·정책이 없다.

  · R-A 갈래가 만든 이름 = `observation_interval_value` · `observation_interval_unit` ·
    `d3_dataset_description_interval_unit_check` ·
    `d3_dataset_description_interval_pair_check` ＋
    `d3_dataset_autometa.file_extension` · `period_granularity` ·
    `d3_dataset_autometa_period_granularity_check`.
  · 8-b 갈래가 만진 이름 = `d3_dataset_description_topic_check` **하나**.
  ⟹ 교집합 **0**. 어느 쪽을 먼저 올려도 결과가 같다. **순수 병합이다.**
  겹쳤다면 여기서 합칠 수 없고 한쪽을 다시 써야 했다.

선언 정본은 `db/platform/schema.sql` 이다 — 이 리비전이 차분을 만들지 않으므로 그 정본은
**두 갈래의 합집합** 그대로다(주제 CHECK 6값 ＋ R-A 의 신설 열·제약). 어긋나면
`schema-diff` 가 red 를 낸다.
"""
from __future__ import annotations

#: ⚠ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
#: `0014_merge_ra1_and_topic_vocab` = 30자.
revision = "0014_merge_ra1_and_topic_vocab"
down_revision = ("0013_ra1_ext_interval_period", "0013_topic_vocab_six")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """**빈 채로 둔다.** 스키마 변경이 여기 들어오면 그것은 머지가 아니라 새 회차다."""


def downgrade() -> None:
    """머지를 되돌리면 head 가 다시 둘이 된다 — 그 상태를 만들 이유가 없다.

    아래 갈래가 전부 전진 전용(`〈168〉-㉲`)이라 어차피 그 아래로는 못 간다.
    """
    raise RuntimeError(
        "0014_merge_ra1_and_topic_vocab 는 되돌리지 않는다 — "
        "되돌리면 head 가 둘로 갈라지고, 아래 갈래는 전진 전용이라 더 내려가지도 못한다."
    )
