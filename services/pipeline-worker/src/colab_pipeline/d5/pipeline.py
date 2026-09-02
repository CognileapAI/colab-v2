"""D5 처리 흐름 — 감지 → 파싱 → 좌표 → COG. fail-closed.

- 좌표를 못 찾으면 crs=[미상] · status=FAILURE (DR-9). 합성 격자는 없다.
- 사람이 올린 tif 는 (이미 COG 여도) **입력**이다 — 산출물로 기록되지 않는다 (DR-2).
- 실패 파일은 목록으로 남는다 — 조용히 건너뛰지 않는다 (완료조건 ④).

**stage2 대기.** 배포 단위·완료 정의에서 빠진다 — 파일·시험 유지(`〈71〉-㉰`).
근거: `dev-package/sessions/S1-PLAN.md` §5.2 행 7 · `PLAN-SoT.md §9 〈74〉〈75〉`.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..kernel import storage_layout
from .cog import OVERVIEW_RESAMPLING, convert_tif_to_cog, write_cog_from_grid
from .detect import detect_format
from .formats import UNKNOWN
from .grid import GridUnavailableError, find_reference_grid
from .internal_grid import InternalGridUnavailable, internal_latlon
from .hsr import decode_block, parse_hsr
from .parse import AutoMetadata, ParseError, parse_metadata
from .renderable import RENDERABLE_FORMATS, is_renderable
from .tiff_probe import classify_tiff


@dataclass
class ArtifactRecord:
    path: Path
    origin: str           # "산출" 만 유효 — 입력은 ArtifactRecord 가 되지 않는다
    source_input: Path

    def __post_init__(self) -> None:
        if self.origin != "산출":
            raise ValueError("입력 파일은 산출물로 기록될 수 없다 (DR-2)")
        if Path(self.path) == Path(self.source_input):
            raise ValueError("입력과 산출이 같은 파일일 수 없다 (DR-2)")


@dataclass
class PipelineResult:
    input_path: Path
    status: str                      # "SUCCESS" | "FAILURE"
    metadata: AutoMetadata | None = None
    input_cog_class: str | None = None   # 입력 tif 의 3부류 판정
    cog_path: str | None = None
    #: 지도 타일이 놓인 **내용 키**. 산출물이 미리보기 루트에 놓였을 때만 값이 있다.
    tile_content_key: str | None = None
    artifact: ArtifactRecord | None = None
    #: 이번 회차가 **굽지 않고 자리에 있던 것을 찾아 썼는가**(완료 정의 ⑵ 축자
    #: 「다시 만들지 않고 찾아 쓸 수 있다」). 자리를 선언하지 않았으면 언제나 False 다.
    reused: bool = False
    #: 자리에 파일이 있었으나 **타일이 아니어서** 다시 구운 건수. 0 이 정상이고,
    #: 0 이 아니면 그 사실이 드러나야 한다 — 삼키면 잔재를 미리보기로 내보낸다.
    rebuilt_unusable: int = 0
    #: 재사용 판정이 왜 그렇게 났는지. **비어 있는 채로 통과시키지 않는다.**
    notes: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def _fail(res: PipelineResult, msg: str) -> PipelineResult:
    res.status = "FAILURE"
    res.failures.append(msg)
    return res


#: COG 프로파일 이름. `cog.py` 가 `cog_profiles.get("deflate")` 로 고정한 값이고,
#: 내용 키의 재료라 **여기서 다시 정하지 않고 그 사실을 이름으로 옮긴다.**
COG_COMPRESSION = "deflate"


def file_digest(path: Path) -> str:
    """원본 바이트의 다이제스트 — 지도 타일 내용 키의 첫 재료."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _grid_digest(grid_dir: Path | None, used_reference_grid: bool) -> str:
    """좌표를 준 것의 다이제스트.

    파일 안 좌표를 썼으면 **명시값**(`내장`)이다 — 빈 값으로 두면 「격자가 없다」와
    「안 물어봤다」가 같은 키를 얻는다.
    """
    if not used_reference_grid or grid_dir is None:
        return storage_layout.GRID_DIGEST_EMBEDDED
    h = hashlib.sha256()
    for f in sorted(Path(grid_dir).iterdir()):
        if f.is_file():
            h.update(f.name.encode("utf-8"))
            h.update(file_digest(f).encode("ascii"))
    return h.hexdigest()


