"""WU-B5 · PRD-07·08·09·10 — Lv 연결 규칙(**부모 Lv ≤ 자기 Lv**)과 파생·불일치 두 열쇠.

기준은 **분류에서 고른 자기 Lv**(`processing_level_user_set`)다. 같은 단계는 허용이고,
시스템이 자기 Lv 를 바꾸거나 잠그지 않는다. 화면 차단이 유일한 방어선이 되지 않도록
**서버 400 이 최종 방어선**이다(`R-B-2-server.md §2` WU-B5 축자).

여기서 재는 것 —
  ㈎ 같은 레벨 부모는 **허용**된다 (PRD-07)
  ㈏ 자기보다 높은 부모는 **400** 이고 문면이 **위반 항목을 열거**한다 (PRD-07)
  ㈐ 서버가 초과 후보를 **지우지 않는다** — 목록이 전부 내려간다 (PRD-08)
  ㈑ 카탈로그 질의 `processingLevel` 은 **사람 값**을 거른다 (PRD-10)
  ㈒ 사후 충돌(자기 Lv 내림)은 연결을 **지우지 않고** 계보 확정 경로가 400 이다 (PRD-09)
  ㈓ 응답에 사람 값·파생값·불일치 **셋 다** 실린다 · 저장은 성공한다 (PRD-10)

⚠ 화면 쪽(안내 문면 · `is-over` · `확인 필요` 칩 · 대비 4.5:1)은
   `frontend/test/lv-rules-20260907.test.tsx` 가 잰다.
"""
from __future__ import annotations

import pathlib

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

_CONTRACT = (pathlib.Path(__file__).resolve().parents[3]
             / "contracts" / "seams" / "fe-core.yaml")


