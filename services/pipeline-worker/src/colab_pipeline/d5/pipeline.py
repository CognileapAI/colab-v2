"""D5 처리 흐름 — 감지 → 파싱 → 좌표 → COG. fail-closed.

- 좌표를 못 찾으면 crs=[미상] · status=FAILURE (DR-9). 합성 격자는 없다.
- 사람이 올린 tif 는 (이미 COG 여도) **입력**이다 — 산출물로 기록되지 않는다 (DR-2).
- 실패 파일은 목록으로 남는다 — 조용히 건너뛰지 않는다 (완료조건 ④).

**stage2 대기.** 배포 단위·완료 정의에서 빠진다 — 파일·시험 유지(`〈71〉-㉰`).
근거: `dev-package/sessions/S1-PLAN.md` §5.2 행 7 · `PLAN-SoT.md §9 〈74〉〈75〉`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .cog import convert_tif_to_cog, write_cog_from_grid
from .detect import detect_format
from .formats import UNKNOWN
from .grid import GridUnavailableError, find_reference_grid
from .internal_grid import InternalGridUnavailable, internal_latlon
from .hsr import decode_block, parse_hsr
from .parse import AutoMetadata, ParseError, parse_metadata
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
    artifact: ArtifactRecord | None = None
    failures: list[str] = field(default_factory=list)


def _fail(res: PipelineResult, msg: str) -> PipelineResult:
    res.status = "FAILURE"
    res.failures.append(msg)
    return res


def run_file(path: Path, *, workdir: Path, grid_dir: Path | None = None,
             kind: str = "continuous") -> PipelineResult:
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
    out_path = workdir / (path.name.split(".")[0] + ".cog.tif")
    try:
        if det.format == "GeoTIFF":
            res.input_cog_class = classify_tiff(path)
            if res.input_cog_class == "cog":
                # 이미 COG 인 업로드 — 변환 불필요. 산출물 기록도 없다 (DR-2).
                res.status = "SUCCESS"
                return res
            convert_tif_to_cog(path, out_path, kind=kind)
        elif det.format == "Binary":
            hsr = parse_hsr(path)
            data = decode_block(hsr.blocks[0])
            write_cog_from_grid(data, grid.lat, grid.lon, out_path, kind=kind)
        elif det.format in ("NetCDF", "HDF4"):
            data = _first_2d_array(path, det.format, meta)
            if grid is not None:
                lat, lon = grid.lat, grid.lon
            else:
                lat, lon = _embedded_latlon(path, det.format)
            write_cog_from_grid(data, lat, lon, out_path, kind=kind)
        else:
            return _fail(res, f"지원 목록 밖: {det.format}")
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
