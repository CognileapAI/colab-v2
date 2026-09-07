"""WU-B4 · PRD-11 — 공개 범위 **3값**(`열림`·`잠김`·`지정 공개`).

수용 기준 6건(`R-B-1-db.md §2` WU-B4) 중 **서버가 잴 수 있는 다섯**이 여기 있다 —
마이그레이션 이관 오라클은 `db/platform/tests/0017-drift.sh` 이고 화면 쪽은
`frontend/test/visibility-three-20260907.test.tsx` 다.

  ㈎ 등록이 고른 값을 `d2_dataset_access` 에 쓴다 (열쇠 부재 = 연구실 기본값)
  ㈏ 승인이 `잠김` → `지정 공개` 로 **같은 트랜잭션에서** 올리고 본체가 열린다
  ㈐ 소유자가 `잠김` 으로 내리면 **유효 grant 전부 만료** ＋ 끊긴 사람 수를 응답이 말한다
  ㈑ `state='잠김'` ∧ 유효 grant ≥1 인 행이 **어느 시점에도 0건** (불변식)
  ㈒ `나만 보기` 데이터셋도 접근 요청을 **접수한다** (마이그레이션 `0010` 회귀)
  ㈓ 연구실 밖 계정은 어느 상태든 **0건** (RLS 경계 무개방)

⛔ **접근 판정 함수는 이 회차가 고치지 않는다**(PRD-11 축자) — `지정 공개` 는 grant 판정을
   그대로 탄다. 아래 `test_designated_rides_the_grant_path` 가 그 사실을 붙잡는다.
"""
from __future__ import annotations

from conftest import (ACC_A_PROF, ACC_A_RES, ACC_B_PROF, DS_A1, DS_A2, LAB_A, LAB_B,
                      TOKEN_B, TOKEN_PROF, TOKEN_RES, auth)
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

#: 유효 grant 두 줄 — 「2명」 문면의 재료다.
_GRANT = """
    INSERT INTO d2_dataset_access_grant
      (id, lab_id, dataset_id, grantee_account_id, approver_account_id,
       approved_at, expires_at)
    VALUES (:id, current_lab_id(), :ds, :grantee, :approver,
            now(), now() + interval '6 months')
"""


def _register_with(client, **extra):
    return register(client, make_upload(client), **extra)


def _state_of(sql, dataset_id: str):
    rows = sql("SELECT state FROM d2_dataset_access WHERE dataset_id = :d",
               {"d": dataset_id})
    return rows[0]["state"] if rows else None


# ═══════ ㈎ 등록이 값을 쓴다 ════════════════════════════════════════════════
def test_registration_writes_the_chosen_state(p2_client, sql) -> None:
    """PRD-11 이 여는 자리 — 「`DatasetCreate` 에 공개 범위 열쇠가 없어 업로드에서 받는
    자리 자체가 없다」."""
    client = p2_client()
    r = _register_with(client, accessState="잠김")
    assert r.status_code == 201, r.text
    assert r.json()["accessState"] == "잠김"
    assert _state_of(sql, r.json()["datasetId"]) == "잠김"


def test_registration_can_choose_the_designated_state(p2_client, sql) -> None:
    """3값의 셋째가 **쓰기 경로에서도** 성립한다 — CHECK 를 한쪽만 넓히면 여기서 500 이 난다."""
    client = p2_client()
    r = _register_with(client, accessState="지정 공개")
    assert r.status_code == 201, r.text
    assert r.json()["accessState"] == "지정 공개"
    assert _state_of(sql, r.json()["datasetId"]) == "지정 공개"


def test_registration_without_the_key_falls_back_to_the_lab_default(p2_client, sql) -> None:
    """NULL = 연구실 기본값(현행 의미 유지) — **행을 지어내지 않는다.**"""
    client = p2_client()
    r = _register_with(client)
    assert r.status_code == 201, r.text
    assert _state_of(sql, r.json()["datasetId"]) is None, \
        "열쇠가 없는데 상태 행을 만들었다 — NULL 과 '열림' 이 구별되지 않는다."
    assert r.json()["accessState"] == "열림"      # A 연구실 기본값


