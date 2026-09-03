"""값 조회 — **답하는 수가 그 칸의 값인가** (`V-2` · `PLAN-SoT §9 〈294〉` · 15차 해제).

완료 정의 `〈254〉` 중 이 파일이 잠그는 것 —
  ⑶ **답하는 수가 평균이 아니라 그 칸의 값이다** — 같은 좌표를 원본에서 연 값과 대조하고,
     좌표를 가진 격자(tif 계열)에서는 **완전히 같다**
  ⑷ 답하는 단위가 **한 칸**임을 응답이 말한다
  ⑸ **값이 없는 칸에서는 「없다」** — 0 으로 바꾸지 않는다(음성)
  ⑵ **다시 그리지 않는다** — 조회가 렌더 작업을 만들지 않는다(음성)
  자리에 산출물이 없으면 **200 ＋ 「없다」** 이고 500 이 아니다(음성)

⚠ **오라클은 픽스처가 아니라 원본이다.** 기대값을 손으로 적으면 그 수가 어디서 왔는지
  아무도 모른다 — 이 시험은 **rasterio 로 원본을 직접 열어** 같은 좌표의 값을 읽고 대조한다.
"""
from __future__ import annotations

import numpy as np
import pytest

from colab_viz.domains.d7_visualization import value_lookup
from colab_viz.kernel import storage_layout

from conftest import AUTH

#: 8×8 격자 · 경계 126~128°E · 36~38°N (`conftest.tiny_geotiff` 와 같은 정의).
#: 칸 한 변은 0.25° 다. 아래 좌표는 **행 2 · 열 3** 의 안쪽 한 점이다.
_LAT, _LON = 37.4, 126.9


def _bake_tile(previews_root, source, *, grid_dir=None):
    """굽는 쪽이 놓는 그 자리에 그 이름으로 COG 를 놓는다.

    ⚠ **자리 이름을 시험이 지어내지 않는다** — 굽는 쪽과 같은 규칙(`map_tile_content_key`
    ＋ 승격된 변환 설정)으로 짓는다. 시험이 자기 자리를 쓰면 배치는 아무도 안 본다
    (`03-HANDOFF §4 #20` 의 그 무늬).
    """
    keys = value_lookup.candidate_tile_keys(source, grid_dir=grid_dir)
    key = keys[-1][0]
    out = storage_layout.preview_path(previews_root, key, ".tif")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(source.read_bytes())
    return out


def _spiky_geotiff(tmp_path, name="spiky.tif"):
    """**이웃과 뚜렷이 다른 값**을 가진 8×8 격자.

    ⚠ **평평한 램프(`conftest.tiny_geotiff` 의 `arange`)를 오라클로 쓰지 않는다** —
    선형이라 3×3 블록 평균이 **가운데 값과 정확히 같아진다.** 그런 픽스처에서는
    「평균을 답했다」와 「그 칸을 답했다」가 구분되지 않고, 시험은 초록인 채로
    아무것도 잠그지 않는다(`CLAUDE.md §4` — 검사 대상이 0 인 green).
    이 함수의 값은 대각선마다 튀어 **평균 ≠ 가운데 값**이다.
    """
    import rasterio
    from rasterio.transform import from_bounds

    path = tmp_path / name
    rng = np.random.default_rng(20260903)
    data = (rng.random((8, 8)) * 1000).astype("float32")
    with rasterio.open(path, "w", driver="GTiff", height=8, width=8, count=1,
                       dtype="float32", crs="EPSG:4326",
                       transform=from_bounds(126.0, 36.0, 128.0, 38.0, 8, 8)) as dst:
        dst.write(data, 1)
    return path


def _expected_from_source(source, lat=_LAT, lon=_LON):
    """**오라클** — 원본을 직접 열어 같은 좌표의 칸을 읽는다."""
    import rasterio

    with rasterio.open(source) as ds:
        row, col = ds.index(lon, lat)
        return float(ds.read(1)[row, col]), int(row), int(col)


def test_값은_그_칸의_값이고_원본과_완전히_같다(client, source_root, put_target, tmp_path):
    """완료 정의 ⑶ — **좌표를 가진 격자에서는 완전히 같다.**

    이 시험의 red 를 실제로 확인했다: 창을 3×3 으로 넓혀 평균을 답하게 바꾸면 red 다
    (평평한 램프 픽스처에서는 red 가 나지 않아 픽스처를 이웃과 다른 값으로 갈았다).
    """
    src = _spiky_geotiff(tmp_path)
    tid = put_target(copy_from=[src])
    body = storage_layout.target_dir(source_root, tid) / src.name
    _bake_tile(client.app.state.settings.preview_dir, body)

    expect, row, col = _expected_from_source(body)

    res = client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "datasetId": tid, "fileId": _file_id(client, tid, body.name),
        "point": {"lat": _LAT, "lon": _LON}})
    assert res.status_code == 200, res.text
    got = res.json()
    assert got["available"] is True
    # **비교가 근사가 아니다** — 블록 평균이면 여기서 갈린다.
    assert got["value"] == expect
    # ⑷ 답하는 단위가 한 칸이라는 것이 값과 같은 응답에 실린다.
    assert got["cell"]["row"] == row and got["cell"]["col"] == col
    assert got["cell"]["sizeDegrees"] == pytest.approx(0.25)
    assert got["exactness"] == "원본과 같은 칸"


