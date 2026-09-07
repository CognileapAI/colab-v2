"""WU-B2 · PRD-16 — 변수를 **행**으로 받는다 (`d3_dataset_variable`).

수용 기준 6건(`R-B-1-db.md §2` WU-B2) 중 **서버가 잴 수 있는 다섯**이 여기 있다 —
나머지 하나(마지막 행 삭제가 화면에서 막힌다)는 프런트 시험이고, 이관 오라클은
`db/platform/tests/0016-drift.sh` 다.

  ㈎ 변수 3행에 각각 다른 단위 → 상세가 **세 행을 각자의 단위와 함께** 낸다
  ㈏ 대표를 안 고르면 → **첫 행**이 대표다 (자동 보정)
  ㈐ 변수 행 0개로 저장 시도 → **400** ＋ 「변수는 하나 이상 있어야 해요」
  ㈑ 대표를 둘 고르면 → **400** (부분 UNIQUE 색인이 500 으로 새지 않는다)
  ㈒ 다른 연구실 계정 → 변수 행 **0건** (cross-tenant 음성)

⛔ **등록·수정 경로가 `d3_dataset_autometa.variables` 를 직접 쓰지 않는다**(PRD-16 축자).
   그 열을 행 표의 미러로 유지하는 트리거는 `M-10` 이고 이 회차 밖이다 — 그래서
   「새로 쓴 변수 행이 그 배열에 안 들어간다」가 **지금은 정상**이고, 아래 시험 하나가
   그 사실 자체를 붙잡아 둔다(다음 회차가 뒤집을 때 이 시험이 먼저 말한다).
"""
from __future__ import annotations

from conftest import ACC_B_PROF, DS_A1, LAB_B, TOKEN_RES, auth, scoped_ro
from sqlalchemy import text
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

THREE = [
    {"name": "precipitation", "unit": "mm", "valueRange": "0~350",
     "missingRate": "0.2%", "representative": True},
    {"name": "temperature", "unit": "℃", "valueRange": "-30~40", "missingRate": None},
    {"name": "runoff", "unit": "m3/s"},
]


def _register_with(client, **extra):
    return register(client, make_upload(client), **extra)


# ═══════ ㈎ 세 행이 각자의 단위와 함께 보인다 ══════════════════════════════
def test_three_rows_keep_their_own_units(p2_client, sql) -> None:
    """PRD-16 이 여는 문장 — 「변수 3개에 단위 1개면 어느 변수 것인지 알 수 없다.」"""
    client = p2_client()
    r = _register_with(client, variables=THREE)
    assert r.status_code == 201, r.text
    got = r.json()["basicInfo"]["variables"]
    assert [v["name"] for v in got] == ["precipitation", "temperature", "runoff"]
    assert [v["unit"] for v in got] == ["mm", "℃", "m3/s"]
    assert [v["valueRange"] for v in got] == ["0~350", "-30~40", None]
    assert [v["missingRate"] for v in got] == ["0.2%", None, None]

    rows = sql("SELECT ordinal, name, unit FROM d3_dataset_variable"
               "  WHERE dataset_id = :d ORDER BY ordinal", {"d": r.json()["datasetId"]})
    assert [(x["ordinal"], x["name"], x["unit"]) for x in rows] == [
        (1, "precipitation", "mm"), (2, "temperature", "℃"), (3, "runoff", "m3/s")]


def test_detail_read_path_returns_the_rows(p2_client) -> None:
    """상세 조회도 **같은 객체 배열**이다 — 등록 응답만 맞고 상세가 다르면 화면이 갈린다."""
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    detail = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert detail.status_code == 200, detail.text
    got = detail.json()["basicInfo"]["variables"]
    assert [v["name"] for v in got] == ["precipitation", "temperature", "runoff"]
    assert [v["representative"] for v in got] == [True, False, False]


# ═══════ ㈏ 대표를 안 고르면 첫 행이 대표다 ════════════════════════════════
def test_first_row_becomes_representative_when_nobody_is_chosen(p2_client, sql) -> None:
    """**대표 없는 저장이 성립하지 않는다**(PRD-16 축자). 서버가 자동 보정한다."""
    client = p2_client()
    r = _register_with(client, variables=[{"name": "가"}, {"name": "나"}, {"name": "다"}])
    assert r.status_code == 201, r.text
    assert [v["representative"] for v in r.json()["basicInfo"]["variables"]] == [True, False, False]
    rows = sql("SELECT ordinal FROM d3_dataset_variable"
               "  WHERE dataset_id = :d AND is_representative", {"d": r.json()["datasetId"]})
    assert [x["ordinal"] for x in rows] == [1]


