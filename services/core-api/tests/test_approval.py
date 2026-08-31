"""승인 처리 (WU-P6) — 접근 요청 · Verified 두 갈래의 실동작과 **음성 다섯**.

오라클은 전부 정본 `Policy_승인_처리`(v1.7) 축자다. 이 파일이 인용하는 조항 —

  §1.2  처리하는 사람 ｜ Verified: **교수만** ｜ 접근 요청: **교수 + `승인 위임` 연구원**
        거절 ｜ Verified: **없음 (승인 / 미승인)** ｜ 접근 요청: **있음 (사유 필수)**
  §1.3-6 접근 승인의 범위는 **데이터 한 건**이고 유효 기간은 **6개월**이다
  §5    요청 사유 0~300자 선택 · 거절 사유 1~300자 **필수** · 취소 사유 0~120자 선택
  §7.2  검토 대기 → 승인됨(허용 목록 추가 · 만료일 = 승인일 + 6개월) / 거절됨(사유 그대로)
  §9    이미 처리된 요청을 다시 처리 → 「이미 처리된 요청이에요」

**음성이 이 파일의 중심이다.** 승인 흐름의 실패는 「승인이 안 된다」로 오지 않고
「안 해야 할 사람에게 열렸다」로 오는데, 그건 화면에서 조용하다.

이 파일이 501 표에서 빼 온 여덟 op — `tests/test_not_implemented.py` 의 `P6_REAL` 이
이 이름들을 여기서 찾는다. **뺀 자리마다 실동작 시험이 있다**는 규칙의 실물이다.

  접근 요청  `createAccessRequest` · `listPendingAccessRequests`
             `approveAccessRequest` · `rejectAccessRequest`
  Verified   `requestVerification` · `listPendingVerificationRequests`
             `approveVerification` · `cancelVerification`
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import text

from conftest import (ACC_A_PROF, ACC_A_RES, DS_A1, DS_A2, DS_B1, TOKEN_B, TOKEN_PROF,
                      TOKEN_RES, auth)

PREFIX = "/api/v1"


def _iso(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _months_between(start: dt.datetime, end: dt.datetime) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


# ── 접근 요청 — 성공 경로 ─────────────────────────────────────────────────────

def test_a_locked_dataset_can_be_requested_and_the_pending_chip_turns_on(live_client):
    """요청 보내기 → 201, 그리고 **상세의 안내 줄이 검토 대기로 바뀐다** (계약 `createAccessRequest` 산문).

    `accessRequestPending` 은 저장처가 없던 동안 서버가 **항상 false** 를 내리던 자리다
    (`routes/catalog.py:596` 종전 주석). 그 false 가 참이 되는 것이 이 시험의 요점이다.
    """
    before = live_client.get(f"{PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES)).json()
    assert before["bodyAccessible"] is False
    assert before["accessRequestPending"] is False
    assert before["actions"]["canRequestAccess"] is True

    made = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                            headers=auth(TOKEN_RES), json={"reason": "격자화에 쓰려고 한다"})
    assert made.status_code == 201, made.text
    body = made.json()
    assert set(body) == {"requestId", "dataset", "requester", "requestedAt", "reason"}
    assert body["dataset"]["datasetId"] == DS_A2
    assert body["requester"]["accountId"] == ACC_A_RES
    assert body["reason"] == "격자화에 쓰려고 한다"

    after = live_client.get(f"{PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES)).json()
    assert after["accessRequestPending"] is True, "요청을 보냈는데 검토 대기 칩이 안 켜진다."
    # **요청만으로 본체가 열리지는 않는다** — 아래 음성 ②가 같은 것을 다른 층에서 본다.
    assert after["bodyAccessible"] is False


def test_the_reason_is_optional_and_capped_at_300(live_client):
    """요청 사유는 **0~300자 선택**이다 (§5). 없어도 되고, 넘으면 거절한다."""
    made = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                            headers=auth(TOKEN_RES))
    assert made.status_code == 201, made.text
    assert made.json()["reason"] is None

    too_long = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                                headers=auth(TOKEN_PROF), json={"reason": "가" * 301})
    assert too_long.status_code == 400


def test_a_second_request_while_one_is_pending_is_a_409(live_client):
    """「이미 검토 대기 중이거나 이미 볼 수 있는 데이터다」 (계약 409 · §9)."""
    first = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests", headers=auth(TOKEN_RES))
    assert first.status_code == 201
    again = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests", headers=auth(TOKEN_RES))
    assert again.status_code == 409


def test_requesting_access_to_an_open_dataset_is_a_409(live_client):
    """이미 볼 수 있는 데이터에는 요청할 자리가 없다 (계약 409)."""
    made = live_client.post(f"{PREFIX}/datasets/{DS_A1}/access-requests", headers=auth(TOKEN_RES))
    assert made.status_code == 409


def test_approval_writes_the_allow_list_row_and_opens_the_body(live_client, sql):
    """승인 → 허용 목록 한 줄 · **만료일 = 승인일 + 6개월** · 그 순간 본체가 열린다 (§1.3-6 · §7.2).

    허용 줄이 있으면 본체가 열린다는 것은 `test_body_access.py` 가 이미 증명했다.
    여기서 새로 증명하는 것은 **승인 op 이 그 줄을 실제로 쓴다**는 것 하나다.
    """
    request_id = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                                  headers=auth(TOKEN_RES)).json()["requestId"]

    approved = live_client.post(f"{PREFIX}/access-requests/{request_id}/approval",
                                headers=auth(TOKEN_PROF))
    assert approved.status_code == 200, approved.text
    grant = approved.json()
    assert set(grant) == {"dataset", "grantee", "approver", "approvedAt", "expiresAt"}
    assert grant["dataset"]["datasetId"] == DS_A2
    assert grant["grantee"]["accountId"] == ACC_A_RES
    assert grant["approver"]["accountId"] == ACC_A_PROF
    assert _months_between(_iso(grant["approvedAt"]), _iso(grant["expiresAt"])) == 6, \
        "유효 기간이 6개월이 아니다 (§1.3-6)."

    # 응답이 그럴듯한 것과 행이 남은 것은 다른 질문이다 (conftest `sql` 주석).
    rows = sql("""SELECT grantee_account_id, expires_at > now() AS alive
                    FROM d2_dataset_access_grant WHERE dataset_id = :d""", {"d": DS_A2})
    assert [(r["grantee_account_id"].strip(), r["alive"]) for r in rows] == [(ACC_A_RES, True)]

    detail = live_client.get(f"{PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES)).json()
    assert detail["bodyAccessible"] is True, "승인했는데 본체가 안 열렸다."
    assert detail["accessRequestPending"] is False, "처리가 끝났는데 검토 대기 칩이 남았다."
    assert live_client.get(f"{PREFIX}/datasets/{DS_A2}/files",
                           headers=auth(TOKEN_RES)).status_code == 200


def test_rejection_needs_a_reason_and_carries_it_back(live_client, sql):
    """거절 사유는 **1~300자 필수**다 (§5 · P-26). 사유 없이 누르면 400 이다 (§9 첫 줄)."""
    request_id = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                                  headers=auth(TOKEN_RES)).json()["requestId"]

    blank = live_client.post(f"{PREFIX}/access-requests/{request_id}/rejection",
                             headers=auth(TOKEN_PROF), json={"reason": ""})
    assert blank.status_code == 400
    missing = live_client.post(f"{PREFIX}/access-requests/{request_id}/rejection",
                               headers=auth(TOKEN_PROF), json={})
    assert missing.status_code == 400

    done = live_client.post(f"{PREFIX}/access-requests/{request_id}/rejection",
                            headers=auth(TOKEN_PROF), json={"reason": "원자료를 먼저 보라"})
    assert done.status_code == 204, done.text

    rows = sql("""SELECT state, rejection_reason FROM d2_dataset_access_request
                   WHERE id = :i""", {"i": request_id})
    assert rows[0]["state"] == "거절됨"
    assert rows[0]["rejection_reason"] == "원자료를 먼저 보라", "사유가 그대로 전달되지 않았다."

    # **거절은 본체를 열지 않는다.**
    detail = live_client.get(f"{PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES)).json()
    assert detail["bodyAccessible"] is False


def test_a_decided_request_cannot_be_decided_again(live_client):
    """「이미 처리된 요청이에요」 (§9). 승인 뒤에도 거절 뒤에도 같다."""
    rid = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                           headers=auth(TOKEN_RES)).json()["requestId"]
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/approval",
                            headers=auth(TOKEN_PROF)).status_code == 200
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/approval",
                            headers=auth(TOKEN_PROF)).status_code == 409
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/rejection",
                            headers=auth(TOKEN_PROF), json={"reason": "늦었다"}).status_code == 409


def test_the_pending_list_is_oldest_first_and_only_for_approvers(live_client):
    """받은 접근 요청 — **오래된 순**(§1.3 「방치를 막기 위해서다」)이고 처리 권한자만 받는다 (§6)."""
    first = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                             headers=auth(TOKEN_RES)).json()["requestId"]
    second = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                              headers=auth(TOKEN_PROF)).json()["requestId"]

    listed = live_client.get(f"{PREFIX}/access-requests/pending", headers=auth(TOKEN_PROF))
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert set(body) == {"items", "totalCount", "nextCursor"}
    ids = [i["requestId"] for i in body["items"]]
    assert ids.index(first) < ids.index(second), "오래된 것이 위로 오지 않는다."
    assert body["totalCount"] >= 2


# ── Verified — 성공 경로 (요청 → 승인 → 취소 왕복) ────────────────────────────

def test_the_verified_round_trip_uses_its_own_ops_only(live_client, sql):
    """취소 → 요청 → 승인. **세 자리가 정본 §8 헤더 행의 ①②③ 그대로다.**

    `canApproveVerification` 은 검토 대기의 저장처가 없던 동안 **항상 false** 였다
    (`routes/catalog.py:608` 종전 주석). 그 값이 참이 되는 것이 이 시험의 요점이다.
    """
    # ③ 승인됨 + 교수 → 승인 취소. 데이터와 계보는 남고 배지만 사라진다 (§1.3-9).
    cancelled = live_client.post(f"{PREFIX}/datasets/{DS_A1}/verification-cancellation",
                                 headers=auth(TOKEN_PROF), json={"reason": "격자 정합을 다시 본다"})
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["verified"] is False
    assert cancelled.json()["cancellationReason"] == "격자 정합을 다시 본다"
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge")[0]["n"] >= 1, "계보까지 지웠다."

    # ① 미승인 + 올린 사람 → `✓ 승인 요청`. A1 이 DSA1 의 올린 사람이다 (seed.sql:41).
    header = live_client.get(f"{PREFIX}/datasets/{DS_A1}", headers=auth(TOKEN_RES)).json()
    assert header["actions"]["canRequestVerification"] is True
    asked = live_client.post(f"{PREFIX}/datasets/{DS_A1}/verification-request",
                             headers=auth(TOKEN_RES))
    assert asked.status_code == 202, asked.text
    assert set(asked.json()) == {"dataset", "requester", "requestedAt"}

    # ② 검토 대기 + 교수 → `승인`.
    prof_view = live_client.get(f"{PREFIX}/datasets/{DS_A1}", headers=auth(TOKEN_PROF)).json()
    assert prof_view["actions"]["canApproveVerification"] is True, \
        "검토 대기가 생겼는데 교수의 승인 자리가 안 켜진다."
    pending = live_client.get(f"{PREFIX}/verification-requests/pending", headers=auth(TOKEN_PROF))
    assert pending.status_code == 200
    assert DS_A1 in [i["dataset"]["datasetId"] for i in pending.json()["items"]]

    approved = live_client.post(f"{PREFIX}/datasets/{DS_A1}/verification",
                                headers=auth(TOKEN_PROF))
    assert approved.status_code == 200, approved.text
    assert approved.json()["verified"] is True
    assert approved.json()["approver"]["accountId"] == ACC_A_PROF
    assert live_client.post(f"{PREFIX}/datasets/{DS_A1}/verification",
                            headers=auth(TOKEN_PROF)).status_code == 409


def test_a_verification_request_has_no_rejection_surface(live_client):
    """Verified 에는 **거절이 없다** (§1.2 축자 「거절 ｜ 없음 (승인 / 미승인)」).

    거절 경로를 만들지 않았다는 것을 계약과 라우트 양쪽에서 못 박는다 — 나중에
    「대칭이니까」로 붙는 것을 막는다.
    """
    import yaml

    from conftest import CONTRACT
    paths = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))["paths"]
    assert not [p for p in paths if "verification" in p and "rejection" in p]


# ══ 음성 다섯 ═══════════════════════════════════════════════════════════════
# 정본이 금지한 것을 **실행해 보고 막히는지** 본다. 「안 만들었으니 안 될 것」은 오라클이 아니다.

def test_negative_1_requests_and_approvals_never_cross_the_lab_boundary(live_client, sql):
    """① 남의 연구실로 새지 않는다 — 요청도, 목록도, 승인도.

    red 만드는 법 — `d2_dataset_access_request` 의 `lab_boundary` 정책을 지운다.
    """
    # B 연구실 교수는 A 의 잠긴 데이터셋을 **존재로도** 못 본다 (404, 403 이 아니다).
    assert live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                            headers=auth(TOKEN_B)).status_code == 404
    # A 에서 만든 검토 대기가 B 의 할 일 함에 **한 건도** 안 섞인다.
    rid = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                           headers=auth(TOKEN_RES)).json()["requestId"]
    b_list = live_client.get(f"{PREFIX}/access-requests/pending", headers=auth(TOKEN_B))
    assert b_list.status_code == 200
    assert [i for i in b_list.json()["items"] if i["requestId"] == rid] == []
    assert b_list.json()["totalCount"] == 0
    # id 를 그대로 알아도 B 는 승인할 수 없다 — 목록에서 가린 것이 아니라 없는 것이다.
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/approval",
                            headers=auth(TOKEN_B)).status_code == 404
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/rejection",
                            headers=auth(TOKEN_B), json={"reason": "남의 것"}).status_code == 404
    # 그리고 B 쪽 데이터셋은 A 가 못 만진다 (반대 방향도 본다).
    assert live_client.post(f"{PREFIX}/datasets/{DS_B1}/access-requests",
                            headers=auth(TOKEN_PROF)).status_code == 404
    assert sql("""SELECT count(*) AS n FROM d2_dataset_access_grant
                   WHERE dataset_id = :d""", {"d": DS_B1})[0]["n"] == 0


def test_negative_2_a_pending_request_does_not_open_the_body(live_client):
    """② 승인 없이는 본문이 열리지 않는다 — **요청 중**도 열림이 아니다.

    red 만드는 법 — `createAccessRequest` 가 허용 줄까지 같이 쓰게 한다
    (요청과 승인을 한 op 으로 합치는 흔한 지름길이 정확히 이 형태다).
    """
    live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests", headers=auth(TOKEN_RES))
    detail = live_client.get(f"{PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES)).json()
    assert detail["accessRequestPending"] is True
    assert detail["bodyAccessible"] is False, "요청만으로 본체가 열렸다."
    assert detail["actions"]["canDownload"] is False
    assert live_client.get(f"{PREFIX}/datasets/{DS_A2}/files",
                           headers=auth(TOKEN_RES)).status_code == 403


def test_negative_3_an_expired_grant_does_not_open_the_body(live_client, sql):
    """③ 만료된 허용 줄은 열지 않는다 (P-25 · §7.2 「승인됨 → 만료됨」).

    승인 op 이 쓴 줄의 만료일을 과거로 밀어 **만료만** 바꾼다 — 줄은 그대로 있다.
    red 만드는 법 — `d2_access.py` 의 `_ACCESS` 에서 `g.expires_at > now()` 를 지운다.
    """
    rid = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                           headers=auth(TOKEN_RES)).json()["requestId"]
    live_client.post(f"{PREFIX}/access-requests/{rid}/approval", headers=auth(TOKEN_PROF))
    assert live_client.get(f"{PREFIX}/datasets/{DS_A2}",
                           headers=auth(TOKEN_RES)).json()["bodyAccessible"] is True

    # **승인 시각도 함께 뒤로 민다.** `CHECK (expires_at > approved_at)` 이 P0 부터 걸려 있어
    # 만료일만 과거로 밀면 DB 가 거부한다 — 그 거부가 옳다(승인보다 먼저 끝나는 허용은 없다).
    # 그래서 「7개월 전에 승인돼 어제 만료된 줄」이라는 **실제로 있을 수 있는 상태**를 만든다.
    sql("""UPDATE d2_dataset_access_grant
              SET approved_at = now() - interval '7 months',
                  expires_at  = now() - interval '1 day'
            WHERE dataset_id = :d AND grantee_account_id = :g""",
        {"d": DS_A2, "g": ACC_A_RES})

    detail = live_client.get(f"{PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES)).json()
    assert detail["bodyAccessible"] is False, "만료된 허용 줄이 본체를 열었다."
    assert live_client.get(f"{PREFIX}/datasets/{DS_A2}/files",
                           headers=auth(TOKEN_RES)).status_code == 403
    # 만료됐으면 **다시 요청할 수 있다** (§7.2 마지막 줄 · §1.3-6).
    assert live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                            headers=auth(TOKEN_RES)).status_code == 201

    # ⚠ **이 시험은 자기 뒷정리를 직접 한다.** conftest 의 자동 되돌림은
    # `approved_at >= 시작시각` 으로 지우는데, 위에서 그 열을 **7개월 전으로 밀었으므로**
    # 이 줄만 그물을 빠져나간다. 남기면 다음 시험이 `DSA2` 를 이미 허용된 채로 만나
    # 「권한 없는 승인이 허용 줄을 남겼다」가 거짓으로 뜬다 — 실제로 그렇게 한 번 깨졌다.
    # **시각으로 지우는 그물의 알려진 구멍이고, 시각을 옮기는 시험이 스스로 메운다.**
    sql("""DELETE FROM d2_dataset_access_grant
            WHERE dataset_id = :d AND grantee_account_id = :g""",
        {"d": DS_A2, "g": ACC_A_RES})


def test_negative_4_there_is_no_batch_approval_surface(live_client, subjects_file):
    """④ **[모두 승인] 이 없다** (`CLAUDE.md §3` AI 응답 규격 · 계약 `approveAccessRequest` 산문
    축자 「사람 단위·연구실 단위 일괄 승인 엔드포인트를 두지 않는다」).

    화면에 버튼이 없는 것으로는 부족하다 — **표면 자체가 없어야** 한다. 계약과 실물 라우트
    양쪽을 센다. red 만드는 법 — `/access-requests/approval` 같은 경로를 하나 추가한다.
    """
    import yaml

    from conftest import CONTRACT
    from colab_core.app.main import create_app

    spec = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    decide = [(p, op) for p, item in spec["paths"].items() for op in item
              if op in ("post", "put", "patch")
              and ("approval" in p or "rejection" in p or p.endswith("/verification")
                   or p.endswith("/verification-cancellation"))]
    # 승인·거절을 내는 **모든** 경로가 대상 하나를 경로에 갖는다. 목록을 몸통으로 받는 자리가 없다.
    for path, _ in decide:
        assert "{requestId}" in path or "{datasetId}" in path, \
            f"대상이 경로에 없는 승인 표면이 생겼다 — 일괄 승인의 입구다: {path}"

    banned = ("batch", "bulk", "approve-all")
    from colab_core.kernel.config import Settings
    app = create_app(Settings(database_url="postgresql+psycopg://x/y",
                              subjects_file=subjects_file))
    surfaces = [getattr(r, "path", "") for r in app.routes
                if "access-request" in getattr(r, "path", "")
                or "verification" in getattr(r, "path", "")]
    assert surfaces, "승인 표면을 한 건도 못 찾았다 — 이 시험이 아무것도 안 세고 있다."
    for path in surfaces:
        assert not any(b in path for b in banned), f"일괄 승인 표면이 생겼다: {path}"


def test_negative_5_a_role_without_the_switch_cannot_decide(live_client, sql):
    """⑤ **승인 권한이 없는 역할은 승인할 수 없다** (§6).

    접근 요청 = 교수 + `승인 위임` 연구원. Verified = **교수만, 위임 불가**(§1.2 · P-22).
    시드의 A1 은 `승인 위임` 이 꺼져 있다 (seed.sql:35) — 픽스처를 새로 만들지 않는다.

    red 만드는 법 — 승인 라우트에서 권한 판정을 빼고 로그인만 본다.
    """
    assert sql("""SELECT enabled FROM d2_permission_switch
                   WHERE account_id = :a AND switch = '승인 위임'""",
               {"a": ACC_A_RES})[0]["enabled"] is False

    rid = live_client.post(f"{PREFIX}/datasets/{DS_A2}/access-requests",
                           headers=auth(TOKEN_RES)).json()["requestId"]
    # 위임이 꺼진 연구원은 **자기 요청조차** 승인하지 못한다 (403 — 존재는 인정한다).
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/approval",
                            headers=auth(TOKEN_RES)).status_code == 403
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/rejection",
                            headers=auth(TOKEN_RES), json={"reason": "내가"}).status_code == 403
    assert sql("""SELECT count(*) AS n FROM d2_dataset_access_grant
                   WHERE dataset_id = :d""", {"d": DS_A2})[0]["n"] == 0, \
        "권한 없는 승인이 허용 줄을 남겼다."

    # Verified 는 위임으로도 안 열린다 — 스위치를 켜도 교수가 아니면 막힌다 (P-22).
    sql("""UPDATE d2_permission_switch SET enabled = true
            WHERE account_id = :a AND switch = '승인 위임'""", {"a": ACC_A_RES})
    assert live_client.post(f"{PREFIX}/access-requests/{rid}/approval",
                            headers=auth(TOKEN_RES)).status_code == 200, \
        "`승인 위임` 을 켰는데도 접근 요청 승인이 막힌다 — 과하게 닫혔다."
    assert live_client.post(f"{PREFIX}/datasets/{DS_A1}/verification-cancellation",
                            headers=auth(TOKEN_RES), json={}).status_code == 403, \
        "`승인 위임` 연구원이 Verified 를 만졌다 — 위임 불가다 (§1.2)."
    assert live_client.post(f"{PREFIX}/datasets/{DS_A2}/verification",
                            headers=auth(TOKEN_RES)).status_code == 403
    assert live_client.get(f"{PREFIX}/verification-requests/pending",
                           headers=auth(TOKEN_RES)).status_code == 403, \
        "Verified 검토 대기 그룹이 교수 아닌 사람에게 보인다 (§3.2 경계 예시)."
