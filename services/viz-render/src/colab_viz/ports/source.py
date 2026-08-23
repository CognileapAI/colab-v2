"""그릴 대상을 파일로 바꾸는 Port.

**왜 Port 인가** — `datasetId` 는 D3, `uploadId` 는 D5 가 소유하는 식별자다. D7 이 그
표를 직접 읽으면 불변규칙 1(도메인은 자기 표 + D1만)을 깬다. 그래서 이 seam 은
「식별자 → 본체 파일들 + 기준 격자 자리」만 요구하는 Protocol 로 두고, 어댑터를 갈아 끼운다.

⚠ **지금 들어 있는 어댑터는 파일시스템 하나다.** `d5_*` 원장(W1 `P2-db`)과 D3 객체
저장 배선은 이 레인의 소유가 아니라서, 실물 배선은 그 표가 서고 난 뒤 어댑터를 하나
더 붙이는 일이 된다. **Protocol 이 이미 그 자리를 비워 두었다는 것이 이 파일의 요점이다.**
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..kernel.ids import _ALPHABET  # noqa: F401  (ULID 알파벳 — 파생 id 인코딩에 쓴다)


@dataclass(frozen=True)
class SourcePart:
    """그릴 조각 하나 — 본체 파일이다."""
    file_id: str
    file_name: str
    path: Path
    size_bytes: int


@dataclass(frozen=True)
class ResolvedTarget:
    target_id: str
    is_upload: bool
    parts: tuple[SourcePart, ...]
    grid_dir: Path | None          # 기준 격자 파일들이 있는 자리. 없으면 None


class TargetNotFound(Exception):
    pass


class SourcePort(Protocol):
    def resolve(self, *, dataset_id: str | None, upload_id: str | None,
                file_ids: list[str] | None) -> ResolvedTarget: ...


def _derive_file_id(target_id: str, file_name: str) -> str:
    """파일 이름에서 결정적으로 만든 ULID 모양 식별자.

    ⚠ **이것은 `NB-A`(업로드가 발급한 `fileId` = `d3_file.id`)의 대체물이 아니다.**
    진짜 `fileId` 는 업로드 경로(`P2-api`)가 발급한다. 파일시스템 어댑터에는 그 원장이
    없어서, **조각을 골라 그리는 경로(`fileIds`)를 시험할 수 있을 만큼만** 결정적 id 를
    만든다. 원장 어댑터가 붙으면 이 함수는 쓰이지 않는다.
    """
    digest = hashlib.sha256(f"{target_id}/{file_name}".encode()).digest()
    value = int.from_bytes(digest[:16], "big")
    out = []
    for _ in range(26):
        out.append(_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


class FilesystemSourcePort:
    """`{root}/{targetId}/` 아래의 본체 파일 + `{root}/{targetId}/grid/` 기준 격자.

    등록된 데이터셋인지 등록 전 업로드인지를 **파일 배치로 구분하지 않는다** — 그것은
    호출자가 어느 식별자를 넘겼는가의 문제이고, 수명(`expiresAt`)만 거기서 갈린다.
    """

    GRID_DIRNAME = "grid"

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def file_id(self, target_id: str, file_name: str) -> str:
        return _derive_file_id(target_id, file_name)

    def resolve(self, *, dataset_id: str | None, upload_id: str | None,
                file_ids: list[str] | None) -> ResolvedTarget:
        target_id = dataset_id or upload_id or ""
        base = self._root / target_id
        if not base.is_dir():
            raise TargetNotFound(f"대상을 찾지 못했다: {target_id}")

        parts: list[SourcePart] = []
        for p in sorted(base.iterdir()):
            if p.is_dir() or p.name == "desktop.ini":
                continue
            parts.append(SourcePart(file_id=_derive_file_id(target_id, p.name),
                                    file_name=p.name, path=p,
                                    size_bytes=p.stat().st_size))
        if file_ids:
            wanted = set(file_ids)
            parts = [p for p in parts if p.file_id in wanted]
            if not parts:
                raise TargetNotFound("고른 조각이 대상 안에 없다")
        if not parts:
            raise TargetNotFound(f"대상에 본체 파일이 없다: {target_id}")

        grid_dir = base / self.GRID_DIRNAME
        return ResolvedTarget(target_id=target_id, is_upload=upload_id is not None,
                              parts=tuple(parts),
                              grid_dir=grid_dir if grid_dir.is_dir() else None)