def test_값이_없는_칸은_0_이_아니라_없다다(client, source_root, put_target, tmp_path):
    """완료 정의 ⑸ — **음성.** nodata 칸을 0 으로 바꾸면 여기서 red 다."""
    import rasterio
    from rasterio.transform import from_bounds

    src = tmp_path / "holes.tif"
    data = np.full((8, 8), -9999.0, dtype="float32")
    with rasterio.open(src, "w", driver="GTiff", height=8, width=8, count=1,
                       dtype="float32", crs="EPSG:4326", nodata=-9999.0,
                       transform=from_bounds(126.0, 36.0, 128.0, 38.0, 8, 8)) as dst:
        dst.write(data, 1)

    tid = put_target(copy_from=[src])
    body = storage_layout.target_dir(source_root, tid) / src.name
    _bake_tile(client.app.state.settings.preview_dir, body)

    got = client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "datasetId": tid, "fileId": _file_id(client, tid, body.name),
        "point": {"lat": _LAT, "lon": _LON}}).json()
    assert got["available"] is False
    assert got["value"] is None                      # **0 이 아니다**
    assert got["unavailableReason"] == "값이 없는 칸이다"
    assert got["cell"] is not None                   # 칸은 찾았다 — 값이 없을 뿐이다


def test_자리에_산출물이_없으면_200_과_없다다(client, source_root, put_target, tiny_geotiff):
    """**500 이 아니다. 경로를 지어내 뒤지지도 않는다.** 「없음」이 답이다."""
    tid = put_target(copy_from=[tiny_geotiff])
    body = storage_layout.target_dir(source_root, tid) / tiny_geotiff.name
    # 굽지 않는다 — 자리는 비어 있다.

    res = client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "datasetId": tid, "fileId": _file_id(client, tid, body.name),
        "point": {"lat": _LAT, "lon": _LON}})
    assert res.status_code == 200, res.text
    got = res.json()
    assert got == {"available": False, "value": None, "unit": None, "variable": None,
                   "exactness": "원본과 같은 칸", "cell": None,
                   "unavailableReason": "자리에 산출물이 없다"}


def test_조회는_렌더_작업을_만들지_않는다(client, source_root, put_target, tiny_geotiff):
    """완료 정의 ⑵ — **음성.** 값 조회가 새 작업을 낳으면 red 다."""
    tid = put_target(copy_from=[tiny_geotiff])
    body = storage_layout.target_dir(source_root, tid) / tiny_geotiff.name
    _bake_tile(client.app.state.settings.preview_dir, body)

    before = len(client.app.state.jobs._jobs)
    client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "datasetId": tid, "fileId": _file_id(client, tid, body.name),
        "point": {"lat": _LAT, "lon": _LON}})
    assert len(client.app.state.jobs._jobs) == before


def test_대상이_없으면_404_다(client):
    res = client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "datasetId": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "fileId": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "point": {"lat": _LAT, "lon": _LON}})
    assert res.status_code == 404


def test_서비스_토큰이_없으면_401_이다(client):
    res = client.post("/viz/v1/value-lookups", json={
        "datasetId": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "fileId": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "point": {"lat": _LAT, "lon": _LON}})
    assert res.status_code == 401


def test_내용_키로는_들어올_수_없다(client):
    """완료 정의 권한 ⓑ — **자리 이름만으로 값을 내주는 길이 없다.**

    키를 실으면 계약이 `additionalProperties: false` 라 거절이다. 이 시험이 red 가 되는
    날은 누군가 그 문을 연 날이다.
    """
    res = client.post("/viz/v1/value-lookups", headers=AUTH, json={
        "contentKey": "tile-" + "0" * 64, "point": {"lat": _LAT, "lon": _LON}})
    assert res.status_code == 400


def _file_id(client, target_id, file_name):
    """파일시스템 어댑터가 그 이름에 붙이는 `fileId` — 원장 어댑터가 붙으면 안 쓰인다."""
    return client.app.state.source.file_id(target_id, file_name)
