"""지원 포맷 — 〈51〉. 숫자가 아니라 목록이다.

PoC 의 4포맷(GRIB·NetCDF·Binary·HDF5)과 수만 같고 구성이 다르다:
GRIB 이 빠지고 GeoTIFF 가 들어오며, HDF 는 실측상 HDF4 다 (SEED-DATA F-2).
"""
from __future__ import annotations

SUPPORTED_FORMATS: list[str] = ["NetCDF", "Binary", "HDF4", "GeoTIFF"]

#: 못 읽은 값의 표기 — 추정으로 채우지 않는다 (DR-9 · DATA-REFERENCE §0)
UNKNOWN = "[미상]"
