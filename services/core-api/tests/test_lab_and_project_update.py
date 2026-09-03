"""`updateLab` · `updateProject` — **올린 뒤 고치는 길을 연구실·프로젝트에도 연다.**

`PLAN-SoT §9 〈149〉-㉱` 가 남긴 결손 2건이다. `〈127〉`·㈏ 가 **데이터셋**에서 연
「올린 뒤 고치는 길」이 **연구실·프로젝트에는 없었다** — 이름을 잘못 적으면 고칠 수단이
없고, `deleteProject` 도 501 이라 지울 수도 없다. **되돌릴 수 없는 제품은 사람이
조심하느라 안 쓰게 된다.**

계약은 이미 완비다(`LabUpdate`·`ProjectUpdate`) — **개정 없이 501 만 걷는다.**

⚠ **프로젝트 이름은 수정 시점에도 중복을 검사해야 한다.** 결정 2-6 이 연구실 단위
유니크를 정했고, 2-7 이 그 함정을 미리 적었다 — **「생성 시점에만 검사하고 수정
시점에 빠뜨리면 유니크 제약의 우회로가 된다」.**
"""
from __future__ import annotations

from conftest import ACC_A_RES, TOKEN_PROF, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX


def _lab(client, token=TOKEN_PROF) -> dict:
    r = client.get(f"{API_PREFIX}/lab", headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def _patch_lab(client, body: dict, token=TOKEN_PROF):
    return client.patch(f"{API_PREFIX}/lab", json=body, headers=auth(token))


def _new_project(client, name: str, token=TOKEN_RES):
    return client.post(f"{API_PREFIX}/projects",
                       json={"type": "국가과제", "name": name}, headers=auth(token))


def _patch_project(client, project_id: str, body: dict, token=TOKEN_RES):
    return client.patch(f"{API_PREFIX}/projects/{project_id}", json=body,
                        headers=auth(token))


# ══════════════════ ① 연구실 정보 — E-01⑦ ══════════════════
def test_the_lab_name_can_finally_be_corrected(p2_client) -> None:
    """**이름을 잘못 적으면 고칠 수단이 없었다.**

    그 이름은 연구실 전환기와 업로드 모달 헤더가 읽는다(`DataModel §2`) — 틀리면
    화면 여러 곳이 함께 틀린다.
    """
    client = p2_client()
    before = _lab(client)["name"]
    r = _patch_lab(client, {"name": "고려대학교 수문학연구실"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "고려대학교 수문학연구실"
    assert _lab(client)["name"] == "고려대학교 수문학연구실"
    _patch_lab(client, {"name": before})          # 다음 시험을 위해 되돌린다


def test_lab_profile_fields_are_editable(p2_client) -> None:
    """소개·지도교수 같은 칸도 고칠 수 있어야 한다 — `LabUpdate` 가 받는 값들이다."""
    client = p2_client()
    r = _patch_lab(client, {"university": "고려대학교", "principalInvestigator": "전창현",
                            "introduction": "수문학 연구 데이터"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["university"] == "고려대학교"
    assert body["principalInvestigator"] == "전창현"


def test_an_empty_lab_name_is_refused(p2_client) -> None:
    """이름은 비울 수 없다 — DB CHECK 이 그렇고 화면도 그렇다."""
    assert _patch_lab(p2_client(), {"name": "   "}).status_code == 400


def test_editing_the_lab_needs_the_switch(p2_client) -> None:
    """**`연구실 설정` 스위치가 켜진 사람만**(`P-2` 행동표 · 계약 산문)."""
    r = _patch_lab(p2_client(), {"name": "연구원이 바꾼 이름"}, token=TOKEN_RES)
    assert r.status_code == 403, "스위치 없는 사람이 연구실 이름을 바꿨다"


def test_a_field_outside_the_contract_is_refused_on_lab(p2_client) -> None:
    """`additionalProperties: false` 를 서버가 지킨다 — `openedAt` 은 고치는 값이 아니다."""
    assert _patch_lab(p2_client(), {"openedAt": "2020-01-01"}).status_code == 400


# ══════════════════ ② 프로젝트 정보 — E-05③ ══════════════════
def test_a_project_can_be_corrected(p2_client) -> None:
    """`〈149〉-㉱` 의 결손. 백로그 `B-02` 가 가리키던 자리다."""
    client = p2_client()
    pid = _new_project(client, "오타 프로젝트").json()["projectId"]
    r = _patch_project(client, pid, {"name": "바로잡은 프로젝트",
                                     "description": "설명을 나중에 적는다"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "바로잡은 프로젝트"


def test_the_project_type_cannot_be_changed(p2_client) -> None:
    """**「유형은 없다 — 만든 뒤에는 바꾸지 않는다」**(`ProjectUpdate` 산문 그대로)."""
    client = p2_client()
    pid = _new_project(client, "유형 고정 확인").json()["projectId"]
    assert _patch_project(client, pid, {"type": "논문"}).status_code == 400


def test_renaming_onto_an_existing_name_is_refused(p2_client) -> None:
    """⚠ **2-7 이 미리 적은 함정이다.**

    「생성 시점에만 검사하고 **수정 시점에 빠뜨리면 유니크 제약의 우회로가 된다**」.
    이름 중복 차단은 결정 #11(빠른 생성 전원 개방)로 **유일한 방어선**이 됐다(2-6).
    """
    client = p2_client()
    _new_project(client, "먼저 있던 이름")
    pid = _new_project(client, "나중에 만든 이름").json()["projectId"]
    r = _patch_project(client, pid, {"name": "먼저 있던 이름"})
    assert r.status_code == 409, "수정으로 이름 중복을 만들 수 있다 — 2-6 의 우회로다"
    assert "이미" in r.text


def test_creating_a_duplicate_name_is_refused(p2_client) -> None:
    """`VAL-010` — 「같은 이름의 프로젝트가 이미 있어요」. **생성 쪽도 막혀 있어야 한다.**"""
    client = p2_client()
    _new_project(client, "중복 확인용 이름")
    r = _new_project(client, "중복 확인용 이름")
    assert r.status_code == 409, r.text


def test_renaming_to_its_own_name_is_fine(p2_client) -> None:
    """**자기 이름으로 저장하는 것은 중복이 아니다.** 설명만 고치려는 사람을 막지 않는다."""
    client = p2_client()
    pid = _new_project(client, "그대로 둘 이름").json()["projectId"]
    r = _patch_project(client, pid, {"name": "그대로 둘 이름", "description": "설명만 고친다"})
    assert r.status_code == 200, r.text


def test_omitted_keys_are_left_alone_on_project(p2_client) -> None:
    """부분 수정이다 — `updateDataset` 과 같은 규칙(`〈127〉`)."""
    client = p2_client()
    pid = _new_project(client, "부분 수정 확인").json()["projectId"]
    _patch_project(client, pid, {"description": "설명"})
    r = client.get(f"{API_PREFIX}/projects/{pid}", headers=auth(TOKEN_RES))
    assert r.json()["name"] == "부분 수정 확인", "보내지 않은 열쇠가 바뀌었다"


def test_an_unknown_project_is_404(p2_client) -> None:
    assert _patch_project(p2_client(), "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                          {"name": "x"}).status_code == 404


def test_editing_a_project_needs_the_switch(p2_client, sql) -> None:
    """**계약이 선언한 `403` 을 서버가 실제로 낸다.**

    `프로젝트 생성` 스위치 하나가 이 화면의 **모든 쓰기 동작**을 가른다
    (`Policy_프로젝트 §6` · `P-6`). 형제 op(`createProject`·`linkProjectDataset`)은
    이미 그 스위치로 막는데 이 op 만 판정 없이 통과했다.
    """
    client = p2_client()
    pid = _new_project(client, "스위치 확인용 프로젝트").json()["projectId"]
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '프로젝트 생성'",
        {"a": ACC_A_RES})
    r = _patch_project(client, pid, {"name": "스위치 없는 사람이 바꾼 이름"})
    assert r.status_code == 403, "스위치 없는 사람이 프로젝트 정보를 고쳤다"
    after = client.get(f"{API_PREFIX}/projects/{pid}", headers=auth(TOKEN_RES))
    assert after.json()["name"] == "스위치 확인용 프로젝트", "막혔다면서 값이 남았다"


# ══════════════════ ③ 기간 — `CODE-REVIEW-20260903` #7 ══════════════════════
def test_a_period_can_be_set_and_read_back(p2_client) -> None:
    """**기간이 실린 수정이 전부 500 이었다.**

    라우트가 `_period()` 로 만든 `date` 를 **버리고**(주석 「형식 검사만」) 도메인은 계약의
    `YYYY-MM` 문자열을 `date` 열에 그대로 바인딩했다 — `'2026-01'::date` 는 파싱 오류다.
    `create_project` 는 처음부터 `_period()` 의 값을 넘겼다 — **두 경로가 갈려 있던 것**이다.
    """
    client = p2_client()
    pid = _new_project(client, "기간을 적는 프로젝트").json()["projectId"]

    r = _patch_project(client, pid, {"period": {"start": "2026-01", "end": "2026-12"}})
    assert r.status_code == 200, r.text
    assert r.json()["period"] == {"start": "2026-01", "end": "2026-12"}

    after = client.get(f"{API_PREFIX}/projects/{pid}", headers=auth(TOKEN_RES))
    assert after.json()["period"] == {"start": "2026-01", "end": "2026-12"}, \
        "응답에는 있고 저장에는 없다 — 화면이 고쳤다고 믿고 떠난다."


def test_a_period_change_does_not_roll_back_its_neighbours(p2_client) -> None:
    """한 요청에 함께 실린 값이 기간 때문에 사라지지 않는다 — 500 은 전부를 롤백했다."""
    client = p2_client()
    pid = _new_project(client, "기간과 이름을 함께 고치는 프로젝트").json()["projectId"]
    r = _patch_project(client, pid, {"name": "기간과 함께 바뀐 이름",
                                     "period": {"start": "2025-03", "end": None}})
    assert r.status_code == 200, r.text
    after = client.get(f"{API_PREFIX}/projects/{pid}", headers=auth(TOKEN_RES)).json()
    assert after["name"] == "기간과 함께 바뀐 이름"
    assert after["period"] == {"start": "2025-03", "end": None}


def test_clearing_the_period_is_null(p2_client) -> None:
    """**비우는 뜻은 `period: null` 이다** — 열쇠 생략(그대로 두기)과 다르다."""
    client = p2_client()
    pid = _new_project(client, "기간을 지우는 프로젝트").json()["projectId"]
    _patch_project(client, pid, {"period": {"start": "2026-01", "end": "2026-12"}})
    r = _patch_project(client, pid, {"period": None})
    assert r.status_code == 200, r.text
    assert r.json()["period"] is None


def test_a_malformed_period_is_still_400(p2_client) -> None:
    """형식 검사는 그대로다 — **넓히지 않았음**을 함께 잰다."""
    client = p2_client()
    pid = _new_project(client, "형식이 틀린 기간").json()["projectId"]
    assert _patch_project(client, pid, {"period": {"start": "2026-13"}}).status_code == 400
    assert _patch_project(client, pid, {"period": "2026-01"}).status_code == 400
