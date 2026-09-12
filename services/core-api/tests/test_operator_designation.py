"""운영자 지정·해제와 운영자의 전 연구실 **읽기** 스코프.

승인 intent = `dev-package/intent/2026-09-12-operator-designation.md`.

세 가지를 못 박는다 —
  ㈎ 지정·해제는 운영자 누구나 하고, **자기 해제**와 **마지막 한 명 해제**는 거절된다.
  ㈏ 지정·해제는 그 계정의 기존 로그인을 전부 끝낸다(자격 버전 +1 ＋ 원장 revoke).
  ㈐ 운영자는 모든 연구실을 **읽기만** 한다. 쓰기는 소속 연구실 그대로이고, 그 사실은
     경계가 열린 채(`app.operator_read='on'`) 도는 DB 층 시험이 증명한다 — HTTP 404 하나로는
     「정책이 막았다」와 「질의가 그 행을 안 골랐다」가 갈리지 않는다.
"""
from __future__ import annotations

import contextlib
import threading
import uuid

import pytest
from conftest import ACC_A_PROF, DS_A1, DS_B1, FILE_B1, LAB_A, LAB_B, TOKEN_PROF, auth
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

SECRET = "test-operator-designation-secret"
LAB_C = "0000000000000000000000000C"
#: `LAB_C` 에는 시드 데이터셋이 없다 — 아래 `_own_lab_dataset` 이 만들고 지운다.
DS_C1 = "0000000000000000000000DSC1"
INITIAL = "시험용-운영자-초기암호-123"
NEW = "시험용-운영자-정상암호-456"


@pytest.fixture(autouse=True)
def _restore_operators(admin_db_url: str):
    """`service_operator` 를 시험 전 상태로 되돌린다.

    이 파일의 시험은 **씨앗 운영자를 실제로 해제한다**(마지막 한 명 규칙을 재려면 그래야 한다).
    되돌리지 않으면 그 다음 시험이 403 을 받고, 그 red 는 코드가 아니라 순서가 만든 것이다.
    """
    engine = create_engine(admin_db_url)
    try:
        with engine.connect() as db:
            before = {r[0] for r in db.execute(text(
                "SELECT account_id FROM account_admin.service_operator"))}
        yield
        with engine.begin() as db:
            db.execute(text("DELETE FROM account_admin.service_operator"))
            for account_id in before:
                db.execute(text(
                    "INSERT INTO account_admin.service_operator(account_id) VALUES (:id)"),
                    {"id": account_id})
    finally:
        engine.dispose()


def _email(tag: str = "op") -> str:
    return f"{tag}-{uuid.uuid4().hex[:12]}@example.com"


def _create(client, email: str, *, role: str = "교수", operator: bool | None = None) -> str:
    body: dict = {"email": email, "name": "운영자 시험", "labId": LAB_C,
                  "role": role, "initialPassword": INITIAL}
    if operator is not None:
        body["operator"] = operator
    made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json=body)
    assert made.status_code == 201, made.text
    return made.json()["accountId"]


def _normal_token(client, email: str) -> str:
    """로그인 → 초기 비밀번호 변경까지. 돌려주는 것은 **정상** 세션 토큰이다."""
    login = client.post("/api/v1/sessions", json={"accountName": email, "password": INITIAL})
    assert login.status_code == 201, login.text
    changed = client.put("/api/v1/me/password", headers=auth(login.json()["token"]),
                         json={"newPassword": NEW})
    assert changed.status_code == 200, changed.text
    return changed.json()["token"]


def _operators(admin_db_url: str) -> set[str]:
    engine = create_engine(admin_db_url)
    try:
        with engine.connect() as db:
            return {r[0] for r in db.execute(text(
                "SELECT account_id FROM account_admin.service_operator"))}
    finally:
        engine.dispose()


def _set_operator(client, token: str, account_id: str, operator: bool):
    return client.post(f"/api/v1/admin/accounts/{account_id}/operator",
                       headers=auth(token), json={"operator": operator})


# ═══════════════════════ ㈎ 지정 · 해제 ═══════════════════════