def map_tile_key(source: Path, *, grid_dir: Path | None, used_reference_grid: bool,
                 kind: str) -> str:
    """이 산출물의 자리를 정하는 **전용 키** — 재료는 파이프라인이 실제로 가진 것뿐이다.

    렌더 산출물의 키 규칙(`viz-render` `render_cache_key`)을 **부르지 않는다** —
    그 규칙의 입력(팔레트·선택 변수·색범위)이 여기 존재하지 않기 때문이고,
    부르면 D5 가 D7 의 렌더 개념을 갖는다(`CLAUDE.md §3-1`).
    """
    if kind not in OVERVIEW_RESAMPLING:
        raise ValueError(f"kind 는 categorical|continuous — 받은 값: {kind}")
    return storage_layout.map_tile_content_key(
        sourceDigest=file_digest(source),
        sourceByteSize=Path(source).stat().st_size,
        gridDigest=_grid_digest(grid_dir, used_reference_grid),
        conversionKind=kind,
        overviewResampling=OVERVIEW_RESAMPLING[kind],
        compression=COG_COMPRESSION,
    )


#: 이미 COG 인 업로드 — 변환도, 산출물 기록도 없다 (DR-2).
_ALREADY_COG = object()


def _cog_geotiff(path, meta, grid, out_path, kind, res):
    res.input_cog_class = classify_tiff(path)
    if res.input_cog_class == "cog":
        return _ALREADY_COG
    convert_tif_to_cog(path, out_path, kind=kind)


def _cog_binary(path, meta, grid, out_path, kind, res):
    hsr = parse_hsr(path)
    data = decode_block(hsr.blocks[0])
    write_cog_from_grid(data, grid.lat, grid.lon, out_path, kind=kind)


def _cog_gridded(path, meta, grid, out_path, kind, res):
    """NetCDF·HDF4 — 파일 내 좌표가 있으면 그것을, 없으면 기준 격자를 쓴다."""
    data = _first_2d_array(path, meta.format, meta)
    lat, lon = (grid.lat, grid.lon) if grid is not None \
        else _embedded_latlon(path, meta.format)
    write_cog_from_grid(data, lat, lon, out_path, kind=kind)


def _cog_numpy(path, meta, grid, out_path, kind, res):
    """`.npy` — 배열만 있고 좌표가 없다 ⟹ **기준 격자가 언제나 필요하다**(`#58`).

    `parse` 가 `crs_embedded=False` 로 두므로 3) 단계에서 격자가 이미 섰다.
    격자가 없으면 여기 오기 전에 실패한다 — 여기서 좌표를 합성하지 않는다(`DR-9`).
    """
    arr = np.load(path, mmap_mode="r", allow_pickle=False)
    data = np.asarray(arr)
    while data.ndim > 2:          # 시각·밴드 축 — 한 번에 값 하나만 굽는다
        data = data[0]
    if data.ndim != 2:
        raise ParseError(f"2차원 배열이 아니다 — shape={arr.shape}")
    write_cog_from_grid(np.asarray(data, dtype="f4"), grid.lat, grid.lon,
                        out_path, kind=kind)


#: **그릴 수 있는 포맷 → COG 경로 분기표.** `RENDERABLE_FORMATS` 와의 어긋남은
#: `tests/test_format_declaration_parity.py` 가 기계로 잡는다 — 새 포맷이 렌더 목록에
#: 들어오고 여기 안 들어오면 **조용히 「COG 변환 실패」로만 보인다**(`#58` 의 무늬).
COG_BUILDERS = {
    "GeoTIFF": _cog_geotiff,
    "Binary": _cog_binary,
    "NetCDF": _cog_gridded,
    "HDF4": _cog_gridded,
    "NumPy": _cog_numpy,
}
assert set(COG_BUILDERS) <= set(RENDERABLE_FORMATS)



