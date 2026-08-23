"""자격 증명이 배선되지 않은 인스턴스 — **열리지 않는다.**

「토큰이 설정 안 됐으니 통과」는 인증을 끄는 것이고, 그것이 v1 의 green-by-skip 과
같은 모양이다. 헬스만 살고 렌더 표면은 503 이다.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from colab_viz.app.main import create_app
from colab_viz.kernel.config import Settings


def _client(tmp_path):
    return TestClient(create_app(Settings(source_root=tmp_path, service_token=None)))


def test_헬스는_살아_있다(tmp_path):
    r = _client(tmp_path).get("/healthz")
    assert r.status_code == 200
    assert r.json()["unit"] == "viz-render"


def test_렌더_표면은_503_이지_통과가_아니다(tmp_path):
    c = _client(tmp_path)
    assert c.get("/viz/v1/palettes").status_code == 503
    # 아무 토큰이나 들이밀어도 503 이다 — 「설정 안 됨」이 「아무나 통과」가 되지 않는다
    assert c.get("/viz/v1/palettes", headers={"Authorization": "Bearer anything"}
                 ).status_code == 503
