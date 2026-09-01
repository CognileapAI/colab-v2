"""연구실 대시보드 (WU-P7) — D8 집계 3 op 의 실동작과 **연구실 경계 음성**.

오라클은 전부 정본 `Policy_홈_대시보드`(v1.5) 축자다. 이 파일이 인용하는 조항 —

  §5  요약 지표 구성 ｜ 프로젝트 · 데이터셋 · **계보 확정** · Verified — **넷을 넘기지 않는다**
  §5  계보 확정 = `확정` + `원천` ｜ 미확정 = `확인 필요` + `기록 없음` ｜ **퍼센트로 바꾸지 않는다**
  §5  데이터 맵 묶음 = 계보 상태별 · 주제별 ｜ 계보 상태 **네 값 전부** — 0이어도 줄을 지우지 않는다
  §5  최근 활동 = 시점 최신순 ｜ 행마다 **행위자와 한 일**
  §10 열람 기록은 **서버에 남기지 않는다** — 목록은 「바꾼 일」만 든다

**음성이 이 파일의 중심이다.** 대시보드는 연구실 전체를 한 숫자로 접는 화면이라, 경계가
새면 그 누출이 **숫자 안에 숨는다** — 남의 연구실 데이터셋 한 건이 섞여도 화면은 조용하다.
그래서 `TOKEN_B` 로 같은 세 op 을 다시 부르고 **A 의 값이 하나도 안 보이는 것**을 잰다.

이 파일이 501 표에서 빼 온 셋 — `tests/test_not_implemented.py` 의 `P7_REAL` 이 이 이름들을
여기서 찾는다. **뺀 자리마다 실동작 시험이 있다**는 규칙의 실물이다.

  `getDashboardSummary` · `getDataMap` · `listActivities`
"""
from __future__ import annotations

from conftest import (ACC_A_RES, DS_A1, DS_A2, DS_B1, TOKEN_B, TOKEN_PROF,
                      TOKEN_RES, auth)

PREFIX = "/api/v1"

#: 계보 상태 네 값. 카탈로그 열의 표기와 **같아야 한다** (`Policy_홈_대시보드 §5`).
STATES = ("확정", "원천", "확인 필요", "기록 없음")


# ── 요약 지표 (§5) ───────────────────────────────────────────────────────────