def run_file(path: Path, *, workdir: Path, grid_dir: Path | None = None,
             kind: str = "continuous",
             previews_root: Path | None = None) -> PipelineResult:
    """`previews_root` 가 주어지면 산출물은 **미리보기 산출물 자리**에 놓인다.

    ⚠ 없으면 예전처럼 `workdir` 임시 자리다 — 그 상태는 「자리를 안 정한 것」이고,
    유실 감지 게이트가 그 사실을 건수로 드러낸다. 조용히 성공으로 세지 않는다.
    """
    path = Path(path)
    workdir = Path(workdir)
    res = PipelineResult(input_path=path, status="FAILURE")

    # 1) 감지 — 매직바이트
    det = detect_format(path)
    if det.format is None:
        return _fail(res, f"감지 실패: {det.reason}")

    # 2) 파싱 — 자동 추출
    try:
        res.metadata = parse_metadata(path, det)
    except (ParseError, Exception) as e:
        return _fail(res, f"파싱 실패({det.format}): {e}")
    meta = res.metadata

    # 입력 tif 의 층 판정은 좌표 이전에 한다 — 판정 자체는 구조(IFD) 문제다 (DR-2)
    if det.format == "GeoTIFF":
        try:
            res.input_cog_class = classify_tiff(path)
        except ValueError as e:
            return _fail(res, f"TIFF 구조 판독 실패: {e}")

    # 2-b) **그릴 수 없는 포맷은 여기서 끝난다 — 그것이 실패가 아니다.**
    #      「그릴 수 없는 것과 등록할 수 없는 것은 다르다」(정본 §9 · 결정 #4 ·
    #      `renderable.py`). 그리지 않을 것에 기준 격자를 요구하면 **받아서 저장한다가
    #      거짓이 된다** — 아래 3) 이 정확히 그것을 요구하므로 그 앞에서 갈린다.
    if not is_renderable(det.format):
        res.notes.append(
            f"{det.format} 은 지원 포맷이지만 미리보기 대상이 아니다 — COG 산출 없음"
            " (〈134〉 결정 2-3). 등록·다운로드·계보 확정은 막지 않는다.")
        res.status = "SUCCESS"
        return res

    # 3) 좌표 — 파일 내 좌표가 없으면 기준 격자. 못 읽으면 [미상] + FAILURE.
    grid = None
    if not meta.crs_embedded:
        expect = meta.grid if isinstance(meta.grid, tuple) else None
        try:
            grid = find_reference_grid(grid_dir, expect_shape=expect)
            meta.crs = "WGS84 (기준 격자 파일)"
        except GridUnavailableError as e:
            meta.crs = UNKNOWN
            return _fail(res, f"좌표/격자 없음 — 지어내지 않는다 (DR-9): {e}")

    # 4) COG — 입력과 산출을 층에서 가른다
    workdir.mkdir(parents=True, exist_ok=True)
    if previews_root is not None:
        try:
            res.tile_content_key = map_tile_key(
                path, grid_dir=grid_dir, used_reference_grid=grid is not None, kind=kind)
        except ValueError as e:
            return _fail(res, f"지도 타일 내용 키를 지을 수 없다: {e}")
        out_path = storage_layout.preview_path(previews_root, res.tile_content_key, ".tif")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # **자리를 보는 것이 곧 찾아 쓰는 것이다** — 키가 내용 주소라 별도의 표가 없다
        # (`contracts/storage/layout.json` `keys.미리보기 산출물`·`contentKeys.지도 타일.why`).
        #
        # ⚠ **「파일이 있다」를 「구워져 있다」로 읽지 않는다.** 0 바이트 잔재·중단된 쓰기가
        #   그 자리에 남을 수 있고, 그것을 재사용하면 **에러 없이 깨진 미리보기**가 나간다 —
        #   이 레포가 여덟 번 중 일곱 번 당한 무늬다(`DATA-REFERENCE §0`). 그래서 **구조로**
        #   판정한다: IFD 를 읽어 COG 층이어야 재사용한다.
        if out_path.exists():
            usable = False
            why = ""
            try:
                cls = classify_tiff(out_path)
                usable = cls == "cog"
                why = f"자리의 파일이 {cls} 다"
            except Exception as e:            # 열리지도 않는 잔재
                why = f"자리의 파일을 판독할 수 없다: {e}"
            if usable:
                res.cog_path = str(out_path)
                res.reused = True
                res.status = "SUCCESS"
                res.notes.append(f"재사용 — 이미 구운 타일을 찾아 썼다({res.tile_content_key})")
                return res
            res.rebuilt_unusable = 1
            res.notes.append(f"재사용하지 않는다 — {why}. 다시 굽는다")
    else:
        out_path = workdir / (path.name.split(".")[0] + ".cog.tif")
        # 자리를 선언하지 않으면 **매번 다시 굽는다** — 정본이 그렇게 적었다.
        # 조용히 성공으로 세지 않고 사실로 남긴다. 유실 감지가 이 사실을 받는다.
        res.notes.append("자리(미리보기 루트)가 선언되지 않았다 — 재사용 없이 임시 자리에 굽는다")
    builder = COG_BUILDERS.get(det.format)
    if builder is None:
        # 여기 오면 **선언과 구현이 갈린 것**이다 — 목록 밖이 아니다(`#58` 과 같은 무늬).
        return _fail(res, f"{det.format} 은 그릴 수 있다고 선언됐는데 COG 경로가 없다 "
                          "— d5/pipeline.py 의 구현 결함이다")
    try:
        if builder(path, meta, grid, out_path, kind, res) is _ALREADY_COG:
            res.status = "SUCCESS"
            return res
    except Exception as e:
        return _fail(res, f"COG 변환 실패: {e}")

    res.cog_path = str(out_path)
    res.artifact = ArtifactRecord(path=out_path, origin="산출", source_input=path)
    res.status = "SUCCESS"
    return res