def test_setServiceAccountOperator_designates_and_revokes(p2_client, admin_db_url: str) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email()
    account_id = _create(client, email)

    assert client.get("/api/v1/admin/accounts",
                      headers=auth(_normal_token(client, email))).status_code == 403

    made = _set_operator(client, TOKEN_PROF, account_id, True)
    assert made.status_code == 200, made.text
    assert made.json() == {"accountId": account_id, "operator": True}
    assert account_id in _operators(admin_db_url)
    # 지정으로 기존 로그인이 끝났으므로 다시 로그인한다 — 그 토큰으로는 목록이 열린다.
    promoted = client.post("/api/v1/sessions",
                           json={"accountName": email, "password": NEW}).json()["token"]
    assert client.get("/api/v1/admin/accounts", headers=auth(promoted)).status_code == 200

    gone = _set_operator(client, TOKEN_PROF, account_id, False)
    assert gone.status_code == 200, gone.text
    assert gone.json() == {"accountId": account_id, "operator": False}
    assert account_id not in _operators(admin_db_url)


def test_any_operator_may_designate_another(p2_client, admin_db_url: str) -> None:
    client = p2_client(session_secret=SECRET)
    first, second = _email("first"), _email("second")
    first_id, second_id = _create(client, first), _create(client, second)
    assert _set_operator(client, TOKEN_PROF, first_id, True).status_code == 200
    token = _normal_token(client, first)

    assert _set_operator(client, token, second_id, True).status_code == 200
    assert {first_id, second_id} <= _operators(admin_db_url)


def test_an_operator_cannot_revoke_itself(p2_client, admin_db_url: str) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email("self")
    account_id = _create(client, email)
    assert _set_operator(client, TOKEN_PROF, account_id, True).status_code == 200
    token = _normal_token(client, email)

    refused = _set_operator(client, token, account_id, False)
    assert refused.status_code == 400, refused.text
    assert account_id in _operators(admin_db_url)


def test_the_last_operator_cannot_be_revoked(p2_client, admin_db_url: str) -> None:
    client = p2_client(session_secret=SECRET)
    helper = _email("helper")
    helper_id = _create(client, helper)
    assert _set_operator(client, TOKEN_PROF, helper_id, True).status_code == 200
    helper_token = _normal_token(client, helper)

    # 씨앗 운영자를 지우면 남는 것은 helper 하나다. 그 하나는 지워지지 않는다.
    assert _set_operator(client, helper_token, ACC_A_PROF, False).status_code == 200
    refused = _set_operator(client, helper_token, helper_id, False)
    assert refused.status_code == 400, refused.text
    assert helper_id in _operators(admin_db_url)


