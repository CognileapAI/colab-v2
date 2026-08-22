"""cross-tenant 음성 4종 — 읽기 · 자식 · 미스코프 · 쓰기(WITH CHECK).

`P0.md §5` 완료 판정 #4 의 본체다. 네 케이스 전부 **red→green** 으로 증명한다 —
red 를 만드는 법은 각 테스트 docstring 에 적었고, 실제 실행 기록은
`dev-package/sessions/P0-rls-proof.md §1` 이다.

**이 테스트가 의미를 가지려면 앱 롤이 NOBYPASSRLS·비소유자여야 한다.**
소유자·superuser 로 돌리면 FORCE RLS 가 무력해져 모든 green 이 거짓이다 —
그래서 아래 첫 테스트가 그 성질을 먼저 못 박는다 (`test_scope_kernel.py` 와 이중으로).
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from conftest import (ACC_A_PROF, ACC_A_RES, ACC_B_PROF, DS_A1, DS_A2, DS_B1,
                      FILE_B1, LAB_A, LAB_B, PRJ_B, scoped_ro)

#: 경계 정책이 걸린 테넌트 테이블 전부. `d1_lab`(테넌트 루트)·`alembic_version_*` 는 면제다.
TENANT_TABLES = (
    "d1_lab_profile", "d1_account",
    "d2_member_role", "d2_permission_switch", "d2_permission_change",
    "d2_dataset_access", "d2_dataset_access_grant", "d2_verified",
    "d3_dataset", "d3_dataset_description", "d3_dataset_autometa", "d3_file",
    "d4_lineage_edge", "d4_lineage_unknown",
    "d6_project", "d6_project_dataset",
    "d8_activity", "d8_download",
)


def test_the_app_role_cannot_bypass_anything(session_factory) -> None:
    """이 파일의 전제. 깨지면 아래 네 음성이 전부 **거짓 green** 이 된다."""
    session = session_factory()
    try:
        row = session.execute(text(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )).one()
        assert row.rolsuper is False and row.rolbypassrls is False
        assert session.execute(text(
            "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tableowner=current_user"
        )).scalar_one() == 0, "앱 롤이 테이블 소유자다 — FORCE RLS 가 무력해진다."
        # 조사 대상이 실제로 FORCE 까지 켜져 있는지도 여기서 본다.
        forced = {r.relname for r in session.execute(text(
            "SELECT relname FROM pg_class WHERE relrowsecurity AND relforcerowsecurity"
        ))}
        assert set(TENANT_TABLES) <= forced, "FORCE RLS 가 빠진 테넌트 테이블이 있다."
    finally:
        session.close()


# ── ① 읽기 ────────────────────────────────────────────────────────────────────

def test_read_never_returns_another_labs_rows(session_factory) -> None:
    """다른 연구실의 행은 **보이지 않는다.**

    red 만드는 법 — `ALTER POLICY lab_boundary ON d3_dataset USING (true) WITH CHECK (true)`
    (= 스코프 한 줄 누락. `P0.md §6` 의 「스코프 누락」 함정 그대로).
    """
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        for table in TENANT_TABLES:
            leaked = db.execute(text(f"SELECT count(*) FROM {table} WHERE lab_id = :other"),
                                {"other": LAB_B}).scalar_one()
            assert leaked == 0, f"{table} 에서 다른 연구실 행이 보였다."
        ids = {r[0] for r in db.execute(text("SELECT id FROM d3_dataset"))}
        assert ids == {DS_A1, DS_A2} and DS_B1 not in ids

    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as db:
        for table in TENANT_TABLES:
            leaked = db.execute(text(f"SELECT count(*) FROM {table} WHERE lab_id = :other"),
                                {"other": LAB_A}).scalar_one()
            assert leaked == 0, f"{table} 에서 다른 연구실 행이 보였다."
        assert {r[0] for r in db.execute(text("SELECT id FROM d3_dataset"))} == {DS_B1}


def test_read_boundary_holds_at_the_http_layer(live_client) -> None:
    """HTTP 층에서도 같다 — `listDatasets` 는 자기 연구실만 낸다."""
    from colab_core.app.main import API_PREFIX
    a = live_client.get(f"{API_PREFIX}/datasets",
                        headers={"Authorization": "Bearer a1-prof-token"}).json()
    b = live_client.get(f"{API_PREFIX}/datasets",
                        headers={"Authorization": "Bearer b1-prof-token"}).json()
    assert {r["datasetId"] for r in a["items"]} == {DS_A1, DS_A2}
    assert {r["datasetId"] for r in b["items"]} == {DS_B1}
    # 존재 자체를 알리지 않는다 (P-9·P-10) — 403 이 아니라 404 다.
    assert live_client.get(f"{API_PREFIX}/datasets/{DS_B1}/files",
                           headers={"Authorization": "Bearer a1-prof-token"}).status_code == 404


# ── ② 자식 ────────────────────────────────────────────────────────────────────

def test_child_rows_of_another_labs_parent_are_invisible(session_factory) -> None:
    """부모(다른 연구실 데이터셋)를 **키로 알고 있어도** 자식 행은 보이지 않는다.

    ID 를 안다는 것과 볼 수 있다는 것은 다르다. 경계는 조인 경로가 아니라 행마다 걸린다.

    red 만드는 법 — `ALTER POLICY lab_boundary ON d3_file USING (true) WITH CHECK (true)`
    (자식 테이블에서만 경계를 빠뜨린 형태. 부모는 여전히 안 보이므로 목록 테스트로는 안 잡힌다).
    """
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        def count(sql: str, **kw) -> int:
            return db.execute(text(sql), kw).scalar_one()

        assert count("SELECT count(*) FROM d3_file WHERE dataset_id = :d", d=DS_B1) == 0
        assert count("SELECT count(*) FROM d3_file WHERE id = :f", f=FILE_B1) == 0
        assert count("SELECT count(*) FROM d3_dataset_description WHERE dataset_id = :d", d=DS_B1) == 0
        assert count("SELECT count(*) FROM d3_dataset_autometa WHERE dataset_id = :d", d=DS_B1) == 0
        assert count("SELECT count(*) FROM d6_project_dataset WHERE dataset_id = :d", d=DS_B1) == 0
        assert count("SELECT count(*) FROM d6_project WHERE id = :p", p=PRJ_B) == 0
        assert count("SELECT count(*) FROM d1_account WHERE id = :a", a=ACC_B_PROF) == 0
        assert count("SELECT count(*) FROM d2_member_role WHERE account_id = :a", a=ACC_B_PROF) == 0
        # 조인으로 우회해도 같다. 2 인 이유 = A 의 파일 3건 중 DSA2(잠김)의 1건은
        # 두 번째 층(`body_access`)이 따로 막는다. B 의 1건은 경계가 막는다.
        assert count("SELECT count(*) FROM d3_dataset d JOIN d3_file f ON f.dataset_id = d.id") == 2
    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as db:
        # A 의 계보 관계도 B 에게는 없다.
        assert db.execute(text("SELECT count(*) FROM d4_lineage_edge")).scalar_one() == 0
        assert db.execute(text(
            "SELECT count(*) FROM d4_lineage_edge WHERE child_dataset_id = :c"), {"c": DS_A2}
        ).scalar_one() == 0


# ── ③ 미스코프 ────────────────────────────────────────────────────────────────

def test_a_connection_without_the_guc_sees_zero_rows(session_factory) -> None:
    """GUC 를 세팅하지 않은 접속은 **한 행도** 보지 못한다 — 기본 거부 (P0-schema §4 설계판단 3).

    스코프 주입을 빠뜨린 경로가 「전부」를 보는 것이 아니라 「아무것도」 못 보게 닫힌다.

    red 만드는 법 — `current_lab_id()` 의 ELSE 를 NULL 대신 고정 연구실 ID 로 바꾼다
    (= 「기본값을 주자」는 흔한 유혹. 그 순간 미스코프가 전체 열람이 된다).
    """
    session = session_factory()
    try:
        assert session.execute(text("SELECT current_lab_id()")).scalar_one() is None
        assert session.execute(text("SELECT current_account_id()")).scalar_one() is None
        for table in TENANT_TABLES:
            assert session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0, \
                f"{table} 이 미스코프 접속에 행을 내줬다."
    finally:
        session.close()


def test_a_garbage_guc_is_the_same_as_no_guc(session_factory) -> None:
    """정규 ID 가 아닌 GUC 는 NULL 로 떨어진다 — 문자열을 끼워 넣는 경로가 없다."""
    session = session_factory()
    try:
        session.begin()
        for bad in ("' OR 1=1 --", "0000000000000000000000000a", "", "0000000000000000000000000I"):
            session.execute(text("SELECT set_config('app.current_lab', :v, true)"), {"v": bad})
            assert session.execute(text("SELECT current_lab_id()")).scalar_one() is None
            assert session.execute(text("SELECT count(*) FROM d3_dataset")).scalar_one() == 0
    finally:
        session.rollback()
        session.close()


# ── ④ 쓰기 (WITH CHECK) ───────────────────────────────────────────────────────

@pytest.mark.parametrize("sql, params", [
    ("INSERT INTO d6_project (id, lab_id, type, name, status) "
     "VALUES ('0000000000000000000000WRT1', :lab, '논문', '남의 연구실에 쓰기', '진행 중')",
     {"lab": LAB_B}),
    ("INSERT INTO d1_account (id, lab_id, name, email) "
     "VALUES ('0000000000000000000000WRT2', :lab, '침입 계정', 'x@b.example')",
     {"lab": LAB_B}),
    ("INSERT INTO d8_activity (id, lab_id, actor_account_id, action, target_kind, target_id) "
     "VALUES ('0000000000000000000000WRT3', :lab, :actor, '위조', '데이터셋', :ds)",
     {"lab": LAB_B, "actor": ACC_A_RES, "ds": DS_B1}),
])
def test_with_check_blocks_writing_into_another_lab(session_factory, sql, params) -> None:
    """남의 `lab_id` 를 써 넣는 경로가 없다.

    `USING` 만 있고 `WITH CHECK` 가 없으면 **읽지는 못하지만 쓸 수는 있는** 구멍이 남는다.

    red 만드는 법 — `ALTER POLICY lab_boundary ON d6_project
    USING (lab_id = current_lab_id()) WITH CHECK (true)`.
    """
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as db:
        with pytest.raises(ProgrammingError) as excinfo:
            db.execute(text(sql), params)
        assert "row-level security" in str(excinfo.value).lower()


def test_moving_an_own_row_to_another_lab_is_blocked(session_factory) -> None:
    """이미 가진 행을 남의 연구실로 **옮기는** 것도 WITH CHECK 가 막는다."""
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        with pytest.raises(ProgrammingError):
            db.execute(text("UPDATE d3_dataset SET lab_id = :other WHERE id = :d"),
                       {"other": LAB_B, "d": DS_A1})


def test_write_boundary_holds_at_the_http_layer(live_client, session_factory) -> None:
    """`createProject` 는 `lab_id` 를 요청에서 받지 않는다 — `current_lab_id()` 가 넣는다."""
    from colab_core.app.main import API_PREFIX
    # ⓐ labId 를 실어 보낼 자리 자체가 없다. 계약에 없는 필드는 400 이다.
    refused = live_client.post(
        f"{API_PREFIX}/projects", headers={"Authorization": "Bearer a1-res-token"},
        json={"type": "논문", "name": "A2 경계 확인", "period": {"start": "2026-03", "end": None},
              "labId": LAB_B},
    )
    assert refused.status_code == 400, "labId 를 받아 주는 경로가 생겼다 (P-9·P-10)."

    # ⓑ 정상 생성분은 반드시 자기 연구실에 들어간다.
    r = live_client.post(
        f"{API_PREFIX}/projects", headers={"Authorization": "Bearer a1-res-token"},
        json={"type": "논문", "name": "A2 경계 확인", "period": {"start": "2026-03", "end": None}},
    )
    assert r.status_code == 201
    project_id = r.json()["projectId"]
    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as db:
        assert db.execute(text("SELECT count(*) FROM d6_project WHERE id = :p"),
                          {"p": project_id}).scalar_one() == 0, "쓴 것이 다른 연구실로 샜다."
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        assert db.execute(text("SELECT lab_id FROM d6_project WHERE id = :p"),
                          {"p": project_id}).scalar_one() == LAB_A
