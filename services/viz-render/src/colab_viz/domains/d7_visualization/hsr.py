"""HSR 레이더 합성 바이너리 판독 — `DATA-REFERENCE §2`.

**PoC 코드를 옮겨 오지 않았다.** 물려받은 것은 *지식*이다 (`PLAN-SoT §6` · `P2.md §10-(가)`):
헤더 1024 B · `<i2` LE · row-major `(ny, nx)` · 값/100 = dBZ.

⚠ **두 가지를 PoC 와 반대로 한다.**
1. **블록 수를 가정하지 않는다** — 헤더의 `num_data` 를 읽는다. 길이를 `1024 + nx·ny·2`
   로 고정한 PoC 두 세대는 3블록 파일의 뒤 두 블록을 조용히 버린다 (`P2.md §2-25`).
2. **fill 은 정확일치로 판정한다** — `-25000`(비관측영역) · `-30000`(반경 밖)만 결측이고
   **`-20000` 은 표시를 위한 유효 하한이지 결측이 아니다.** `값 <= -20000` 같은 범위
   비교를 쓰지 않는다. PoC 가 `>= 249` 로 진짜 관측값을 지운 출시 버그가 이 포맷에서
   실물로 다시 나온다 (`DATA-REFERENCE §2.1` · `P2.md §2-26`).

⚠ 좌표는 여기서 나오지 않는다 — 실측 결과 헤더의 투영 파라미터 칸이 전부 0 이다
(`P2-W0-HSR-grid-measurement §2.5`). 위경도는 동봉 기준 격자에서만 온다.
"""
from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

HEADER_BYTES = 1024
FILL_NON_OBSERVED = -25000      # 관측영역내 비관측영역
FILL_OUT_OF_RADIUS = -30000     # 관측반경 밖
DISPLAY_MIN = -20000            # ⚠ 결측이 아니다 — 표시를 위한 최소값
SCALE_DIVISOR = 100.0           # 값/100 → dBZ

DATA_CODE_NAMES = {1: "에코", 2: "고도", 3: "지점순서", 4: "자료수",
                   5: "강수량", 6: "수상체", 15: "저고도에코탐지횟수"}

_CHUNK_ROWS = 256               # 스트리밍 단위 — 통째로 변환하지 않는다 (`DR-11`)


class HsrParseError(Exception):
    pass


@dataclass(frozen=True)
class HsrHeader:
    tm: datetime
    nx: int
    ny: int
    nz: int
    dxy_m: int
    num_data: int
    data_code: tuple[int, ...]


@dataclass
class HsrResult:
    header: HsrHeader
    blocks: list[np.ndarray]            # 원시 int16 (ny, nx)
    block_count_mismatch: bool

    def block_label(self, index: int) -> str:
        code = self.header.data_code[index] if index < len(self.header.data_code) else 0
        return DATA_CODE_NAMES.get(code, f"블록{index + 1}")


def parse_header(raw: bytes) -> HsrHeader:
    if len(raw) < HEADER_BYTES:
        raise HsrParseError(f"헤더가 {len(raw)} B — 1024 B 미만")
    yy, = struct.unpack_from("<h", raw, 3)
    mm, dd, hh, mi, ss = raw[5], raw[6], raw[7], raw[8], raw[9]
    nx, ny, nz, dxy = struct.unpack_from("<hhhh", raw, 20)
    num_data = raw[32]
    codes = tuple(c for c in raw[33:49] if c != 0)
    try:
        tm = datetime(yy, mm, dd, hh, mi, ss)
    except ValueError as e:
        raise HsrParseError(f"TIME_SS 판독 불가: {e}") from e
    if nx <= 0 or ny <= 0 or num_data <= 0:
        raise HsrParseError(f"헤더 값 불합리: nx={nx} ny={ny} num_data={num_data}")
    return HsrHeader(tm=tm, nx=nx, ny=ny, nz=nz, dxy_m=dxy,
                     num_data=num_data, data_code=codes)


def _open_maybe_gz(path: Path):
    with open(path, "rb") as f:
        magic = f.read(2)
    return gzip.open(path, "rb") if magic == b"\x1f\x8b" else open(path, "rb")


def parse_hsr(path: Path) -> HsrResult:
    """스트리밍 판독. `num_data` 가 선언한 만큼 읽되 **실재하는 블록만** 담는다."""
    path = Path(path)
    with _open_maybe_gz(path) as f:
        header = parse_header(f.read(HEADER_BYTES))
        block_bytes = header.nx * header.ny * 2
        blocks: list[np.ndarray] = []
        while len(blocks) < header.num_data:
            buf = f.read(block_bytes)
            if not buf:
                break
            if len(buf) < block_bytes:
                raise HsrParseError(f"블록 {len(blocks)} 이 잘렸다: {len(buf)}/{block_bytes} B")
            blocks.append(np.frombuffer(buf, dtype="<i2").reshape(header.ny, header.nx))
    if not blocks:
        raise HsrParseError("자료 블록이 하나도 없다")
    return HsrResult(header=header, blocks=blocks,
                     block_count_mismatch=len(blocks) != header.num_data)


def decode_block(raw: np.ndarray, *, scale: float = SCALE_DIVISOR) -> np.ndarray:
    """원시값 → dBZ. **fill 판정을 스케일 적용 전에, 정확일치로** 한다.

    순서를 지키는 이유 — 스케일을 먼저 걸면 `-200.0` 과 `-250.0` 을 비교하게 되고
    부동소수 비교로 정확일치가 흔들린다. 원시 정수에서 판정하고 그 자리에 NaN 을 넣는다.
    """
    out = np.empty(raw.shape, dtype="f4")
    for r0 in range(0, raw.shape[0], _CHUNK_ROWS):
        chunk = raw[r0:r0 + _CHUNK_ROWS]
        mask = (chunk == FILL_NON_OBSERVED) | (chunk == FILL_OUT_OF_RADIUS)
        dec = chunk.astype("f4") / scale
        dec[mask] = np.nan
        out[r0:r0 + _CHUNK_ROWS] = dec
    return out
