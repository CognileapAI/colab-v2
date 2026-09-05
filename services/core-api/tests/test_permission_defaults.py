"""권한 스위치 **기본값** — 저장된 행이 없을 때의 판정 (WU-A1 · PRD-25).

정본 —
  · `contracts/schemas/common.json#/$defs/PermissionSwitchSet.default`
    앞의 둘(`업로드·편집`·`프로젝트 생성`) 켜짐 / 위임 성격 둘(`승인 위임`·`연구실 설정`) 꺼짐
  · `db/platform/schema.sql` `d2_permission_switch` 머리 주석 `P-4` — 같은 사실
  · `P-5` 교수는 네 스위치가 항상 켜진 것으로 **판정**된다 (저장이 아니다)

**행이 없는 상태가 「기본값」이다.** DB 에 기본값 행을 만들지 않는다 — 상수는 서버 한 자리
(`d2_access.DEFAULT_SWITCHES`)에만 둔다. 그래서 마이그레이션이 0 건이다.

저장된 행은 그대로 이긴다 — **명시적으로 꺼 둔 계정이 이 변경으로 켜지지 않는다.**
"""
from __future__ import annotations

import json

from conftest import ACC_A_PROF, ACC_A_RES, LAB_A, REPO, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.domains import d2_access

SWITCHES = ["업로드·편집", "프로젝트 생성", "승인 위임", "연구실 설정"]
DEFAULT = {"업로드·편집": True, "프로젝트 생성": True,
           "승인 위임": False, "연구실 설정": False}

HDF5_MAGIC = b"\x89HDF\r\n\x1a\n" + b"\x00" * 32


def _drop_rows(sql, switches: list[str] | None = None) -> None:
    """A1 연구원의 스위치 행을 지운다 = 「행이 없는 계정」을 만든다.

    되돌림은 conftest 의 `_RESTORE` 가 맡는다 (INSERT ... ON CONFLICT).
    """
    names = switches if switches is not None else SWITCHES
    sql("DELETE FROM d2_permission_switch"
        " WHERE account_id = :a AND switch = ANY(:s)",
        {"a": ACC_A_RES, "s": names}, account_id=ACC_A_PROF, lab_id=LAB_A)


