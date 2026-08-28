"""`updateDataset` — **올린 뒤에 고치는 길** (`PLAN-SoT §9 〈127〉`·`〈138〉`·`〈140〉`).

Ted 판정 ㈎(2026-08-26) = `#36`(설명 결손 2건)의 해소 수단은 **`updateDataset` 구현**이다.
ⓑ 삭제 후 재적재는 **데이터 손실을 수반**하고, ⓒ 평가셋 기대값 개정은 `〈117〉-㉯` 가
금지한 「결과에 기대를 맞추기」다.

그리고 Ted 판정 ㈏(2026-08-27)로 대상이 넓어졌다 — 종전에는 올린 뒤 고칠 수 있는 것이
**이름·주제·요약 셋뿐**이었고 Lv·원천 표기·변수·좌표계·기간·대표 조각은 못 고쳤다.
`deleteDataset` 도 501 이라 **잘못 올리면 되돌릴 길이 없었다.**

**부분 수정이다.** 보내지 않은 열쇠는 안 건드리고, `null` 을 **명시적으로** 보내는 것은
**비우라는 뜻**이다. 둘을 접으면 「요약만 고치려다 Lv 가 날아가는」 일이 생긴다.
"""
from __future__ import annotations

from conftest import ACC_A_RES, TOKEN_RES, auth
from test_dataset_registration import make_upload, register  # noqa: F401
from test_lineage_confirm import _add_parent, _new_dataset

from colab_core.app.main import API_PREFIX


def _patch(client, dataset_id: str, body: dict, token: str = TOKEN_RES):
    return client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json=body,
                        headers=auth(token))


