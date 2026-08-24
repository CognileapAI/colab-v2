"""K1b — 온톨로지 2차: 개념 그래프 두 표 (d9_concept · d9_concept_edge)

내용 정본 = dev-package/sessions/K1b-ONTOLOGY-CONTENT.md §A·§B·§C·§E
판정      = Ted 2026-08-25 (PLAN-SoT §9) — F-9 ㈎ E5 신설 · F-10 ㈏ E2 1행 · F-11 확장 경계 그대로
            · F-13 ㈎ **기존 3표를 그대로 두고 새로 세운다**(합치지 않는다)
범위 정본 = dev-package/ONTOLOGY-SCOPE.md §2차 범위

**왜 두 표를 새로 세우는가.** `㊸-④-4`(2026-08-23)는 「그래프 구조를 만들지 않는다」였다.
그 판정은 **정본이 준 값의 양이 그래프를 정당화하지 않는다**는 근거 위에 있었고,
`SEED-DATA §5` 가 실데이터 어휘를 실측해 그 전제를 바꿨다(사전과 실데이터가 서로 다른 공간·방법 어휘를 쓴다).
`〈82〉`(KG 도메인의 다음 투자는 그래프이지 임베딩이 아니다) 와 이번 판정이 그 자리를 다시 연 것이다.
**되돌린 것은 「그래프 없음」이지 「경계 없음」이 아니다** — §D-6 의 확장 경계 넷이 expandable 열과
완료 오라클로 함께 들어온다.

이 리비전은 DDL 만 만든다. 시드는 0005 이고, 시드가 없어도 스키마는 성립한다.
선언 정본은 db/ai/schema.sql 이고 이 리비전은 그 정본을 재현하는 절차다 (env.py — autogenerate 를 쓰지 않는다).
그래서 DDL 을 schema.sql 과 **한 글자도 다르지 않게** 적는다. 갈라지면 schema-diff 가 red 를 낸다.

두 표 어디에도 lab_id 가 없다 — 연구실 공통 지식이라 테넌트별로 갈리지 않는다 (0002 와 같은 근거).
RLS 면제는 gates/config/rls-allowlist.toml 에 이름을 하나씩 적어 사람이 판단을 남긴다.
기록 체인(D1~D8)으로 가는 FK 가 하나도 없다 (CLAUDE.md §3-1·§3-3 — 애초에 다른 체인이다).

⚠ 이 파일의 산문에 기록 체인의 **경로 문자열**을 적지 않는다. `ai-no-lineage-write` ⑨ 는 그 경로가
db/ai 안에서 글자로 나타나면 주석이라도 red 를 낸다. 게이트가 맞다 — 정규식이 산문과 코드를 가르려
들면 진짜 참조를 놓칠 문이 생긴다. 같은 실수가 이 레포에서 두 번 났다(S1-search-infra · K1b).
**고칠 것은 게이트가 아니라 문장이다.**

Revision ID: 0004_k1b_concept_graph
Revises: 0003_k2_ontology_seed
"""
from __future__ import annotations

from alembic import op

revision = "0004_k1b_concept_graph"
down_revision = "0003_k2_ontology_seed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE d9_concept (
          concept_id   text        PRIMARY KEY
                       CHECK (concept_id ~ '^[a-z0-9]+(-[a-z0-9]+)*$'
                              AND length(concept_id) BETWEEN 1 AND 60),
          kind         text        NOT NULL
                       CHECK (kind IN ('방법', '주제', '지명', '원천표기')),
          label        text        NOT NULL
                       CHECK (btrim(label) = label AND length(label) BETWEEN 1 AND 120),
          source_grade smallint    NOT NULL CHECK (source_grade BETWEEN 1 AND 6),
          source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
          expandable   boolean     NOT NULL DEFAULT true,
          created_at   timestamptz NOT NULL DEFAULT now(),
          UNIQUE (kind, label)
        )
        """
    )
    op.execute("CREATE INDEX d9_concept_kind_idx ON d9_concept (kind)")
    op.execute("CREATE INDEX d9_concept_grade_idx ON d9_concept (source_grade)")
    op.execute(
        """
        CREATE TABLE d9_concept_edge (
          src          text        NOT NULL REFERENCES d9_concept (concept_id),
          relation     text        NOT NULL
                       CHECK (relation IN ('같은 말이다', '~의 한 가지다', '안에 있다')),
          dst          text        NOT NULL REFERENCES d9_concept (concept_id),
          source_grade smallint    NOT NULL CHECK (source_grade BETWEEN 1 AND 6),
          source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
          created_at   timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (src, relation, dst),
          CONSTRAINT d9_concept_edge_no_self CHECK (src <> dst),
          CONSTRAINT d9_concept_edge_sym_normalized
                       CHECK (relation <> '같은 말이다' OR src < dst)
        )
        """
    )
    op.execute("CREATE INDEX d9_concept_edge_dst_idx ON d9_concept_edge (relation, dst)")


def downgrade() -> None:
    op.execute("DROP TABLE d9_concept_edge")
    op.execute("DROP TABLE d9_concept")