# ═══════ ㈐ 0행은 400 ＋ 정해진 문면 ═══════════════════════════════════════
def test_empty_variable_list_is_rejected_with_the_copy(p2_client) -> None:
    """마지막 행 삭제를 화면이 막고, **서버가 뒷문**이다 (PRD-16 「행이 0개인 데이터셋은
    허용하지 않는다」). 문면은 rev1 축자 그대로다."""
    client = p2_client()
    created = _register_with(client, variables=[])
    assert created.status_code == 400, created.text
    assert created.json()["message"] == "변수는 하나 이상 있어야 해요"

    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    patched = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json={"variables": []},
                           headers=auth(TOKEN_RES))
    assert patched.status_code == 400, patched.text
    assert patched.json()["message"] == created.json()["message"], \
        "생성과 수정이 다른 문면을 낸다 — 검사기가 두 벌이다."


# ═══════ ㈑ 대표 둘은 400 (500 이 아니다) ═════════════════════════════════
def test_two_representatives_are_a_400_not_a_500(p2_client) -> None:
    """부분 UNIQUE 색인이 뒷문이고 **앞문이 400** 이다. 앞문이 없으면 IntegrityError 가
    500 으로 나가 사용자의 선택이 서버 잘못이 된다 (`CODE-REVIEW-20260903` #12 와 같은 자리)."""
    client = p2_client()
    r = _register_with(client, variables=[
        {"name": "가", "representative": True}, {"name": "나", "representative": True}])
    assert r.status_code == 400, r.text


def test_blank_variable_name_is_a_400(p2_client) -> None:
    """이름은 **빈 문자열이 아니다** — DB CHECK 가 뒷문이고 여기가 앞문이다."""
    client = p2_client()
    assert _register_with(client, variables=[{"name": "  "}]).status_code == 400


# ═══════ 수정 = 행 집합 통째 교체 ═════════════════════════════════════════
def test_update_replaces_the_whole_row_set(p2_client, sql) -> None:
    """**delete-then-insert 한 트랜잭션.** 부분 갱신이 아니다 — 3행을 2행으로 고치면
    셋째 행이 남지 않는다(남으면 화면과 DB 가 갈린다)."""
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"variables": [{"name": "runoff", "unit": "m3/s"},
                                         {"name": "swe", "representative": True}]},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    rows = sql("SELECT ordinal, name, is_representative FROM d3_dataset_variable"
               "  WHERE dataset_id = :d ORDER BY ordinal", {"d": dataset_id})
    assert [(x["ordinal"], x["name"], x["is_representative"]) for x in rows] == [
        (1, "runoff", False), (2, "swe", True)]


# ═══════ ㈒ cross-tenant 음성 ═════════════════════════════════════════════
def test_another_lab_sees_zero_variable_rows(session_factory, sql) -> None:
    """다른 연구실 계정의 스코프에서는 **0건**이다 (`CLAUDE.md §3-5`).

    red 만드는 법 — `ALTER POLICY lab_boundary ON d3_dataset_variable USING (true)`.
    """
    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as db:
        n = db.execute(text("SELECT count(*) FROM d3_dataset_variable"
                            " WHERE dataset_id = :d"), {"d": DS_A1}).scalar_one()
        assert n == 0, "다른 연구실에서 변수 행이 보였다."
        leaked = db.execute(text("SELECT count(*) FROM d3_dataset_variable"
                                 " WHERE lab_id <> :own"), {"own": LAB_B}).scalar_one()
        assert leaked == 0


# ═══════ M-10 이 아직 없다는 사실 자체를 붙잡는다 ═════════════════════════
def test_registration_does_not_write_autometa_variables(p2_client, sql) -> None:
    """**등록·수정 경로는 `autometa.variables` 를 직접 쓰지 않는다**(PRD-16 축자
    「트리거만 쓴다」). 그 트리거(`M-10`)는 `R-B-2-server.md` · WU-B7 소속이라 아직 없다 —
    그래서 지금은 그 배열이 **비어 있는 것이 정상**이고, 검색이 새 변수명을 못 잡는다.

    ⚠ 이 시험은 **잔여 위험을 문서가 아니라 코드로** 붙잡아 둔다. `M-10` 이 서면 이
    시험이 먼저 red 를 내고, 그 자리에서 기대값을 미러로 바꾼다.
    """
    client = p2_client()
    dataset_id = _register_with(client, variables=THREE).json()["datasetId"]
    rows = sql("SELECT variables FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": dataset_id})
    assert list(rows[0]["variables"]) == [], \
        "등록 경로가 autometa.variables 를 직접 썼다 — 미러의 방향이 둘이 된다(M-10 이 정본)."
