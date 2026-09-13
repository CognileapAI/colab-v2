"""`searchDatasets` 의 **범위 줄이 실제로 뒤진 범위를 말한다** (`R-LTH-REVIEW-1` Task 2 · spec §6 ㉰).

실측된 결함(조사 `dev-package/reports/issues/2026-09-13-lth-survey-A.md` §4-7) —
  · 분모 = `searched_count = d3_catalog.count_datasets(db)` 가 **요청 트랜잭션**(`scoped_db`)에서
    돌고, 검색은 `POST` 라 `deps._operator_read` 가 거짓이다 ⟹ 운영자도 **자기 연구실만** 센다.
  · 결과 = `with read_only_scope(..., operator_read=subject.operator)` 에서 돈다 ⟹ 운영자는
    **전 연구실**을 뒤진다.
  ⟹ 화면의 「{labName} 데이터 {searchedCount}건을 뒤졌어요」가 **뒤진 범위보다 작은 수**를 말한다.

이 파일의 오라클 둘 —
  ⑴ `searchedCount` = **결과와 같은 유효 스코프**에서 센 값. 판정은 라우트가 쓰는 것과
     같은 스코프(`read_only_scope(..., operator_read=subject.operator)`)를 시험이 직접 열어
     센 값과 대조한다 — 상수 2·3 을 시험에 박으면 시드가 바뀔 때 오라클이 거짓이 된다.
  ⑵ `labName` = **유효 연구실 집합의 표기**. 운영자는 상단 칩과 같은 말(「전체 연구실 (읽기 전용)」),
     일반 구성원은 소속 연구실 이름.

green-by-skip 방지(spec §8-6 ⑵) = **연구실 2개 ＋ 양쪽에 데이터셋**이 전제다. 한 연구실만 심으면
두 스코프가 우연히 같아져 통과한다 — 그래서 아래 `two_labs_with_datasets` 가 「두 수가 다르다」를
먼저 단언하고, 그 전제가 깨지면 이 파일 전체가 red 다.

⚠ 경계 회귀 = 일반 구성원의 분모는 **넓어지지 않는다**(`CLAUDE.md §3` 규칙 5). 대조군이 그것을 잰다.
"""
from __future__ import annotations

import pytest
from conftest import ACC_A_RES, LAB_A, LAB_B, TOKEN_RES, auth
from test_search_relay import _ai_body, fake_ai  # noqa: F401  (픽스처 재사용)

from colab_core.app.main import API_PREFIX

SEARCH = f"{API_PREFIX}/dataset-searches"
TERMS = ["강우"]

#: 운영자 범위 표기 — 상단 셸 칩(`frontend/src/shell/Gnb.tsx` 앵커 `연구실 전환 · 전체 연구실 (읽기 전용)`)과
#: **같은 말**이다. 두 자리가 다른 말을 하면 사용자가 같은 범위를 두 이름으로 읽는다.
OPERATOR_SCOPE_LABEL = "전체 연구실 (읽기 전용)"
OPERATOR_TOKEN = "lth-operator-token"


def _subject(*, operator: bool):
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    return Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A), operator=operator)


def _visible_datasets(session_factory, *, operator: bool) -> int:
    """라우트의 **결과 스코프와 같은 인자**로 열어 센다."""
    from colab_core.domains import d3_catalog
    from colab_core.kernel.scope import read_only_scope

    subject = _subject(operator=operator)
    with read_only_scope(session_factory, subject, operator_read=subject.operator) as ro:
        return d3_catalog.count_datasets(ro)


@pytest.fixture()
def two_labs_with_datasets(sql, session_factory) -> tuple[int, int]:
    """전제 = 연구실 2개에 각각 데이터셋 1건 이상이고, **두 스코프의 수가 다르다**."""
    own = sql("SELECT count(*) AS n FROM d3_dataset WHERE lab_id=:lab AND deleted_at IS NULL",
              {"lab": LAB_A})[0]["n"]
    assert own >= 1, "소속 연구실에 데이터셋이 없으면 분모 시험이 오라클이 아니다."
    every = _visible_datasets(session_factory, operator=True)
    other = every - own
    assert other >= 1, (
        f"다른 연구실의 데이터셋이 {other}건이다 — 연구실 2개 ＋ 양쪽에 데이터셋이 아니면 "
        "두 스코프가 우연히 같아져 통과한다(spec §8-6 ⑵).")
    return own, every


@pytest.fixture()
def operator_client(p2_client, fake_ai):  # noqa: F811
    """운영자 주체를 토큰 하나에 심는다.

    정적 주체 표(`tests/fixtures/subjects.json`)에 운영자 칸이 없고, 지정 흐름 전체
    (계정 생성 → 지정 → 로그인)는 이 시험의 대상이 아니다 — 대상은 **라우트가
    `subject.operator` 를 어떤 스코프로 읽는가** 하나다. 주체 밖의 것은 바꾸지 않는다.
    """
    fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A)

    def build(*, is_data_query: bool = True):
        fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A, is_data_query=is_data_query)
        client = p2_client(ai_base_url=fake_ai["url"])
        inner = client.app.state.authenticators
        operator = _subject(operator=True)

        class _WithOperator:
            adapters = getattr(inner, "adapters", ())

            def resolve(self, token: str):
                return operator if token == OPERATOR_TOKEN else inner.resolve(token)

        client.app.state.authenticators = _WithOperator()
        return client

    return build


