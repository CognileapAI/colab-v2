"""WU-A6 · PRD-17 · PRD-18 — 관측 간격 두 칸 · 기간의 최소 단위 한 칸.

여기서 재는 것 (라운드 파일 §5 WU-A6 수용 기준 그대로)

  PRD-17 · 관측 간격 (`M-6` · `d3_dataset_description` 두 칸)
    ⑴ 단위 `분` ＋ `10` 저장 후 재조회 → `value=10` · `unit='분'`
    ⑵ 숫자만 채우고 단위를 비우면 `createDataset` **400** (반쪽이 저장되지 않는다)
    ⑶ 값을 비운 채 등록하면 **성공** — 선택 항목이고 ⛔ 등록 게이트가 아니다
    ⑷ 기존 행(= 안 적은 행)은 `observationInterval: null` 이고 상세가 **200** 이다

  PRD-18 · 기간의 최소 단위 (`M-7` · `d3_dataset_autometa` 한 칸)
    ⑸ granularity 가 저장되고 그대로 돌아온다
    ⑹ 6값 밖은 **400** (CHECK 위반이 500 으로 새지 않는다)
    ⑺ granularity 를 안 보낸 기존 행은 **종전 표기 그대로** — `start`·`end` 가 안 바뀐다

⚠ **여기서 재지 않는 것** — 화면이 조립하는 글자(`10분` · 기간 뒤 ` (10분)`)는 PRD-35 이고
   `frontend/test/interval-period-20260906.test.tsx` 가 잰다. 계약이 표시 문자열을 안 싣는다.
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX


def _read(client, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def _register(client, **extra):
    return register(client, make_upload(client), **extra)


# ═══════════════════════════ PRD-17 · 관측 간격 ═══════════════════════════
def test_interval_round_trips_value_and_unit(p2_client) -> None:
    """⑴ `10` ＋ `분` 이 그대로 저장되고 그대로 돌아온다. **표시 문자열은 없다.**"""
    client = p2_client()
    r = _register(client, observationInterval={"value": 10, "unit": "분"})
    assert r.status_code == 201, r.text
    basic = _read(client, r.json()["datasetId"])["basicInfo"]
    assert basic["observationInterval"] == {"value": 10, "unit": "분"}, basic
    # 계약이 표시 문자열을 싣지 않는다 — 조립은 화면의 일이다 (PRD-17 축자).
    assert "label" not in basic["observationInterval"]
    assert "text" not in basic["observationInterval"]


def test_half_filled_interval_is_rejected_with_400(p2_client) -> None:
    """⑵ **숫자만 채우면 400** — 반쪽 값이 저장되지 않는다.

    `10` 만 남은 행은 화면이 무엇으로도 못 그린다: `10분` 인지 `10일` 인지 아무도 모른다.
    """
    r = _register(p2_client(), observationInterval={"value": 10, "unit": None})
    assert r.status_code == 400, r.text


def test_half_filled_interval_unit_only_is_also_rejected(p2_client) -> None:
    """⑵-b 반대쪽(단위만)도 같다 — 한쪽만 보는 검사를 두지 않는다."""
    r = _register(p2_client(), observationInterval={"value": None, "unit": "분"})
    assert r.status_code == 400, r.text


def test_interval_unit_outside_the_six_values_is_400_not_500(p2_client) -> None:
    """단위 6값 밖은 **400** 이다 — CHECK 위반이 500 으로 새면 사용자 오타가 서버 잘못이 된다."""
    r = _register(p2_client(), observationInterval={"value": 10, "unit": "minute"})
    assert r.status_code == 400, r.text


def test_registering_without_interval_succeeds(p2_client) -> None:
    """⑶ **선택 항목이다** — 비운 채 등록하면 성공하고 `null` 로 내려온다.

    ⛔ 관측 간격을 등록 게이트에 올리지 않는다 (PRD-17 축자 · 미결-4 ⓐ).
    """
    client = p2_client()
    r = _register(client)
    assert r.status_code == 201, r.text
    basic = _read(client, r.json()["datasetId"])["basicInfo"]
    assert basic["observationInterval"] is None, basic


def test_empty_interval_object_is_treated_as_not_written(p2_client) -> None:
    """폼 기본값(`{value: null, unit: null}`)이 그대로 실려 와도 **등록은 성공**한다.

    「폼 기본값 통과 ≠ 사람이 적었다」 — 두 칸이 다 비면 안 적은 것이다.
    """
    client = p2_client()
    r = _register(client, observationInterval={"value": None, "unit": None})
    assert r.status_code == 201, r.text
    assert _read(client, r.json()["datasetId"])["basicInfo"]["observationInterval"] is None


def test_existing_row_without_interval_reads_200(p2_client) -> None:
    """⑷ 안 적은 행의 상세는 **200 이고 `null`** 이다 — 화면이 안 깨지고 재선택도 없다."""
    client = p2_client()
    dataset_id = _register(client).json()["datasetId"]
    detail = _read(client, dataset_id)
    assert detail["basicInfo"]["observationInterval"] is None
    # 열쇠 자체는 **있다** — 계약 `required` 라, 없으면 화면이 undefined 를 그린다.
    assert "observationInterval" in detail["basicInfo"]


def test_interval_can_be_filled_through_update(p2_client) -> None:
    """기존 행은 **그 행을 고칠 때** 채워진다 — 일괄 채우기가 아니다."""
    client = p2_client()
    dataset_id = _register(client).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"observationInterval": {"value": 1, "unit": "시"}},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _read(client, dataset_id)["basicInfo"]["observationInterval"] == \
        {"value": 1, "unit": "시"}


def test_interval_can_be_cleared_through_update(p2_client) -> None:
    """`null` 은 **비우라는 뜻**이다 — 두 칸이 함께 빈다(반쪽이 남지 않는다)."""
    client = p2_client()
    dataset_id = _register(client, observationInterval={"value": 10, "unit": "분"}) \
        .json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"observationInterval": None}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _read(client, dataset_id)["basicInfo"]["observationInterval"] is None


def test_half_filled_interval_on_update_is_400(p2_client) -> None:
    """수정 경로도 **같은 검사기**를 쓴다 — 두 벌을 두면 한쪽만 고쳐지는 날이 온다."""
    client = p2_client()
    dataset_id = _register(client).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"observationInterval": {"value": 10, "unit": None}},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


# ═══════════════════════ PRD-18 · 기간의 최소 단위 ════════════════════════
PERIOD = {"start": "2025-06-01T00:00:00Z", "end": "2025-06-30T00:00:00Z"}


def test_period_granularity_round_trips(p2_client) -> None:
    """⑸ 단위 `일` 이 저장되고 그대로 돌아온다. **시각값 저장은 안 바뀐다.**"""
    client = p2_client()
    r = _register(client, period={**PERIOD, "granularity": "일"})
    assert r.status_code == 201, r.text
    period = _read(client, r.json()["datasetId"])["basicInfo"]["period"]
    assert period["granularity"] == "일", period
    # 저장 모양은 종전 그대로다 — 최소 단위는 **읽는 방법**이지 저장 형식이 아니다(미결-18 ⓐ).
    assert period["start"].startswith("2025-06-01")
    assert period["end"].startswith("2025-06-30")


def test_period_granularity_accepts_all_six_values(p2_client) -> None:
    """6값이 **전부** 통과한다 — 하나라도 빠지면 화면 셀렉트와 서버가 갈린다."""
    client = p2_client()
    dataset_id = _register(client, period=PERIOD).json()["datasetId"]
    for unit in ("년", "월", "일", "시", "분", "초"):
        r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                         json={"period": {**PERIOD, "granularity": unit}},
                         headers=auth(TOKEN_RES))
        assert r.status_code == 200, f"{unit} → {r.text}"
        assert _read(client, dataset_id)["basicInfo"]["period"]["granularity"] == unit


def test_period_granularity_outside_the_six_values_is_400_not_500(p2_client) -> None:
    """⑹ 6값 밖은 **400** 이다 — CHECK 위반이 500 이 되면 사용자의 오타가 서버 잘못이 된다."""
    r = _register(p2_client(), period={**PERIOD, "granularity": "day"})
    assert r.status_code == 400, r.text


def test_row_without_granularity_keeps_the_previous_shape(p2_client) -> None:
    """⑺ granularity NULL 인 행은 **종전 표기 그대로**다 — 재선택을 강제하지 않는다."""
    client = p2_client()
    r = _register(client, period=PERIOD)
    assert r.status_code == 201, r.text
    period = _read(client, r.json()["datasetId"])["basicInfo"]["period"]
    assert period["granularity"] is None, period
    assert period["start"].startswith("2025-06-01")
    assert period["end"].startswith("2025-06-30")


def test_clearing_the_period_clears_the_granularity_too(p2_client) -> None:
    """기간을 비우면 단위도 함께 빈다 — 없는 기간에 단위만 남으면 「무엇의 단위인가」가 없다."""
    client = p2_client()
    dataset_id = _register(client, period={**PERIOD, "granularity": "일"}).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json={"period": None},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _read(client, dataset_id)["basicInfo"]["period"] is None


def test_unknown_period_key_is_still_rejected(p2_client) -> None:
    """열쇠 집합은 **셋뿐**이다 — `granularity` 를 연 것이 아무 열쇠나 연 것이 아니다."""
    r = _register(p2_client(), period={**PERIOD, "precision": "일"})
    assert r.status_code == 400, r.text