def _first_2d_array(path: Path, fmt: str, meta: AutoMetadata) -> np.ndarray:
    if fmt == "NetCDF":
        from netCDF4 import Dataset
        ds = Dataset(path, "r")
        try:
            for name in meta.variables:
                v = ds.variables[name]
                if v.ndim == 2:
                    return np.asarray(v[:], dtype="f4")
                if v.ndim == 3:
                    return np.asarray(v[0], dtype="f4")
        finally:
            ds.close()
        raise ParseError("2차원 데이터 변수를 찾지 못했다")
    from pyhdf.SD import SD, SDC
    sd = SD(str(path), SDC.READ)
    try:
        for name in meta.variables:
            sds = sd.select(name)
            info = sds.info()
            if info[1] == 2:
                return np.asarray(sds[:], dtype="f4")
        raise ParseError("2차원 SDS 를 찾지 못했다")
    finally:
        sd.end()


def _embedded_latlon(path: Path, fmt: str) -> tuple[np.ndarray, np.ndarray]:
    """파일 내부에서 위경도를 얻는다 — ① 좌표 변수 ② 투영 속성.

    ②(`internal_grid`)가 없던 동안 GK2A·MODIS 는 좌표 변수가 없다는 이유만으로
    기준 격자 후주입을 강요받았다 — 운영 dry-run 39건의 실패가 그것이다.
    둘 다 못 세우면 예외다. **지어내지 않는다 (DR-9).**
    """
    if fmt == "NetCDF":
        from netCDF4 import Dataset
        ds = Dataset(path, "r")
        try:
            names = {v.lower(): v for v in ds.variables}
            lat_n = names.get("lat") or names.get("latitude")
            lon_n = names.get("lon") or names.get("longitude")
            if lat_n and lon_n:
                lat = np.asarray(ds.variables[lat_n][:], dtype="f8")
                lon = np.asarray(ds.variables[lon_n][:], dtype="f8")
                if lat.ndim == 1 and lon.ndim == 1:
                    lon, lat = np.meshgrid(lon, lat)
                return lat, lon
        finally:
            ds.close()
    try:
        lat, lon, _note = internal_latlon(path, fmt)
    except InternalGridUnavailable as e:
        raise GridUnavailableError(f"{fmt} 는 파일 내 위경도를 세울 수 없다: {e}") from e
    return lat, lon


def run_batch(paths: list[Path], *, workdir: Path, grid_dirs: dict[str, Path] | None = None,
              ) -> tuple[list[PipelineResult], list[PipelineResult]]:
    """(성공, 실패) — 실패는 목록으로 남는다. 조용히 건너뛰지 않는다."""
    ok: list[PipelineResult] = []
    bad: list[PipelineResult] = []
    for p in paths:
        gd = None
        if grid_dirs:
            cand = Path(p).parent.parent / "04.Lat_Lon_info"
            gd = grid_dirs.get(str(p)) or (cand if cand.is_dir() else None)
        r = run_file(Path(p), workdir=workdir, grid_dir=gd)
        (ok if r.status == "SUCCESS" else bad).append(r)
    return ok, bad
