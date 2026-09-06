"""주제 어휘를 4값 → 6값으로 넓힌다 — `가뭄` · `파일 포맷 예제` 추가

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0012 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

왜 (PLAN-SoT §9 〈359〉 · Ted 판정 2026-09-06)
  `0003` 이 4값을 박을 때 스스로 적어 둔 대가가 실제로 왔다 — 축자 「4값이 담지 못하는
  실데이터(`D-11` SPI/SPEI · `D-12` GK2A L2 LST)는 **영원히 NULL** 이다. 억지로 가까운
  값에 배정하면 검색·분류가 조용히 틀린다」. dev 초기 적재(`〈356〉`)의 14 데이터셋 중
  **6 건**(가뭄 1 · 파일 포맷 5)이 정확히 그 자리였다(`〈357〉`).
  Ted 판정 = **억지 배정도 NULL 도 아니라 어휘를 넓힌다** — 분류 손실 0.

무엇이 바뀌고 무엇이 안 바뀌는가
  ⑴ 넓히는 것뿐이다 — 기존 4값은 한 글자도 건드리지 않는다. **기존 행은 전건 그대로 통과**한다.
  ⑵ nullable 유지 — 「값이 있다면 여섯 중 하나」이지 「반드시 있다」가 아니다(`〈55〉`-③ 그대로).
  ⑶ ⭑ **위반 행 사전 조회를 하지 않는다.** `0003` 이 그것을 한 이유는 **좁히는** 변경이라
    기존 행이 걸릴 수 있어서였다. 이번은 **넓히는** 변경이라 4값을 만족하던 행은 6값도
    만족한다 — 잴 대상이 없다. ⛔ 그래서 `NO FORCE ROW LEVEL SECURITY` 구간도 열지 않는다.
  ⑷ 데이터 재작성 0 — forward-only 이고 백필이 없다.

⚠ `downgrade` 는 4값 CHECK 를 되돌려 건다. 새 두 값을 쓰는 행이 있으면 **거기서 크게 실패한다** —
  그것이 맞다. 마이그레이션이 사람의 분류값을 조용히 버리지 않는다(`0009` 머리말과 같은 규율).

Revision ID: 0013_topic_vocab_six
Revises: 0012_merge_lv1_and_transfer
"""
from __future__ import annotations

from alembic import op

revision = "0013_topic_vocab_six"  # ⚠ 리비전 id 는 32자 이하다(alembic_version_platform.version_num)
down_revision = "0012_merge_lv1_and_transfer"
branch_labels = None
depends_on = None

#: 종전 4값 — `0003_p1_topic_check.TOPICS` 와 같은 문자열이다.
TOPICS_4 = "'강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC'"
#: 새 6값 — 선언 정본은 `db/platform/schema.sql` 의 같은 줄이다.
TOPICS_6 = TOPICS_4 + ", '가뭄', '파일 포맷 예제'"

_DROP = (
    "ALTER TABLE d3_dataset_description "
    "DROP CONSTRAINT IF EXISTS d3_dataset_description_topic_check"
)


def upgrade() -> None:
    op.execute(_DROP)
    # NOT VALID 를 쓰지 않는다 — `0003` 과 같은 이유다. 넓히는 변경이라 검증이 값싸다.
    op.execute(
        "ALTER TABLE d3_dataset_description "
        "  ADD CONSTRAINT d3_dataset_description_topic_check "
        f"  CHECK (topic IS NULL OR topic IN ({TOPICS_6}))"
    )


def downgrade() -> None:
    op.execute(_DROP)
    op.execute(
        "ALTER TABLE d3_dataset_description "
        "  ADD CONSTRAINT d3_dataset_description_topic_check "
        f"  CHECK (topic IS NULL OR topic IN ({TOPICS_4}))"
    )