def _read(client, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def _make(client, *, level: str | None = None, parents: list[str] | None = None, **extra):
    """데이터셋 하나. `level` 은 **사람이 고른 값**이고 `parents` 는 확인된 부모 ID 다."""
    body = dict(extra)
    if level is not None:
        body["processingLevelUserSet"] = level
    if parents:
        body["lineageParents"] = [{"parentDatasetId": p, "origin": "manual"} for p in parents]
    return register(client, make_upload(client), **body)


def _created(client, **kw) -> str:
    r = _make(client, **kw)
    assert r.status_code == 201, r.text
    return r.json()["datasetId"]


def _rows(client, **params) -> list[dict]:
    r = client.get(f"{API_PREFIX}/datasets", params=params, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()["items"]


# ═══════════ ㈎ 같은 레벨은 허용된다 (PRD-07 수용 기준 ⑴) ═══════════
def test_a_parent_of_the_same_level_is_allowed(p2_client) -> None:
    """축자 — 「같은 단계끼리 가공하는 일이 있어 부모+1 로 강제하면 담기지 않는다.」"""
    client = p2_client()
    parent = _created(client, level="Lv2")
    r = _make(client, level="Lv2", parents=[parent])
    assert r.status_code == 201, r.text


def test_a_lower_parent_is_allowed(p2_client) -> None:
    """`부모 Lv ≤ 자기 Lv` 의 부등호가 참인 쪽 — 대조군이다."""
    client = p2_client()
    parent = _created(client, level="Lv0")
    assert _make(client, level="Lv2", parents=[parent]).status_code == 201


# ═══════════ ㈏ 초과 부모는 400 이고 문면이 열거한다 (수용 기준 ⑵) ═══════════
def test_a_parent_above_my_level_is_a_400_that_lists_the_offenders(p2_client) -> None:
    client = p2_client()
    parent = _created(client, level="Lv2", name="초과 부모")
    r = _make(client, level="Lv1", parents=[parent])
    assert r.status_code == 400, r.text
    # **문면이 위반 항목을 열거한다** — 몇 건인지가 아니라 어느 것인지를 말한다.
    assert parent in r.text, r.text
    assert "Lv2" in r.text and "Lv1" in r.text, r.text


def test_the_rule_does_not_fire_when_my_level_is_not_chosen(p2_client) -> None:
    """기존 엣지 무검사 — 사람 Lv 가 NULL 이면 **기준값이 없다**(PRD-07 기존 데이터)."""
    client = p2_client()
    parent = _created(client, level="Lv3")
    assert _make(client, parents=[parent]).status_code == 201


def test_add_lineage_parent_enforces_the_same_rule(p2_client) -> None:
    """계보 확정 경로도 같은 400 이다 — 등록만 막으면 뒷문이 열려 있다."""
    client = p2_client()
    parent = _created(client, level="Lv3")
    child = _created(client, level="Lv1")
    r = client.post(f"{API_PREFIX}/datasets/{child}/lineage/parents",
                    json={"parentDatasetId": parent}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert parent in r.text, r.text


# ═══════════ ㈐ 서버가 초과 후보를 지우지 않는다 (PRD-08) ═══════════
def test_the_server_does_not_drop_candidates_above_my_level(p2_client) -> None:
    """축자 — 「숨기지는 않는다. 없는 것과 못 고르는 것은 다르다.」

    ⛔ 부모 후보 검색은 **자기 Lv 를 모른다** — 전부 내려보내고 화면이 상태로 가른다.
    """
    client = p2_client()
    high = _created(client, level="Lv3")
    assert high in {r["datasetId"] for r in _rows(client)}


def test_the_candidate_search_takes_a_processing_level_query_parameter(p2_client) -> None:
    """찾기 모달의 가공 단계 셀렉트가 쓰는 축 — 고른 단계만 내려온다."""
    client = p2_client()
    lv0 = _created(client, level="Lv0")
    lv3 = _created(client, level="Lv3")
    ids = {r["datasetId"] for r in _rows(client, processingLevel=0)}
    assert lv0 in ids, ids
    assert lv3 not in ids, ids


def test_level_three_is_not_rejected_by_the_filter(p2_client) -> None:
    """상한이 `Lv3` 다(미결-7 ⓐ) — `LV_CAP=2` 가 남아 있으면 여기서 400 이 난다."""
    client = p2_client()
    lv3 = _created(client, level="Lv3")
    assert lv3 in {r["datasetId"] for r in _rows(client, processingLevel=3)}


def test_no_derived_query_parameter_exists(p2_client) -> None:
    """⛔ `processingLevelDerived` 로 거르는 질의 파라미터를 만들지 않는다(PRD-10 축자)."""
    text = _CONTRACT.read_text(encoding="utf-8")
    assert "name: processingLevelDerived" not in text


# ═══════════ ㈑ 필터 축은 사람 값이다 (PRD-10) ═══════════
def test_the_filter_matches_the_human_value_not_the_derived_one(p2_client) -> None:
    """사람 Lv2 · 파생 Lv1 인 행은 **`processingLevel=2` 로 걸린다.**

    ⚠ 파생값은 **계보 그래프**에서만 나온다 — 부모의 *사람* Lv 를 타지 않는다
       (`processing_level(summary)` 무수정). 그래서 Lv0 부모 하나면 파생은 `1` 이다.
    """
    client = p2_client()
    parent = _created(client, level="Lv0")
    child = _created(client, level="Lv2", parents=[parent])
    assert _read(client, child)["basicInfo"]["processingLevelDerived"] == 1
    assert child in {r["datasetId"] for r in _rows(client, processingLevel=2)}
    assert child not in {r["datasetId"] for r in _rows(client, processingLevel=1)}


def test_rows_without_a_human_value_fall_back_to_the_derived_one(p2_client) -> None:
    """사람 값이 NULL 인 행만 파생값으로 대신 걸린다 — 그 행은 선언이 없다."""
    client = p2_client()
    parent = _created(client, level="Lv0")
    child = _created(client, parents=[parent])          # 사람 값 없음 → 파생 1
    assert child in {r["datasetId"] for r in _rows(client, processingLevel=1)}


# ═══════════ ㈒ 사후 충돌 — 연결을 지우지 않는다 (PRD-09) ═══════════
def test_lowering_my_level_keeps_the_edge_and_makes_confirmation_a_400(p2_client) -> None:
    """축자 — 「사람이 한 연결을 시스템이 되돌리지 않는다.」 그리고 그 상태의 **API 직접 호출은 400**."""
    client = p2_client()
    parent = _created(client, level="Lv2")
    child = _created(client, level="Lv2", parents=[parent])
    r = client.patch(f"{API_PREFIX}/datasets/{child}",
                     json={"processingLevelUserSet": "Lv1"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    graph = client.get(f"{API_PREFIX}/datasets/{child}/lineage", headers=auth(TOKEN_RES)).json()
    assert any(e["parentDatasetId"] == parent for e in graph["edges"]), "연결이 지워졌다."
    conf = client.post(f"{API_PREFIX}/datasets/{child}/lineage/confirmation",
                       headers=auth(TOKEN_RES))
    assert conf.status_code == 400, conf.text
    assert parent in conf.text, conf.text


def test_raising_my_level_back_makes_confirmation_work_again(p2_client) -> None:
    """되돌리면 막힌 것이 풀린다 — 상태이지 도장이 아니다."""
    client = p2_client()
    parent = _created(client, level="Lv2")
    child = _created(client, level="Lv2", parents=[parent])
    client.patch(f"{API_PREFIX}/datasets/{child}",
                 json={"processingLevelUserSet": "Lv1"}, headers=auth(TOKEN_RES))
    client.patch(f"{API_PREFIX}/datasets/{child}",
                 json={"processingLevelUserSet": "Lv2"}, headers=auth(TOKEN_RES))
    conf = client.post(f"{API_PREFIX}/datasets/{child}/lineage/confirmation",
                       headers=auth(TOKEN_RES))
    assert conf.status_code == 200, conf.text


# ═══════════ ㈓ 사람 값·파생값·불일치 셋 다 (PRD-10 수용 기준) ═══════════
def test_detail_carries_all_three_and_prefers_the_human_value(p2_client) -> None:
    client = p2_client()
    parent = _created(client, level="Lv2")
    child = _created(client, level="Lv2", parents=[parent])
    detail = _read(client, child)
    assert detail["processingLevel"] == 2, detail["processingLevel"]
    basic = detail["basicInfo"]
    assert basic["processingLevelDerived"] == 1, basic
    assert basic["processingLevelMismatch"] is True, basic
    assert basic["processingLevelUserSet"] == "Lv2"


def test_a_row_without_a_human_value_is_never_a_mismatch(p2_client) -> None:
    """사람 값 NULL 행은 불일치가 **정의되지 않는다** — `false` 다(PRD-10 기존 데이터)."""
    client = p2_client()
    parent = _created(client, level="Lv0")
    child = _created(client, parents=[parent])
    detail = _read(client, child)
    assert detail["basicInfo"]["processingLevelMismatch"] is False, detail
    assert detail["processingLevel"] == 1, detail
    assert detail["basicInfo"]["processingLevelDerived"] == 1, detail


def test_the_row_type_carries_the_two_keys_too(p2_client) -> None:
    """`DatasetRow` 도 두 열쇠를 싣는다 — 목록이 상세와 다른 사실을 말하지 않는다."""
    client = p2_client()
    parent = _created(client, level="Lv2")
    child = _created(client, level="Lv2", parents=[parent])
    row = next(r for r in _rows(client, processingLevel=2) if r["datasetId"] == child)
    assert row["processingLevel"] == 2 and row["processingLevelDerived"] == 1
    assert row["processingLevelMismatch"] is True, row


def test_a_mismatch_never_blocks_saving(p2_client) -> None:
    """불일치는 **경고만**이다 — 저장이 성공한다(미결-2 ⓐ)."""
    client = p2_client()
    parent = _created(client, level="Lv0")
    r = _make(client, level="Lv3", parents=[parent])
    assert r.status_code == 201, r.text
    assert r.json()["basicInfo"]["processingLevelMismatch"] is True, r.text
