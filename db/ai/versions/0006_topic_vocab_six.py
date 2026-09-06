"""주제 어휘를 4값 → 6값으로 넓히고 새 두 값의 동의어를 심는다 — ai 체인

선언 정본은 `db/ai/schema.sql` 이다. 이 파일은 `0005` 까지의 스키마에 그 정본의 **차분만**
더한다 — 두 쪽이 갈라지면 `schema-diff` 게이트가 red 를 낸다.

왜 (PLAN-SoT §9 〈359〉-㉶ 가 스스로 적어 둔 다음 회차 · Ted 판정 2026-09-06 · 창 9)
  `〈359〉` 는 platform 쪽 어휘만 넓히고 축자로 적었다 — 「**못 본 축(다음 회차 진입조건)** =
  `db/ai` 체인. `d9_topic_synonym` 의 CHECK 는 **아직 4값**이고 새 두 값의 **동의어 행이 0** 이다
  ⟹ 자연어 검색이 「가뭄」을 주제로 못 맞춘다」. 그 상태의 증상은 실패가 아니라 **침묵**이다:
  「가뭄」·「SPI」 질의가 주제 축으로 안 잡혀 **조용히 덜 찾는다**(`〈360〉`).
  `〈360〉` 이 멈춘 이유는 하나였다 — **동의어 값이 정본 무근거**라 지어내지 않았다.
  이번 회차에 **Ted 가 값을 판정해 내려보냈다** ⟹ 지어낼 것이 없어졌다.

회차
  **20차 안의 ai 체인 잔여분**이다 — 새 회차를 열지 않는다. 근거 = `〈359〉` 가 이미 20차로
  연 것이 **같은 어휘 결정**이고, 이 리비전은 그 결정이 못 덮은 두 번째 체인을 덮을 뿐이다.
  ⭑ **계약 표면 변경은 0** — `contracts/` 전수에 주제 값이 0건이고(`fe-core.yaml` `DatasetCreate.topic`
  축자 「값 집합은 DB CHECK 가 지킨다」) 그 설계를 바꾸지 않았다.

무엇이 바뀌고 무엇이 안 바뀌는가
  ⑴ **넓히는 것뿐이다** — 기존 4값은 한 글자도 건드리지 않고 기존 행 5건은 전건 그대로 통과한다.
  ⑵ 동의어 13행 추가 — `ON CONFLICT … DO UPDATE` 라 멱등하다. **기존 행을 지우지 않는다.**
  ⑶ ⛔ **위반 행 사전 조회를 하지 않는다.** 그 장치는 **좁히는** 변경의 것이고, 넓히는 변경에는
    잴 대상이 없다(4값을 만족하던 행은 6값도 만족한다). `NO FORCE RLS` 구간도 열지 않는다 —
    애초에 이 체인의 D9 다섯 표에는 `lab_id` 가 없어 RLS 대상이 아니다.
  ⑷ 데이터 재작성 0 · 백필 0 · forward-only.
  ⑸ ⛔ **개념 그래프(`d9_concept`·`d9_concept_edge`)는 만지지 않았다** — Ted 판정은 **동의어**를
    말했다. 그래프 쪽 주제 노드 4개(`k2b_graph_check.CANON_TOPICS`)는 그대로다. 넓히려면
    `k2b-graph-standard.tsv` 라는 별도 오라클을 함께 고쳐야 하고, 그것은 이 판정 밖이다 → 등록만.

⚠ `downgrade` 는 새 동의어 13행을 지우고 **4값 CHECK 를 되돌려 건다**. 새 두 값을 쓰는 행이
  남아 있으면 거기서 크게 실패한다 — 그것이 맞다(`0013_topic_vocab_six` 머리말과 같은 규율).
  마이그레이션이 사람의 분류값을 조용히 버리지 않는다.

Revision ID: 0006_topic_vocab_six
Revises: 0005_k2b_concept_graph_seed
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0006_topic_vocab_six"  # ⚠ 32자 이하다(`alembic_version_ai.version_num`)
down_revision = "0005_k2b_concept_graph_seed"
branch_labels = None
depends_on = None

#: 종전 4값 — `0002_k1_ontology` 가 표를 만들 때 박은 문자열과 같다.
TOPICS_4 = "'강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC'"
#: 새 6값 — 선언 정본은 `db/ai/schema.sql` 의 같은 줄이고, platform 쪽 `0013_topic_vocab_six` 와 같은 값이다.
TOPICS_6 = TOPICS_4 + ", '가뭄', '파일 포맷 예제'"

_DROP = (
    "ALTER TABLE d9_topic_synonym "
    "DROP CONSTRAINT IF EXISTS d9_topic_synonym_topic_check"
)

# db/ai/versions/<이 파일> → db/ai/seed/topic_synonym_six.sql
SEED_SQL = Path(__file__).resolve().parents[1] / "seed" / "topic_synonym_six.sql"

#: `downgrade` 가 지울 질의어 — 시드 파일과 **같은 목록**이다. 이 목록을 시드에서
#: 생성하지 않는 이유는 `k2-coverage-standard.tsv` 를 적재물에서 만들지 않는 이유와 같다.
NEW_SYNONYMS = ("가뭄", "가뭄지수", "SPI", "SPEI", "drought",
                "grib", "netcdf", "nc", "bin", "tif", "geotiff", "hdf5", "hdf")


def _seed_sql() -> str:
    """파일이 제 트랜잭션을 여닫는다 — alembic 이 이미 트랜잭션 안이므로 BEGIN/COMMIT 은 뺀다."""
    return "\n".join(
        line for line in SEED_SQL.read_text(encoding="utf-8").splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )


def upgrade() -> None:
    # 순서가 규약이다 — CHECK 를 먼저 넓히지 않으면 다음 INSERT 가 그 자리에서 죽는다.
    op.execute(_DROP)
    # NOT VALID 를 쓰지 않는다 — 넓히는 변경이라 검증이 값싸다(`0013_topic_vocab_six` 와 같은 판단).
    op.execute(
        "ALTER TABLE d9_topic_synonym "
        "  ADD CONSTRAINT d9_topic_synonym_topic_check "
        f"  CHECK (topic IN ({TOPICS_6}))"
    )
    op.execute(_seed_sql())


def downgrade() -> None:
    joined = ", ".join(f"'{s}'" for s in NEW_SYNONYMS)
    op.execute(f"DELETE FROM d9_topic_synonym WHERE synonym IN ({joined})")
    op.execute(_DROP)
    op.execute(
        "ALTER TABLE d9_topic_synonym "
        "  ADD CONSTRAINT d9_topic_synonym_topic_check "
        f"  CHECK (topic IN ({TOPICS_4}))"
    )
