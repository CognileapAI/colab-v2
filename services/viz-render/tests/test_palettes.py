"""listPalettes — `RenderStyle.palette` 의 값 출처. (`D2c` C1 열린 항목 ① 을 여기서 닫는다)

정본은 **「팔레트 3종」까지만** 말하고 이름을 열거하지 않는다
(`Policy_데이터셋_상세.md:163` 시각화 컨트롤). 그래서 계약이 이름을 안 박고
`listPalettes` 로 서빙한다 — 이름·색 견본은 viz-render 소유다.
"""
from __future__ import annotations

from conftest import AUTH


def test_팔레트는_정본대로_3종이다(client):
    r = client.get("/viz/v1/palettes", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    # ListEnvelope — items·totalCount·nextCursor 셋 다 필수다 (common.json#ListEnvelope)
    assert set(body) == {"items", "totalCount", "nextCursor"}
    assert body["totalCount"] == 3
    assert len(body["items"]) == 3
    assert body["nextCursor"] is None


def test_팔레트_항목은_PaletteOption_모양이다(client):
    items = client.get("/viz/v1/palettes", headers=AUTH).json()["items"]
    for it in items:
        assert set(it) <= {"palette", "label", "sampleColors"}
        assert it["palette"] and it["label"]
        assert all(c.startswith("#") and len(c) == 7 for c in it["sampleColors"])
    # 불투명 스타일 키다 — ULID 가 아니다 (계약 산문이 명시)
    assert not any(len(it["palette"]) == 26 and it["palette"].isupper() for it in items)


def test_팔레트_목록도_인증을_받는다(client):
    assert client.get("/viz/v1/palettes").status_code == 401
