"""PRD-42 · WU-A7R — **빠른 프로젝트 생성의 이름 중복 검사**.

판정은 **연구실 경계 안**이고, 유형(`type`)이 달라도 같은 이름이면 겹침이다.
거절은 **400 ＋ rev2 축자 문면** 하나로 온다 — 화면이 그 문면을 그대로 띄운다
(`업로드_계보_260905_rev2_이태헌.html` `makeQuickProj()` · `toast('…')`).

⚠ **빈 이름 문면은 이 회차가 고치지 않는다** (`Policy_프로젝트 §9` 가 정본이고 이긴다).
⭑ **⟨개정 2026-09-08 · WU-C7 · `0020`⟩ DB UNIQUE 제약이 섰다.**
／ 종전 ~~「DB UNIQUE 제약을 이번에 걸지 않는다 — 응용 층 검사다」~~ — 그 자리가 **유일한
   방어선**이라 그 함수를 안 타는 경로에서는 같은 이름이 그대로 들어갔다. 응용 400 은
   **문면을 주는 앞문**이고 `d6_project_lab_name_unique` 가 **뒷문**이다.
⚠ 기존에 겹치는 행은 여전히 지우거나 고치지 않는다 — 마이그레이션이 **멈추고 건수를 적는다**
   (그쪽 오라클은 `db/platform/tests/0020-drift.sh` ㈑ 다).

경계 시험이 **다른 연구실**을 쓴다 — 그쪽 행은 `p2_client` 정리(`LAB_A` 스코프)가
닿지 않는다. 그래서 시험이 **자기가 만든 B 연구실 행을 스스로 지운다**(`deleteProject`
는 데이터셋 0건일 때 열린다). 안 지우면 다음 회차에서 B 연구실 안의 중복이 되어 이
시험의 오라클이 뒤집히고, `test_project_screens` 의 연구실 경계 시험이 그 잔존 행을
세어 함께 깨진다(실측).
"""
from __future__ import annotations

import pytest
from conftest import ACC_B_PROF, LAB_B, TOKEN_B, TOKEN_RES, auth
from sqlalchemy.exc import IntegrityError

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


# ═══════ ⟨WU-C7 · `0020`⟩ 뒷문 — **앱을 우회해도 DB 가 거절한다** ══════════
#: 응용 층을 한 번도 타지 않는 경로. `routes/project.py` 의 400 은 여기서 안 돈다.
_RAW_INSERT = ("INSERT INTO d6_project (id, lab_id, type, name)"
               " VALUES (:id, current_lab_id(), '국가과제', :name)")


def test_the_db_refuses_a_duplicate_name_even_when_the_app_is_bypassed(p2_client, sql) -> None:
    """수용 기준 축자 — 「같은 연구실 같은 이름 INSERT 가 **DB 에서** 거절(앱 우회)」.

    red 만드는 법 — `ALTER TABLE d6_project DROP CONSTRAINT d6_project_lab_name_unique`.
    """
    client = p2_client()
    name = "DB 뒷문 확인용 이름"
    assert _create(client, name).status_code == 201
    with pytest.raises(IntegrityError):
        sql(_RAW_INSERT, {"id": "00000000000000000000000CX1", "name": name})


def test_the_same_name_in_another_lab_still_passes_the_db(p2_client, sql) -> None:
    """판정 축은 **연구실 경계 안**이다 — 제약이 `(lab_id, name)` 두 칸이라 남의 연구실은 통과한다.

    ⚠ B 연구실 행은 `p2_client` 정리(`LAB_A` 스코프)가 닿지 않는다 — **스스로 지운다**.
    """
    client = p2_client()
    name = "DB 뒷문 · 다른 연구실 동명"
    assert _create(client, name).status_code == 201
    made = "00000000000000000000000CX2"
    try:
        sql(_RAW_INSERT, {"id": made, "name": name},
            account_id=ACC_B_PROF, lab_id=LAB_B)
        left = sql("SELECT count(*) AS n FROM d6_project WHERE id = :id", {"id": made},
                   account_id=ACC_B_PROF, lab_id=LAB_B)[0]["n"]
        assert left == 1, "다른 연구실의 동명이 서지 않았다 — 제약이 연구실을 안 가른다."
    finally:
        sql("DELETE FROM d6_project WHERE id = :id", {"id": made},
            account_id=ACC_B_PROF, lab_id=LAB_B)


def test_the_constraint_is_two_columns_not_three(sql) -> None:
    """⛔ 열쇠에 `type` 이 섞이면 유형이 다른 동명이 뒷문을 통과한다(PRD-42 수용 기준 2행)."""
    cols = sql("""
        SELECT string_agg(a.attname, ',' ORDER BY k.ord) AS cols
          FROM pg_constraint c
          JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
          JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
         WHERE c.conrelid = 'd6_project'::regclass
           AND c.conname = 'd6_project_lab_name_unique'
    """)[0]["cols"]
    assert cols == "lab_id,name", f"제약 열쇠가 {cols!r} 다 (기대 lab_id,name)."
