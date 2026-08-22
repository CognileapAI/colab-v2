"""스코프 커널이 무엇을 막는가 — 증명.

  ① GUC 를 세팅하지 않은 접속은 **한 행도** 보지 못한다 (기본 거부).
  ② `SET LOCAL` 이라 트랜잭션이 끝나면 경계가 사라진다 — 풀 커넥션이 앞 요청의 lab_id 를
     물려받지 않는다. 이것이 비-LOCAL `SET` 을 쓰지 않는 이유다.
  ③ 앱 롤은 NOBYPASSRLS 이고 테이블 소유자가 아니다 — 아니면 위 둘이 **거짓 green** 이 된다.

cross-tenant 음성 4종의 본체는 A2(WU-P0 산출물 #2)가 맡는다. 여기서는 커널 자체를 본다.
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from colab_core.kernel.auth import Subject
from colab_core.kernel.db import make_engine, make_session_factory
from colab_core.kernel.ids import Ulid
from colab_core.kernel.scope import scoped_session

LAB_A = Ulid("0000000000000000000000000A")
ACC_A1 = Ulid("000000000000000000000000A1")


@pytest.fixture(scope="module")
def factory():
    url = os.environ.get("COLAB_CORE_TEST_DATABASE_URL")
    if not url:
        pytest.fail("COLAB_CORE_TEST_DATABASE_URL 이 없다. DB 를 못 붙인 것은 통과가 아니다.")
    return make_session_factory(make_engine(url))


def test_no_guc_sees_nothing(factory) -> None:
    session = factory()
    try:
        assert session.execute(text("SELECT count(*) FROM d3_dataset")).scalar_one() == 0
        assert session.execute(text("SELECT current_lab_id()")).scalar_one() is None
    finally:
        session.close()


def test_scope_makes_rows_visible_then_forgets_them(factory) -> None:
    subject = Subject(account_id=ACC_A1, lab_id=LAB_A)
    with scoped_session(factory, subject) as session:
        assert session.execute(text("SELECT count(*) FROM d3_dataset")).scalar_one() == 2
        connection_id = session.execute(text("SELECT pg_backend_pid()")).scalar_one()

    # 같은 풀에서 다시 꺼낸 커넥션 — 경계가 남아 있으면 여기서 2 가 나온다.
    session = factory()
    try:
        assert session.execute(text("SELECT pg_backend_pid()")).scalar_one() == connection_id, \
            "풀이 같은 커넥션을 돌려주지 않았다 — 이 테스트가 증명하려는 상황이 아니다."
        assert session.execute(text("SELECT count(*) FROM d3_dataset")).scalar_one() == 0, \
            "SET LOCAL 이 아니라 SET 을 썼다 — 다음 요청으로 lab_id 가 샌다."
    finally:
        session.close()


def test_app_role_is_nobypassrls_and_not_the_owner(factory) -> None:
    session = factory()
    try:
        row = session.execute(text(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )).one()
        assert row.rolsuper is False, "앱 롤이 superuser 다 — 경계 증명이 전부 무의미해진다."
        assert row.rolbypassrls is False, "앱 롤이 BYPASSRLS 다 — 정책이 통째로 무시된다."
        owned = session.execute(text(
            "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tableowner=current_user"
        )).scalar_one()
        assert owned == 0, "앱 롤이 테이블 소유자다 — 소유자와 접속 주체를 갈라 둔다."
    finally:
        session.close()


def test_scope_rejects_non_canonical_ids(factory) -> None:
    with pytest.raises(ValueError):
        with scoped_session(factory, Subject(account_id=ACC_A1, lab_id="' OR 1=1 --")):  # type: ignore[arg-type]
            pass
