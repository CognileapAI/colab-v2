"""무소속 **비운영자** 계정은 만들어지지 않는다 (핫픽스 HF-B ③).

`kernel/login_sessions.py` `issue_database` 에는 갈래가 하나 있다 —
`row["lab_id"] is None and not operator → None`(＝ 401). 그 갈래는 **마지막 방어선**이고,
그 앞에서 「연구실 없고 운영자도 아닌 계정」이 아예 생기지 않아야 한다. 생긴다면 그 사람은
비밀번호가 맞는데도 영영 401 을 받고, 응답은 「심어 둔 계정이 아니다」라 **본인도 운영자도
원인을 못 찾는다**.

여기서 못 박는 것 —
  ⓐ 발급 두 입구(`createServiceAccount`·`createServiceAccountV2`)가 그 상태를 거절한다
  ⓑ 이미 선 계정을 무소속 비운영자로 **내리는 경로**도 거절된다(관리자 해제 거절)
  ⓒ 소속을 사후에 비우는 SQL 경로가 제품 코드·스키마에 **없다** — 정적 오라클
  ⓓ 그럼에도 그 갈래는 **죽은 코드가 아니다** — 저장소를 직접 그 상태로 만들면 401 이 난다
"""
from __future__ import annotations

import pathlib
import re
import uuid

import pytest
from conftest import TOKEN_PROF, auth
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

SECRET = "test-labless-guard-secret"
LAB_C = "0000000000000000000000000C"
INITIAL = "시험용-무소속-초기암호-123"
REPO = pathlib.Path(__file__).resolve().parents[3]


def _email(tag: str) -> str:
    return f"{tag}-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def _remove_created_accounts(admin_db_url: str):
    """이 시험이 등록한 계정만 지운다 (`test_operator_designation.py` 와 같은 방식).

    ⓝ 삭제는 **소유자 롤**로만 된다 — `colab_account_admin` 은 `d1_account` 에 INSERT 는
    되지만 DELETE 권한이 없다(실측). 게이트의 일회용 postgres 에서는 그 롤로 붙고, 붙지
    못하는 자리에서는 **정리만 못 한다**(시험의 판정은 여기에 걸려 있지 않다 — 이메일이
    회차마다 새 UUID 라 남은 행이 다음 회차를 물들이지 않는다).
    """
    account_ids: list[str] = []
    try:
        yield account_ids
    finally:
        try:
            engine = create_engine(
                make_url(admin_db_url).set(username="postgres", password=None))
        except Exception:  # noqa: BLE001 — 정리 실패가 판정을 바꾸지 않는다
            return
        try:
            with engine.begin() as db:
                for account_id in account_ids:
                    db.execute(text("DELETE FROM d1_account WHERE id=:id"), {"id": account_id})
        except OperationalError:
            pass
        finally:
            engine.dispose()


# ═════════════ ⓐ 두 입구가 무소속 비운영자를 거절한다 ═════════════════════════
@pytest.mark.parametrize("path", ["/api/v1/admin/accounts", "/api/v1/admin/accounts-v2"])
@pytest.mark.parametrize("affiliation", [
    {},                              # 연구실도 역할도 없다
    {"labId": LAB_C},                # 역할만 빠졌다
    {"role": "연구원"},               # 연구실만 빠졌다
])
def test_neither_entrance_creates_a_labless_non_operator(
    p2_client, path: str, affiliation: dict,
) -> None:
    """**운영자 표시가 없는 계정은 연구실과 역할을 함께 가져야 한다.**"""
    client = p2_client(session_secret=SECRET)
    response = client.post(path, headers=auth(TOKEN_PROF), json={
        "email": _email("labless"), "name": "무소속 비운영자", "operator": False,
        "initialPassword": INITIAL, **affiliation,
    })
    assert response.status_code in (400, 422), \
        f"{path} 가 무소속 비운영자를 만들었다 — 그 계정은 영영 401 을 받는다: {response.text}"


def test_the_operator_flag_defaults_to_false_so_omitting_it_is_also_refused(p2_client) -> None:
    """`operator` 를 아예 안 보내도 같은 거절이다 — 기본값이 관대한 쪽으로 떨어지지 않는다."""
    client = p2_client(session_secret=SECRET)
    response = client.post("/api/v1/admin/accounts-v2", headers=auth(TOKEN_PROF), json={
        "email": _email("labless-default"), "name": "무소속 기본값",
        "initialPassword": INITIAL,
    })
    assert response.status_code in (400, 422), response.text


# ═════════════ ⓑ 이미 선 계정을 그 상태로 내리는 경로도 없다 ═══════════════════
#
# ⓝ **여기에 시험을 새로 두지 않는다.** 무소속 관리자의 권한 해제가 거절되는 것은
#    `tests/test_operator_designation.py::test_labless_operator_full_login_cycle_and_demotion_guard`
#    가 이미 잰다(400 ＋ 「소속」). 같은 사실을 두 번 재면 무소속 계정 행이 회차마다 두 개씩
#    남고, 그 행은 **소유자 롤이 없으면 지울 수 없다**(`_remove_created_accounts` 주석).