def _scope_of(client, token: str) -> dict:
    r = client.post(SEARCH, json={"query": "강우"}, headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()["scope"]


# ════════ ⑴ 분모는 결과와 같은 스코프에서 나온다 ════════

def test_an_operator_search_counts_every_lab_it_actually_searched(
        operator_client, session_factory, two_labs_with_datasets) -> None:
    """운영자의 결과는 전 연구실에서 오고, **분모도 그 범위**여야 한다."""
    own, every = two_labs_with_datasets
    scope = _scope_of(operator_client(), OPERATOR_TOKEN)
    assert scope["searchedCount"] == every, (
        f"운영자가 뒤진 범위는 {every}건인데 범위 줄은 {scope['searchedCount']}건을 말한다 — "
        f"소속 연구실({own}건)만 센 값이면 화면이 뒤진 범위보다 작은 수를 말한다.")
    assert scope["searchedCount"] != own, \
        "두 스코프의 수가 같으면 이 시험은 오라클이 아니다(시드 전제가 깨졌다)."


def test_a_member_search_counts_only_its_own_lab(
        p2_client, fake_ai, session_factory, two_labs_with_datasets) -> None:  # noqa: F811
    """대조군 = 일반 구성원의 분모는 **넓어지지 않는다**(`CLAUDE.md §3` 규칙 5)."""
    own, every = two_labs_with_datasets
    fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A)
    scope = _scope_of(p2_client(ai_base_url=fake_ai["url"]), TOKEN_RES)
    assert scope["searchedCount"] == own, \
        f"일반 구성원의 분모가 소속 연구실({own}건)이 아니다: {scope['searchedCount']}건."
    assert scope["searchedCount"] == _visible_datasets(session_factory, operator=False)
    assert scope["searchedCount"] < every, "일반 구성원의 분모가 전 연구실 셈으로 넓어졌다."


def test_the_count_is_filled_even_when_the_question_is_not_a_data_query(
        operator_client, two_labs_with_datasets) -> None:
    """`isDataQuery` 가 거짓이어도 범위 줄이 먼저 선다 — 0건에도 범위·개수는 남는다."""
    _own, every = two_labs_with_datasets
    scope = _scope_of(operator_client(is_data_query=False), OPERATOR_TOKEN)
    assert scope["searchedCount"] == every, \
        "데이터 질문이 아닌 갈래에서 분모가 결과 스코프와 갈렸다."


# ════════ ⑵ 범위 줄의 이름이 유효 연구실 집합을 말한다 ════════

def test_an_operator_scope_is_named_as_the_set_it_searched(
        operator_client, two_labs_with_datasets) -> None:
    scope = _scope_of(operator_client(), OPERATOR_TOKEN)
    assert scope["labName"] == OPERATOR_SCOPE_LABEL, (
        f"운영자 범위 줄이 소속 연구실 이름을 말한다: {scope['labName']!r} — "
        f"상단 칩과 같은 말({OPERATOR_SCOPE_LABEL!r})이어야 한다.")


def test_a_member_scope_is_named_after_its_own_lab(p2_client, fake_ai) -> None:  # noqa: F811
    fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A)
    scope = _scope_of(p2_client(ai_base_url=fake_ai["url"]), TOKEN_RES)
    assert scope["labName"] == "A 연구실", \
        f"일반 구성원 범위 줄이 소속 연구실 이름이 아니다: {scope['labName']!r}."


def test_the_scope_keeps_a_required_ulid_lab_id_for_both(operator_client, p2_client,
                                                         fake_ai) -> None:  # noqa: F811
    """계약 무변 = `AiSearchScope.labId` 는 필수 `Ulid` 로 **남는다**(spec §6 ㉰).

    운영자 응답에서도 소속 연구실 id 가 실리고 `labName` 만 집합을 말한다 — 의미 불일치는
    스펙에 명시된 것이고, `scopeKind` 류 열쇠를 신설하지 않는다.
    """
    from colab_core.kernel.ids import Ulid

    operator_scope = _scope_of(operator_client(), OPERATOR_TOKEN)
    assert Ulid.is_valid(operator_scope["labId"]), operator_scope["labId"]
    assert operator_scope["labId"] == LAB_A
    assert LAB_B not in operator_scope["labId"]

    fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A)
    member_scope = _scope_of(p2_client(ai_base_url=fake_ai["url"]), TOKEN_RES)
    assert Ulid.is_valid(member_scope["labId"])
    assert set(operator_scope) == set(member_scope) == {"labId", "labName", "searchedCount"}, \
        "범위 열쇠가 늘거나 줄었다 — 계약(`additionalProperties: false`)이 깨진다."