# ═══════════════════════ ① 행 없는 연구원 = 정본 기본값 ══════════════════════
def test_me_falls_back_to_the_canonical_defaults_when_no_row_is_stored(
        live_client, sql) -> None:
    """`/me` — 행이 하나도 없으면 앞의 둘 켜짐 · 위임 성격 둘 꺼짐이다.

    현행 코드는 네 스위치를 **모두 꺼짐**으로 내려서 새 연구원이 아무것도 못 올린다.
    """
    _drop_rows(sql)
    r = live_client.get(f"{API_PREFIX}/me", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert r.json()["permissions"] == DEFAULT


def test_member_grid_uses_the_same_defaults_as_me(live_client, sql) -> None:
    """격자 표(`listLabMembers`)도 **같은 판정**을 쓴다 — 두 자리가 갈리지 않는다.

    격자를 여는 것은 `연구실 설정` 이라 **교수 토큰으로** 본다 — 기본 꺼짐인 연구원은
    자기 행이 없어도 이 화면에 못 들어온다(그것이 정본이다).
    """
    _drop_rows(sql)
    r = live_client.get(f"{API_PREFIX}/lab/members", headers=auth("a1-prof-token"))
    assert r.status_code == 200, r.text
    rows = {m["accountId"]: m["permissions"] for m in r.json()["items"]}
    assert rows[ACC_A_RES] == DEFAULT
    assert rows[ACC_A_PROF] == {s: True for s in SWITCHES}, "교수는 판정으로 전부 켜진다 (P-5)."


# ═══════════════════════ ② 저장된 행이 이긴다 ═══════════════════════════════
def test_an_explicit_false_row_is_not_flipped_on_by_the_default(live_client, sql) -> None:
    """명시적으로 꺼 둔 계정이 이 변경으로 켜지지 않는다 — 행이 있으면 그 값이 이긴다."""
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'",
        {"a": ACC_A_RES}, account_id=ACC_A_PROF, lab_id=LAB_A)
    r = live_client.get(f"{API_PREFIX}/me", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert r.json()["permissions"]["업로드·편집"] is False
    assert r.json()["permissions"]["프로젝트 생성"] is True


def test_an_explicit_true_row_on_a_default_off_switch_is_honoured(live_client, sql) -> None:
    """반대 방향도 같다 — 기본 꺼짐인 `승인 위임` 을 켜 두면 켜진 채로 내려간다."""
    sql("UPDATE d2_permission_switch SET enabled = true"
        " WHERE account_id = :a AND switch = '승인 위임'",
        {"a": ACC_A_RES}, account_id=ACC_A_PROF, lab_id=LAB_A)
    r = live_client.get(f"{API_PREFIX}/me", headers=auth(TOKEN_RES))
    assert r.json()["permissions"]["승인 위임"] is True


def test_a_partially_stored_account_mixes_row_and_default(live_client, sql) -> None:
    """행이 **일부만** 있는 계정 — 있는 칸은 저장값, 없는 칸은 기본값이다."""
    _drop_rows(sql, ["업로드·편집", "승인 위임"])
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '프로젝트 생성'",
        {"a": ACC_A_RES}, account_id=ACC_A_PROF, lab_id=LAB_A)
    permissions = live_client.get(f"{API_PREFIX}/me",
                                  headers=auth(TOKEN_RES)).json()["permissions"]
    assert permissions == {"업로드·편집": True,      # 행 없음 → 기본 켜짐
                           "프로젝트 생성": False,   # 저장값이 이긴다
                           "승인 위임": False,       # 행 없음 → 기본 꺼짐
                           "연구실 설정": False}


# ═══════════════════════ ③ 교수는 현행 유지 ═════════════════════════════════
def test_the_professor_still_gets_all_four_switches_true(live_client) -> None:
    """교수는 저장이 아니라 판정이다 (P-5) — 행이 없어도 원래 전부 켜져 있었다."""
    r = live_client.get(f"{API_PREFIX}/me", headers=auth("a1-prof-token"))
    assert r.status_code == 200, r.text
    assert r.json()["permissions"] == {s: True for s in SWITCHES}


# ═══════════════════════ ④ 회귀 방지 — 실제 업로드가 된다 ════════════════════
def test_a_researcher_with_no_row_can_actually_upload(p2_client, sql) -> None:
    """**이 WU 가 고치는 결함 그 자체다** — 시드가 채우지 않은 계정은 업로드가 막혔다."""
    _drop_rows(sql)
    r = p2_client().post(
        f"{API_PREFIX}/uploads",
        files=[("files", ("a.nc", HDF5_MAGIC, "application/octet-stream"))],
        headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text


# ═══════════════════════ ⑤ 상수는 한 자리 · 계약과 같다 ══════════════════════
def test_the_default_constant_matches_the_contract() -> None:
    """서버 상수와 `common.json#PermissionSwitchSet.default` 가 같은 값이다.

    두 자리가 갈리면 화면과 서버가 다른 권한을 믿는다. 상수는 서버 한 자리에만 둔다.
    FE(`components/members/permissions.ts`)는 그 계약 위치를 **가리키는 주석만** 갖는다.
    """
    common = json.loads((REPO / "contracts" / "schemas" / "common.json").read_text("utf-8"))
    canonical = common["$defs"]["PermissionSwitchSet"]["default"]
    assert canonical == DEFAULT, "이 시험이 red 면 정본이 바뀐 것이다 — 코드가 아니라 정본을 본다."
    assert d2_access.DEFAULT_SWITCHES == canonical
    assert set(d2_access.DEFAULT_SWITCHES) == set(d2_access.SWITCHES)
