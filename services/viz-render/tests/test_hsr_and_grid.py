"""음성 시험 — 지어내지 않는다, 그리고 유효값을 결측으로 지우지 않는다.

둘 다 **에러 없이 그럴듯한 값**을 내는 부류다 (`DATA-REFERENCE §0` — 여덟 중 여섯).
양성 시험으로는 못 잡는다.
"""
from __future__ import annotations

import numpy as np
import pytest

from conftest import AUTH


def test_fill_은_정확일치로_판정한다_20000은_살린다():
    """`값 <= -20000` 으로 자르면 표시 최소값을 결측으로 만든다 (`DATA-REFERENCE §2.1`)."""
    from colab_viz.domains.d7_visualization.hsr import decode_block

    raw = np.array([[-20000, -25000, -30000, -19999, 0, 1234]], dtype="<i2")
    out = decode_block(raw)
    assert out[0, 0] == pytest.approx(-200.0)      # -20000 은 유효한 하한이다
    assert np.isnan(out[0, 1])                     # -25000 비관측영역
    assert np.isnan(out[0, 2])                     # -30000 관측반경 밖
    assert out[0, 3] == pytest.approx(-199.99)
    assert out[0, 5] == pytest.approx(12.34)


def test_블록_수를_가정하지_않고_num_data_를_읽는다():
    from colab_viz.domains.d7_visualization.hsr import parse_header

    raw = bytearray(1024)
    raw[3:5] = (2025).to_bytes(2, "little", signed=True)
    raw[5], raw[6], raw[7], raw[8], raw[9] = 8, 13, 10, 0, 0
    raw[20:22] = (2305).to_bytes(2, "little", signed=True)
    raw[22:24] = (2881).to_bytes(2, "little", signed=True)
    raw[24:26] = (1).to_bytes(2, "little", signed=True)
    raw[26:28] = (500).to_bytes(2, "little", signed=True)
    raw[32] = 3
    raw[33:36] = bytes([1, 2, 3])
    h = parse_header(bytes(raw))
    assert (h.nx, h.ny, h.num_data, h.data_code) == (2305, 2881, 3, (1, 2, 3))


def test_좌표를_못_구하면_경성_실패다_근사_격자를_만들지_않는다(client, put_target):
    """PoC 구세대는 임의 격자를 지어내고 「성공」을 반환했다 (`DR-9`). 그 경로가 없다."""
    from colab_viz.domains.d7_visualization.grid import GridUnavailableError, find_reference_grid

    with pytest.raises(GridUnavailableError):
        find_reference_grid(None, expect_shape=(10, 10))


def _hsr_blob(nx: int = 4, ny: int = 3) -> bytes:
    raw = bytearray(1024)
    raw[3:5] = (2025).to_bytes(2, "little", signed=True)
    raw[5], raw[6], raw[7] = 8, 13, 10
    raw[20:22] = nx.to_bytes(2, "little")
    raw[22:24] = ny.to_bytes(2, "little")
    raw[24:26] = (1).to_bytes(2, "little")
    raw[26:28] = (500).to_bytes(2, "little")
    raw[32] = 1
    raw[33] = 1
    return bytes(raw) + np.arange(nx * ny, dtype="<i2").tobytes()


def test_좌표_없는_HSR_은_보류가_아니라_완료다_지도형만_빠진다(client, put_target):
    """**두 번째 동결 해제**(`PLAN-SoT §9-〈85〉` · Ted 2026-08-24 판정 ㈎).

    좌표가 하나도 없는 ②비지도형은 **완료**로 나간다 — `bounds` 는 지도형 갈래에만
    필수다. 경계를 지어내지 않으므로(`DR-9`) 결과에 `bounds`·사이드카가 **없다**.
    옛 코드는 이 상태를 `실패(REFERENCE_GRID_MISSING)` 로 두고 진짜 산출물 URL 을
    `failure.details` 로 밀어 넣었다 — 그 우회가 사라졌다.
    """
    tid = put_target(files={"RDR_CMP_HSR_TEST.bin": _hsr_blob()})
    rid = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()

    assert job["status"] == "완료", job.get("failure")
    assert "failure" not in job
    result = job["result"]
    assert result["imageUrl"]                       # ②비지도형 1024 px PNG 가 결과다
    assert "bounds" not in result                   # 좌표가 없으니 경계도 없다
    assert "sidecarUrl" not in result and "worldFileUrl" not in result
    assert result["precisionBadge"] == "격자 없음 — 지도형 보류"
    assert result["colorRangeStage"] in ("잠정", "확정")
    assert 3 <= len(result["legend"]["classes"]) <= 9


def test_격자를_붙였는데_못_쓰면_그대로_실패다(client, put_target):
    """음성 — **보류와 실패를 한 덩어리로 접지 않는다.**

    격자 파일을 붙였다는 것은 지도형을 요구한 것이다. 그 격자가 값과 형상이 달라
    좌표를 세울 수 없으면 이것은 「좌표가 없는 상태」가 아니라 **실패**다.
    """
    from colab_viz.domains.d7_visualization.failures import RenderFailure

    bad_lat = np.zeros((7, 9), dtype="f4")          # 값은 (3, 4) 다 — 형상이 다르다
    bad_lon = np.zeros((7, 9), dtype="f4")
    tid = put_target(files={"RDR_CMP_HSR_TEST.bin": _hsr_blob()},
                     grid={"Lat_HSR.npy": bad_lat, "Lon_HSR.npy": bad_lon})
    rid = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()

    assert job["status"] == "실패"
    assert job["failure"]["code"] == RenderFailure.NO_REFERENCE_GRID
    assert "result" not in job


def test_격자를_주면_같은_HSR_이_그려진다(client, put_target):
    nx, ny = 4, 3
    raw = bytearray(1024)
    raw[3:5] = (2025).to_bytes(2, "little", signed=True)
    raw[5], raw[6], raw[7] = 8, 13, 10
    raw[20:22] = nx.to_bytes(2, "little")
    raw[22:24] = ny.to_bytes(2, "little")
    raw[24:26] = (1).to_bytes(2, "little")
    raw[26:28] = (500).to_bytes(2, "little")
    raw[32] = 1
    raw[33] = 1
    blob = bytes(raw) + (np.arange(nx * ny, dtype="<i2") * 100).tobytes()

    lat = np.repeat(np.linspace(38.0, 36.0, ny)[:, None], nx, axis=1).astype("f4")
    lon = np.repeat(np.linspace(126.0, 128.0, nx)[None, :], ny, axis=0).astype("f4")
    tid = put_target(files={"RDR_CMP_HSR_TEST.bin": blob},
                     grid={"Lat_HSR.npy": lat, "Lon_HSR.npy": lon})
    rid = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    assert job["status"] == "완료", job.get("failure")
    b = job["result"]["bounds"]
    # 경계는 **읽은 좌표 배열**에서 나온다 — 지어낸 값이 아니다
    assert b["west"] == pytest.approx(126.0, abs=1e-4)
    assert b["north"] == pytest.approx(38.0, abs=1e-4)


def test_짝_파일_없이_그려_보기_는_파일_안_위경도를_쓴다(client, put_target, tiny_geotiff):
    """미리 막으면 그릴 수 있는 것까지 못 그린다 (정본 §8 기준 격자 파일)."""
    tid = put_target(copy_from=[tiny_geotiff])       # 격자 폴더가 없다
    rid = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid}, "style": {"palette": "단색-파랑"},
        "withoutReferenceGrid": True}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    assert job["status"] == "완료", job.get("failure")
