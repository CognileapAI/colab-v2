"""WU-B7 · PRD-05 · PRD-06 — 3축 목록 필터(AND · `미지정`) ＋ 상세 3행.

여기서 재는 것 (`dev-package/prd/rounds/R-B-2-server.md` WU-B7 수용 기준 축자)

  ⑴ `category=수문 인자` 질의 → **그 분류의 데이터셋만** 나온다
  ⑵ 세 축 동시 지정 → **AND** 로 걸린다
  ⑶ 유형 NULL 행이 있을 때 `dataType=미지정` → **그 행이 나온다**
  ⑷ 상세 조회 → 세 값이 **목록 필터 값과 문자열이 같다**
  ⑸ `topic` 파라미터가 **살아 있다**(이관 중 · 신규 사용 금지)
  ⑹ 패싯이 세 축의 값별 건수를 낸다 — 0건 값도 안 사라지고 `미지정` 이 각 축에 있다

⚠ **여기서 재지 않는 것**
  · 화면 문면(`분류 전체` 셀렉트 · 상세 3행 순서) → `frontend/test/axis-filters-20260907.test.tsx`.
  · 색인 재정의·미러 트리거(`M-10`) → `db/platform/tests/0019-drift.sh` · `test_variable_rows.py`.
  · `processingLevel` **정수** 조건의 판정 → `test_lv_parent_rules.py`(WU-B5 · 회귀).
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

#: 값이 NULL 인 행을 고르는 파수꼴. **정본은 서버 상수 한 곳**이다(`catalog.UNSPECIFIED`).
UNSPECIFIED = "미지정"


def _created(client, **body) -> str:
    r = register(client, make_upload(client), **body)
    assert r.status_code == 201, r.text
    return r.json()["datasetId"]


def _ids(client, **params) -> set[str]:
    r = client.get(f"{API_PREFIX}/datasets", params=params, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return {row["datasetId"] for row in r.json()["items"]}


def _detail(client, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def _axes(client, **params) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/facets", params=params, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return {a["axis"]: {v["value"]: v["count"] for v in a["values"]}
            for a in r.json().get("axes", [])}


# ═════════════════════════ ⑴ 한 축 ═══════════════════════════════════
def test_category_filter_returns_only_that_category(p2_client) -> None:
    """⑴ `category=수문 인자` → 그 분류의 데이터셋만 나온다."""
    client = p2_client()
    hydro = _created(client, category="수문 인자", dataType="지상관측자료")
    other = _created(client, category="환경 인자", dataType="지상관측자료")
    ids = _ids(client, category="수문 인자")
    assert hydro in ids, ids
    assert other not in ids, ids


def test_data_type_filter_returns_only_that_type(p2_client) -> None:
    """⑴-b 유형 축도 같은 규율이다 — 세 축은 서로 독립이다(미결-14 ⓐ)."""
    client = p2_client()
    sat = _created(client, category="수문 인자", dataType="위성자료")
    ground = _created(client, category="수문 인자", dataType="지상관측자료")
    ids = _ids(client, dataType="위성자료")
    assert sat in ids and ground not in ids, ids


# ═════════════════════════ ⑵ AND ════════════════════════════════════
def test_the_three_axes_are_combined_with_and(p2_client) -> None:
    """⑵ 세 축 동시 지정은 **AND** 다 — 한 축이라도 어긋나면 안 나온다."""
    client = p2_client()
    match = _created(client, category="수문 인자", dataType="위성자료",
                     processingLevelUserSet="Lv2")
    wrong_type = _created(client, category="수문 인자", dataType="지상관측자료",
                          processingLevelUserSet="Lv2")
    wrong_level = _created(client, category="수문 인자", dataType="위성자료",
                           processingLevelUserSet="Lv1")
    ids = _ids(client, category="수문 인자", dataType="위성자료", processingLevel="2")
    assert match in ids, ids
    assert wrong_type not in ids, ids
    assert wrong_level not in ids, ids


# ═════════════════════════ ⑶ 미지정 파수꼴 ════════════════════════════
def test_unspecified_data_type_finds_the_null_rows(p2_client) -> None:
    """⑶ `dataType=미지정` → **유형이 NULL 인 행**이 나온다.

    재선택이 필요한 행을 사람이 찾아낼 **유일한 경로**다(PRD-05 축자).
    """
    client = p2_client()
    # `dataType=None` 은 등록 required 를 깨므로 등록 뒤 수정으로 비운다 — 기존 행의 상태다.
    blank = _created(client, category="수문 인자", dataType="위성자료")
    r = client.patch(f"{API_PREFIX}/datasets/{blank}", json={"dataType": None},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    filled = _created(client, category="수문 인자", dataType="위성자료")
    ids = _ids(client, dataType=UNSPECIFIED)
    assert blank in ids, ids
    assert filled not in ids, ids


def test_unspecified_category_finds_the_null_rows(p2_client) -> None:
    """⑶-b 분류 축의 파수꼴도 같다."""
    client = p2_client()
    blank = _created(client, category="수문 인자", dataType="위성자료")
    r = client.patch(f"{API_PREFIX}/datasets/{blank}", json={"category": None},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    filled = _created(client, category="수문 인자", dataType="위성자료")
    ids = _ids(client, category=UNSPECIFIED)
    assert blank in ids and filled not in ids, ids


def test_unspecified_processing_level_finds_rows_without_a_human_value(p2_client) -> None:
    """⑶-c 가공 단계 축의 파수꼴 = **사람이 고른 값이 NULL 인 행**이다.

    ⚠ 표시용 `processingLevel` 은 파생값으로 채워지므로 NULL 이 아니다 — 파수꼴이 보는
    것은 **선언의 유무**(`processingLevelUserSet`)이고, 그것이 재선택 대상의 정의다.
    """
    client = p2_client()
    unset = _created(client, category="수문 인자", dataType="위성자료")
    chosen = _created(client, category="수문 인자", dataType="위성자료",
                      processingLevelUserSet="Lv1")
    ids = _ids(client, processingLevel=UNSPECIFIED)
    assert unset in ids, ids
    assert chosen not in ids, ids


def test_the_integer_processing_level_filter_is_unchanged(p2_client) -> None:
    """⑶-d **회귀** — 정수 조건은 한 글자도 바뀌지 않았다(WU-B5)."""
    client = p2_client()
    lv1 = _created(client, category="수문 인자", dataType="위성자료",
                   processingLevelUserSet="Lv1")
    lv3 = _created(client, category="수문 인자", dataType="위성자료",
                   processingLevelUserSet="Lv3")
    ids = _ids(client, processingLevel="1")
    assert lv1 in ids and lv3 not in ids, ids


def test_a_processing_level_that_is_neither_an_integer_nor_the_sentinel_is_400(p2_client) -> None:
    """⑶-e 파수꼴도 정수도 아닌 값은 **400** 이다 — 조용한 빈 결과로 접지 않는다."""
    r = p2_client().get(f"{API_PREFIX}/datasets", params={"processingLevel": "Lv2"},
                        headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


# ═════════════════════════ ⑷ 상세 3행 ═════════════════════════════════
def test_detail_carries_the_three_axis_values_as_the_filter_strings(p2_client) -> None:
    """⑷ 상세의 세 값이 **목록 필터에 넣는 문자열과 같다**.

    같지 않으면 사람이 상세에서 본 글자를 필터에 넣었을 때 0건이 나온다.
    """
    client = p2_client()
    dataset_id = _created(client, category="수문 인자", dataType="위성자료",
                          processingLevelUserSet="Lv2")
    basic = _detail(client, dataset_id)["basicInfo"]
    assert basic["category"] == "수문 인자"
    assert basic["dataType"] == "위성자료"
    assert basic["processingLevelUserSet"] == "Lv2"
    assert dataset_id in _ids(client, category=basic["category"])
    assert dataset_id in _ids(client, dataType=basic["dataType"])


def test_the_two_axis_keys_are_always_present_in_basic_info(p2_client) -> None:
    """⑷-b `category`·`dataType` 이 **required** 다 — 값이 NULL 이어도 열쇠는 있다."""
    client = p2_client()
    dataset_id = _created(client, category="수문 인자", dataType="위성자료")
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"category": None, "dataType": None}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    basic = _detail(client, dataset_id)["basicInfo"]
    assert "category" in basic and basic["category"] is None
    assert "dataType" in basic and basic["dataType"] is None


# ═════════════════════════ ⑸ topic 이관 표기 ══════════════════════════
def test_the_topic_parameter_is_kept_for_one_release(p2_client) -> None:
    """⑸ `topic` 파라미터가 **살아 있다** — 한 릴리즈 동안 유지한다(PRD-05 축자)."""
    client = p2_client()
    rain = _created(client, category="수문 인자", dataType="위성자료", topic="강우·강수")
    dem = _created(client, category="수문 인자", dataType="위성자료", topic="지형·DEM")
    ids = _ids(client, topic="강우·강수")
    assert rain in ids and dem not in ids, ids


# ═════════════════════════ ⑹ 패싯 ═══════════════════════════════════
def test_facets_count_the_three_axes(p2_client) -> None:
    """⑹ 축마다 값별 건수 ＋ 파수꼴 `미지정` 이 있다. 0건 값은 사라지지 않는다."""
    client = p2_client()
    _created(client, category="수문 인자", dataType="위성자료")
    axes = _axes(client)
    assert list(axes) == ["분류", "유형", "가공 단계"], axes
    assert axes["분류"]["수문 인자"] >= 1, axes
    # 0건 값이 지워지면 그 조건이 화면에서 사라진다 (`Policy_데이터_찾기 §5`).
    assert "환경 인자" in axes["분류"], axes
    for axis in ("분류", "유형", "가공 단계"):
        assert UNSPECIFIED in axes[axis], axis


def test_facets_apply_the_other_axes_conditions_first(p2_client) -> None:
    """⑹-b 자기 축의 조건은 빼고 센다 — 안 그러면 고른 값에서 갈아탈 수가 없다."""
    client = p2_client()
    _created(client, category="수문 인자", dataType="위성자료")
    _created(client, category="환경 인자", dataType="위성자료")
    axes = _axes(client, category="수문 인자")
    assert axes["분류"]["환경 인자"] == 1, axes
    assert axes["유형"]["위성자료"] == 1, axes
