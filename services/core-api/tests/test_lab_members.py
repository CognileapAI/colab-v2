"""`listLabMembers` · `saveLabMemberPermissions` 실동작 — 권한 값의 원천 한 자리.

정본 —
  · `Policy_역할과_권한 §2·§3` 스위치 4종 · 교수 행 고정 · 고치는 자리는 한 곳
  · `Policy_역할과_권한 §6`   위임은 재위임되지 않는다  → `P-31`
  · `P-19` 실시간 저장이 아니다(확인 모달 1회 = 요청 1회) · `P-33` append-only 이력
  · `P-11` 화면에서 숨긴 것은 서버가 같은 기준으로 막는다 — **403 은 서버가 낸다**
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from colab_core.app.main import API_PREFIX, create_app
from colab_core.kernel.config import Settings

SWITCHES = ["업로드·편집", "프로젝트 생성", "승인 위임", "연구실 설정"]
DELEGABLE = ["업로드·편집", "프로젝트 생성"]
ACC_A_PROF = "00000000000000000000000AP1"
ACC_A_RES = "000000000000000000000000A1"
ACC_B_PROF = "00000000000000000000000BP1"


@pytest.fixture(scope="module")
def client() -> TestClient:
    url = os.environ.get("COLAB_CORE_TEST_DATABASE_URL")
    subjects = os.environ.get("COLAB_CORE_TEST_SUBJECTS_FILE")
    if not url or not subjects:
        pytest.fail("COLAB_CORE_TEST_DATABASE_URL · COLAB_CORE_TEST_SUBJECTS_FILE 가 없다.")
    return TestClient(create_app(Settings(database_url=url, subjects_file=subjects)))


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def members(client: TestClient, token: str) -> dict:
    r = client.get(f"{API_PREFIX}/lab/members", headers=auth(token))
    assert r.status_code == 200, r.text
    return {m["accountId"]: m for m in r.json()["items"]}


def save(client: TestClient, token: str, items: list[dict]):
    return client.put(f"{API_PREFIX}/lab/members/permissions",
                      headers=auth(token), json={"items": items})


def switch_state(client: TestClient, account_id: str, switch: str) -> bool:
    return members(client, "a1-prof-token")[account_id]["permissions"][switch]


# ── 격자 ────────────────────────────────────────────────────────────────────
def test_the_grid_is_members_by_four_switches(client: TestClient) -> None:
    rows = members(client, "a1-prof-token")
    assert set(rows) == {ACC_A_PROF, ACC_A_RES}
    for m in rows.values():
        assert list(m["permissions"]) == SWITCHES, "스위치는 정확히 넷이고 다섯째를 만들지 않는다."
        assert set(m) == {"accountId", "name", "email", "role",
                          "permissions", "editablePermissions"}


def test_professor_row_is_all_on_and_fixed(client: TestClient) -> None:
    prof = members(client, "a1-prof-token")[ACC_A_PROF]
    assert prof["role"] == "교수"
    assert all(prof["permissions"].values()), "교수는 네 스위치가 항상 켜진 것으로 취급한다 (P-5)."
    assert prof["editablePermissions"] == [], "교수 행은 고정이라 아무도 못 고친다 (P-5)."


def test_professor_can_edit_every_switch_of_a_researcher(client: TestClient) -> None:
    res = members(client, "a1-prof-token")[ACC_A_RES]
    assert res["role"] == "연구원"
    assert res["editablePermissions"] == SWITCHES


def test_a_member_without_the_lab_settings_switch_is_403(client: TestClient) -> None:
    """권한 스위치를 고치는 자리는 `연구실 설정` 한 곳이다 (P-18 · P-11)."""
    r = client.get(f"{API_PREFIX}/lab/members", headers=auth("a1-res-token"))
    assert r.status_code == 403
    assert r.json()["code"] == "FORBIDDEN"


def test_members_never_cross_the_lab_boundary(client: TestClient) -> None:
    assert set(members(client, "b1-prof-token")) == {ACC_B_PROF}


def test_requires_a_subject(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/lab/members").status_code == 401
    assert client.put(f"{API_PREFIX}/lab/members/permissions",
                      json={"items": []}).status_code == 401


# ── 저장 ────────────────────────────────────────────────────────────────────
def test_save_writes_the_switch_and_returns_the_grid(client: TestClient) -> None:
    assert switch_state(client, ACC_A_RES, "승인 위임") is False
    r = save(client, "a1-prof-token", [{"accountId": ACC_A_RES, "changes": {"승인 위임": True}}])
    assert r.status_code == 200
    try:
        rows = {m["accountId"]: m for m in r.json()["items"]}
        assert rows[ACC_A_RES]["permissions"]["승인 위임"] is True, "응답이 저장 후 격자다."
        assert switch_state(client, ACC_A_RES, "승인 위임") is True
    finally:
        save(client, "a1-prof-token", [{"accountId": ACC_A_RES, "changes": {"승인 위임": False}}])
    assert switch_state(client, ACC_A_RES, "승인 위임") is False


def test_one_switch_becomes_one_audit_row(client: TestClient) -> None:
    """스위치 하나당 한 줄 · append-only (P-33). 두 칸이 바뀌면 두 줄이다."""
    from sqlalchemy import text

    engine = client.app.state.engine

    def _count() -> int:
        with engine.begin() as conn:
            conn.execute(text("SELECT set_config('app.current_lab', :l, true)"),
                         {"l": "0000000000000000000000000A"})
            conn.execute(text("SELECT set_config('app.current_account', :a, true)"),
                         {"a": ACC_A_PROF})
            return conn.execute(text("SELECT count(*) FROM d2_permission_change")).scalar_one()

    before = _count()
    save(client, "a1-prof-token", [{"accountId": ACC_A_RES,
                                    "changes": {"승인 위임": True, "연구실 설정": True}}])
    try:
        assert _count() == before + 2
        with engine.begin() as conn:
            conn.execute(text("SELECT set_config('app.current_lab', :l, true)"),
                         {"l": "0000000000000000000000000A"})
            conn.execute(text("SELECT set_config('app.current_account', :a, true)"),
                         {"a": ACC_A_PROF})
            row = conn.execute(text(
                "SELECT actor_account_id, target_account_id, switch, direction "
                "FROM d2_permission_change ORDER BY changed_at DESC, id DESC LIMIT 1"
            )).mappings().one()
        assert row["actor_account_id"].strip() == ACC_A_PROF
        assert row["target_account_id"].strip() == ACC_A_RES
        assert row["direction"] == "켬"
    finally:
        save(client, "a1-prof-token", [{"accountId": ACC_A_RES,
                                        "changes": {"승인 위임": False, "연구실 설정": False}}])


def test_the_professor_row_cannot_be_touched(client: TestClient) -> None:
    r = save(client, "a1-prof-token", [{"accountId": ACC_A_PROF, "changes": {"승인 위임": False}}])
    assert r.status_code == 403, "교수 행은 켜진 채로 고정돼 끌 수 없다 (§3 · P-5)."


def test_a_member_without_the_switch_cannot_save(client: TestClient) -> None:
    r = save(client, "a1-res-token", [{"accountId": ACC_A_RES, "changes": {"승인 위임": True}}])
    assert r.status_code == 403


def test_unknown_target_is_404(client: TestClient) -> None:
    r = save(client, "a1-prof-token",
             [{"accountId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "changes": {"승인 위임": True}}])
    assert r.status_code == 404, "경계 밖·없는 계정은 존재를 알리지 않는다 (P-9·P-10)."


def test_cross_lab_target_is_404(client: TestClient) -> None:
    r = save(client, "a1-prof-token", [{"accountId": ACC_B_PROF, "changes": {"승인 위임": True}}])
    assert r.status_code == 404


def test_a_fifth_switch_is_rejected(client: TestClient) -> None:
    r = save(client, "a1-prof-token", [{"accountId": ACC_A_RES, "changes": {"데이터 삭제": True}}])
    assert r.status_code == 400, "다섯 번째 스위치를 만들지 않는다."


def test_empty_items_is_rejected(client: TestClient) -> None:
    assert save(client, "a1-prof-token", []).status_code == 400


# ── 재위임 금지 (P-31) — 서버가 강제한다 ─────────────────────────────────────
def test_a_delegate_edits_only_two_columns_and_is_blocked_on_the_other_two(
        client: TestClient) -> None:
    save(client, "a1-prof-token", [{"accountId": ACC_A_RES, "changes": {"연구실 설정": True}}])
    try:
        rows = members(client, "a1-res-token")

        # ① 행별 `editablePermissions` 가 재위임 금지를 말한다
        assert rows[ACC_A_RES]["editablePermissions"] == DELEGABLE
        assert rows[ACC_A_PROF]["editablePermissions"] == []

        # ② 편집 불가 열도 **값은 보인다** — 열을 지우면 표 구조가 깨진다 (P-31)
        assert list(rows[ACC_A_RES]["permissions"]) == SWITCHES

        # ③ 그리고 서버가 실제로 막는다
        ok = save(client, "a1-res-token",
                  [{"accountId": ACC_A_RES, "changes": {"업로드·편집": False}}])
        assert ok.status_code == 200
        save(client, "a1-res-token", [{"accountId": ACC_A_RES, "changes": {"업로드·편집": True}}])

        blocked = save(client, "a1-res-token",
                       [{"accountId": ACC_A_RES, "changes": {"승인 위임": True}}])
        assert blocked.status_code == 403, "위임은 재위임되지 않는다 (P-31)."
        assert switch_state(client, ACC_A_RES, "승인 위임") is False, "403 이면 한 칸도 쓰이지 않는다."

        # ④ 한 요청에 허용 칸과 금지 칸이 섞이면 **통째로 거부** — 절반만 저장하지 않는다
        mixed = save(client, "a1-res-token",
                     [{"accountId": ACC_A_RES,
                       "changes": {"프로젝트 생성": False, "연구실 설정": False}}])
        assert mixed.status_code == 403
        assert switch_state(client, ACC_A_RES, "프로젝트 생성") is True
    finally:
        save(client, "a1-prof-token", [{"accountId": ACC_A_RES,
                                        "changes": {"연구실 설정": False,
                                                    "업로드·편집": True,
                                                    "프로젝트 생성": True}}])
    assert switch_state(client, ACC_A_RES, "연구실 설정") is False
