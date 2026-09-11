"""J-1~J-5 — worker만 실제 파일에서 격자/지도 프로필을 만든다."""
from __future__ import annotations

import numpy as np

from colab_pipeline.domains.d5_ingestion import IngestionService, UploadFileWork, UploadWork
from colab_pipeline.kernel import storage_layout
from memory_ledger import MemoryLedger

LAB = "01JQ0000000000000000000001"
ACCOUNT = "01JQ0000000000000000000002"
UPLOAD = "01JQ0000000000000000000003"


def _ledger() -> MemoryLedger:
    ledger = MemoryLedger()
    ledger.accept(upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT)
    return ledger


def test_external_grid_profile_uses_actual_shape_digest_format_and_bounds(tmp_path) -> None:
    body = tmp_path / "body.npy"
    np.save(body, np.arange(20, dtype="f4").reshape(4, 5))
    grid_dir = tmp_path / "grid"
    grid_dir.mkdir()
    lat = grid_dir / "lat.npy"
    lon = grid_dir / "lon.npy"
    np.save(lat, np.repeat(np.linspace(31.0, 34.0, 4)[:, None], 5, axis=1))
    np.save(lon, np.repeat(np.linspace(124.0, 128.0, 5)[None, :], 4, axis=0))
    work = UploadWork(
        upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT,
        workdir=tmp_path / "work", previews_root=tmp_path / "previews",
        files=[
            UploadFileWork("01JQ00000000000000000000B1", body, "본체", body.name),
            UploadFileWork("01JQ00000000000000000000G1", lat, "기준 격자 파일", lat.name,
                           "uploads/u/grid/lat.npy"),
            UploadFileWork("01JQ00000000000000000000G2", lon, "기준 격자 파일", lon.name,
                           "uploads/u/grid/lon.npy"),
        ],
    )
    ledger = _ledger()
    result = IngestionService(ledger).process_upload(work, stage1=False)
    assert result.events[-1]["type"] == "upload.ready"
    profile = ledger.grid_profiles[UPLOAD]
    assert profile["body_shape"] == [4, 5]
    assert profile["grid_shape"] == [4, 5]
    assert profile["grid_digest"] == storage_layout.map_tile_grid_digest(grid_dir, True)
    assert profile["grid_format_signature"] == "NumPy+NumPy"
    assert (profile["west"], profile["south"], profile["east"], profile["north"]) == (
        124.0, 31.0, 128.0, 34.0)
    assert profile["map_state"] == "지도 있음"


def test_missing_grid_records_no_map_without_fabricated_geometry(tmp_path) -> None:
    body = tmp_path / "body.npy"
    np.save(body, np.arange(20, dtype="f4").reshape(4, 5))
    ledger = _ledger()
    IngestionService(ledger).process_upload(UploadWork(
        upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT,
        workdir=tmp_path / "work", previews_root=tmp_path / "previews",
        files=[UploadFileWork("01JQ00000000000000000000B1", body, "본체", body.name)],
    ), stage1=False)
    profile = ledger.grid_profiles[UPLOAD]
    assert profile["body_shape"] == [4, 5]
    assert profile["grid_shape"] is None and profile["grid_digest"] is None
    assert all(profile[key] is None for key in ("west", "south", "east", "north"))
    assert profile["map_state"] == "지도 없음"


def test_embedded_body_bounds_take_precedence_over_unused_external_grid(tmp_path) -> None:
    """렌더러는 본체의 실재 좌표를 우선하므로 예상 영역도 그 좌표여야 한다."""
    import rasterio
    from rasterio.transform import from_bounds

    body = tmp_path / "body.tif"
    with rasterio.open(body, "w", driver="GTiff", width=5, height=4,
                       count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_bounds(124, 31, 128, 34, 5, 4)) as target:
        target.write(np.arange(20, dtype="f4").reshape(4, 5), 1)
    grid_dir = tmp_path / "grid"
    grid_dir.mkdir()
    lat, lon = grid_dir / "lat.npy", grid_dir / "lon.npy"
    np.save(lat, np.repeat(np.linspace(41.0, 44.0, 4)[:, None], 5, axis=1))
    np.save(lon, np.repeat(np.linspace(134.0, 138.0, 5)[None, :], 4, axis=0))
    ledger = _ledger()
    IngestionService(ledger).process_upload(UploadWork(
        upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT,
        workdir=tmp_path / "work", previews_root=tmp_path / "previews",
        files=[
            UploadFileWork("01JQ00000000000000000000B1", body, "본체", body.name),
            UploadFileWork("01JQ00000000000000000000G1", lat, "기준 격자 파일", lat.name),
            UploadFileWork("01JQ00000000000000000000G2", lon, "기준 격자 파일", lon.name),
        ],
    ), stage1=False)
    profile = ledger.grid_profiles[UPLOAD]
    assert (profile["west"], profile["south"], profile["east"], profile["north"]) == (
        124.0, 31.0, 128.0, 34.0)


def test_unreadable_partial_grid_is_unknown_not_no_map(tmp_path) -> None:
    lon = tmp_path / "lon.npy"
    np.save(lon, np.ones((3, 4), dtype="f4"))
    ledger = _ledger()
    IngestionService(ledger).process_upload(UploadWork(
        upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT,
        workdir=tmp_path / "work",
        files=[UploadFileWork("01JQ00000000000000000000G1", lon,
                              "기준 격자 파일", lon.name, "uploads/u/grid/lon.npy")],
    ))
    assert ledger.grid_profiles[UPLOAD]["map_state"] == "아직 모름"
