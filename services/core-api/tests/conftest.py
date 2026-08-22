from __future__ import annotations

import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REPO = pathlib.Path(__file__).resolve().parents[3]
CONTRACT = REPO / "contracts" / "seams" / "fe-core.yaml"


# ─────────────────────────────────────────────────────────────────────────────
# A2 — 음성·실효 증명이 함께 쓰는 재료 (WU-P0 산출물 #2 · sessions/P0-rls-proof.md)
#
# 시드는 `tests/fixtures/seed.sql`, 주체 표는 `tests/fixtures/subjects.json` 이다.
# DB 가 없으면 **skip 이 아니라 fail** 이다 — 그 skip 이 정확히 v1 의 실패였다 (P0.md §6).
# ─────────────────────────────────────────────────────────────────────────────
import contextlib  # noqa: E402
import os  # noqa: E402

import pytest  # noqa: E402

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

LAB_A = "0000000000000000000000000A"
LAB_B = "0000000000000000000000000B"
ACC_A_PROF = "00000000000000000000000AP1"
ACC_A_RES = "000000000000000000000000A1"
ACC_B_PROF = "00000000000000000000000BP1"
DS_A1 = "0000000000000000000000DSA1"   # 열림 · 파일 2
DS_A2 = "0000000000000000000000DSA2"   # 잠김 · 파일 1 · DSA1 의 자식
DS_B1 = "0000000000000000000000DSB1"   # 다른 연구실
FILE_B1 = "00000000000000000000000FB1"
PRJ_B = "0000000000000000000000PRJB"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} 이 없다. DB 를 못 붙인 것은 통과가 아니다 (CLAUDE.md §4).")
    return value


@pytest.fixture(scope="session")
def app_db_url() -> str:
    """앱 롤(NOBYPASSRLS·비소유자)로 접속하는 URL."""
    return _require("COLAB_CORE_TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def subjects_file() -> str:
    return os.environ.get("COLAB_CORE_TEST_SUBJECTS_FILE") or str(FIXTURES / "subjects.json")


@pytest.fixture(scope="session")
def session_factory(app_db_url: str):
    from colab_core.kernel.db import make_engine, make_session_factory
    return make_session_factory(make_engine(app_db_url))


@contextlib.contextmanager
def scoped_ro(factory, account_id: str, lab_id: str):
    """경계를 심고 **반드시 rollback** 하는 트랜잭션.

    증명용 쓰기(허용 줄 추가 등)를 시드에 남기지 않기 위해서다 —
    시드가 테스트 순서에 따라 달라지면 그 오라클은 오라클이 아니다.
    """
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    session = factory()
    try:
        session.begin()
        apply_scope(session, Subject(account_id=Ulid(account_id), lab_id=Ulid(lab_id)))
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def live_client(app_db_url: str, subjects_file: str):
    """HTTP 층 증명용. DB 층과 **같은 앱 롤**로 붙는다 — 층만 다르고 경계는 하나다."""
    from fastapi.testclient import TestClient

    from colab_core.app.main import create_app
    from colab_core.kernel.config import Settings

    return TestClient(create_app(Settings(database_url=app_db_url, subjects_file=subjects_file)))
