"""프로필 캡처 시험과 같은 실좌표의 RenderResult 경계 4값을 대조한다."""
import numpy as np
import pytest

from conftest import AUTH


@pytest.mark.parametrize("embedded", [False, True])
def test_render_bounds_match_expected_profile_extent(client, put_target, tmp_path, embedded):
    values = np.arange(20, dtype="f4").reshape(4, 5)
    if embedded:
        import rasterio
        from rasterio.transform import from_bounds

        body = tmp_path / "body.tif"
        with rasterio.open(body, "w", driver="GTiff", width=5, height=4,
                           count=1, dtype="float32", crs="EPSG:4326",
                           transform=from_bounds(124, 31, 128, 34, 5, 4)) as output:
            output.write(values, 1)
    else:
        body = tmp_path / "body.npy"
        np.save(body, values)
    # 本体에 좌표가 있는 갈래는 일부러 다른 외부 격자를 준다.
    offset = 10 if embedded else 0
    lat = np.repeat(np.linspace(31 + offset, 34 + offset, 4)[:, None], 5, axis=1)
    lon = np.repeat(np.linspace(124 + offset, 128 + offset, 5)[None, :], 4, axis=0)
    target_id = put_target(copy_from=[body], grid={"lat.npy": lat, "lon.npy": lon})
    response = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": target_id},
        "style": {"palette": "단색-파랑", "classCount": 6},
    })
    assert response.status_code == 202, response.text
    job = client.get(f"/viz/v1/renders/{response.json()['renderId']}", headers=AUTH).json()
    assert job["status"] == "완료", job.get("failure")
    assert job["result"]["bounds"] == {
        "west": 124.0, "south": 31.0, "east": 128.0, "north": 34.0,
    }
