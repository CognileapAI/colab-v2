"""이미 구운 지도 타일을 **다시 굽지 않고 찾아 쓴다** — 완료 정의 ⑵ 축자.

정본이 말하는 것 (`contracts/storage/layout.json`):
  · `keys.미리보기 산출물` 주석 축자 — 「**자리가 있어야 이미 구운 것을 찾아 쓴다.**
    자리가 없으면 같은 그림을 매번 다시 굽는다.」
  · `contentKeys.지도 타일.why` 축자 — 「같은 원본을 같은 설정으로 변환하면 같은 키이므로
    **재사용이 성립하고**, 원본이나 설정이 하나라도 바뀌면 키가 갈려 무효화가 키 자신의 일이 된다.」

**자리 자체가 기록이다** — 내용 주소이므로 별도의 표도, 계약 페이로드 확장도 필요 없다.
그래서 「찾아 쓴다」는 그 자리를 **보는 것**으로 성립한다.

세 상태 (`CLAUDE.md §4` · 관대한 기본값 금지):
  ⓐ 자리에 **쓸 수 있는 타일**이 있다      → 재사용한다. 다시 굽지 않는다
  ⓑ 자리에 파일이 있으나 **타일이 아니다** → 재사용하지 않고 다시 굽는다. **그 사실을 드러낸다**
  ⓒ 자리가 **선언되지 않았다**             → 키가 없고 재사용도 없다. 조용히 성공으로 세지 않는다

⚠ ⓑ 가 이 시험의 핵심이다. 「파일이 있다」를 「구워져 있다」로 읽으면 **0바이트 잔재를
   미리보기로 내보낸다** — 에러 없이 그럴듯한 값(`DATA-REFERENCE §0`)의 이 도메인 판이다.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from colab_pipeline.d5 import pipeline as d5_pipeline
from colab_pipeline.d5.tiff_probe import classify_tiff
from colab_pipeline.kernel import storage_layout

from fixture_builders import make_hsr_bin_gz, make_npy_2d

pytestmark = pytest.mark.stage2

_NX, _NY = 600, 520


def _source(tmp_path: Path) -> tuple[Path, Path]:
    src = make_hsr_bin_gz(tmp_path / "hsr.bin.gz", nx=_NX, ny=_NY,
                          blocks=[[100] * (_NX * _NY)])
    gd = tmp_path / "04.Lat_Lon_info"
    gd.mkdir()
    make_npy_2d(gd / "Lat_HSR.npy", _NY, _NX, start=33.0)
    make_npy_2d(gd / "Lon_HSR.npy", _NY, _NX, start=124.0)
    return src, gd


def _run(src: Path, gd: Path, previews: Path | None, work: Path):
    return d5_pipeline.run_file(src, workdir=work, grid_dir=gd, previews_root=previews)


# ── ⓐ 자리에 쓸 수 있는 타일이 있다 → 재사용 ────────────────────────────────
def test_second_run_reuses_the_tile_instead_of_rebuilding_it(tmp_path: Path):
    src, gd = _source(tmp_path)
    previews = tmp_path / "previews"

    first = _run(src, gd, previews, tmp_path / "w1")
    assert first.status == "SUCCESS", first.failures
    assert first.reused is False          # 처음은 구운 것이다
    out = Path(first.cog_path)
    stamp = (out.stat().st_mtime_ns, out.stat().st_size)

    second = _run(src, gd, previews, tmp_path / "w2")
    assert second.status == "SUCCESS", second.failures
    assert second.tile_content_key == first.tile_content_key
    assert Path(second.cog_path) == out
    # **다시 굽지 않았다** — 바이트도 시각도 그대로다. 「같은 자리」만으로는 증명이 안 된다
    assert (out.stat().st_mtime_ns, out.stat().st_size) == stamp
    assert second.reused is True
    # 재사용은 **산출**이 아니다 — 이번 회차가 만든 것이 없다
    assert second.artifact is None


def test_a_changed_source_does_not_reuse_the_other_tile(tmp_path: Path):
    """재료가 갈리면 키가 갈리고, 갈린 키 자리에는 아직 아무것도 없다."""
    src, gd = _source(tmp_path)
    previews = tmp_path / "previews"
    first = _run(src, gd, previews, tmp_path / "w1")
    assert first.status == "SUCCESS", first.failures

    other = make_hsr_bin_gz(tmp_path / "hsr2.bin.gz", nx=_NX, ny=_NY,
                            blocks=[[101] * (_NX * _NY)])
    second = _run(other, gd, previews, tmp_path / "w2")
    assert second.status == "SUCCESS", second.failures
    assert second.tile_content_key != first.tile_content_key
    assert second.reused is False


# ── ⓑ 자리에 파일이 있으나 타일이 아니다 → 다시 굽고 드러낸다 ──────────────
@pytest.mark.parametrize("junk", [b"", b"not a tiff at all"])
def test_an_unusable_file_at_the_key_is_never_reused(tmp_path: Path, junk: bytes):
    """**0바이트·쓰레기 잔재를 「이미 구웠다」로 세지 않는다.**

    파일 존재만 보고 재사용하면 미리보기가 조용히 깨진 채 나간다 — 에러가 나지 않는다.
    """
    src, gd = _source(tmp_path)
    previews = tmp_path / "previews"

    key = d5_pipeline.map_tile_key(src, grid_dir=gd, used_reference_grid=True,
                                   kind="continuous")
    seeded = storage_layout.preview_path(previews, key, ".tif")
    seeded.parent.mkdir(parents=True, exist_ok=True)
    seeded.write_bytes(junk)

    r = _run(src, gd, previews, tmp_path / "w1")
    assert r.status == "SUCCESS", r.failures
    assert r.tile_content_key == key
    assert r.reused is False
    # 다시 구웠다 — 자리에 있는 것이 이제 진짜 타일이다
    assert classify_tiff(Path(r.cog_path)) == "cog"
    # **건수를 삼키지 않는다** — 왜 재사용하지 않았는지가 결과에 남는다
    assert r.rebuilt_unusable == 1
    assert any("재사용" in m for m in r.notes), r.notes


# ── ⓒ 자리가 선언되지 않았다 → 키도 재사용도 없다 ──────────────────────────
def test_no_declared_slot_means_no_reuse_and_it_is_stated(tmp_path: Path):
    src, gd = _source(tmp_path)
    r1 = _run(src, gd, None, tmp_path / "w1")
    assert r1.status == "SUCCESS", r1.failures
    assert r1.tile_content_key is None and r1.reused is False
    r2 = _run(src, gd, None, tmp_path / "w2")
    # 자리가 없으면 **매번 다시 굽는다** — 정본이 그렇게 적었다. 그 사실이 드러나야 한다
    assert r2.reused is False
    assert any("자리" in m for m in r2.notes), r2.notes


# ── 실데이터 — 완료 정의 축자 「**실데이터에서 돌고**」 ──────────────────────
# 위 넷은 합성 픽스처다. 합성으로만 증명하면 「돌더라」가 아니라 「내가 만든 것에서 돌더라」다.
# 원천 마운트가 없으면 **skip 이 아니라 fail** — 이 배포 단위의 기존 규율 그대로다.
_ENV = "COLAB_REFERENCE_DATA"


def _reference_root() -> Path:
    import os
    v = os.environ.get(_ENV)
    if not v or not Path(v).is_dir():
        pytest.fail(f"{_ENV} 가 원천 디렉터리를 가리키지 않는다 — 실데이터 시험은 skip 하지 않는다")
    return Path(v)


@pytest.mark.e2e
@pytest.mark.parametrize(
    "folder,pattern,grid",
    [
        ("file_format_3_bin", "*.bin.gz", True),    # HSR — 격자 파일이 반드시 필요하다
        ("file_format_2_nc", "gk2a_*.nc", True),
        ("file_format_5_HDF5", "*.hdf", True),
    ],
)
def test_real_source_lands_in_the_slot_and_the_next_run_reuses_it(
        tmp_path: Path, folder: str, pattern: str, grid: bool):
    """원천 파일이 **미리보기 자리에 지도용 영상으로 놓이고, 두 번째 회차는 굽지 않는다.**"""
    d = _reference_root() / "02.File-format" / folder
    if not d.is_dir():
        pytest.fail(f"원천 폴더 없음: {d}")
    files = sorted(p for p in (d / "00.Data").glob(pattern) if p.name != "desktop.ini")
    if not files:
        pytest.fail(f"{d / '00.Data'} 에 {pattern} 없음")
    src = files[0]
    gd = (d / "04.Lat_Lon_info") if grid else None
    previews = tmp_path / "previews"

    first = d5_pipeline.run_file(src, workdir=tmp_path / "w1", grid_dir=gd,
                                 previews_root=previews)
    assert first.status == "SUCCESS", first.failures
    assert first.reused is False
    assert first.tile_content_key and storage_layout.is_map_tile_key(first.tile_content_key)
    out = Path(first.cog_path)
    assert out == storage_layout.preview_path(previews, first.tile_content_key, ".tif")
    assert classify_tiff(out) == "cog"       # 지도용 영상이다 — 개관까지 들어 있다
    stamp = (out.stat().st_mtime_ns, out.stat().st_size)

    second = d5_pipeline.run_file(src, workdir=tmp_path / "w2", grid_dir=gd,
                                  previews_root=previews)
    assert second.status == "SUCCESS", second.failures
    assert second.reused is True and Path(second.cog_path) == out
    assert (out.stat().st_mtime_ns, out.stat().st_size) == stamp