def test_a_value_outside_the_three_is_a_400(p2_client) -> None:
    """값 집합 밖은 **400** 이다 — CHECK 위반을 IntegrityError 500 으로 떨어뜨리지 않는다."""
    client = p2_client()
    r = _register_with(client, accessState="전체 공개")
    assert r.status_code == 400, r.text
    assert "지정 공개" in r.text


# ═══════ ㈏ 승인이 상태를 올린다 (같은 트랜잭션) ════════════════════════════
def test_approval_flips_locked_to_designated_and_opens_the_body(p2_client, sql) -> None:
    """PRD-11 상태 전이표 — 「`잠김` ＋ 요청 승인 → **`지정 공개`**」.

    「상태는 잠김인데 볼 수 있는 사람이 있다」가 **한 순간도** 생기지 않는다.
    """
    client = p2_client()
    assert _state_of(sql, DS_A2) == "잠김"
    made = client.post(f"{API_PREFIX}/datasets/{DS_A2}/access-requests",
                       json={"reason": "분석에 쓰려고요"}, headers=auth(TOKEN_RES))
    assert made.status_code == 201, made.text
    request_id = made.json()["requestId"]

    approved = client.post(f"{API_PREFIX}/access-requests/{request_id}/approval",
                           headers=auth(TOKEN_PROF))
    assert approved.status_code == 200, approved.text
    # 응답이 바뀐 상태를 싣는다 — 화면이 되읽지 않는다 (PRD-11 계약 축자).
    assert approved.json()["accessState"] == "지정 공개"
    assert _state_of(sql, DS_A2) == "지정 공개"

    detail = client.get(f"{API_PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES))
    assert detail.status_code == 200, detail.text
    assert detail.json()["accessState"] == "지정 공개"
    assert detail.json()["bodyAccessible"] is True


def test_rejection_leaves_the_state_alone(p2_client, sql) -> None:
    """전이표 — 「`잠김` ＋ 거절 → `잠김`」. 거절이 상태를 올리면 불변식이 깨진다."""
    client = p2_client()
    made = client.post(f"{API_PREFIX}/datasets/{DS_A2}/access-requests",
                       json=None, headers=auth(TOKEN_RES))
    request_id = made.json()["requestId"]
    rejected = client.post(f"{API_PREFIX}/access-requests/{request_id}/rejection",
                           json={"reason": "지금은 어려워요"}, headers=auth(TOKEN_PROF))
    assert rejected.status_code == 204, rejected.text
    assert _state_of(sql, DS_A2) == "잠김"


# ═══════ ㈐ 내리면 전부 만료 ＋ 끊긴 사람 수 ════════════════════════════════
def test_lowering_to_locked_expires_every_valid_grant_and_reports_the_count(
        p2_client, sql) -> None:
    """전이표 마지막 줄 — 「어느 상태든 소유자가 `잠김` 으로 내림 → `잠김` ＋ **유효 grant
    전부 만료**」. 화면 되묻는 문면의 `2명` 이 이 숫자다."""
    client = p2_client()
    sql("UPDATE d2_dataset_access SET state = '지정 공개' WHERE dataset_id = :d",
        {"d": DS_A2})
    for i, grantee in enumerate((ACC_A_RES, ACC_A_PROF), start=1):
        sql(_GRANT, {"id": f"0000000000000000000000GR0{i}", "ds": DS_A2,
                     "grantee": grantee, "approver": ACC_A_PROF})

    before = client.get(f"{API_PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES))
    assert before.json()["activeGrantCount"] == 2, before.text

    lowered = client.patch(f"{API_PREFIX}/datasets/{DS_A2}",
                           json={"accessState": "잠김"}, headers=auth(TOKEN_PROF))
    assert lowered.status_code == 200, lowered.text
    assert lowered.json()["accessState"] == "잠김"
    assert lowered.json()["activeGrantCount"] == 0

    left = sql("SELECT count(*) AS n FROM d2_dataset_access_grant"
               "  WHERE dataset_id = :d AND expires_at > now()", {"d": DS_A2})
    assert left[0]["n"] == 0, "잠김으로 내렸는데 유효 grant 가 남았다 (불변식)."


# ═══════ ㈑ 불변식 — 어느 시점에도 0건 ═════════════════════════════════════
def test_no_locked_dataset_ever_holds_a_valid_grant(p2_client, sql) -> None:
    """`잠김` ∧ 유효 grant ≥1 은 **성립하지 않는다.** 승인 왕복을 한 바퀴 돈 뒤에 센다."""
    client = p2_client()
    made = client.post(f"{API_PREFIX}/datasets/{DS_A2}/access-requests",
                       json=None, headers=auth(TOKEN_RES))
    client.post(f"{API_PREFIX}/access-requests/{made.json()['requestId']}/approval",
                headers=auth(TOKEN_PROF))
    rows = sql("""
        SELECT count(*) AS n
          FROM d2_dataset_access a
         WHERE a.state = '잠김'
           AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                        WHERE g.dataset_id = a.dataset_id AND g.expires_at > now())
    """)
    assert rows[0]["n"] == 0


# ═══════ ㈒ 잠김이어도 요청은 접수된다 (0010 회귀) ══════════════════════════
def test_a_locked_dataset_still_accepts_access_requests(p2_client) -> None:
    """3값 도입이 **요청 경로를 막지 않는다** — 전이표 「`잠김` ＋ 접근 요청 → `잠김`」."""
    client = p2_client()
    made = client.post(f"{API_PREFIX}/datasets/{DS_A2}/access-requests",
                       json={"reason": "보고 싶어요"}, headers=auth(TOKEN_RES))
    assert made.status_code == 201, made.text


def test_a_designated_dataset_also_accepts_access_requests(p2_client, sql) -> None:
    """전이표 — 「`지정 공개` ＋ 접근 요청 → `지정 공개`(요청 허용)」."""
    client = p2_client()
    sql("UPDATE d2_dataset_access SET state = '지정 공개' WHERE dataset_id = :d",
        {"d": DS_A2})
    made = client.post(f"{API_PREFIX}/datasets/{DS_A2}/access-requests",
                       json=None, headers=auth(TOKEN_RES))
    assert made.status_code == 201, made.text


# ═══════ 접근 판정 함수 무수정 — `지정 공개` 는 grant 판정을 그대로 탄다 ═════
def test_designated_rides_the_grant_path(p2_client, sql) -> None:
    """양성·음성 둘 다 — 허용 목록에 있으면 열리고, 없으면 `잠김` 과 **같은 경로로** 막힌다."""
    client = p2_client()
    sql("UPDATE d2_dataset_access SET state = '지정 공개' WHERE dataset_id = :d",
        {"d": DS_A2})
    # 음성 — grant 가 없으면 지정 공개도 안 열린다.
    shut = client.get(f"{API_PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES))
    assert shut.json()["accessState"] == "지정 공개"
    assert shut.json()["bodyAccessible"] is False
    # 양성 — 유효 grant 한 줄이면 종전과 같이 열린다.
    sql(_GRANT, {"id": "0000000000000000000000GR09", "ds": DS_A2,
                 "grantee": ACC_A_RES, "approver": ACC_A_PROF})
    open_ = client.get(f"{API_PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES))
    assert open_.json()["bodyAccessible"] is True


# ═══════ ㈓ cross-tenant 음성 — RLS 경계 무개방 ═════════════════════════════
def test_another_lab_sees_no_access_rows(p2_client, sql) -> None:
    """3값 도입이 RLS 경계를 열지 않았다. B 연구실 계정에게 A 의 데이터셋은 **없다.**"""
    client = p2_client()
    for dataset_id in (DS_A1, DS_A2):
        r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_B))
        assert r.status_code == 404, r.text
    rows = sql("SELECT count(*) AS n FROM d2_dataset_access",
               account_id=ACC_B_PROF, lab_id=LAB_B)
    assert rows[0]["n"] == 0, "B 세션에서 A 의 접근 상태 행이 보인다 (경계 개방)."
    mine = sql("SELECT count(*) AS n FROM d2_dataset_access",
               account_id=ACC_A_RES, lab_id=LAB_A)
    assert mine[0]["n"] >= 2, "A 세션에서도 0 이면 위의 0 은 경계가 만든 0 이 아니다."


# ═══════ ㈑ 이어서 — **동시성**: 승인 ∥ 내림이 겹쳐도 불변식이 0건 ══════════
#
# ⭑ **⟨advisor ② ㊀⟩ 「어느 시점에도」는 직렬 경로만으로는 참이 아니다.**
#
# READ COMMITTED 에서 잠금이 없으면 두 트랜잭션이 이렇게 엇갈린다 —
#   T1(승인)  INSERT grant → UPDATE state='지정 공개'        … 아직 커밋 전
#   T2(내림)  UPDATE grants SET expires_at=now()             … T1 의 grant 가 안 보여 0행
#             UPSERT state='잠김' → 커밋
#   T1 커밋   → `잠김` ∧ 유효 grant 1건 = **불변식 위반**
#
# 그래서 두 쓰기 경로의 **첫 문장**이 데이터셋 단위 `pg_advisory_xact_lock` 을 잡는다.
# 이 시험은 그 잠금이 실제로 **막는지**를 잰다 — 두 세션을 동시에 열고, T2 가 T1 커밋
# 전에 끝나지 않음을 확인한 뒤, 커밋 순서를 강제하고 불변식을 센다.
def test_approval_and_lowering_cannot_interleave(session_factory, sql) -> None:
    """두 세션이 겹쳐도 `잠김` ∧ 유효 grant = 0건. **잠금이 없으면 red 다.**"""
    import threading

    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    from colab_core.domains import d2_access

    # 요청 한 줄을 미리 세워 둔다 — 승인 경로가 소비할 재료다.
    request_id = "0000000000000000000000AR90"
    sql("""
        INSERT INTO d2_dataset_access_request
          (id, lab_id, dataset_id, requester_account_id, reason)
        VALUES (:id, current_lab_id(), :ds, :requester, '동시성 시험')
    """, {"id": request_id, "ds": DS_A2, "requester": ACC_A_RES},
        account_id=ACC_A_PROF)

    def opened(account_id: str):
        s = session_factory()
        s.begin()
        apply_scope(s, Subject(account_id=Ulid(account_id), lab_id=Ulid(LAB_A)))
        return s

    t1 = opened(ACC_A_PROF)       # 승인
    t2 = opened(ACC_A_PROF)       # 내림
    lowered: list = []
    failed: list = []

    def lower() -> None:
        try:
            lowered.append(d2_access.set_access_state(
                t2, dataset_id=Ulid(DS_A2), state="잠김"))
            t2.commit()
        except Exception as exc:      # noqa: BLE001 — 실패 원인을 본체로 옮긴다
            failed.append(exc)
            t2.rollback()

    try:
        d2_access.decide_access_request(
            t1, request_id=request_id, decider_id=Ulid(ACC_A_PROF),
            approve=True, rejection_reason=None)
        # T1 은 아직 커밋 전이다 — 여기서 T2 를 띄운다.
        worker = threading.Thread(target=lower, daemon=True)
        worker.start()
        worker.join(timeout=2.0)
        assert worker.is_alive(), \
            "내림이 승인 트랜잭션 커밋 전에 끝났다 — 데이터셋 단위 잠금이 없다."
        t1.commit()
        worker.join(timeout=10.0)
        assert not worker.is_alive(), "잠금 해제 뒤에도 내림이 끝나지 않았다."
        assert not failed, f"내림이 예외로 끝났다: {failed!r}"
        # 잠금이 걸렸으므로 T2 의 만료가 T1 의 grant 를 **본다**.
        assert lowered == [1], f"끊긴 사람 수가 1 이 아니다: {lowered!r}"
    finally:
        for s in (t1, t2):
            try:
                s.rollback()
            finally:
                s.close()

    rows = sql("""
        SELECT count(*) AS n
          FROM d2_dataset_access a
         WHERE a.state = '잠김'
           AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                        WHERE g.dataset_id = a.dataset_id AND g.expires_at > now())
    """)
    assert rows[0]["n"] == 0, "승인 ∥ 내림이 겹쳐 잠김 ∧ 유효 grant 가 생겼다."
