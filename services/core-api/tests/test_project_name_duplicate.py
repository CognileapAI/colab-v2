"""PRD-42 · WU-A7R — **빠른 프로젝트 생성의 이름 중복 검사**.

판정은 **연구실 경계 안**이고, 유형(`type`)이 달라도 같은 이름이면 겹침이다.
거절은 **400 ＋ rev2 축자 문면** 하나로 온다 — 화면이 그 문면을 그대로 띄운다
(`업로드_계보_260905_rev2_이태헌.html` `makeQuickProj()` · `toast('…')`).

⚠ **빈 이름 문면은 이 회차가 고치지 않는다** (`Policy_프로젝트 §9` 가 정본이고 이긴다).
⚠ **DB UNIQUE 제약을 이번에 걸지 않는다** — 응용 층 검사다. 기존에 겹치는 행은
   지우거나 고치지 않고 **신규 생성만** 막는다(라운드 파일 §2-③ 축자).

경계 시험이 **다른 연구실**을 쓴다 — 그쪽 행은 `p2_client` 정리(`LAB_A` 스코프)가
닿지 않는다. 그래서 시험이 **자기가 만든 B 연구실 행을 스스로 지운다**(`deleteProject`
는 데이터셋 0건일 때 열린다). 안 지우면 다음 회차에서 B 연구실 안의 중복이 되어 이
시험의 오라클이 뒤집히고, `test_project_screens` 의 연구실 경계 시험이 그 잔존 행을
세어 함께 깨진다(실측).
"""
from __future__ import annotations

from conftest import TOKEN_B, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

#: rev2 축자. 한 글자도 바꾸지 않는다.
DUPLICATE_NAME_MESSAGE = "같은 이름의 프로젝트가 이미 있어요. 목록에서 골라 주세요"


def _create(client, name: str, *, type_: str = "국가과제", token: str = TOKEN_RES):
    return client.post(f"{API_PREFIX}/projects",
                       json={"type": type_, "name": name}, headers=auth(token))


def test_same_name_in_the_same_lab_is_refused_with_the_rev2_message(p2_client) -> None:
    client = p2_client()
    name = "중복 검사용 이름 A"
    assert _create(client, name).status_code == 201
    r = _create(client, name)
    assert r.status_code == 400, r.text
    assert r.json()["message"] == DUPLICATE_NAME_MESSAGE


def test_a_different_kind_with_the_same_name_is_refused_too(p2_client) -> None:
    """유형이 갈려도 겹침이다 — PRD-42 수용 기준 2행."""
    client = p2_client()
    name = "중복 검사용 이름 B"
    assert _create(client, name, type_="국가과제").status_code == 201
    r = _create(client, name, type_="논문")
    assert r.status_code == 400, r.text
    assert r.json()["message"] == DUPLICATE_NAME_MESSAGE


def test_the_same_name_in_another_lab_succeeds(p2_client) -> None:
    """판정은 **연구실 경계 안**이다 — 남의 연구실 이름이 내 생성을 막지 않는다."""
    client = p2_client()
    name = "다른 연구실 동명 확인"
    assert _create(client, name).status_code == 201
    r = _create(client, name, token=TOKEN_B)
    assert r.status_code == 201, r.text
    made = r.json()["projectId"]
    try:
        # 같은 이름이 B 쪽에도 실제로 섰다 — 201 이 빈 성공이 아니다
        assert r.json()["name"] == name
    finally:
        # B 연구실 행은 `p2_client` 정리가 닿지 않는다. 시험이 스스로 되돌린다.
        assert client.delete(f"{API_PREFIX}/projects/{made}",
                             headers=auth(TOKEN_B)).status_code == 204


def test_the_empty_name_message_is_untouched(p2_client) -> None:
    """⚠ **정본 문면 유지** — 중복 문면을 붙이면서 이 자리를 건드리지 않았다."""
    client = p2_client()
    r = _create(client, "   ")
    assert r.status_code == 400, r.text
    assert r.json()["message"] != DUPLICATE_NAME_MESSAGE
