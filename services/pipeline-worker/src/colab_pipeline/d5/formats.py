"""지원 포맷 — 〈51〉. 숫자가 아니라 목록이다.

PoC 의 4포맷(GRIB·NetCDF·Binary·HDF5)과 수만 같고 구성이 다르다:
GRIB 이 빠지고 GeoTIFF 가 들어오며, HDF 는 실측상 HDF4 다 (SEED-DATA F-2).

⭑ `NumPy` 가 `〈77〉` 로 들어왔다 — Ted 판정: 「npy 도 처리해야 하는 포맷이다만.
추가 포맷으로 한다. nc 랑은 다른 파일이다.」 **격자 파일의 다른 표현형이 아니라
독립 포맷이고, 본체로 올라오면 본체다** — 무엇인지는 `kind` 가 정한다(`§E.3b`).
⚠ 같은 이름의 목록이 `services/viz-render/.../readers.py` 에도 있다. 함께 고친다.
"""
from __future__ import annotations

SUPPORTED_FORMATS: list[str] = ["NetCDF", "Binary", "HDF4", "GeoTIFF", "NumPy"]

#: 못 읽은 값의 표기 — 추정으로 채우지 않는다 (DR-9 · DATA-REFERENCE §0)
UNKNOWN = "[미상]"
