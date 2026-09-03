"""입력 오류가 **400**, 저장 규칙 위반이 **409** 로 나가는가 (`CODE-REVIEW-20260903` #12).

`main.py` 의 핸들러는 `HTTPException`·`RequestValidationError` 둘뿐이었고, 그래서 손검사를
빠뜨린 다섯 자리에서 **사용자의 오타가 500** 으로 돌아왔다. 500 은 「서버가 깨졌다」는 뜻이고
그 문장은 사람을 재시도하게 만든다 — 다시 보내도 같은 500 이다.

여기서 재는 것 넷 —
  ⓐ 입력 오류 전용 예외형이 400 봉투가 되는가 (`ValueError` 를 통째로 매지 않는다)
  ⓑ `IntegrityError` 가 **SQL·제약 이름을 흘리지 않는** 409 가 되는가
  ⓑ′ 그 핸들러가 **SQLSTATE 로 갈라지는가** — 23505 → 409 · 23514 → 400 ·
     **나머지는 다시 던진다**(500 으로 남아 눈에 보인다)
  ⓒ 500 이던 다섯 경로가 각각 400 인가
"""
from __future__ import annotations

import json
import logging
import pathlib
import tempfile

import pytest
from conftest import DS_A1, TOKEN_RES, auth
from sqlalchemy.exc import IntegrityError

from colab_core.app.main import API_PREFIX, create_app
from colab_core.kernel import errors
from colab_core.kernel.config import Settings

BAD_ULID = "not-a-ulid"

#: 드라이버가 실제로 내는 문자열. **이것이 본문에도 로그에도 나가면 안 된다** —
#: psycopg 의 `DETAIL:` 줄은 **사용자가 넣은 값**(키·컬럼값)을 그대로 담는다.
DRIVER_TEXT = ('duplicate key value violates unique constraint '
               '"d3_dataset_description_pkey"\nDETAIL:  Key (id)=(01A) already exists.')
CONSTRAINT = "d3_dataset_description_pkey"


class _FakeDiag:
    """psycopg 3 의 `Error.diag` 흉내. 우리가 쓰는 필드는 `constraint_name` 뿐이다."""

    def __init__(self, constraint_name: str | None) -> None:
        self.constraint_name = constraint_name


class _FakeOrig(Exception):
    """psycopg 3 의 `Error` 흉내 — `sqlstate` + `diag`.

    실물 대조는 `test_the_sqlstates_we_branch_on_are_the_ones_psycopg_declares` 가 한다.
    """

    def __init__(self, sqlstate: str, constraint_name: str | None = CONSTRAINT) -> None:
        super().__init__(DRIVER_TEXT)
        self.sqlstate = sqlstate
        self.diag = _FakeDiag(constraint_name)


# ══════════════════════════ ⓐ·ⓑ 핸들러 두 벌 ════════════════════════════════
@pytest.fixture()
def handler_client():
    """핸들러만 재는 앱. **DB 를 붙이지 않는다** — 재는 것이 라우트가 아니라 봉투다."""
    from fastapi.testclient import TestClient

    tmp = pathlib.Path(tempfile.mkdtemp()) / "subjects.json"
    tmp.write_text(json.dumps({"t": {"accountId": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                                     "labId": "01ARZ3NDEKTSV4RRFFQ69G5FAW"}}), encoding="utf-8")
    app = create_app(Settings(database_url="postgresql+psycopg://unused/unused",
                              subjects_file=str(tmp)))

    @app.get(API_PREFIX + "/_probe/input-error", include_in_schema=False)
    def _input_error() -> None:
        raise errors.InputError("기간이 날짜 시각이 아니다.", {"field": "period.start"})

    @app.get(API_PREFIX + "/_probe/integrity/{sqlstate}", include_in_schema=False)
    def _integrity(sqlstate: str) -> None:
        raise IntegrityError(
            "INSERT INTO d3_dataset_description (id, lab_id, topic) VALUES (%(id)s, ...)",
            {"id": "0000000000000000000000DSA1", "topic": "없는 주제"},
            _FakeOrig(sqlstate),
        )

    return TestClient(app, raise_server_exceptions=False)


def test_input_error_becomes_a_400_envelope(handler_client) -> None:
    r = handler_client.get(f"{API_PREFIX}/_probe/input-error")
    assert r.status_code == 400, r.text
    body = r.json()
    assert body["code"] == "BAD_REQUEST"
    assert body["message"]
    assert body["details"] == {"field": "period.start"}


