"""alembic 환경 — ai 체인.

접속 URL 은 환경변수 COLAB_AI_DB_URL 로 들어온다. 이 파일에 적지 않는다.
**값 대신 경로로도 받는다** — COLAB_AI_DB_URL_FILE (`PLAN-SoT §9 〈121〉-㉯`).
`docker inspect` 의 환경변수 목록에 접속 문자열이 통째로 남는 것을 막는다. 판정 규칙은
`ai_db_url.py` 한 곳에 있다.
autogenerate 를 쓰지 않는다 — 선언 정본은 schema.sql 이고, 마이그레이션은 그 정본을 재현하는 절차다.
두 쪽이 갈라졌는지는 schema-diff 게이트가 본다.
"""
from __future__ import annotations

import pathlib
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# alembic 의 `prepend_sys_path` 는 **cwd 기준**이라 러너가 어디서 부르느냐에 따라 흔들린다.
# 판독기는 이 파일 옆에 있으므로 그 자리를 직접 잡는다.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ai_db_url import resolve_db_url  # noqa: E402

config = context.config
URL = resolve_db_url()
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
