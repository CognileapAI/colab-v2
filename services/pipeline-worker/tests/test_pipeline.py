"""파이프라인 fail-closed(①) · COG 산출/출처 분리(⑤ · DR-2) · 계보 가공방식(DR-15)."""
from pathlib import Path

import pytest

from colab_pipeline.d5.cog import convert_tif_to_cog, OVERVIEW_RESAMPLING
from colab_pipeline.d5.lineage import make_lineage_record
from colab_pipeline.d5.pipeline import run_file
from colab_pipeline.d5.tiff_probe import classify_tiff

from fixture_builders import make_hsr_bin_gz, make_npy_2d, make_netcdf, make_tiled_only_tiff


def test_coords_missing_returns_failure_not_success(tmp_path: Path):
    # 완료조건 ① 핵심 음성 — 좌표 못 찾은 파일이 「성공」을 반환하지 않는다
    nx, ny = 8, 6
    p = make_hsr_bin_gz(tmp_path / "hsr.bin.gz", nx=nx, ny=ny)
    r = run_file(p, workdir=tmp_path / "out", grid_dir=None)
    assert r.status == "FAILURE"
    assert r.metadata.crs == "[미상]"
    assert any("좌표" in f or "격자" in f for f in r.failures)


def test_hsr_with_reference_grid_completes(tmp_path: Path):
    # 오버뷰가 최소 1단 생기도록 256 타일보다 큰 격자를 쓴다
    nx, ny = 600, 520
    p = make_hsr_bin_gz(tmp_path / "hsr.bin.gz", nx=nx, ny=ny,
                        blocks=[[100] * (nx * ny)])
    gd = tmp_path / "04.Lat_Lon_info"
    gd.mkdir()
    make_npy_2d(gd / "Lat_HSR.npy", ny, nx, start=33.0)
    make_npy_2d(gd / "Lon_HSR.npy", ny, nx, start=124.0)
    r = run_file(p, workdir=tmp_path / "out", grid_dir=gd)
    assert r.status == "SUCCESS"
    assert r.metadata.format == "Binary"
    assert r.metadata.grid == (ny, nx)
    assert r.cog_path is not None and classify_tiff(Path(r.cog_path)) == "cog"
    # DR-2 — 산출 COG 만 우리 산출물로 기록된다
    assert r.artifact is not None and r.artifact.origin == "산출"
    assert str(r.artifact.path) != str(p)


def test_unknown_format_is_failure(tmp_path: Path):
    p = tmp_path / "junk.dat"
    p.write_bytes(b"\xde\xad\xbe\xef" * 100)
    r = run_file(p, workdir=tmp_path / "out")
    assert r.status == "FAILURE"


def test_human_uploaded_cog_is_never_our_artifact(tmp_path: Path):
    # DR-2 — 사람이 올린 tif 는 (COG 여도) 입력이지 산출물이 아니다
    import fixture_builders as fb
    p = fb.make_cog_tiff(tmp_path / "uploaded.tif")
    r = run_file(p, workdir=tmp_path / "out")
    assert r.input_cog_class == "cog"
    assert r.artifact is None or str(r.artifact.path) != str(p)


def test_overview_resampling_split():
    # DR-12 — 범주형/연속형 분기
    assert OVERVIEW_RESAMPLING["categorical"] == "nearest"
    assert OVERVIEW_RESAMPLING["continuous"] == "average"


def test_lineage_record_carries_method():
    # DR-15 — 가공 방식은 관계에 부착한다
    rec = make_lineage_record(
        parent_dataset_id="01ARZ3NDEKTSV4RRFFQ69G5FAA",
        child_dataset_id="01ARZ3NDEKTSV4RRFFQ69G5FAB",
        relation_type="derived",
        method="bilinear 다운스케일",
        params={"target_res_m": 250},
    )
    assert rec["method"] == "bilinear 다운스케일"
    assert rec["params"]["target_res_m"] == 250
    with pytest.raises(ValueError):
        make_lineage_record(
            parent_dataset_id="x", child_dataset_id="y",
            relation_type="derived", method="", params={},
        )  # 가공 방식 공란 금지
