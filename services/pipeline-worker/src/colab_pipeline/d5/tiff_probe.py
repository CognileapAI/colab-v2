"""TIFF IFD 판독 — 순수 파이썬, 전체 파일을 읽지 않는다 (DR-11).

판정 정본 (DATA-REFERENCE §4):
  COG        = 내부 타일(태그 322/323) **그리고** 오버뷰(IFD 2개 이상)
  tiled-only = 타일 있으나 오버뷰 없음   ← 원천 실측 16건의 급소
  stripped   = 태그 278 (스트립)

「타일링 있으면 COG」로 판정하면 16건을 우리 산출물로 오인한다.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

TAG_ROWS_PER_STRIP = 278
TAG_TILE_WIDTH = 322
TAG_TILE_LENGTH = 323

_MAX_IFDS = 64  # 순환 IFD 방어


@dataclass(frozen=True)
class TiffStructure:
    ifd_count: int
    main_tiled: bool
    main_stripped: bool


def _read_ifds(path: Path) -> TiffStructure:
    with open(path, "rb") as f:
        header = f.read(8)
        if len(header) < 8:
            raise ValueError("TIFF 헤더가 짧다")
        bo = {b"II": "<", b"MM": ">"}.get(header[:2])
        if bo is None:
            raise ValueError("TIFF 매직 아님")
        magic, = struct.unpack(bo + "H", header[2:4])
        big = magic == 43
        if big:
            f.seek(4)
            offsize, _ = struct.unpack(bo + "HH", f.read(4))
            offset, = struct.unpack(bo + "Q", f.read(8))
            entry_fmt, count_fmt, off_fmt = 20, "Q", "Q"
        elif magic == 42:
            offset, = struct.unpack(bo + "I", header[4:8])
            entry_fmt, count_fmt, off_fmt = 12, "H", "I"
        else:
            raise ValueError(f"TIFF 버전 미상: {magic}")

        ifd_count = 0
        main_tags: set[int] = set()
        while offset and ifd_count < _MAX_IFDS:
            f.seek(offset)
            n, = struct.unpack(bo + count_fmt, f.read(struct.calcsize(count_fmt)))
            entries = f.read(n * entry_fmt)
            if len(entries) < n * entry_fmt:
                raise ValueError("IFD 가 잘렸다")
            tags = {
                struct.unpack_from(bo + "H", entries, i * entry_fmt)[0]
                for i in range(n)
            }
            if ifd_count == 0:
                main_tags = tags
            nxt = f.read(struct.calcsize(off_fmt))
            offset, = struct.unpack(bo + off_fmt, nxt)
            ifd_count += 1

        return TiffStructure(
            ifd_count=ifd_count,
            main_tiled=TAG_TILE_WIDTH in main_tags or TAG_TILE_LENGTH in main_tags,
            main_stripped=TAG_ROWS_PER_STRIP in main_tags,
        )


def classify_tiff(path: Path) -> str:
    """'cog' | 'tiled-only' | 'stripped'  — 원천 실측 6 / 16 / 40 이 각 부류다."""
    s = _read_ifds(Path(path))
    if s.main_tiled and s.ifd_count >= 2:
        return "cog"
    if s.main_tiled:
        return "tiled-only"
    return "stripped"
