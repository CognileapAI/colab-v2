"""두 갈래를 합친다 — 창 9 주제 어휘 6값 ↔ R-C 동의어 분류 5값 (ai 체인)

**스키마를 한 글자도 바꾸지 않는다.** 이 리비전이 하는 일은 갈라진 두 head 를 하나로
잇는 것뿐이고, `upgrade` 는 비어 있다.

━━ 왜 생겼나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**배포 창 중에 발견한 자리다**(Ted 판정 ⓐ · 2026-09-08). 두 갈래가 **같은
`0005_k2b_concept_graph_seed` 위에 각자 얹혔다.**

    … ─ 0005_k2b_concept_graph_seed ─┬─ 0006_topic_vocab_six ─────────┐
                                     └─ 0006_rc7_synonym_category ────┴─ (이 리비전이 둘을 잇는다)

  · `0006_topic_vocab_six` = 창 9 회차(20차 안의 ai 체인 잔여분 · `〈369〉`).
    `d9_topic_synonym_topic_check` 를 4값 → **6값**으로 다시 걸고 동의어 13행을 심는다.
    ⭑ **dev 에 이미 적용된 id 다** — dev 의 `alembic_version_ai` 가 이 값으로 스탬프돼 있다.
  · `0006_rc7_synonym_category` = R-C `WU-C7`(PRD-01 · 질의 5).
    `d9_topic_synonym.category` 한 칸을 **옆에** 세우고 5값 CHECK 를 건다.

⚠ **번호를 다시 붙이지 않는다 — `0006_topic_vocab_six` 는 이미 dev 에 적용된 id 다.**
alembic 의 위치는 파일 이름이 아니라 **리비전 id** 이고, id 는 한 번 배포되면 사실이다.
⟹ 다음 dev 배포가 받는 것은 **`0006_rc7_synonym_category` ＋ 이 리비전** 둘이다.
   staging·빈 DB 는 반대로 `0006_topic_vocab_six` ＋ 이 리비전을 받는다.
   **두 순서가 같은 최종 스키마로 수렴한다** — 그것이 이 리비전이 성립하는 조건이고,
   `db/ai/tests/0007-drift.sh` 가 일회용 postgres 에서 두 순서를 실제로 돌려 대조한다.

━━ 무엇을 확인했나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

두 갈래가 **같은 표를 만지지만 만지는 이름이 갈린다.**

  · 창 9 갈래가 만진 이름 = `d9_topic_synonym_topic_check`(제약 하나) ＋ 동의어 **행** 13.
  · R-C 갈래가 만든 이름 = `d9_topic_synonym.category`(열) ＋ 그 열의 익명 CHECK
    ＋ 기존 행 셋의 `category` **값**.
  ⟹ 이름의 교집합 **0**. 남는 물음은 **행 수준의 교차** 둘뿐이고, 둘 다 닫혀 있다:

  ⑴ **rc7 의 `UPDATE` 가 창 9 의 새 13행을 만나면?** `WHERE topic IN ('강우·강수',
     '식생·NDVI', '토지피복·LULC')` 라 `가뭄`·`파일 포맷 예제` 행은 **애초에 안 걸린다.**
     ⟹ 새 13행의 `category` 는 어느 순서에서도 **NULL** 이다. (rc7 먼저면 그 행들이 아직
     없어서 NULL 로 들어오고, 창 9 먼저면 `UPDATE` 가 안 걸려 NULL 로 남는다 — 같은 결과.)
  ⑵ **창 9 의 `INSERT … ON CONFLICT DO UPDATE` 가 `category` 를 건드리는가?**
     `DO UPDATE SET topic = EXCLUDED.topic, source_note = EXCLUDED.source_note` 뿐이다 —
     `category` 는 SET 목록에 없다. ⟹ 기존 행의 분류를 **덮지 않는다.**
     (겹치는 질의어도 실측상 0건이다 — 13개 낱말은 `k2_ontology_seed.sql` 에 없다.)

  ⛔ 창 9 갈래는 **`category` 열의 존재를 가정하지 않는다** — 컬럼을 나열하지 않는
     `INSERT … (synonym, topic, source_note)` 라 열이 있든 없든 같은 문장이 돈다.
  ⛔ rc7 갈래는 **주제 CHECK 를 다시 걸지 않는다** — `ADD COLUMN category` 하나뿐이라
     6값 CHECK 를 되돌릴 수단이 없다. 그래서 rc7 을 뒤에 올려도 6값이 그대로 산다.
  ⟹ **순수 병합이다.** 겹쳤다면 여기서 합칠 수 없고 한쪽을 다시 써야 했다.

선언 정본은 `db/ai/schema.sql` 이다 — 이 리비전이 차분을 만들지 않으므로 그 정본은
**두 갈래의 합집합** 그대로다(주제 CHECK 6값 ＋ 맨 뒤 `category` 열). 어긋나면
`schema-diff` 가 red 를 낸다.

Revision ID: 0007_merge_topic_vocab_and_rc7_category
Revises: 0006_topic_vocab_six, 0006_rc7_synonym_category
"""
from __future__ import annotations

#: ⚠ **32자를 넘기지 않는다** — `alembic_version_ai.version_num` 이 `varchar(32)` 다.
#: `0007_merge_vocab_and_category` = 29자. (파일 이름은 길어도 되지만 **id 는 이것이다.**)
revision = "0007_merge_vocab_and_category"
down_revision = ("0006_topic_vocab_six", "0006_rc7_synonym_category")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """**빈 채로 둔다.** 스키마 변경이 여기 들어오면 그것은 머지가 아니라 새 회차다."""


def downgrade() -> None:
    """머지를 되돌리면 head 가 다시 둘이 된다 — 그 상태를 만들 이유가 없다.

    아래 갈래가 전부 전진 전용(`〈168〉-㉲`)이고, `0006_topic_vocab_six` 는 **dev 에 이미
    적용된** id 라 되돌릴 자리 자체가 없다.
    """
    raise RuntimeError(
        "0007_merge_vocab_and_category 는 되돌리지 않는다 — "
        "되돌리면 head 가 둘로 갈라지고, 아래 갈래는 전진 전용이다."
    )