def test_the_summary_counts_what_the_lab_actually_has(live_client):
    """시드 A = 데이터셋 2 · 프로젝트 1 · Verified 1 · 계보 확정 2(확정 1 + 원천 1).

    `DSA1` 은 부모가 없고 원천 표기(`기상청`)가 있어 **원천**, `DSA2` 는 부모가 있고
    확정일이 마지막 수정보다 뒤라 **확정**이다 (`d3_catalog.lineage_state`).
    """
    r = live_client.get(f"{PREFIX}/dashboard/summary", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    # **넷을 넘기지 않는다** (§5). 미확정 건수는 계보 확정 타일에 딸린 값이라 다섯째 지표가 아니다.
    assert set(body) == {"projectCount", "datasetCount", "lineageSettledCount",
                         "lineageUnsettledCount", "verifiedCount"}
    assert body["datasetCount"] == 2
    assert body["projectCount"] == 1
    assert body["verifiedCount"] == 1
    assert body["lineageSettledCount"] == 2
    assert body["lineageUnsettledCount"] == 0
    # **퍼센트가 없다** (§5 축자 「퍼센트로 바꿔 적지 않는다」).
    assert not any("percent" in k.lower() or "ratio" in k.lower() for k in body)


def test_the_settled_count_is_confirmed_plus_origin(live_client, sql):
    """지표의 계보 확정 = 맵의 `확정` + `원천` 이다 (§5 「지표와 맵의 계산 관계」).

    두 op 을 따로 부르고 **둘의 값이 서로 맞는지**를 잰다 — 화면이 카드 안에 적는
    한 줄(`확정 71 + 원천 16 = 87`)이 거짓이 되지 않게 하는 자리다.
    """
    summary = live_client.get(f"{PREFIX}/dashboard/summary", headers=auth(TOKEN_RES)).json()
    data_map = live_client.get(f"{PREFIX}/dashboard/data-map", headers=auth(TOKEN_RES)).json()
    by_state = {row["value"]: row["count"] for row in data_map["byLineageState"]}
    assert summary["lineageSettledCount"] == by_state["확정"] + by_state["원천"]
    assert summary["lineageUnsettledCount"] == by_state["확인 필요"] + by_state["기록 없음"]


# ── 데이터 맵 (§5) ───────────────────────────────────────────────────────────

def test_the_data_map_keeps_all_four_lineage_rows_even_at_zero(live_client):
    """**0이어도 줄을 지우지 않는다** (계약 `DataMap.byLineageState` 산문 축자).

    시드 A 에는 `확인 필요`·`기록 없음` 이 0건이다. 그 둘이 빠지면 화면은 「그런 상태는
    없다」로 읽고, 채워야 할 칸이 있다는 사실 자체가 사라진다.
    """
    r = live_client.get(f"{PREFIX}/dashboard/data-map", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"totalCount", "byLineageState", "byTopic"}
    assert [row["value"] for row in body["byLineageState"]] == list(STATES)
    by_state = {row["value"]: row["count"] for row in body["byLineageState"]}
    assert by_state == {"확정": 1, "원천": 1, "확인 필요": 0, "기록 없음": 0}
    assert body["totalCount"] == 2
    # 주제는 시드 A 가 한 값(`강우·강수`)에 둘 다 붙어 있다.
    assert body["byTopic"] == [{"value": "강우·강수", "count": 2}]


def test_the_data_map_total_is_the_denominator_of_the_bars(live_client):
    """비율 막대의 분모는 `totalCount` 다 (계약 산문). 계보 축의 합과 같아야 한다 —
    다르면 막대가 100% 를 넘거나 못 채운다."""
    body = live_client.get(f"{PREFIX}/dashboard/data-map", headers=auth(TOKEN_RES)).json()
    assert sum(row["count"] for row in body["byLineageState"]) == body["totalCount"]


# ── 최근 활동 (§5 · §10) ─────────────────────────────────────────────────────

def test_the_activity_list_carries_who_did_what(live_client):
    """행마다 **행위자와 한 일**이 있어야 한다 (§5 축자). 이름을 지어내지 않는다.

    **시드 줄로 재지 않는다** — `d8_activity` 는 append-only 라 앞선 회차가 남긴 줄이
    계속 쌓이고, 가장 오래된 시드 줄은 곧 첫 쪽 밖으로 밀려난다(`conftest._CLEANUP`
    주석). 그래서 이 시험이 **자기 줄을 만들고** 그 줄의 모양을 본다.
    """
    made = live_client.post(f"{PREFIX}/datasets/{DS_A2}/lineage/confirmation",
                            headers=auth(TOKEN_RES))
    assert made.status_code == 200, made.text

    r = live_client.get(f"{PREFIX}/dashboard/activities", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"items", "totalCount", "nextCursor"}
    row = body["items"][0]
    assert set(row) == {"activityId", "actor", "action", "target", "occurredAt"}
    assert row["actor"] == {"accountId": ACC_A_RES, "name": "A 연구원"}
    assert row["action"] == "계보 확정"
    assert row["target"] == {"kind": "데이터셋", "id": DS_A2, "name": "A 강우 격자화"}


def test_a_new_activity_is_recorded_and_comes_first(live_client):
    """**바꾼 일이 목록을 만든다** (§7 전이표). 프로젝트를 만들면 그 줄이 맨 위로 온다.

    절대 개수를 세지 않는다 — `d8_activity` 는 append-only 라 회차를 넘어 쌓인다
    (`conftest._CLEANUP` 주석). 그래서 **부르기 전후의 차이**를 본다.
    """
    before = live_client.get(f"{PREFIX}/dashboard/activities", headers=auth(TOKEN_RES)).json()
    made = live_client.post(f"{PREFIX}/projects", headers=auth(TOKEN_PROF),
                            json={"type": "논문", "name": "P7 활동 기록 시험"})
    assert made.status_code == 201, made.text
    after = live_client.get(f"{PREFIX}/dashboard/activities", headers=auth(TOKEN_RES)).json()

    assert after["totalCount"] == before["totalCount"] + 1
    top = after["items"][0]
    assert top["target"]["kind"] == "프로젝트"
    assert top["target"]["name"] == "P7 활동 기록 시험"
    assert top["actor"]["name"] == "A 교수"


def test_reading_is_not_recorded(live_client, sql):
    """**열람은 서버에 남기지 않는다** (§10 · `DataModel §6.1`). 상세를 열어도 줄이 안 는다.

    이 음성이 없으면 「브라우저에만 둔다」는 조항이 코드 어디에도 강제되지 않는다.
    """
    before = live_client.get(f"{PREFIX}/dashboard/activities", headers=auth(TOKEN_RES)).json()
    assert live_client.get(f"{PREFIX}/datasets/{DS_A1}", headers=auth(TOKEN_RES)).status_code == 200
    after = live_client.get(f"{PREFIX}/dashboard/activities", headers=auth(TOKEN_RES)).json()
    assert after["totalCount"] == before["totalCount"], "열람이 활동으로 남았다 — §10 위반이다."


# ── 음성 — 연구실 경계 (`CLAUDE.md §3-5` · P-9·P-10) ──────────────────────────

def test_another_lab_sees_only_its_own_numbers(live_client):
    """**대시보드는 숫자로 접힌 화면이라 누출이 안 보인다.** 그래서 여기서 잰다.

    B 연구실 = 데이터셋 1(`DSB1` · 원천) · 프로젝트 1 · Verified 0. A 의 값(데이터셋 2 ·
    Verified 1 · 주제 `강우·강수`)이 **하나도 섞이지 않아야 한다.**
    """
    summary = live_client.get(f"{PREFIX}/dashboard/summary", headers=auth(TOKEN_B))
    assert summary.status_code == 200, summary.text
    assert summary.json() == {"projectCount": 1, "datasetCount": 1,
                              "lineageSettledCount": 1, "lineageUnsettledCount": 0,
                              "verifiedCount": 0}

    data_map = live_client.get(f"{PREFIX}/dashboard/data-map", headers=auth(TOKEN_B)).json()
    assert data_map["totalCount"] == 1
    assert {r["value"]: r["count"] for r in data_map["byLineageState"]} == {
        "확정": 0, "원천": 1, "확인 필요": 0, "기록 없음": 0}
    # A 의 주제가 B 의 맵에 없다 — 패싯이 경계를 넘는지 보는 자리다.
    assert data_map["byTopic"] == [{"value": "토지피복·LULC", "count": 1}]

    activities = live_client.get(f"{PREFIX}/dashboard/activities", headers=auth(TOKEN_B)).json()
    targets = {row["target"]["id"] for row in activities["items"]}
    assert DS_B1 in targets
    assert targets & {DS_A1, DS_A2} == set(), "남의 연구실 활동이 목록에 섞였다."
    assert not any(row["actor"]["name"] == "A 연구원" for row in activities["items"])


def test_the_dashboard_is_closed_without_a_subject(live_client):
    """미인증은 401 이다 (계약). 경계 밖에서 연구실 규모를 읽게 두지 않는다."""
    for path in ("/dashboard/summary", "/dashboard/data-map", "/dashboard/activities"):
        r = live_client.get(PREFIX + path)
        assert r.status_code == 401, f"{path} 가 무토큰으로 열렸다."