def _detail(client, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


# ══════════════ ① `#36` 의 실제 문제 — 설명을 채울 공개 경로가 없었다 ══════════════
def test_a_missing_summary_can_be_filled_through_the_public_path(p2_client) -> None:
    """**이것이 `#36` 이 열려 있던 이유다.**

    `D-01`·`D-02` 의 `summary` 가 `NULL` 인 것은 코드 결함이 아니라 화면 적재 시
    선택 입력 공백이었다(`〈115〉-㉱`). 그런데 **채울 수단이 없었다** — `updateDataset`
    501 · `deleteDataset` 501 · 재적재는 12 → 14 를 만들고 · DB 직접 UPDATE 는
    `㊾-③` 위반. **공개 경로 하나가 그 넷을 다 대체한다.**
    """
    client = p2_client()
    dataset_id = _new_dataset(client, "설명 없이 올린 자료")
    assert _detail(client, dataset_id)["summary"] is None

    r = _patch(client, dataset_id, {"summary": "GK-2A NDVI 2 km 한반도 (2024-06-15~24)"})
    assert r.status_code == 200, r.text
    assert r.json()["summary"] == "GK-2A NDVI 2 km 한반도 (2024-06-15~24)"
    assert _detail(client, dataset_id)["summary"] == "GK-2A NDVI 2 km 한반도 (2024-06-15~24)"


# ══════════════ ② 부분 수정 — 안 보낸 것은 안 건드린다 ══════════════
def test_omitted_keys_are_left_alone(p2_client) -> None:
    """**요약만 고치려다 이름이 날아가면 안 된다.**"""
    client = p2_client()
    dataset_id = _new_dataset(client, "원래 이름", topic="강우·강수")
    _patch(client, dataset_id, {"summary": "설명"})
    after = _detail(client, dataset_id)
    assert after["name"] == "원래 이름", "보내지 않은 열쇠는 그대로다"
    assert after["topic"] == "강우·강수"


def test_an_explicit_null_clears_the_value(p2_client) -> None:
    """**생략과 `null` 은 다르다.** 명시적 `null` 은 「비워라」다."""
    client = p2_client()
    dataset_id = _new_dataset(client, "설명 있는 자료", summary="지울 설명")
    assert _detail(client, dataset_id)["summary"] == "지울 설명"
    assert _patch(client, dataset_id, {"summary": None}).status_code == 200
    assert _detail(client, dataset_id)["summary"] is None


def test_an_empty_body_is_a_no_op_not_an_error(p2_client) -> None:
    """고칠 것이 없다고 400 을 내지 않는다 — 화면이 저장을 눌렀을 뿐이다."""
    client = p2_client()
    dataset_id = _new_dataset(client, "그대로 둘 자료")
    assert _patch(client, dataset_id, {}).status_code == 200


# ══════════════ ③ 가공 단계 — 사람이 고른 값은 자동 보정이 덮지 않는다 ══════════════
def test_a_chosen_level_survives_a_later_lineage_change(p2_client) -> None:
    """**`POL-020` 의 예외와 `TC-W-001` 이 요구하는 그대로다.**

    「Lv1 로 직접 선택 → Lv1 부모를 연결 → 보정하지 않음(사람이 정한 값 유지)」.
    """
    client = p2_client()
    parent = _new_dataset(client, "부모 자료")          # 부모 없음 → Lv0
    child = _new_dataset(client, "가공했지만 계보를 안 적은 자료")
    assert _detail(client, child)["processingLevel"] == 0, "부모가 없으면 파생은 Lv0"

    # 가공했는데 계보를 안 적은 사람이 **1 로 고른다** (Ted 2026-08-27).
    assert _patch(client, child, {"processingLevel": 1}).status_code == 200
    assert _detail(client, child)["processingLevel"] == 1

    # 나중에 계보를 이어도 **사람이 고른 값이 이긴다.**
    assert _add_parent(client, child, parent, parentRole="주입력",
                       method="집계").status_code == 201
    assert _detail(client, child)["processingLevel"] == 1, (
        "자동 보정이 사람이 고른 값을 덮었다 — POL-020 예외 위반")


def test_clearing_the_choice_returns_to_the_derived_value(p2_client) -> None:
    """`null` 을 보내면 **사람의 선택을 지우고 파생으로 되돌린다.**"""
    client = p2_client()
    parent = _new_dataset(client, "파생 확인용 부모")
    child = _new_dataset(client, "파생 확인용 자식")
    _add_parent(client, child, parent, parentRole="주입력", method="집계")
    assert _detail(client, child)["processingLevel"] == 1

    _patch(client, child, {"processingLevel": 0})
    assert _detail(client, child)["processingLevel"] == 0
    _patch(client, child, {"processingLevel": None})
    assert _detail(client, child)["processingLevel"] == 1, "파생으로 되돌아와야 한다"


def test_a_level_above_the_cap_is_rejected(p2_client) -> None:
    """**`Lv3` 은 정본이 「존재할 수 없는 값」이라 했다**(`VAL-005`·`〈133〉`)."""
    client = p2_client()
    dataset_id = _new_dataset(client, "상한 확인용")
    assert _patch(client, dataset_id, {"processingLevel": 3}).status_code == 400
    assert _patch(client, dataset_id, {"processingLevel": -1}).status_code == 400


# ══════════════ ④ 원천 표기 — 있는데 고칠 길이 없던 값 ══════════════
def test_the_source_label_can_finally_be_corrected(p2_client) -> None:
    """`DatasetCreate` 에는 있는데 `DatasetUpdate` 에 없어서 못 고치던 값이다."""
    client = p2_client()
    dataset_id = _new_dataset(client, "원천 오타 자료")
    assert _patch(client, dataset_id, {"sourceLabel": "ERA5"}).status_code == 200
    assert _detail(client, dataset_id)["basicInfo"]["sourceLabel"] == "ERA5"


# ══════════════ ⑤ 경계 · 계약 ══════════════
def test_a_field_outside_the_contract_is_rejected(p2_client) -> None:
    """`additionalProperties: false` 를 서버가 지킨다 — 조용히 무시하지 않는다."""
    client = p2_client()
    dataset_id = _new_dataset(client, "계약 밖 필드 확인")
    r = _patch(client, dataset_id, {"format": "NetCDF"})
    assert r.status_code == 400, "`format` 은 자동이고 사람이 고칠 수 없다 (VAL-003)"


def test_an_unknown_dataset_is_404(p2_client) -> None:
    assert _patch(p2_client(), "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                  {"summary": "x"}).status_code == 404


def test_editing_a_dataset_needs_the_upload_edit_switch(p2_client, sql) -> None:
    """**계약이 선언한 `403` 을 서버가 실제로 낸다.**

    seam 산문이 못 박은 대로 「`업로드·편집` 스위치가 판정한다」(`〈59〉-②`) —
    형제 op(`createUpload`·`addDatasetFile`)은 이미 그 스위치로 막는데
    이 op 만 판정 없이 통과했다. **화면에서 숨긴 것을 서버가 같은 기준으로 막는다**
    (`P-11`·`P-12`).
    """
    client = p2_client()
    dataset_id = _new_dataset(client, "스위치 확인용 자료")
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'",
        {"a": ACC_A_RES})
    r = _patch(client, dataset_id, {"summary": "스위치 없는 사람이 적은 설명"})
    assert r.status_code == 403, "스위치 없는 사람이 데이터셋 정보를 고쳤다"
    assert _detail(client, dataset_id)["summary"] is None, "막혔다면서 값이 남았다"