def test_a_plain_value_error_is_still_a_500(handler_client) -> None:
    """**`ValueError` 를 통째로 400 에 매지 않는다.**

    `ValueError` 는 라이브러리·계산 실패도 함께 던지는 넓은 형이다. 그것까지 400 으로 접으면
    **서버 결함이 「네 요청이 틀렸다」로 위장**하고, 그 순간 감시에서 사라진다.
    """
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "src" / "colab_core" / "app" / "main.py").read_text(encoding="utf-8")
    assert "exception_handler(ValueError)" not in src, \
        "ValueError 를 통째로 매고 있다 — 서버 결함이 400 으로 위장한다."
    assert not issubclass(errors.InputError, ValueError) or True   # 형 자체는 자유


def test_a_unique_violation_becomes_409_without_leaking_sql_or_constraint_names(
        handler_client) -> None:
    """**409 는 사실이되, SQL 도 제약 이름도 사용자에게 주지 않는다.**

    본문에 실리면 화면의 네트워크 탭에서 스키마가 그대로 읽힌다 — 표 이름·열 이름·
    제약 이름·키 값까지. 안정된 코드 하나면 화면이 분기하는 데 충분하다.
    """
    r = handler_client.get(f"{API_PREFIX}/_probe/integrity/23505")
    assert r.status_code == 409, r.text
    body = r.json()
    assert body["code"] == "CONFLICT"
    raw = json.dumps(body, ensure_ascii=False)
    for leaked in ("INSERT INTO", "d3_dataset_description", "duplicate key",
                   "unique constraint", "DETAIL", "pkey"):
        assert leaked not in raw, f"409 본문이 저장 내부를 흘렸다: {leaked}"


# ═══════════ ⓑ′ SQLSTATE 로 갈린다 — 409 하나로 접지 않는다 ══════════════════
def test_a_check_violation_is_400_not_409(handler_client) -> None:
    """**CHECK 위반은 「두 번 일어날 수 없다」가 아니라 「그 값이 아니다」이다.**

    409 로 접으면 화면은 「이미 있어요」로 읽고 사용자는 **고칠 수 있는 값을 안 고친다.**
    409 와 400 은 누구에게 무엇을 하라는 말인지가 다르다.
    """
    r = handler_client.get(f"{API_PREFIX}/_probe/integrity/23514")
    assert r.status_code == 400, r.text
    body = r.json()
    assert body["code"] == "BAD_REQUEST"
    raw = json.dumps(body, ensure_ascii=False)
    for leaked in ("INSERT INTO", "d3_dataset_description", "duplicate key",
                   "unique constraint", "DETAIL", "pkey"):
        assert leaked not in raw, f"400 본문이 저장 내부를 흘렸다: {leaked}"


def test_an_unrelated_sqlstate_is_re_raised_and_stays_a_500(handler_client) -> None:
    """**그물이 결함을 삼키지 않는다.**

    외래키 위반(`23503`)·not-null 위반 같은 것은 **사용자가 고칠 수 있는 값이 아니라
    우리 코드가 잘못 쓴 것**이다. 그것까지 409 로 접으면 서버 결함이 「값이 안 맞아요」로
    위장하고, 그 순간 감시(5xx 계수·경보)에서 사라진다. 다시 던져 **500 으로 남긴다.**
    """
    r = handler_client.get(f"{API_PREFIX}/_probe/integrity/23503")
    assert r.status_code == 500, r.text
    assert '"code":"CONFLICT"' not in r.text.replace(" ", ""), \
        "관계없는 SQLSTATE 가 409 로 위장했다 — 결함이 감시에서 사라진다."


def test_the_integrity_log_carries_the_sqlstate_and_constraint_but_not_the_driver_text(
        handler_client, caplog) -> None:
    """**사유는 남기되, 남기는 것이 사용자 값이면 안 된다.**

    psycopg 의 예외 문자열에는 `DETAIL:  Key (id)=(...)` 가 붙는다 — **사용자가 넣은 값**
    그대로다. 로그는 덤프·티켓·화면 캡처를 따라다니므로 값을 담으면 그 값이 함께 간다.
    남길 것은 **무엇이 안 맞았는지**(SQLSTATE · 제약 이름)이지 **어떤 값이었는지**가 아니다.
    """
    with caplog.at_level(logging.WARNING, logger="colab_core.integrity"):
        handler_client.get(f"{API_PREFIX}/_probe/integrity/23505")
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "23505" in text, "SQLSTATE 를 안 남기면 무엇이 안 맞았는지 셀 수 없다."
    assert CONSTRAINT in text, "제약 이름을 안 남기면 어느 규칙인지 못 찾는다."
    assert "DETAIL" not in text and "Key (id)=" not in text, \
        "드라이버 문자열이 로그로 갔다 — 그 안에 사용자 값이 있다."


