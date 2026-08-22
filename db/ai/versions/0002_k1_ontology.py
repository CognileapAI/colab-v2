"""K1 — 온톨로지 1차: 시드 테이블 3개

범위 정본 = dev-package/ONTOLOGY-SCOPE.md (G8, Ted 승인 2026-08-23)
결정      = PLAN-SoT §9-㊸-④-4 「시드 테이블 3개 — 가공 방식 후보 · 주제 동의어 · 지명 별칭.
            그래프 구조·개념 유형 체계는 만들지 않는다」

선언 정본은 db/ai/schema.sql 이고 이 리비전은 그 정본을 재현하는 절차다 (env.py — autogenerate 를 쓰지 않는다).
그래서 DDL 을 schema.sql 과 **한 글자도 다르지 않게** 적는다. 갈라지면 schema-diff 가 red 를 낸다.

세 표 어디에도 lab_id 가 없다 — 연구실 공통 지식이라 테넌트별로 갈리지 않는다 (DOMAINS.md D9).
RLS 면제는 gates/config/rls-allowlist.toml 에 이름을 하나씩 적어 사람이 판단을 남긴다.

이 체인은 기록 도메인(D1~D8)과 마이그레이션 체인이 분리된다 (CLAUDE.md §3-3).
여기에 계보 테이블은 없다 — AI 는 제안만 하고, 사람이 확인한 것만 기록 쪽 체인으로 넘어간다 (§3-2).

Revision ID: 0002_k1_ontology
Revises: 0001_p0_ai
"""
from __future__ import annotations

from alembic import op

revision = "0002_k1_ontology"
down_revision = "0001_p0_ai"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE d9_method_term (
          term         text        PRIMARY KEY
                       CHECK (btrim(term) = term AND length(term) BETWEEN 1 AND 120),
          source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
          created_at   timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE d9_topic_synonym (
          synonym      text        PRIMARY KEY
                       CHECK (btrim(synonym) = synonym AND length(synonym) BETWEEN 1 AND 120),
          topic        text        NOT NULL
                       CHECK (topic IN ('강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC')),
          source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
          created_at   timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX d9_topic_synonym_topic_idx ON d9_topic_synonym (topic)")
    op.execute(
        """
        CREATE TABLE d9_place_alias (
          alias        text        PRIMARY KEY
                       CHECK (btrim(alias) = alias AND length(alias) BETWEEN 1 AND 120),
          place_name   text        NOT NULL
                       CHECK (btrim(place_name) = place_name AND length(place_name) BETWEEN 1 AND 120),
          source_note  text        NOT NULL CHECK (length(btrim(source_note)) > 0),
          created_at   timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX d9_place_alias_place_idx ON d9_place_alias (place_name)")


def downgrade() -> None:
    op.execute("DROP TABLE d9_place_alias")
    op.execute("DROP TABLE d9_topic_synonym")
    op.execute("DROP TABLE d9_method_term")
