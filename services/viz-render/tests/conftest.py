"""시험 배선 — 실행 방식을 시험이 고른다.

렌더는 작업(job)이라 비동기다. 스레드로만 돌리면 「단계 3값이 실제로 흘렀는가」를
경합 없이 볼 수 없어서, 실행기를 세 가지로 둔다:
  inline — POST 안에서 끝까지 돈다 (결과 단언용)
  manual — 접수만 하고 멈춘다 (`그리는 중` 상태·409 단언용)
  thread — 운영 기본값
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from colab_viz.app.main import create_app
from colab_viz.kernel import storage_layout
from colab_viz.kernel.config import Settings
from colab_viz.kernel.ids import new_ulid

TOKEN = "p2viz-test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
#: 타일 서명 비밀 (`〈68〉`). 서비스 토큰과 **다른 값**이어야 한다 — 같은 값이면
#: 「서명이 실은 토큰을 그대로 쓰고 있다」를 시험이 구분하지 못한다.
SIGNING_SECRET = "p2viz-test-tile-secret"


@pytest.fixture
def source_root(tmp_path):
    d = tmp_path / "sources"
    d.mkdir()
    return d


def make_client(source_root, execution: str, **overrides) -> TestClient:
    """시험이 설정을 하나씩 바꿔 세운다 — 서명 수명·비밀은 시험마다 다르다."""
    fields = dict(
        source_root=source_root,
        service_token=TOKEN,
        tile_signing_secret=SIGNING_SECRET,
        execution=execution,
        max_render_bytes=500 * 1024 * 1024,
        result_ttl_seconds=3600,
        # 미리보기 산출물은 **실제로 디스크에 놓인다** — 시험도 진짜로 쓴다.
        preview_dir=Path(source_root).parent / "previews",
    )
    fields.update(overrides)
    return TestClient(create_app(Settings(**fields)))


_make_client = make_client


@pytest.fixture
def client(source_root):
    return _make_client(source_root, "inline")


@pytest.fixture
def manual_client(source_root):
    return _make_client(source_root, "manual")


@pytest.fixture
def put_target(source_root):
    """대상 하나를 만든다 — 반환값은 ULID. 본체 파일들을 그 아래 놓는다.

    ⚠ **자리는 픽스처가 정하지 않는다** — `kernel/storage_layout`(생성물)이 정한다.
    이 픽스처가 자기 배치를 쓰고 있었던 것이 `03-HANDOFF §4 #20` 이 시험을 전부 green 인
    채로 통과한 이유다: 시험이 자기가 놓은 자리에서 읽으면 **배치는 아무도 안 본다.**
    """
    def _put(files: dict[str, bytes] | None = None, *, grid: dict[str, np.ndarray] | None = None,
             copy_from: list = None) -> str:
        tid = new_ulid()
        d = storage_layout.target_dir(source_root, tid)
        d.mkdir(parents=True)
        for name, blob in (files or {}).items():
            (d / name).write_bytes(blob)
        for src in (copy_from or []):
            (d / src.name).write_bytes(src.read_bytes())
        if grid:
            g = storage_layout.grid_dir(source_root, tid)
            g.mkdir()
            for name, arr in grid.items():
                np.save(g / name, arr)
        return tid
    return _put


@pytest.fixture
def tiny_geotiff(tmp_path):
    """작은 실제 GeoTIFF — 합성이 아니라 rasterio 가 실제로 쓴 파일이다.

    ⚠ 좌표를 **지어내는** 것과 다르다. 이것은 시험용으로 우리가 정의한 격자를
    파일 안에 명시적으로 적어 넣은 것이고, 렌더 경로는 그 파일에 적힌 값만 읽는다.
    실데이터 판정은 tests/test_e2e_real.py 가 따로 한다.
    """
    import rasterio
    from rasterio.transform import from_bounds

    path = tmp_path / "tiny.tif"
    data = np.arange(64, dtype="float32").reshape(8, 8)
    with rasterio.open(
        path, "w", driver="GTiff", height=8, width=8, count=1, dtype="float32",
        crs="EPSG:4326", transform=from_bounds(126.0, 36.0, 128.0, 38.0, 8, 8),
    ) as dst:
        dst.write(data, 1)
    return path


@pytest.fixture(autouse=True)
def _실데이터포맷_표식을_리포트에_남긴다(request, record_property):
    """`e2e_format` 마커를 junit 속성으로 옮긴다 — 게이트가 읽는 유일한 경로다.

    ⚠ **케이스 이름으로 포맷을 짐작하지 않는다.** 이름 규칙으로 세면 이름을 바꾸는
    순간 대상이 조용히 0 이 되고, 게이트는 그것을 「통과」로 보고한다(`CLAUDE.md §4`).
    표식은 시험이 **명시적으로** 선언한다.
    """
    m = request.node.get_closest_marker("e2e_format")
    if m is not None:
        if len(m.args) != 1 or not isinstance(m.args[0], str) or not m.args[0]:
            raise ValueError("e2e_format 마커는 포맷 이름 하나를 받는다")
        record_property("실데이터포맷", m.args[0])
