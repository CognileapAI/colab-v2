"""검색 계약 확장 16차 — **Verified 우선 정렬 · 서버 걸름 · 요약·기간** (`PLAN-SoT §9 〈298〉`).

`〈295〉` 가 화면 레인에서 **셋을 STOP** 했고 그 사유가 전부 이 파일의 대상이다 —
  ⑴ 정렬 = 「`verified` 는 D3 의 값이 아니다. 정렬을 걸 수 있는 유일한 자리는
     `routes/catalog.py` 의 조립 루프」(`〈295〉`-㉯)
  ⑵ `요약`·`기간` = 「계약에 칸이 없다」(`〈295〉`-㉰) → 16차로 열었다
  ⑶ `Verified만 보기` 서버 걸름 = 「`SearchQuery` 에 `verified` 칸이 없고 라우트가 계약에
     없는 필드를 400 으로 막는다」(`〈295〉`-㉱) → 16차로 열었다

오라클 = 정본 `Policy_데이터_찾기.md` v2.1
  · `:117` 「기본 정렬 … 검색: **Verified 우선 + 관련도**」
  · `:120` 「결과 카드 구성 = 파일명 · 포맷 · Lv · Verified · 관련도 막대 · **요약** ·
    AI 근거 · **기간** · 원천 · 소유」
  · `:150` 「Verified만 보기 … 켜면 승인 결과만, **건수 갱신**. 검색 전용이다」

⚠ **「우선」은 관련도를 버리는 것이 아니다.** 승인 여부로 **두 무리로 가르기만** 하고
무리 **안의 순서는 관련도 그대로**다 — 그래서 정렬은 안정 정렬 한 줄이고, 아래 두 번째
묶음이 그 성질 자체를 오라클로 든다.
"""
from __future__ import annotations

import pytest
from conftest import DS_A1, DS_A2, LAB_A, TOKEN_RES, auth
from test_search_relay import _ai_body, fake_ai  # noqa: F401  (픽스처 재사용)

from colab_core.app.main import API_PREFIX

SEARCH = f"{API_PREFIX}/dataset-searches"

#: 「강우 격자화」의 **관련도 순서는 `[DS_A2, DS_A1]`** 이다 — 「격자화」가 A2 의 이름에만
#: 있고 이름 가중치가 A 다(`test_search_relay.py` 의 같은 오라클). 그리고 시드는
#: **A1 만 승인**돼 있다(`seed.sql` `d2_verified`) — 즉 **관련도와 승인이 서로 어긋나는
#: 배치**라, 이 질의 하나로 「우선이 걸렸나」와 「관련도가 살아 있나」를 둘 다 잰다.
TERMS = ["강우", "격자화"]
RELEVANCE_ORDER = [DS_A2, DS_A1]


def _search(client, *, body: dict) -> dict:
    r = client.post(SEARCH, json=body, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture()
def searching(p2_client, fake_ai):  # noqa: F811
    fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A)
    return p2_client(ai_base_url=fake_ai["url"])


@pytest.fixture()
def verified_of(sql):
    """승인 배지를 시험이 직접 세운다. **끝나면 시드 값으로 되돌린다** — 되돌리지 않으면
    다음 시험의 「A1 만 승인」 전제가 조용히 거짓이 된다."""
    def set_(dataset_id: str, value: bool) -> None:
        # 스키마가 「승인이면 승인 시각이 있다」를 CHECK 로 지킨다 — 시험이 그 규칙을
        # 우회하지 않고 함께 세운다 (`schema.sql` `CHECK (NOT verified OR approved_at IS NOT NULL)`).
        sql("""UPDATE d2_verified
                  SET verified = :v,
                      approver_account_id = CASE WHEN :v
                          THEN CAST('00000000000000000000000AP1' AS ulid) END,
                      approved_at = CASE WHEN :v
                          THEN CAST('2026-01-03T00:00:00Z' AS timestamptz) END
                WHERE dataset_id = :d""", {"v": value, "d": dataset_id})
    yield set_
    set_(DS_A1, True)
    set_(DS_A2, False)


