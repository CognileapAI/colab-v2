"""alembic 환경 — ai 체인.

접속 URL 은 환경변수 COLAB_AI_DB_URL 로만 들어온다. 파일에 적지 않는다.
autogenerate 를 쓰지 않는다 — 선언 정본은 schema.sql 이고, 마이그레이션은 그 정본을 재현하는 절차다.
두 쪽이 갈라졌는지는 schema-diff 게이트가 본다.
"""
from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
URL = os.environ.get("COLAB_AI_DB_URL", "")
if URL:
    config.set_main_option("sqlalchemy.url", URL)

VERSION_TABLE = config.get_main_option("version_table")


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=None,
        literal_binds=True,
        version_table=VERSION_TABLE,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            version_table=VERSION_TABLE,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