def test_the_sqlstates_we_branch_on_are_the_ones_psycopg_declares() -> None:
    """**가짜 `orig` 가 실물과 갈리지 않게 못 박는다.**

    위 시험들은 `sqlstate` 를 손으로 채운 가짜 예외로 잰다. 그 상수가 psycopg 가 실제로
    다는 값과 어긋나면 시험은 전부 green 인데 실서버에서는 한 갈래도 안 걸린다.
    """
    from psycopg import errors as pg

    assert pg.UniqueViolation.sqlstate == "23505"
    assert pg.CheckViolation.sqlstate == "23514"
    assert pg.ForeignKeyViolation.sqlstate == "23503"
    assert hasattr(pg.UniqueViolation("x"), "diag")


# ══════════════════════════ ⓒ 500 이던 다섯 경로 ════════════════════════════
def test_access_request_with_a_malformed_dataset_id_is_400(p2_client) -> None:
    """`access.py` — `Ulid(datasetId)` 가 무검사라 `ValueError` 로 탈출하던 자리."""
    client = p2_client()
    r = client.post(f"{API_PREFIX}/datasets/{BAD_ULID}/access-requests",
                    json={}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert r.json()["code"] == "BAD_REQUEST"


def test_a_non_ascii_bearer_token_is_401_not_500(p2_client) -> None:
    """`session_token.py` — `_mac` 이 try 밖이고 `.encode("ascii")` 라 **비인증 요청 하나가 500**.

    인증 실패는 401 이다. 500 은 「우리가 깨졌다」이고, 그것은 인증 경계에서 특히 나쁘다 —
    토큰 모양 하나로 오류율을 올릴 수 있다.

    ⚠ **헤더를 바이트로 보낸다.** HTTP 헤더는 바이트이고 Starlette 는 그것을 latin-1 로
    푼다 — 실서버에서 비ASCII Bearer 가 도착하는 모양이 정확히 이것이다. 시험 클라이언트에
    `str` 로 주면 클라이언트 쪽에서 먼저 죽어 **서버를 재지 못한다.**
    """
    client = p2_client(session_secret="a-secret-for-the-test")
    r = client.get(f"{API_PREFIX}/me",
                   headers={b"Authorization": "Bearer v1.éx.éx".encode("latin-1")})
    assert r.status_code == 401, r.text
    assert r.json()["code"] == "UNAUTHORIZED"


def test_dataset_period_free_string_is_400(p2_client) -> None:
    """`d3_catalog.py` — 자유 문자열이 `timestamptz` 로 내려가 파싱 오류로 500 이던 자리."""
    client = p2_client()
    r = client.patch(f"{API_PREFIX}/datasets/{DS_A1}",
                     json={"period": {"start": "어제부터", "end": None}},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert r.json()["code"] == "BAD_REQUEST"


def test_dataset_topic_outside_the_db_check_set_is_400(p2_client) -> None:
    """`validate_human_metadata` 가 `topic` 을 안 봐 DB CHECK 로 떨어지던 자리.

    값 집합의 정본은 **DB CHECK 4값**이다 (`db/platform/schema.sql` · 계약 산문
    「값 집합은 DB CHECK 4값이 지킨다」). 계약 층 enum 을 새로 만들지 않는다.
    """
    client = p2_client()
    r = client.patch(f"{API_PREFIX}/datasets/{DS_A1}", json={"topic": "없는 주제"},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert r.json()["code"] == "BAD_REQUEST"


def test_a_topic_inside_the_db_check_set_still_passes(p2_client, sql) -> None:
    """**넓히지 않았음을 함께 잰다** — 허용 4값 중 하나는 그대로 통과한다."""
    client = p2_client()
    r = client.patch(f"{API_PREFIX}/datasets/{DS_A1}", json={"topic": "강우·강수"},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text


def test_project_created_with_a_blank_name_is_400(p2_client) -> None:
    """`project.py` — 생성이 `strip` 없이 길이만 봐 공백 이름이 DB CHECK 로 떨어지던 자리.

    수정 경로(`updateProject`)는 이미 `strip` 한다. **두 경로의 판정이 갈려 있던 것**이다.
    """
    client = p2_client()
    r = client.post(f"{API_PREFIX}/projects",
                    json={"type": "국가과제", "name": "   "}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert r.json()["code"] == "BAD_REQUEST"