@pytest.fixture()
def period_of(sql):
    """기간은 **상세와 같은 열**(`d3_dataset_autometa.period_start/end`)에서 온다.
    시드는 이 열을 비워 두므로 시험이 세우고 **되돌린다**."""
    def set_(dataset_id: str, start: str | None, end: str | None) -> None:
        sql("""UPDATE d3_dataset_autometa
                  SET period_start = CAST(:s AS timestamptz),
                      period_end   = CAST(:e AS timestamptz)
                WHERE dataset_id = :d""", {"s": start, "e": end, "d": dataset_id})
    yield set_
    set_(DS_A1, None, None)
    set_(DS_A2, None, None)


# ═════════════ ⑴ Verified 우선 정렬 — `〈295〉`-㉯ 가 멈춘 자리 ═════════════
def test_verified_results_come_first(searching) -> None:
    """`Policy :117` 「검색: Verified 우선 + 관련도」.

    관련도만이면 `[DS_A2, DS_A1]` 인데(승인 안 된 A2 가 먼저), 승인된 A1 이 위로 올라온다.
    화면이 카드에 적는 「교수 승인이라 위로 올렸어요」가 **이 줄에서 참이 된다**(`〈295〉`-㉳).
    """
    items = _search(searching, body={"query": "강우 격자화"})["items"]
    assert [i["datasetId"] for i in items] == [DS_A1, DS_A2]
    assert items[0]["verified"] is True and items[1]["verified"] is False


def test_relevance_order_survives_inside_each_group(searching, verified_of) -> None:
    """**안정 정렬이라 무리 안의 순서는 관련도 그대로다.**

    둘 다 승인이면 한 무리이고, 둘 다 미승인이어도 한 무리다 — 어느 쪽이든 순서는
    관련도 순(`[DS_A2, DS_A1]`)이어야 한다. 이 성질이 깨지면 「우선」이 「관련도 폐기」가 된다.
    """
    verified_of(DS_A1, True)
    verified_of(DS_A2, True)
    assert [i["datasetId"] for i in _search(searching, body={"query": "강우 격자화"})["items"]] \
        == RELEVANCE_ORDER

    verified_of(DS_A1, False)
    verified_of(DS_A2, False)
    assert [i["datasetId"] for i in _search(searching, body={"query": "강우 격자화"})["items"]] \
        == RELEVANCE_ORDER


# ═════════════ ⑵ `Verified만 보기` — **`limit` 보다 먼저** 거른다 ═════════════
def test_the_verified_filter_runs_before_the_limit(searching) -> None:
    """`〈295〉`-㉲-ⓑ 가 적어 둔 한계를 닫는다.

    화면이 받은 쪽을 거르면 `limit=1` 의 첫 쪽은 관련도 1위인 **미승인 A2** 한 건이고,
    거른 결과는 **0건**이 된다 — 승인된 A1 은 켜도 영영 오지 않는다.
    서버가 `limit` 앞에서 거르면 A1 이 온다.
    """
    body = _search(searching, body={"query": "강우 격자화", "limit": 1, "verified": True})
    assert [i["datasetId"] for i in body["items"]] == [DS_A1]
    assert body["totalCount"] == 1, "건수도 걸른 뒤의 건수다 (`Policy :150` 「건수 갱신」)."


def test_the_filter_keeps_only_approved_rows(searching) -> None:
    items = _search(searching, body={"query": "강우 격자화", "verified": True})["items"]
    assert [i["datasetId"] for i in items] == [DS_A1]
    assert all(i["verified"] is True for i in items)


