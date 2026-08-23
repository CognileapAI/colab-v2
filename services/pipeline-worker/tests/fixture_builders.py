"""합성 픽스처 빌더 — 바이트 수준 규칙은 DATA-REFERENCE §2·§3·§4.

실파일을 복사하지 않는다. 여기서 만드는 것은 판정 규칙을 시험할 최소 구조다.
"""
from __future__ import annotations

import gzip
import struct
from pathlib import Path

# ── TIFF ────────────────────────────────────────────────────────────────
# 판정 정본(DATA-REFERENCE §4): COG = 타일(322/323) 있고 IFD 2개 이상(오버뷰).
# 타일만 = 322/323 있고 IFD 1개. 스트립 = 278 만.

_T_WIDTH, _T_LENGTH = 256, 257
_T_BITS, _T_PHOTO = 258, 262
_T_STRIP_OFFSETS, _T_ROWS_PER_STRIP, _T_STRIP_BYTECOUNTS = 273, 278, 279
_T_TILE_WIDTH, _T_TILE_LENGTH = 322, 323
_T_TILE_OFFSETS, _T_TILE_BYTECOUNTS = 324, 325
_T_NEWSUBFILETYPE = 254


def _ifd_bytes(entries: list[tuple[int, int, int, int]], next_off: int) -> bytes:
    out = struct.pack("<H", len(entries))
    for tag, typ, cnt, val in sorted(entries):
        out += struct.pack("<HHII", tag, typ, cnt, val)
    out += struct.pack("<I", next_off)
    return out


def _write_tiff(path: Path, ifds: list[list[tuple[int, int, int, int]]]) -> Path:
    """리틀엔디안 classic TIFF — IFD 만 실재하면 판정기는 픽셀 데이터를 안 본다."""
    header = struct.pack("<2sHI", b"II", 42, 8)
    body = b""
    offset = 8
    blobs = []
    for i, entries in enumerate(ifds):
        size = 2 + 12 * len(entries) + 4
        blobs.append((offset, entries, size))
        offset += size
    out = header
    for i, (off, entries, size) in enumerate(blobs):
        next_off = blobs[i + 1][0] if i + 1 < len(blobs) else 0
        out += _ifd_bytes(entries, next_off)
    path.write_bytes(out)
    return path


def _base_entries(w: int, h: int) -> list[tuple[int, int, int, int]]:
    return [(_T_WIDTH, 3, 1, w), (_T_LENGTH, 3, 1, h), (_T_BITS, 3, 1, 8), (_T_PHOTO, 3, 1, 1)]


def make_stripped_tiff(path: Path, w: int = 64, h: int = 64) -> Path:
    e = _base_entries(w, h) + [
        (_T_STRIP_OFFSETS, 4, 1, 8),
        (_T_ROWS_PER_STRIP, 3, 1, h),
        (_T_STRIP_BYTECOUNTS, 4, 1, w * h),
    ]
    return _write_tiff(path, [e])


def make_tiled_only_tiff(path: Path, w: int = 512, h: int = 512) -> Path:
    e = _base_entries(w, h) + [
        (_T_TILE_WIDTH, 3, 1, 256),
        (_T_TILE_LENGTH, 3, 1, 256),
        (_T_TILE_OFFSETS, 4, 1, 8),
        (_T_TILE_BYTECOUNTS, 4, 1, 256 * 256),
    ]
    return _write_tiff(path, [e])


def make_cog_tiff(path: Path, w: int = 512, h: int = 512, n_overviews: int = 2) -> Path:
    main = _base_entries(w, h) + [
        (_T_TILE_WIDTH, 3, 1, 256),
        (_T_TILE_LENGTH, 3, 1, 256),
        (_T_TILE_OFFSETS, 4, 1, 8),
        (_T_TILE_BYTECOUNTS, 4, 1, 256 * 256),
    ]
    ifds = [main]
    for k in range(1, n_overviews + 1):
        ov = _base_entries(w >> k, h >> k) + [
            (_T_NEWSUBFILETYPE, 4, 1, 1),  # reduced-resolution
            (_T_TILE_WIDTH, 3, 1, 256),
            (_T_TILE_LENGTH, 3, 1, 256),
            (_T_TILE_OFFSETS, 4, 1, 8),
            (_T_TILE_BYTECOUNTS, 4, 1, 256 * 256),
        ]
        ifds.append(ov)
    return _write_tiff(path, ifds)