def test_two_concurrent_revokes_leave_exactly_one_operator(
    p2_client, admin_db_url: str, tmp_path,
) -> None:
    """마지막 한 명 셈은 **잠금 아래**여야 한다. 아니면 둘이 동시에 「나 말고도 있다」를 본다.

    ⚠ 두 행위자의 자격은 **심어 둔 토큰**이다. 로그인 세션으로 하면 먼저 성공한 해제가 상대의
    세션을 끊어 두 번째 요청이 401 로 끝나고, 그러면 이 시험이 재려던 경합이 아예 일어나지
    않는다(실측 — 종전 판이 `[200, 401]` 을 냈다).
    """
    import json

    setup = p2_client(session_secret=SECRET)
    left, right = _email("left"), _email("right")
    left_id, right_id = _create(setup, left), _create(setup, right)

    planted = tmp_path / "operator-subjects.json"
    planted.write_text(json.dumps({
        TOKEN_PROF: {"accountId": ACC_A_PROF, "labId": LAB_A},
        "left-token": {"accountId": left_id, "labId": LAB_C},
        "right-token": {"accountId": right_id, "labId": LAB_C},
    }), encoding="utf-8")
    client = p2_client(session_secret=SECRET, subjects_file_override=str(planted))

    for account_id in (left_id, right_id):
        assert _set_operator(client, TOKEN_PROF, account_id, True).status_code == 200
    left_token, right_token = "left-token", "right-token"
    assert _set_operator(client, left_token, ACC_A_PROF, False).status_code == 200
    assert _operators(admin_db_url) == {left_id, right_id}

    codes: list[int] = []
    guard = threading.Lock()
    start = threading.Barrier(2)

    def revoke(actor_token: str, target: str) -> None:
        start.wait()
        response = _set_operator(client, actor_token, target, False)
        with guard:
            codes.append(response.status_code)

    threads = [
        threading.Thread(target=revoke, args=(left_token, right_id)),
        threading.Thread(target=revoke, args=(right_token, left_id)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # **하나만 통과한다.** 진 쪽의 코드는 둘 중 하나다 —
    #   400 : 잠금 안에서 「마지막 한 명」에 걸렸다.
    #   403 : 이긴 쪽의 트랜잭션이 진 쪽의 운영자 행을 먼저 지웠다(자격 확인에서 걸린다).
    # 어느 쪽이든 **남는 운영자는 1명**이고, 그것이 이 시험이 지키는 불변식이다.
    # 잠금이 없으면 둘 다 「나 말고도 있다」를 보고 통과해 0명이 된다 — 백오피스로는
    # 되돌릴 수 없는 상태이고, 아래 마지막 줄이 정확히 그것을 잡는다.
    assert codes.count(200) == 1, f"동시 해제가 갈리지 않았다: {codes}"
    assert {code for code in codes if code != 200} <= {400, 403}, f"뜻밖의 코드다: {codes}"
    assert len(_operators(admin_db_url)) == 1, f"마지막 운영자가 사라졌다: {codes}"


def test_designation_ends_the_existing_logins_of_that_account(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email("ends")
    account_id = _create(client, email)
    token = _normal_token(client, email)
    other = _email("bystander")
    _create(client, other)
    other_token = _normal_token(client, other)

    assert client.get("/api/v1/me", headers=auth(token)).status_code == 200
    assert _set_operator(client, TOKEN_PROF, account_id, True).status_code == 200

    assert client.get("/api/v1/me", headers=auth(token)).status_code == 401, \
        "운영자 지정 뒤에도 옛 로그인이 살아 있다."
    assert client.get("/api/v1/me", headers=auth(other_token)).status_code == 200, \
        "남의 세션까지 끊었다."


def test_createServiceAccount_can_mark_the_new_account_as_an_operator(
    p2_client, admin_db_url: str,
) -> None:
    client = p2_client(session_secret=SECRET)
    plain, boss = _email("plain"), _email("boss")
    plain_id = _create(client, plain)
    boss_id = _create(client, boss, operator=True)

    assert plain_id not in _operators(admin_db_url), "operator 를 생략했는데 운영자가 됐다."
    assert boss_id in _operators(admin_db_url)
    assert client.get("/api/v1/admin/accounts",
                      headers=auth(_normal_token(client, boss))).status_code == 200


def test_the_operator_path_is_operator_only(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email("outsider")
    account_id = _create(client, email)
    token = _normal_token(client, email)
    refused = _set_operator(client, token, account_id, True)
    assert refused.status_code == 403, refused.text


def test_the_account_list_carries_the_operator_flag(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email("listed"), operator=True)
    listed = client.get("/api/v1/admin/accounts", headers=auth(TOKEN_PROF))
    assert listed.status_code == 200, listed.text
    rows = {row["accountId"]: row for row in listed.json()["accounts"]}
    assert rows[account_id]["operator"] is True


# ═══════════════════════ ㈐ 전 연구실 읽기 ═══════════════════════

def _operator_identity(client) -> tuple[str, str]:
    """운영자 계정 하나 — `(accountId, 정상 세션 토큰)`. 반출 시험은 계정 ID 도 쓴다."""
    email = _email("reader")
    account_id = _create(client, email)
    assert _set_operator(client, TOKEN_PROF, account_id, True).status_code == 200
    return account_id, _normal_token(client, email)


def _operator_token(client) -> str:
    return _operator_identity(client)[1]


def test_an_operator_reads_datasets_of_every_lab(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    token = _operator_token(client)

    listed = client.get("/api/v1/datasets", headers=auth(token))
    assert listed.status_code == 200, listed.text
    seen = {row["datasetId"] for row in listed.json()["items"]}
    assert {DS_A1, DS_B1} <= seen, f"운영자가 전 연구실 카탈로그를 못 본다: {sorted(seen)}"

    for dataset in (DS_A1, DS_B1):
        detail = client.get(f"/api/v1/datasets/{dataset}", headers=auth(token))
        assert detail.status_code == 200, detail.text


def test_a_non_operator_still_sees_only_its_own_lab(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email("plainreader")
    _create(client, email)
    token = _normal_token(client, email)
    listed = client.get("/api/v1/datasets", headers=auth(token))
    assert listed.status_code == 200, listed.text
    seen = {row["datasetId"] for row in listed.json()["items"]}
    assert not ({DS_A1, DS_B1} & seen), f"비운영자가 남의 연구실을 봤다: {sorted(seen)}"


@pytest.mark.parametrize("method,path", [
    ("patch", f"/api/v1/datasets/{DS_B1}"),
    ("delete", f"/api/v1/datasets/{DS_B1}/representative-image"),
    ("delete", f"/api/v1/datasets/{DS_B1}/files/{FILE_B1}"),
])
def test_an_operator_cannot_write_into_another_lab(p2_client, method: str, path: str) -> None:
    """읽기가 열려도 **고치는 op 은 남의 연구실 행을 찾지 못한다** — 쓰기 스코프는 안 켜진다."""
    client = p2_client(session_secret=SECRET)
    token = _operator_token(client)
    response = client.request(method.upper(), path, headers=auth(token))
    assert response.status_code in (403, 404), f"{method.upper()} {path} → {response.status_code}"


def test_the_read_scope_never_opens_a_write(session_factory) -> None:
    """**이것이 진짜 오라클이다.** 경계를 연 채(`app.operator_read='on'`) 쓰기를 시도한다.

    HTTP 404 는 「정책이 막았다」와 「질의가 그 행을 안 골랐다」를 가르지 않는다. 여기서는
    읽기가 실제로 열린 것을 먼저 보이고, 같은 경계 아래의 쓰기가 막히는 것을 본다.
    """
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    subject = Subject(account_id=Ulid(ACC_A_PROF), lab_id=Ulid(LAB_A), operator=True)
    session = session_factory()
    try:
        session.begin()
        apply_scope(session, subject, operator_read=True)
        visible = session.execute(text(
            "SELECT count(*) FROM d3_dataset WHERE lab_id=:lab"), {"lab": LAB_B}).scalar_one()
        assert visible > 0, "운영자 읽기 스코프가 남의 연구실 행을 열지 못했다."

        # UPDATE·DELETE 는 **조용히 0 행**이다 — 고를 때 쓰기 정책이 걸러 낸다.
        for statement in ("UPDATE d3_dataset SET source_label='고쳐 본다' WHERE lab_id=:lab",
                          "DELETE FROM d3_dataset WHERE lab_id=:lab"):
            touched = session.execute(text(statement), {"lab": LAB_B}).rowcount
            assert touched == 0, f"운영자가 남의 연구실을 고쳤다 ({touched} 행): {statement}"
        assert session.execute(text(
            "SELECT count(*) FROM d3_dataset WHERE lab_id=:lab AND source_label='고쳐 본다'"),
            {"lab": LAB_B}).scalar_one() == 0

        # INSERT 는 조용하지 않다 — WITH CHECK 이 거절한다.
        with pytest.raises(ProgrammingError) as refused:
            session.execute(text("""
                INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id)
                VALUES ('00000000000000000000009PX1', :lab, :account, :account)
            """), {"lab": LAB_B, "account": ACC_A_PROF})
        assert "row-level security" in str(refused.value).lower()
    finally:
        session.rollback()
        session.close()


def test_lab_info_stays_whole_for_an_operator(p2_client) -> None:
    """`GET /lab` 은 **자기 연구실 한 벌**이어야 한다 — 이름과 구성원이 갈리면 안 된다.

    ⚠ `d1_lab` 은 테넌트 루트라 RLS 정책이 없고, 그래서 연구실 행은 질의가 직접
    `current_lab_id()` 로 고른다(`domains/d1_identity.py` 주석). 구성원 수·구성원 목록은
    RLS 에만 기대고 있었는데, 운영자 읽기 스코프가 열리면 그 둘만 전 연구실로 넓어진다 —
    화면에는 **내 연구실 이름 아래 남의 연구실 사람들**이 서게 된다. 읽기를 넓히는 것과
    한 화면의 두 값이 서로 다른 범위를 말하는 것은 다른 일이다.
    """
    client = p2_client(session_secret=SECRET)
    token = _operator_token(client)

    lab = client.get("/api/v1/lab", headers=auth(token))
    assert lab.status_code == 200, lab.text
    assert lab.json()["labId"] == LAB_C, "운영자의 연구실 정보가 자기 연구실이 아니다."

    grid = client.get("/api/v1/lab/members", headers=auth(token))
    assert grid.status_code == 200, grid.text
    assert lab.json()["memberCount"] == grid.json()["totalCount"], \
        "연구실 정보의 구성원 수와 구성원 격자의 길이가 갈린다 — 두 값의 범위가 다르다."

    # 정답은 **그 연구실의 계정 수**다. 운영자 목록을 연구실로 좁혀 세어 대조한다.
    listed = client.get("/api/v1/admin/accounts", headers=auth(TOKEN_PROF),
                        params={"labId": LAB_C})
    assert listed.status_code == 200, listed.text
    in_lab_c = len(listed.json()["accounts"])
    assert grid.json()["totalCount"] == in_lab_c, \
        f"구성원 격자가 자기 연구실({in_lab_c}명) 밖까지 담았다: {grid.json()['totalCount']}명"


# ═══════════════════════ ㈑ 읽기는 넓어도 **반출은 자기 연구실** ═══════════════════════

def _download_rows(session_factory) -> int:
    """`d8_download` 를 **전 연구실로** 센다 — `0029` 가 이 표에도 읽기 정책을 걸었다.

    자기 연구실만 세면 「남의 연구실 데이터셋을 받았는데 이력은 내 연구실에 적힌다」를
    못 가른다. `record_download` 의 `lab_id` 는 `current_lab_id()` 라 실제로 그렇게 적힌다.
    """
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    session = session_factory()
    try:
        session.begin()
        apply_scope(session, Subject(account_id=Ulid(ACC_A_PROF), lab_id=Ulid(LAB_A),
                                     operator=True), operator_read=True)
        return int(session.execute(text("SELECT count(*) FROM d8_download")).scalar_one())
    finally:
        session.rollback()
        session.close()


@contextlib.contextmanager
def _own_lab_dataset(session_factory, account_id: str):
    """운영자 자기 연구실(`LAB_C`)의 데이터셋 한 행 — 시드에 없어서 시험이 만들고 지운다.

    묶음 티켓은 조각을 읽지 않으므로(`routes/download.py::_issue` · `row=None`) `d3_file`
    없이 `d3_dataset` ＋ `d3_dataset_description` 두 행이면 200 이 선다.
    """
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    def run(*statements: str) -> None:
        session = session_factory()
        try:
            session.begin()
            apply_scope(session, Subject(account_id=Ulid(account_id), lab_id=Ulid(LAB_C)))
            for statement in statements:
                session.execute(text(statement), {"id": DS_C1, "account": account_id})
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    run("""INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id)
             VALUES (:id, current_lab_id(), :account, :account)""",
        """INSERT INTO d3_dataset_description (dataset_id, lab_id, name)
             VALUES (:id, current_lab_id(), \'운영자 자기 연구실 데이터셋\')""")
    try:
        yield DS_C1
    finally:
        run("DELETE FROM d3_dataset_description WHERE dataset_id = :id",
            "DELETE FROM d3_dataset WHERE id = :id")


def test_an_operator_cannot_download_another_labs_dataset(p2_client, session_factory) -> None:
    """전 연구실 **읽기**가 반출까지 열지 않는다 — 바이트는 자기 연구실 것만이다.

    두 발급 op(`downloadDataset`·`downloadDatasetFile`)이 남의 연구실 데이터셋에 대해
    **없는 것과 같은 봉투**(404 · `NOT_FOUND`)를 내고, `d8_download` 에 한 줄도 안 적는다.
    이력이 적히면 「반출을 거절했다」와 「반출했다」가 원장에서 갈리지 않는다.
    """
    client = p2_client(session_secret=SECRET)
    account_id, token = _operator_identity(client)

    with _own_lab_dataset(session_factory, account_id) as mine:
        before = _download_rows(session_factory)
        for path in (f"/api/v1/datasets/{DS_B1}/download",
                     f"/api/v1/datasets/{DS_B1}/files/{FILE_B1}/download"):
            refused = client.get(path, headers=auth(token))
            assert refused.status_code == 404, f"{path} → {refused.status_code}: {refused.text}"
            assert refused.json()["code"] == "NOT_FOUND", refused.text
        assert _download_rows(session_factory) == before, \
            "거절된 반출이 다운로드 이력에 남았다."

        # 자기 연구실은 그대로 열린다 — 좁힌 것은 경계 밖뿐이다.
        ok = client.get(f"/api/v1/datasets/{mine}/download", headers=auth(token))
        assert ok.status_code == 200, ok.text
        assert _download_rows(session_factory) == before + 1, \
            "자기 연구실 반출이 이력에 안 남았다."