# ═════════════ ⓒ 소속을 사후에 비우는 경로가 없다 (정적 오라클) ═══════════════
_SOURCES = (
    "services/core-api/src", "services/core-api/ops",
    "services/ai-service/src", "services/pipeline-worker/src", "services/viz-render/src",
    "db",
)
#: `UPDATE d1_account … SET … lab_id …` 를 한 문장 안에서 잡는다(줄바꿈 포함).
_UPDATE_LAB = re.compile(r"UPDATE\s+d1_account\b[^;]*?\bSET\b[^;]*?\blab_id\b",
                         re.IGNORECASE | re.DOTALL)
#: 연구실이 지워질 때 계정의 소속이 조용히 비는 경로.
_SET_NULL = re.compile(r"lab_id[^,;)]*REFERENCES\s+d1_lab[^,;)]*ON\s+DELETE\s+SET\s+NULL",
                       re.IGNORECASE)


def _production_text() -> list[tuple[pathlib.Path, str]]:
    out: list[tuple[pathlib.Path, str]] = []
    for root in _SOURCES:
        base = REPO / root
        for path in sorted(base.rglob("*")):
            if path.suffix not in (".py", ".sql") or not path.is_file():
                continue
            if "tests" in path.parts or "__pycache__" in path.parts:
                continue
            out.append((path, path.read_text(encoding="utf-8")))
    return out


def test_no_production_path_empties_the_affiliation_of_a_standing_account() -> None:
    """**실측 결과를 못 박는다** — 지금은 그런 경로가 0건이고, 생기면 여기서 red 다.

    있으면 「그 경로가 운영자 계정에만 적용되는가」를 묻는 시험을 그 자리에 세워야 한다.
    """
    found = [str(path.relative_to(REPO)) for path, body in _production_text()
             if _UPDATE_LAB.search(body)]
    assert found == [], \
        f"계정의 소속을 사후에 고치는 경로가 생겼다 — 운영자 한정인지 따로 재야 한다: {found}"


def test_deleting_a_lab_does_not_silently_empty_its_accounts() -> None:
    """`ON DELETE SET NULL` 이면 연구실 삭제 한 번이 그 연구실 전원을 무소속으로 만든다."""
    found = [str(path.relative_to(REPO)) for path, body in _production_text()
             if _SET_NULL.search(body)]
    assert found == [], f"`d1_account.lab_id` 가 연구실 삭제에 딸려 비워진다: {found}"


# ═════════════ ⓓ 그 갈래는 죽은 코드가 아니다 ═════════════════════════════════
def test_the_401_branch_still_fires_if_the_state_is_forced(
    p2_client, admin_db_url: str, _remove_created_accounts: list[str],
) -> None:
    """저장소를 **직접** 그 상태로 만들면 로그인이 401 이다 — 마지막 방어선이 살아 있다.

    앞의 시험들이 「그 상태가 생기지 않는다」를 재고, 이 시험이 「그래도 생기면 막힌다」를 잰다.
    둘 중 하나만 있으면 다음 회차가 조용히 그 상태를 만들 수 있다.
    """
    client = p2_client(session_secret=SECRET)
    email = _email("labless-forced")
    made = client.post("/api/v1/admin/accounts-v2", headers=auth(TOKEN_PROF), json={
        "email": email, "name": "무소속 관리자", "initialPassword": INITIAL,
        "operator": True,
    })
    assert made.status_code == 201, made.text
    account_id = made.json()["accountId"]
    _remove_created_accounts.append(account_id)
    assert client.post("/api/v1/sessions", json={
        "accountName": email, "password": INITIAL}).status_code == 201

    engine = create_engine(admin_db_url)
    try:
        with engine.begin() as db:
            db.execute(text("DELETE FROM account_admin.service_operator WHERE account_id=:id"),
                       {"id": account_id})
        denied = client.post("/api/v1/sessions", json={
            "accountName": email, "password": INITIAL})
        assert denied.status_code == 401, \
            f"무소속 비운영자가 로그인했다 — 마지막 방어선이 없다: {denied.text}"
    finally:
        engine.dispose()
    # ⛔ **운영자 행을 되돌리지 않는다.** 되돌리면 이 계정이 운영자로 남고, 운영자를 **집합으로**
    # 재는 시험(`test_operator_designation.py::test_two_concurrent_revokes_leave_exactly_one_operator`)
    # 이 그 한 줄 때문에 red 가 된다 — 소유자 롤이 없는 자리에서는 계정 행을 지울 수 없어
    # 그 운영자가 다음 시험까지 살아남는다. 지운 채로 두면 운영자 집합은 시험 전과 같다.
