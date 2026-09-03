"""지도 타일 **전용 내용 키** 규칙 — 한 슬롯에 사는 두 규칙이 서로를 침범하지 않는다.

왜 전용 규칙인가 (`contracts/storage/layout.json` `contentKeys.지도 타일`):
렌더 산출물의 키 규칙(`viz-render` `render_cache_key`)의 입력은 렌더 파라미터이고
파이프라인에는 그 값이 **존재하지 않는다**. 부르는 순간 D5 가 D7 의 렌더 개념을 갖는다
(`CLAUDE.md §3-1`). 그래서 파이프라인이 실제로 가진 재료만으로 짓는다.

이 시험이 지키는 것 넷 — ⓐ 같은 재료면 같은 키 ⓑ 재료 하나만 달라도 키가 갈린다
ⓒ **재료가 빠지면 키를 짓지 않는다**(관대한 기본값 금지) ⓓ 두 규칙의 키가 섞이지 않는다.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from colab_pipeline.d5 import pipeline as d5_pipeline
from colab_pipeline.kernel import storage_layout

from fixture_builders import make_hsr_bin_gz, make_npy_2d

_MATERIAL = {
    "sourceDigest": "a" * 64,
    "sourceByteSize": 1234,
    "gridDigest": "b" * 64,
    "conversionKind": "continuous",
    "overviewResampling": "average",
    "compression": "deflate",
}


@pytest.mark.stage2
def test_same_material_same_key_and_change_splits_it():
    k = storage_layout.map_tile_content_key(**_MATERIAL)
    assert k == storage_layout.map_tile_content_key(**_MATERIAL)
    for field in _MATERIAL:
        other = dict(_MATERIAL, **{field: "달라진 값"})
        assert storage_layout.map_tile_content_key(**other) != k, field


@pytest.mark.stage2
@pytest.mark.parametrize("missing", sorted(_MATERIAL))
def test_missing_material_refuses_to_build_a_key(missing: str):
    """**재료가 없으면 짓지 않는다.** 기본값으로 메우면 다른 산출물이 같은 자리를 차지한다."""
    for empty in (None, ""):
        with pytest.raises(ValueError):
            storage_layout.map_tile_content_key(**dict(_MATERIAL, **{missing: empty}))


@pytest.mark.stage2
def test_unknown_material_is_refused():
    with pytest.raises(ValueError):
        storage_layout.map_tile_content_key(**dict(_MATERIAL, palette="viridis"))


@pytest.mark.stage2
def test_two_rules_share_one_slot_without_colliding():
    """렌더 다이제스트와 타일 키는 **같은 슬롯**에 놓이지만 서로를 침범하지 않는다."""
    render_like = "c" * 64                       # `render_cache_key` 가 내는 모양
    tile = storage_layout.map_tile_content_key(**_MATERIAL)
    assert storage_layout.is_map_tile_key(tile)
    assert not storage_layout.is_map_tile_key(render_like)
    assert storage_layout.preview_key(tile, ".tif") != storage_layout.preview_key(
        render_like, ".tif")
    # 둘 다 **미리보기 루트 기준** 상대 키다 — 접수분 루트로 새지 않는다
    for key in (tile, render_like):
        assert not storage_layout.preview_key(key, ".tif").startswith(
            storage_layout.UPLOADS_PREFIX)


@pytest.mark.stage2
def test_embedded_coordinates_are_named_not_blank(tmp_path: Path):
    """좌표가 파일 안에 있던 경우의 `gridDigest` 는 **명시값**이다 — 빈 값이 아니다."""
    src = tmp_path / "x.bin"
    src.write_bytes(b"0123456789")
    embedded = d5_pipeline.map_tile_key(src, grid_dir=None, used_reference_grid=False,
                                        kind="continuous")
    assert storage_layout.GRID_DIGEST_EMBEDDED == "내장"
    # 「격자를 안 썼다」와 「격자를 썼다」가 같은 키를 얻지 않는다
    gd = tmp_path / "grid"
    gd.mkdir()
    make_npy_2d(gd / "Lat_x.npy", 4, 4, start=33.0)
    used = d5_pipeline.map_tile_key(src, grid_dir=gd, used_reference_grid=True,
                                    kind="continuous")
    assert embedded != used


@pytest.mark.stage2
def test_output_lands_in_the_preview_slot_when_a_root_is_declared(tmp_path: Path):
    """**산출물이 임시 자리를 떠난다** — 선언된 미리보기 루트의 전용 키 자리에 놓인다."""
    nx, ny = 600, 520
    src = make_hsr_bin_gz(tmp_path / "hsr.bin.gz", nx=nx, ny=ny, blocks=[[100] * (nx * ny)])
    gd = tmp_path / "04.Lat_Lon_info"
    gd.mkdir()
    make_npy_2d(gd / "Lat_HSR.npy", ny, nx, start=33.0)
    make_npy_2d(gd / "Lon_HSR.npy", ny, nx, start=124.0)
    previews = tmp_path / "previews"

    r = d5_pipeline.run_file(src, workdir=tmp_path / "work", grid_dir=gd,
                             previews_root=previews)
    assert r.status == "SUCCESS", r.failures
    assert r.tile_content_key and storage_layout.is_map_tile_key(r.tile_content_key)
    expected = storage_layout.preview_path(previews, r.tile_content_key, ".tif")
    assert Path(r.cog_path) == expected and expected.is_file()
    # 접수분 루트 아래가 아니다 — 원본과 산출물은 다른 볼륨이다
    assert storage_layout.UPLOADS_PREFIX not in expected.relative_to(previews).parts

    # 같은 원본·같은 설정을 다시 돌리면 **같은 자리**다 (내용 주소)
    r2 = d5_pipeline.run_file(src, workdir=tmp_path / "work2", grid_dir=gd,
                              previews_root=previews)
    assert r2.tile_content_key == r.tile_content_key


@pytest.mark.stage2
def test_without_a_declared_root_the_output_stays_in_the_workdir(tmp_path: Path):
    """루트를 선언하지 않으면 예전 자리다 — **그 사실이 키 없음으로 드러난다.**"""
    nx, ny = 600, 520
    src = make_hsr_bin_gz(tmp_path / "hsr.bin.gz", nx=nx, ny=ny, blocks=[[100] * (nx * ny)])
    gd = tmp_path / "04.Lat_Lon_info"
    gd.mkdir()
    make_npy_2d(gd / "Lat_HSR.npy", ny, nx, start=33.0)
    make_npy_2d(gd / "Lon_HSR.npy", ny, nx, start=124.0)
    r = d5_pipeline.run_file(src, workdir=tmp_path / "work", grid_dir=gd)
    assert r.status == "SUCCESS", r.failures
    assert r.tile_content_key is None
    assert Path(r.cog_path).parent == tmp_path / "work"


# ══════════════════════════════════════════════════════════════════════════════
# 변환 설정 승격 (`PLAN-SoT §9 〈294〉` · 15차 동결 해제)
#
# 셋(`conversionKind`·`overviewResampling`·`compression`)이 D5 상수에서 저장 규약으로
# 올라갔다. **읽는 쪽(D7)이 같은 키를 지을 수 있게 하는 것**이 목적이고, 그 대가로
# **굽는 쪽의 키가 한 비트라도 달라지면 이미 구운 산출물 전부가 자리를 잃는다.**
# 그래서 승격 전 상수로 지은 키를 **못으로 박아** 둔다 — 값이 아니라 못이다.
# ══════════════════════════════════════════════════════════════════════════════

#: 승격 **이전** 코드(`d5/cog.py OVERVIEW_RESAMPLING` · `d5/pipeline.py COG_COMPRESSION` ·
#: `UploadWork.kind` 기본값 `"continuous"`)로 지은 키다. 이 값이 바뀌면 승격이
#: **동작을 바꾼 것**이고, 그것은 조용한 재굽기다.
_PROOF_BYTES = b"colab-v2 tile key proof\n"
_PROOF_KEY = "tile-3b64060250079e0c6e4fcc56060306a5afd03b75ee588b4b90b555228109d45b"


@pytest.mark.stage2
def test_promoted_settings_keep_the_key_byte_identical(tmp_path: Path):
    """**승격 전후로 같은 입력이 같은 키를 낳는다.**"""
    src = tmp_path / "proof.bin"
    src.write_bytes(_PROOF_BYTES)
    got = d5_pipeline.map_tile_key(src, grid_dir=None, used_reference_grid=False,
                                   kind=storage_layout.MAP_TILE_CONVERSION_KIND)
    assert got == _PROOF_KEY


@pytest.mark.stage2
def test_promoted_settings_are_the_values_that_were_in_d5():
    """승격은 **옮긴 것**이지 새로 정한 것이 아니다 — 값이 실물과 같아야 한다."""
    from colab_pipeline.d5 import cog as d5_cog

    assert storage_layout.MAP_TILE_CONVERSION_KIND == "continuous"
    assert storage_layout.MAP_TILE_COMPRESSION == "deflate"
    assert storage_layout.MAP_TILE_OVERVIEW_RESAMPLING == {
        "categorical": "nearest", "continuous": "average"}
    # D5 가 여전히 같은 표를 쓴다 — 승격이 `DR-12` 분기를 지우지 않았다.
    assert d5_cog.OVERVIEW_RESAMPLING == storage_layout.MAP_TILE_OVERVIEW_RESAMPLING
    assert d5_pipeline.COG_COMPRESSION == storage_layout.MAP_TILE_COMPRESSION


@pytest.mark.stage2
def test_grid_digest_rule_lives_in_one_place(tmp_path: Path):
    """굽는 쪽과 읽는 쪽이 **같은 함수**로 격자 다이제스트를 짓는다."""
    grid = tmp_path / "grid"
    grid.mkdir()
    (grid / "LAT_x.npy").write_bytes(b"lat")
    (grid / "LON_x.npy").write_bytes(b"lon")

    assert storage_layout.map_tile_grid_digest(grid, False) == storage_layout.GRID_DIGEST_EMBEDDED
    assert storage_layout.map_tile_grid_digest(None, True) == storage_layout.GRID_DIGEST_EMBEDDED
    used = storage_layout.map_tile_grid_digest(grid, True)
    assert used != storage_layout.GRID_DIGEST_EMBEDDED and len(used) == 64
    # D5 의 내부 함수가 그 생성물을 부른다 (규칙이 두 곳에 있지 않다).
    assert d5_pipeline._grid_digest(grid, True) == used
