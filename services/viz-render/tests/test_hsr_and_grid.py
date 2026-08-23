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


def test_격자_없는_HSR_은_완료가_아니라_실패다(client, put_target, tmp_path):
    """같은 파일이라도 격자를 못 주면 성공이 아니다 — 실패에 `기준 격자 없음`이 담긴다."""
    from colab_viz.domains.d7_visualization.failures import RenderFailure

    raw = bytearray(1024)
    raw[3:5] = (2025).to_bytes(2, "little", signed=True)
    raw[5], raw[6], raw[7] = 8, 13, 10
    nx, ny = 4, 3
    raw[20:22] = nx.to_bytes(2, "little")
    raw[22:24] = ny.to_bytes(2, "little")
    raw[24:26] = (1).to_bytes(2, "little")
    raw[26:28] = (500).to_bytes(2, "little")
    raw[32] = 1
    raw[33] = 1
    blob = bytes(raw) + np.arange(nx * ny, dtype="<i2").tobytes()

    tid = put_target(files={"RDR_CMP_HSR_TEST.bin": blob})
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
