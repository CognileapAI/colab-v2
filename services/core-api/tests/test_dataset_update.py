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
def test_a_missing_summary_can_be_filled_through_the_public_path(p2_client, sql) -> None:
    """**이것이 `#36` 이 열려 있던 이유다.**

    `D-01`·`D-02` 의 `summary` 가 `NULL` 인 것은 코드 결함이 아니라 화면 적재 시
    선택 입력 공백이었다(`〈115〉-㉱`). 그런데 **채울 수단이 없었다** — `updateDataset`
    501 · `deleteDataset` 501 · 재적재는 12 → 14 를 만들고 · DB 직접 UPDATE 는
    `㊾-③` 위반. **공개 경로 하나가 그 넷을 다 대체한다.**

    ⭑ **⟨19차 해제 · PRD-15 · WU-A4⟩ 그 상태를 등록 경로로는 더 못 만든다** — 설명이
    필수가 되어서다. 그래도 **이미 있는 행은 그대로 남으므로**(미결-5 ⓐ · `NOT NULL` 금지)
    이 창구는 그대로 필요하다. 그래서 시험이 과거 상태를 DB 로 재현해 잰다.
    """
    client = p2_client()
    dataset_id = _new_dataset(client, "설명 없이 올린 자료")
    sql("UPDATE d3_dataset_description SET summary = NULL WHERE dataset_id = :d",
        {"d": dataset_id})
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
    """**생략과 `null` 은 다르다.** 명시적 `null` 은 「비워라」다.

    ⭑ **⟨개정 2026-09-05 · 19차 해제 · PRD-15 · WU-A4⟩ `summary` 는 이 규칙에서 빠졌다.**
    설명이 필수가 되어 「비워라」의 뜻 자체가 없어졌다(`type: string, minLength: 1`).
    **규칙이 없어진 것이 아니라 적용 칸이 줄었다** — 그래서 여기서 재는 칸을
    `sourceLabel` 로 옮긴다. 「생략 ≠ `null`」이 여전히 성립함을 그 칸이 증명하고,
    설명 쪽이 400 이 되는 것은 `test_summary_required.py` 가 따로 잰다.
    """
    client = p2_client()
    dataset_id = _new_dataset(client, "원천 표기 있는 자료", sourceLabel="지울 표기")
    assert _detail(client, dataset_id)["basicInfo"]["sourceLabel"] == "지울 표기"
    assert _patch(client, dataset_id, {"sourceLabel": None}).status_code == 200
    assert _detail(client, dataset_id)["basicInfo"]["sourceLabel"] is None


def test_an_empty_body_is_a_no_op_not_an_error(p2_client) -> None:
    """고칠 것이 없다고 400 을 내지 않는다 — 화면이 저장을 눌렀을 뿐이다."""
    client = p2_client()
    dataset_id = _new_dataset(client, "그대로 둘 자료")
    assert _patch(client, dataset_id, {}).status_code == 200


# ══════════════ ③ 가공 단계 — 사람이 고르는 경로가 없다 (`〈194〉` 「예외 없음」) ══════════════
def test_the_level_cannot_be_chosen_through_the_update_path(p2_client) -> None:
    """**`LV-1`** — `DatasetUpdate` 에 `processingLevel` 이 없다.

    종전에는 사람이 고른 값을 실으면 200 이었고 그 값이 자동 보정을 이겼다
    (`POL-020` 예외 · `TC-W-001`). `〈194〉`(2026-08-29 Ted)가 그 예외를 없앴다 —
    **레벨은 언제나 계보에서 나온다.** 그래서 이제 계약에 없는 필드이고 400 이다.
    """
    client = p2_client()
    dataset_id = _new_dataset(client, "가공 단계를 고르려는 자료")
    r = _patch(client, dataset_id, {"processingLevel": 1})
    assert r.status_code == 400, r.text
    assert "processingLevel" not in r.json().get("detail", {}).get("allowed", [])
    # 상한 밖 값도 「범위 위반」이 아니라 **없는 필드**로 떨어진다.
    assert _patch(client, dataset_id, {"processingLevel": 3}).status_code == 400
    assert _patch(client, dataset_id, {"processingLevel": None}).status_code == 400


def test_the_level_always_follows_the_lineage(p2_client) -> None:
    """**파생이 언제나 이긴다** — 덮을 사람 값이 존재하지 않기 때문이다."""
    client = p2_client()
    parent = _new_dataset(client, "부모 자료")          # 부모 없음 → Lv0
    child = _new_dataset(client, "자식 자료")
    assert _detail(client, child)["processingLevel"] == 0, "부모가 없으면 파생은 Lv0"
    assert _add_parent(client, child, parent, parentRole="주입력",
                       method="집계").status_code == 201
    assert _detail(client, child)["processingLevel"] == 1, (
        "계보를 이으면 파생값이 그대로 따라와야 한다")


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
    before = _detail(client, dataset_id)["summary"]
    r = _patch(client, dataset_id, {"summary": "스위치 없는 사람이 적은 설명"})
    assert r.status_code == 403, "스위치 없는 사람이 데이터셋 정보를 고쳤다"
    # ⭑ 등록이 설명을 요구하게 되어(19차 · PRD-15) 이 행은 더 이상 `None` 으로 시작하지
    #    않는다. 재는 것은 **값이 안 바뀌었다**이지 「값이 없다」가 아니다.
    assert _detail(client, dataset_id)["summary"] == before, "막혔다면서 값이 바뀌었다"