def test_omitting_verified_filters_nothing(searching) -> None:
    """**생략은 「거르지 않는다」다.** `false` 도 같은 뜻이다 —
    「승인되지 않은 것만」은 정본에 없는 조작이라 이 칸이 표현하지 않는다."""
    both = {DS_A1, DS_A2}
    assert {i["datasetId"] for i in
            _search(searching, body={"query": "강우 격자화"})["items"]} == both
    assert {i["datasetId"] for i in
            _search(searching, body={"query": "강우 격자화", "verified": False})["items"]} == both


def test_verified_must_be_a_boolean(searching) -> None:
    """계약이 `boolean` 이라고 적었다 — 문자열을 참으로 접지 않는다."""
    r = searching.post(SEARCH, json={"query": "강우", "verified": "true"},
                       headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


def test_an_unknown_field_is_still_a_400(searching) -> None:
    """칸을 하나 열었다고 문이 열린 것이 아니다 — 계약 밖 열쇠는 그대로 400 이다."""
    r = searching.post(SEARCH, json={"query": "강우", "verifed": True},
                       headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


# ═════════════ ⑶ 카드의 `요약`·`기간` — `〈295〉`-㉰ 가 멈춘 자리 ═════════════
def test_every_row_carries_summary_and_period(searching, period_of) -> None:
    """`Policy :120` 결과 카드 구성. **칸이 늘 있다** — 값이 없으면 `null` 이고
    그것이 「없다」는 사실이다. 칸 자체가 없으면 화면이 지어낼 자리가 생긴다."""
    period_of(DS_A1, "2025-06-01T00:00:00Z", "2025-09-30T00:00:00Z")
    items = _search(searching, body={"query": "강우 격자화"})["items"]
    for item in items:
        assert "summary" in item and "period" in item

    a1 = next(i for i in items if i["datasetId"] == DS_A1)
    assert a1["summary"] == "관측 원자료", "요약이 상세와 다른 열에서 오면 두 화면이 갈라진다."
    assert a1["period"]["start"].startswith("2025-06")
    assert a1["period"]["end"].startswith("2025-09")


def test_a_dataset_without_a_period_gets_null_not_a_made_up_range(searching) -> None:
    items = _search(searching, body={"query": "강우 격자화"})["items"]
    assert all(i["period"] is None for i in items), "없는 기간을 지어내지 않는다."


def test_an_open_ended_period_keeps_its_start(searching, period_of) -> None:
    """`〈283〉`(14차 해제) — **끝이 없는 것은 무기한이지 기간이 없는 것이 아니다.**
    `DataPeriod` 를 그대로 재사용하므로 그 성질이 검색 카드에도 그대로 온다."""
    period_of(DS_A2, "2024-01-01T00:00:00Z", None)
    a2 = next(i for i in _search(searching, body={"query": "강우 격자화"})["items"]
              if i["datasetId"] == DS_A2)
    assert a2["period"] is not None and a2["period"]["end"] is None
    assert a2["period"]["start"].startswith("2024-01")


def test_a_locked_row_still_carries_its_summary(searching) -> None:
    """`P-13` — 잠긴 데이터도 **이름·요약까지는** 보인다. 상세(`DatasetDetail.summary`)와
    같은 성질이다. 잠긴 카드가 `기간` 을 안 그리는 것은 **화면의 규칙**이지 서버가
    값을 빼는 것이 아니다 (`Policy :151`)."""
    a2 = next(i for i in _search(searching, body={"query": "강우 격자화"})["items"]
              if i["datasetId"] == DS_A2)
    assert a2["bodyAccessible"] is False
    assert a2["summary"] == "격자화 결과"


def test_the_catalog_row_shape_is_untouched(searching, p2_client) -> None:
    """**`DatasetRow` 는 건드리지 않았다** — 요약·기간은 검색 전용 두 칸이다.
    카탈로그 표가 같이 넓어졌으면 required 13칸 규약이 깨진 것이다."""
    rows = p2_client().get(f"{API_PREFIX}/datasets", headers=auth(TOKEN_RES)).json()["items"]
    assert rows
    for row in rows:
        assert "summary" not in row and "period" not in row
