"""Run the real role bootstrap SQL against disposable PostgreSQL, including non-superusers."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


ROLE_SQL = Path(__file__).resolve().parents[1] / "ops" / "account-admin-role.sql"


@pytest.fixture
def role_bootstrap(admin_db_url):
    url = make_url(admin_db_url).set(username="postgres", password=None)
    engine = create_engine(url)
    suffix = uuid4().hex
    bootstrap = f"test_bootstrap_{suffix}"
    target = f"test_admin_{suffix}"

    def execute(statement):
        with engine.begin() as conn:
            return conn.execute(text(statement))

    def run(role):
        env = {
            **os.environ,
            "PGHOST": url.host,
            "PGPORT": str(url.port or 5432),
            "PGDATABASE": url.database,
            "PGUSER": role,
            "PGPASSWORD": "",
        }
        result = subprocess.run(
            ["psql", "-X", "-At", "--single-transaction", "-v", "ON_ERROR_STOP=1",
             "-v", f"admin={target}", "-v", "admin_password=disposable-test-only",
             "-c", "SELECT current_user, rolsuper FROM pg_roles WHERE rolname=current_user",
             "-f", str(ROLE_SQL)],
            env=env, capture_output=True, text=True, timeout=30,
        )
        # This is the executing session's identity, not the setup connection's privileges.
        assert result.stdout.splitlines()[0] == f"{role}|{'t' if role == 'postgres' else 'f'}"
        return result

    try:
        execute(f"CREATE ROLE {bootstrap} LOGIN NOSUPERUSER CREATEDB CREATEROLE NOBYPASSRLS")
        execute(f"CREATE ROLE {target} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT BYPASSRLS")
        execute(f"GRANT colab_owner TO {bootstrap}")
        execute(f"GRANT {target} TO {bootstrap} WITH ADMIN OPTION")
        assert execute(
            "SELECT admin_option FROM pg_auth_members "
            f"WHERE roleid='{target}'::regrole AND member='{bootstrap}'::regrole"
        ).scalar_one() is True
        yield execute, run, bootstrap, target
    finally:
        for role in (bootstrap, target):
            if execute(f"SELECT EXISTS (SELECT FROM pg_roles WHERE rolname='{role}')").scalar_one():
                execute(f"DROP OWNED BY {role}")
                execute(f"DROP ROLE {role}")
        engine.dispose()


def assert_restricted(execute, target):
    assert tuple(execute(
        "SELECT rolsuper, rolcreatedb, rolcreaterole, rolinherit, rolbypassrls, rolcanlogin "
        f"FROM pg_roles WHERE rolname='{target}'"
    ).one()) == (False, False, False, False, True, True)


@pytest.mark.parametrize("drift", ["INHERIT", "CREATEDB", "CREATEROLE", "CREATEDB CREATEROLE INHERIT"])
def test_non_superuser_repairs_only_drifted_attributes(role_bootstrap, drift):
    execute, run, bootstrap, target = role_bootstrap
    execute(f"ALTER ROLE {target} {drift}")
    result = run(bootstrap)
    assert result.returncode == 0, result.stderr
    assert_restricted(execute, target)


def test_non_superuser_can_repeat_correct_bootstrap(role_bootstrap):
    execute, run, bootstrap, target = role_bootstrap
    for _ in range(2):
        result = run(bootstrap)
        assert result.returncode == 0, result.stderr
    assert_restricted(execute, target)


def test_non_superuser_cannot_add_bypassrls(role_bootstrap):
    execute, run, bootstrap, target = role_bootstrap
    execute(f"ALTER ROLE {target} NOBYPASSRLS")
    result = run(bootstrap)
    assert result.returncode != 0
    assert "BYPASSRLS" in result.stderr
    assert execute(f"SELECT rolbypassrls FROM pg_roles WHERE rolname='{target}'").scalar_one() is False


def test_superuser_creates_fresh_admin_role(role_bootstrap):
    execute, run, _, target = role_bootstrap
    execute(f"DROP ROLE {target}")
    result = run("postgres")
    assert result.returncode == 0, result.stderr
    assert_restricted(execute, target)


def test_existing_superuser_is_rejected_by_final_check(role_bootstrap):
    execute, run, _, target = role_bootstrap
    execute(f"ALTER ROLE {target} SUPERUSER")
    result = run("postgres")
    assert result.returncode != 0
    assert "계정 관리자 롤이 superuser다" in result.stderr
