"""포맷 감지 — 매직바이트가 정본이고 확장자는 힌트다 (DR-3 · DATA-REFERENCE §3).

세 번 다 확장자가 거짓말을 했다:
- 폴더명 HDF5 · DB enum HDF5 → 실체 HDF4 (`0e 03 13 01`)
- `.nc` → 실체 HDF5 컨테이너 (NetCDF4 라 기술적으로 정상이지만 로더가 갈린다)
- `.tif` → 이미 COG (입·산출 층 구분이 필요)

`\\x89HDF` 만으로는 NetCDF4 와 순수 HDF5 를 못 가른다 — try-open 이 필수다.
감지 실패는 실패다. 지어내지 않는다.
"""
from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from pathlib import Path

MAGIC_HDF4 = b"\x0e\x03\x13\x01"
MAGIC_HDF5 = b"\x89HDF\r\n\x1a\n"
MAGIC_TIFF_LE = b"II*\x00"
MAGIC_TIFF_BE = b"MM\x00*"
MAGIC_GZIP = b"\x1f\x8b"
MAGIC_CDF1 = b"CDF\x01"
MAGIC_CDF2 = b"CDF\x02"
MAGIC_CDF5 = b"CDF\x05"
#: GRIB1·GRIB2 공통 매직. **판(edition) 은 offset 7 이고 1 또는 2 다** (`〈134〉`).
MAGIC_GRIB = b"GRIB"
GRIB_EDITIONS = (1, 2)

_EXT_CLAIMS = {
    ".nc": "NetCDF",
    ".bin": "Binary",
    ".hdf": "HDF4",
    ".h5": "HDF4",   # 원천의 오표기 계열 — 어차피 힌트일 뿐이다
    ".tif": "GeoTIFF",
    ".tiff": "GeoTIFF",
    # GRIB 는 표기가 넷으로 흩어져 있다 — 어차피 힌트이고 판정은 매직이 한다.
    ".grib": "GRIB",
    ".grib2": "GRIB",
    ".grb": "GRIB",
    ".grb2": "GRIB",
}


@dataclass(frozen=True)
class DetectionResult:
    format: str | None          # SUPPORTED_FORMATS 의 하나, 또는 None(미상 = 실패)
    container: str | None       # "gzip" | "HDF5" | None
    extension_claim: str | None
    extension_mismatch: bool
    reason: str = ""


def _ext_claim(path: Path) -> str | None:
    name = path.name.lower()
    if name.endswith(".gz"):
        name = name[:-3]
    return _EXT_CLAIMS.get(Path(name).suffix)


def _plausible_hsr_header(head: bytes) -> bool:
    """HSR 헤더 개연성 — 배치는 실파일 실측 (hsr.py 참조)."""
    if len(head) < 64:
        return False
    yy, = struct.unpack_from("<h", head, 3)
    mm, dd, hh = head[5], head[6], head[7]
    nx, ny, nz, dxy = struct.unpack_from("<hhhh", head, 20)
    return (
        1990 <= yy <= 2100 and 1 <= mm <= 12 and 1 <= dd <= 31 and hh <= 23
        and nx > 0 and ny > 0 and nz > 0 and dxy > 0
    )


#: `.npy` — 매직 + 버전 2B + 길이 2B + ASCII 헤더 dict(`descr`·`fortran_order`·`shape`).
#: 헤더가 ASCII 라 numpy 없이도 읽힌다(`DATA-REFERENCE §1`). **확장자 판정이 아니다.**
MAGIC_NPY = b"\x93NUMPY"


def _is_grib(head: bytes) -> bool:
    """`GRIB` 매직 **＋ 판 바이트**. 매직만 보면 산문이 GRIB 이 된다.

    「GRIB is a format used in meteorology.」 로 시작하는 텍스트 파일이 실제로 잡힌다 —
    `GRIB` 은 사람이 쓰는 낱말이기도 하다. 다른 포맷의 매직(`\\x0e\\x03\\x13\\x01` 등)과
    달리 **인쇄 가능한 ASCII 라 우연히 겹칠 수 있는 유일한 매직**이다.

    GRIB1 = `GRIB` ＋ 전체 길이 3B ＋ 판 1B, GRIB2 = `GRIB` ＋ 예약 2B ＋ 분야 1B ＋
    판 1B. **둘 다 offset 7 이 판**이고 값은 1 또는 2 다. 지어내지 않는다 — 판을
    못 읽으면 GRIB 이라고 말하지 않는다(`DR-9`).
    """
    if not head.startswith(MAGIC_GRIB) or len(head) < 8:
        return False
    return head[7] in GRIB_EDITIONS


def _sniff_bytes(head: bytes) -> tuple[str | None, str | None, str]:
    """(format, container, reason). HDF5 매직은 여기서 확정하지 않는다."""
    if _is_grib(head):
        return "GRIB", None, f"magic GRIB (판 {head[7]})"
    if head.startswith(MAGIC_HDF4):
        return "HDF4", None, "magic 0e031301"
    if head.startswith(MAGIC_HDF5):
        return "__HDF5__", "HDF5", "magic \\x89HDF — try-open 필요"
    if head.startswith((MAGIC_CDF1, MAGIC_CDF2, MAGIC_CDF5)):
        return "NetCDF", None, "magic CDF (classic)"
    if head.startswith((MAGIC_TIFF_LE, MAGIC_TIFF_BE)):
        return "GeoTIFF", None, "magic TIFF"
    if head.startswith(MAGIC_NPY):
        return "NumPy", None, "magic \\x93NUMPY"
    if _plausible_hsr_header(head):
        return "Binary", None, "HSR 헤더 개연성 (실측 배치)"
    return None, None, "알려진 매직바이트 없음"


def _resolve_hdf5_container(path: Path) -> tuple[str | None, str]:
    """\\x89HDF 를 try-open 으로 가른다 — NetCDF4 인가, 순수 HDF5 인가."""
    try:
        from netCDF4 import Dataset
        ds = Dataset(path, "r")
        ds.close()
        return "NetCDF", "HDF5 컨테이너 — netCDF4 try-open 성공"
    except Exception:
        # 순수 HDF5 는 〈51〉 지원 목록 밖이다 — 미상으로 fail-closed
        return None, "HDF5 컨테이너인데 NetCDF 로 열리지 않는다 — 지원 목록(〈51〉) 밖"


def detect_format(path: Path) -> DetectionResult:
    path = Path(path)
    claim = _ext_claim(path)
    try:
        with open(path, "rb") as f:
            head = f.read(64)
    except OSError as e:
        return DetectionResult(None, None, claim, False, f"읽기 실패: {e}")

    container = None
    if head.startswith(MAGIC_GZIP):
        container = "gzip"
        try:
            with gzip.open(path, "rb") as f:
                head = f.read(64)
        except OSError as e:
            return DetectionResult(None, "gzip", claim, False, f"gzip 해제 실패: {e}")

    fmt, inner_container, reason = _sniff_bytes(head)
    if fmt == "__HDF5__":
        if container == "gzip":
            return DetectionResult(None, "gzip", claim, False,
                                   "gzip 안의 HDF5 컨테이너 — 미지원 조합")
        fmt, reason = _resolve_hdf5_container(path)
        inner_container = "HDF5"
    if container is None:
        container = inner_container

    if fmt is None:
        return DetectionResult(None, container, claim, False, reason)
    mismatch = claim is not None and claim != fmt
    return DetectionResult(fmt, container, claim, mismatch, reason)
