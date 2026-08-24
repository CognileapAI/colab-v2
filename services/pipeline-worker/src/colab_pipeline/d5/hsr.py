"""HSR 레이더 합성 바이너리 — 확정 스펙 (DATA-REFERENCE §2 · HARVEST ⑦).

헤더 1024 B = RDR_CMP_HEAD(64) + RDR_CMP_STN_LIST(20)×48.
자료 블록 = int16 LE × nx × ny, num_data 개 (에코·고도·지점 …).

필드 오프셋 근거 — 실파일 실측 (2026-08-23, RDR_CMP_HSR_PUB_202508131000):
  TIME_SS(관측)@3 이 파일명 시각과 일치 · nx=2305@20 · ny=2881@22 · nz=1@24 ·
  dxy=500@26 · num_data@32 · data_code[16]@33 (실물 값 3 / 1,2,3).
  바이트 0~2, 17~19 는 판독 못 한 필드 — 쓰지 않는다.
  **36~63 B(투영 파라미터 자리)는 실물에서 전부 0 이다** — 헤더로 위경도를 세울 수 없다.

**stage2 대기.** 배포 단위·완료 정의에서 빠진다 — 파일·시험 유지(`〈71〉-㉰`).
근거: `dev-package/sessions/S1-PLAN.md` §5.2 행 7 · `PLAN-SoT.md §9 〈74〉〈75〉`.
  명세 기재값(Lambert·표준위도 30/60·기준 38/126)으로 재현하면 위도 0.053°(≈5.9 km)
  어긋난다 → HSR 은 기준 격자 파일(Lat_HSR.npy/Lon_HSR.npy)이 **필수**다.
  (DATA-REFERENCE §0 M-8 · §1.1 · DATA-PIPELINE-MEASUREMENT.md)

⚠ 블록 수를 가정하지 않는다 — `num_data` 를 읽는다 (P2 §2 행 25).
  단, 원천 배포본은 헤더가 3을 선언하고 1블록만 담는다 — 실크기와 대조해
  mismatch 를 기록하고, 실재하는 블록만 읽는다. 조용히 버리지도, 넘겨짚지도 않는다.

⚠ NULL 은 세 값이고 fill 판정은 정확일치다 (행 26):
  -25000(비관측) · -30000(반경 밖)만 결측. **-20000 은 유효 하한이다.**
"""
from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

HEADER_BYTES = 1024
FILL_NON_OBSERVED = -25000
FILL_OUT_OF_RADIUS = -30000
DISPLAY_MIN = -20000          # 결측이 아니다
SCALE_DIVISOR = 100.0         # 값/100 → dBZ (반사도 블록)

DATA_CODE_NAMES = {1: "에코", 2: "고도", 3: "지점순서", 4: "자료수",
                   5: "강수량", 6: "수상체", 15: "저고도에코탐지횟수"}

_CHUNK_ROWS = 256  # 스트리밍 단위 — 전체 블록을 한 번에 변환하지 않는다


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
    blocks_present: int
    block_count_mismatch: bool
    blocks: list[np.ndarray]   # 원시 int16 (ny, nx) — 변환은 decode_block


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
    """스트리밍 판독 — 파일 전체를 단일 버퍼로 올리지 않는다 (DR-11)."""
    path = Path(path)
    with _open_maybe_gz(path) as f:
        header = parse_header(f.read(HEADER_BYTES))
        block_bytes = header.nx * header.ny * 2
        blocks: list[np.ndarray] = []
        while len(blocks) < header.num_data:
            buf = f.read(block_bytes)
            if len(buf) == 0:
                break
            if len(buf) < block_bytes:
                raise HsrParseError(
                    f"블록 {len(blocks)} 이 잘렸다: {len(buf)}/{block_bytes} B")
            arr = np.frombuffer(buf, dtype="<i2").reshape(header.ny, header.nx)
            blocks.append(arr)
    return HsrResult(
        header=header,
        blocks_present=len(blocks),
        block_count_mismatch=(len(blocks) != header.num_data),
        blocks=blocks,
    )


def decode_block(raw: np.ndarray, *, scale: float = SCALE_DIVISOR) -> np.ndarray:
    """반사도 블록 변환 — fill 은 **정확일치**. -20000 은 살린다."""
    out = np.empty_like(raw, dtype="f4")
    for r0 in range(0, raw.shape[0], _CHUNK_ROWS):
        chunk = raw[r0:r0 + _CHUNK_ROWS]
        dec = chunk.astype("f4") / scale
        mask = (chunk == FILL_NON_OBSERVED) | (chunk == FILL_OUT_OF_RADIUS)
        dec[mask] = np.nan
        out[r0:r0 + _CHUNK_ROWS] = dec
    return out
