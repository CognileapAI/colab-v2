"""자동완성 후보 — **이미 쓰인 말만 돌려준다** (`listDatasetFieldSuggestions`).

근거 = `_결정_업로드계보_260826.md §2-10` · `PLAN-SoT §9 〈138〉` · `VAL-006`·`VAL-009`.

정본이 변수·좌표계·원천 표기를 **자유 입력**으로 두었으므로 같은 것을 두 사람이 다르게
적는 일이 생긴다 — `ERA5` / `era5` / `ECMWF ERA5` / `ERA-5`. 결정 2-10 이 대가를 적어
뒀다: **「데이터가 쌓인 뒤의 소급 정리는 사람이 하나씩 묶어야 하므로 입력 단계 차단과
비용 차이가 크다」**, 그리고 원천은 **계보 그래프의 뿌리 노드**라 파편화되면 그래프
상단이 통째로 갈라진다.
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth

from colab_core.app.main import API_PREFIX


def _get(client, **params):
    return client.get(f"{API_PREFIX}/dataset-field-suggestions",
                      params=params, headers=auth(TOKEN_RES))


def test_an_unknown_field_is_rejected_not_silently_empty(p2_client) -> None:
    """**모르는 칸은 400 이다.**

    계약이 값 집합을 enum 으로 박지 않았으므로(`NB-E`) 여기가 유일한 관문이다.
    조용히 빈 목록을 내면 화면이 「후보가 없다」로 읽고 **오타 난 필드 이름이 영원히
    안 드러난다** — 자동완성이 안 뜨는데 아무도 이유를 모른다.
    """
    r = _get(p2_client(), field="소스라벨")
    assert r.status_code == 400, r.text
    assert "sourceLabel" in r.text, "무엇이 허용되는지 함께 말한다"


def test_method_is_not_suggestable_here_because_it_belongs_to_d9(p2_client) -> None:
    """**`가공 방식` 은 이 op 의 것이 아니다** — 경계를 지키는 음성 시험.

    그 어휘는 D9 온톨로지 시드가 소유하고(`d9_method_term`, 결정 2-11) **core-api 는
    그 저장소에 붙지 않는다**(`CLAUDE.md §3-1`·`§3-3`). 편하다고 여기 넣으면
    불변규칙을 깬다. **막는 것이 아니라 다른 표면으로 가는 것이다.**
    """
    r = _get(p2_client(), field="method")
    assert r.status_code == 400, "D9 어휘를 core-api 가 내주면 안 된다"


def test_an_empty_result_is_normal_and_is_not_an_error(p2_client) -> None:
    """**첫 사람은 후보가 없다.** 빈 목록이 정상이고 억지로 채우지 않는다."""
    r = _get(p2_client(), field="sourceLabel", q="존재하지않을낱말")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["field"] == "sourceLabel"
    assert body["items"] == []


def test_the_shape_matches_the_contract(p2_client) -> None:
    r = _get(p2_client(), field="crs")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"field", "items"}
    for item in body["items"]:
        assert set(item) == {"value", "useCount"}
        assert isinstance(item["value"], str) and item["value"]
        assert isinstance(item["useCount"], int) and item["useCount"] >= 1


def test_a_wildcard_in_the_query_is_a_letter_not_a_pattern(p2_client) -> None:
    """**`%` 를 친 사람이 전체를 훑지 않는다.**

    `ILIKE` 특수문자를 그대로 넘기면 `%` 한 글자가 「전부」가 된다. 검색이 아니라
    자동완성이므로 사용자가 그걸 의도했을 리 없고, 의도했다면 더 문제다.
    """
    r = _get(p2_client(), field="sourceLabel", q="%")
    assert r.status_code == 200, r.text
    assert r.json()["items"] == [], "`%` 는 글자다 — 전체를 돌려주면 안 된다"


def test_limit_is_bounded(p2_client) -> None:
    assert _get(p2_client(), field="crs", limit=0).status_code == 400
    assert _get(p2_client(), field="crs", limit=21).status_code == 400
    assert _get(p2_client(), field="crs", limit=20).status_code == 200


def test_it_needs_a_subject(p2_client) -> None:
    """경계는 주체에서 나온다 — 토큰이 없으면 401 이다."""
    r = p2_client().get(f"{API_PREFIX}/dataset-field-suggestions",
                        params={"field": "crs"})
    assert r.status_code == 401, r.text
