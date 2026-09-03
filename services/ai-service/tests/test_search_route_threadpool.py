"""`POST /searches` 는 **스레드풀에서 돈다** (코드리뷰 20260903 #10 형제).

`search_datasets` 가 `async def` 인데 본문에서 막는 일을 한다 — `dictionaries.py` 의
사전 조회 5 SELECT 는 동기 psycopg 이고, `llm` 모드에서는 `interpret.py` 의
`urlopen(timeout=8)` 이 최대 8초를 붙든다. 코루틴 안에서 그러면 **이벤트 루프가 통째로
멈춘다** — uvicorn 워커가 하나라 같은 프로세스의 `/healthz` 까지 답을 못 하고,
compose 의 헬스 체크(3초)가 그 사이에 지나간다.

FastAPI 는 **`def` 로 선언된 라우트를 스레드풀에서** 돌린다. 그래서 이 한 줄이
「막는 일을 루프 밖으로 뺀다」의 전부다. 본문 읽기(`await request.body()`)만
비동기 의존으로 남는다 — **읽기는 루프에서, 판단은 스레드풀에서.**

⚠ 이 시험은 **DB 없이** 돈다 — `COLAB_AI_TEST_DICT_DB_URL` 을 쓰지 않는다.
「AI 없이도 v2 는 완결된 제품이다」가 이 표면에서 참인지 함께 본다.
"""
from __future__ import annotations

import inspect

from colab_ai.app.main import create_app
from colab_ai.kernel.config import Settings
from fastapi.testclient import TestClient

LAB = "0000000000000000000000000A"
ACC = "000000000000000000000000A1"


def _app():
    """사전 DB 도 모델 키도 없는 판 — 이 단위의 최소 설정이다."""
    return create_app(Settings(dict_db_url=None, openai_api_key=None))


def _headers():
    return {"X-CoLAB-Lab": LAB, "X-CoLAB-Account": ACC}


def _body():
    return {"scope": {"labId": LAB, "labName": "A 연구실"}, "query": "강우 데이터 찾아줘"}


def _route(app, path: str):
    return next(r for r in app.routes if getattr(r, "path", None) == path)


def test_검색_라우트는_코루틴이_아니다():
    """코루틴이면 FastAPI 가 **이벤트 루프에서** 부른다 — 막는 일이 루프를 세운다."""
    fn = _route(_app(), "/searches").endpoint
    assert not inspect.iscoroutinefunction(fn), (
        "`search_datasets` 가 코루틴이다 — 동기 DB·LLM 호출이 이벤트 루프를 막는다")


def test_DB_없이도_검색어가_나온다():
    res = TestClient(_app()).post("/searches", json=_body(), headers=_headers())
    assert res.status_code == 200, res.text
    body = res.json()
    assert "강우" in body["interpretation"]["terms"]
    assert {"items", "totalCount", "nextCursor"} == set(body["results"])


def test_본문이_JSON_이_아니면_400_이다():
    """`def` 로 바꾸면서 본문 해석을 프레임워크에 넘기면 이 갈래가 422 로 바뀐다 —
    계약의 오류 봉투(`common.json#ErrorEnvelope`)를 유지한다."""
    res = TestClient(_app()).post(
        "/searches", content=b"{ this is not json",
        headers={**_headers(), "content-type": "application/json"})
    assert res.status_code == 400, res.text
    assert res.json()["code"] == "bad_request"


def test_본문이_객체가_아니면_400_이다():
    res = TestClient(_app()).post("/searches", json=[1, 2, 3], headers=_headers())
    assert res.status_code == 400, res.text
    assert res.json()["code"] == "bad_request"


def test_본문이_비어_있어도_400_이다():
    res = TestClient(_app()).post("/searches", headers=_headers())
    assert res.status_code == 400, res.text
    assert res.json()["code"] == "bad_request"


def test_경계_검사는_그대로다():
    """헤더와 본문의 연구실이 다르면 400 · 주체가 없으면 401 — 표면이 바뀌지 않았다."""
    client = TestClient(_app())
    other = "0000000000000000000000000B"
    assert client.post("/searches", json=_body(),
                       headers={"X-CoLAB-Lab": other, "X-CoLAB-Account": ACC}
                       ).status_code == 400
    assert client.post("/searches", json=_body(),
                       headers={"X-CoLAB-Lab": LAB}).status_code == 401