# ── HSR Binary ──────────────────────────────────────────────────────────
# 헤더 배치는 실파일 실측(2026-08-23, RDR_CMP_HSR_PUB_202508131000)으로 확정:
# TIME_SS@3 · nx@20 · ny@22 · nz@24 · dxy@26 · num_data@32 · data_code@33.

def make_hsr_header(
    nx: int, ny: int, *, nz: int = 1, dxy: int = 500, num_data: int = 1,
    data_code: bytes = b"\x01", yy: int = 2025, mm: int = 8, dd: int = 13,
    hh: int = 10, mi: int = 0, ss: int = 0,
) -> bytes:
    h = bytearray(1024)
    h[0], h[1], h[2] = 1, 5, 0
    h[3:5] = struct.pack("<h", yy)
    h[5:10] = bytes([mm, dd, hh, mi, ss])
    h[10:12] = struct.pack("<h", yy)
    h[12:17] = bytes([mm, dd, hh, mi, ss])
    h[20:22] = struct.pack("<h", nx)
    h[22:24] = struct.pack("<h", ny)
    h[24:26] = struct.pack("<h", nz)
    h[26:28] = struct.pack("<h", dxy)
    h[32] = num_data
    h[33:33 + len(data_code)] = data_code
    return bytes(h)


def make_hsr_bin_gz(
    path: Path, *, nx: int = 8, ny: int = 6, blocks: list[list[int]] | None = None,
    declared_num_data: int | None = None,
) -> Path:
    """작은 격자의 합성 HSR. blocks = int16 값 목록(블록별, 길이 nx*ny)."""
    if blocks is None:
        blocks = [[100] * (nx * ny)]
    num = declared_num_data if declared_num_data is not None else len(blocks)
    code = bytes(range(1, len(blocks) + 1))
    payload = make_hsr_header(nx, ny, num_data=num, data_code=code)
    for b in blocks:
        payload += struct.pack(f"<{nx * ny}h", *b)
    with gzip.open(path, "wb") as f:
        f.write(payload)
    return path


# ── npy 기준 격자 ────────────────────────────────────────────────────────

def make_npy_2d(path: Path, rows: int, cols: int, *, start: float = 33.0, step: float = 0.01,
                dtype: str = "<f4") -> Path:
    import numpy as np
    arr = (start + step * np.arange(rows * cols, dtype="f8")).reshape(rows, cols).astype(dtype)
    np.save(path, arr)
    return path


# ── NetCDF (netCDF4 라이브러리로 생성 — 진짜 컨테이너) ────────────────────

def make_netcdf(path: Path, *, with_latlon: bool = True, fmt: str = "NETCDF4") -> Path:
    import numpy as np
    from netCDF4 import Dataset

    ds = Dataset(path, "w", format=fmt)
    ds.createDimension("y", 4)
    ds.createDimension("x", 5)
    v = ds.createVariable("LST", "f4", ("y", "x"))
    v[:] = np.arange(20, dtype="f4").reshape(4, 5)
    if with_latlon:
        lat = ds.createVariable("lat", "f4", ("y", "x"))
        lon = ds.createVariable("lon", "f4", ("y", "x"))
        lat[:] = np.linspace(33, 39, 20).reshape(4, 5)
        lon[:] = np.linspace(124, 130, 20).reshape(4, 5)
    ds.close()
    return path


def make_hdf4_magic_stub(path: Path) -> Path:
    """HDF4 매직만 가진 스텁 — 감지 시험용(파싱 시험용 아님)."""
    path.write_bytes(b"\x0e\x03\x13\x01" + b"\x00" * 60)
    return path
