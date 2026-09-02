"""그릴 대상을 파일로 바꾸는 Port.

**왜 Port 인가** — `datasetId` 는 D3, `uploadId` 는 D5 가 소유하는 식별자다. D7 이 그
표를 직접 읽으면 불변규칙 1(도메인은 자기 표 + D1만)을 깬다. 그래서 이 seam 은
「식별자 → 본체 파일들 + 기준 격자 자리」만 요구하는 Protocol 로 두고, 어댑터를 갈아 끼운다.

어댑터 둘 — **파일시스템**(core-api 가 놓은 디스크 그대로) · **S3**(`PLAN-SoT §9 〈178〉-㉴` V-3 —
버킷의 대상을 **작업 디렉터리로 내려받아** 같은 배치로 놓는다). 읽기 쪽(`readers.py`·`detect_format`)은
로컬 경로·랜덤 액세스를 전제하므로 두 어댑터 모두 `resolve` → `materialize` 뒤에는 **로컬 경로**를 낸다.
파일시스템의 `materialize` 는 항등이다.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol

from ..kernel import storage_layout
from ..kernel.ids import _ALPHABET  # noqa: F401  (ULID 알파벳 — 파생 id 인코딩에 쓴다)

#: ULID 26자. **배치가 본체를 `fileId` 로 이름 붙이므로** 디스크의 이름이 곧 원장의 id 다.
_ULID_RE = re.compile(rf"^[{_ALPHABET}]{{26}}$")


@dataclass(frozen=True)
class SourcePart:
    """그릴 조각 하나 — 본체 파일이다.

    `version` 은 객체 저장소의 판본(ETag). 파일시스템 조각은 None 이고 캐시 키는 mtime 을 쓴다 —
    S3 조각은 내려받을 때마다 mtime 이 새로 찍히므로 ETag 가 대신 키에 들어간다(`source_digest.py`).
    """
    file_id: str
    file_name: str
    path: Path
    size_bytes: int
    version: str | None = None


@dataclass(frozen=True)
class ResolvedTarget:
    target_id: str
    is_upload: bool
    parts: tuple[SourcePart, ...]
    grid_dir: Path | None          # 기준 격자 파일들이 있는 자리. 없으면 None
    #: 격자 파일 목록 — S3 어댑터가 내려받을 것을 알기 위해 든다. 파일시스템은 비어 있다(디렉터리가 곧 목록).
    grid_parts: tuple[SourcePart, ...] = ()


class TargetNotFound(Exception):
    pass


class SizeMismatch(Exception):
    """목록·HeadObject·받은 바이트의 크기가 서로 다르다 — 그 사이 객체가 바뀌었거나 전송이 잘렸다."""


class WorkspaceExceeded(Exception):
    """대상 하나가 작업 디렉터리 상한보다 크다 — 내려받기 전에 거절한다."""


class SourcePort(Protocol):
    def resolve(self, *, dataset_id: str | None, upload_id: str | None,
                file_ids: list[str] | None) -> ResolvedTarget: ...

    def materialize(self, target: ResolvedTarget) -> ResolvedTarget:
        """`resolve` 가 낸 경로에 바이트가 실제로 있게 한다. 파일시스템은 항등."""
        ...


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


def _file_id_of(target_id: str, file_name: str) -> str:
    """디스크의 이름이 **이미 `fileId`** 면 그것을 쓴다.

    ⚠ 이 갈림이 없으면 `fileIds` 로 조각을 고르는 경로가 **실배포에서만** 깨진다.
    요청이 싣는 `fileIds` 는 업로드가 발급한 ULID 인데, 파생 id 는 파일명을 해시한
    다른 값이라 어느 것도 안 맞고, 그 실패는 404 「고른 조각이 대상 안에 없다」로 나온다.
    파일명에서 만든 id 는 원장 없이 세운 시험 픽스처를 위한 자리로 남는다.
    """
    return file_name if _ULID_RE.match(file_name) else _derive_file_id(target_id, file_name)


class FilesystemSourcePort:
    """접수한 바이트를 **core-api 가 놓은 자리 그대로** 읽는다.

    배치의 정본은 `kernel/storage_layout`(생성물 · `contracts/storage/layout.json`)이고
    core-api·pipeline-worker 가 쓰는 것과 **같은 함수**다. `root` 는 저장소 루트이지
    `uploads/` 안쪽이 아니다 — 「한 층 아래」를 배포 설정이 손으로 세던 자리가
    `03-HANDOFF §4 #20` 이 난 자리다.

    등록된 데이터셋인지 등록 전 업로드인지를 **파일 배치로 구분하지 않는다** — 그것은
    호출자가 어느 식별자를 넘겼는가의 문제이고, 수명(`expiresAt`)만 거기서 갈린다.
    """

    #: 배치의 정본은 생성물이다. 이 별칭은 옛 이름을 부르던 자리를 위해 남긴다.
    GRID_DIRNAME = storage_layout.GRID_DIRNAME

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def file_id(self, target_id: str, file_name: str) -> str:
        return _derive_file_id(target_id, file_name)

    def resolve(self, *, dataset_id: str | None, upload_id: str | None,
                file_ids: list[str] | None) -> ResolvedTarget:
        target_id = dataset_id or upload_id or ""
        base = storage_layout.target_dir(self._root, target_id)
        if not base.is_dir():
            raise TargetNotFound(f"대상을 찾지 못했다: {target_id}")

        parts: list[SourcePart] = []
        for p in sorted(base.iterdir()):
            if p.is_dir() or p.name == "desktop.ini":
                continue
            parts.append(SourcePart(file_id=_file_id_of(target_id, p.name),
                                    file_name=p.name, path=p,
                                    size_bytes=p.stat().st_size))
        parts = _pick(parts, file_ids, target_id)

        grid_dir = storage_layout.grid_dir(self._root, target_id)
        return ResolvedTarget(target_id=target_id, is_upload=upload_id is not None,
                              parts=tuple(parts),
                              grid_dir=grid_dir if grid_dir.is_dir() else None)

    def materialize(self, target: ResolvedTarget) -> ResolvedTarget:
        return target


def _pick(parts: list[SourcePart], file_ids: list[str] | None, target_id: str) -> list[SourcePart]:
    if file_ids:
        wanted = set(file_ids)
        parts = [p for p in parts if p.file_id in wanted]
        if not parts:
            raise TargetNotFound("고른 조각이 대상 안에 없다")
    if not parts:
        raise TargetNotFound(f"대상에 본체 파일이 없다: {target_id}")
    return parts


class S3SourcePort:
    """버킷의 대상을 작업 디렉터리에 **같은 배치로** 내려받는다 (`〈178〉-㉴`).

    - `resolve` 는 목록(`ListObjectsV2`, 접두사 하나)만 본다 — 바이트를 만지지 않는다. 크기는 목록 값이고
      경로는 **작업 디렉터리의 예정 경로**다(`storage_layout.storage_path(workdir, …)`).
    - `materialize` 가 내려받는다: HeadObject(크기·ETag) → 목록 크기와 대조 → `.part` 임시파일 →
      받은 바이트 대조 → rename. 어느 대조든 어긋나면 `SizeMismatch` 이고 파일을 남기지 않는다.
    - **캐시** = 작업 디렉터리. 같은 ETag·같은 크기의 파일이 이미 있으면 내려받지 않는다.
      상한(`max_bytes`)은 숫자거나 명시 무제한(`math.inf`)이어야 하고, 넘으면 **가장 오래 안 쓴 대상**부터
      지운다. 대상 하나가 상한보다 크면 내려받기 전에 `WorkspaceExceeded`.
    - 캐시 키는 ETag 로 든다(`SourcePart.version`) — 내려받은 파일의 mtime 은 렌더마다 새로워지므로
      그것을 키에 넣으면 `previews/` 가 무한히 는다.
    ETag 기록은 프로세스 메모리다 — 재기동 뒤엔 캐시 미스로 다시 내려받는다(정직한 쪽).
    """

    def __init__(self, client: Any, *, workdir: Path, max_bytes: float) -> None:
        if not isinstance(max_bytes, (int, float)) or isinstance(max_bytes, bool):
            raise TypeError("max_bytes 는 숫자(바이트) 또는 math.inf 여야 한다 — 미설정은 기동 거부다")
        if max_bytes <= 0:
            raise ValueError("max_bytes 는 양수여야 한다")
        self.client = client
        self.workdir = Path(workdir)
        self.max_bytes = max_bytes
        self._etags: dict[Path, str] = {}
        self._last_used: dict[str, float] = {}
        self._tick = 0.0
        self._lock = threading.Lock()

    # ── resolve ─────────────────────────────────────────────────────────────
    def resolve(self, *, dataset_id: str | None, upload_id: str | None,
                file_ids: list[str] | None) -> ResolvedTarget:
        target_id = dataset_id or upload_id or ""
        prefix = f"{storage_layout.UPLOADS_PREFIX}/{target_id}/"
        grid_prefix = f"{prefix}{storage_layout.GRID_DIRNAME}/"
        parts: list[SourcePart] = []
        grids: list[SourcePart] = []
        for key, size in self.client.list_objects(prefix):
            rest = key[len(prefix):]
            if not rest:
                continue
            if key.startswith(grid_prefix):
                name = key[len(grid_prefix):]
                if not name or "/" in name:
                    continue
                grids.append(SourcePart(
                    file_id=name, file_name=name,
                    path=storage_layout.grid_dir(self.workdir, target_id) / name, size_bytes=size))
                continue
            if "/" in rest:
                continue
            parts.append(SourcePart(
                file_id=_file_id_of(target_id, rest), file_name=rest,
                path=storage_layout.storage_path(self.workdir, target_id, file_id=rest,
                                                 kind=storage_layout.BODY_KIND),
                size_bytes=size))
        if not parts and not grids:
            raise TargetNotFound(f"대상을 찾지 못했다: {target_id}")
        parts = _pick(parts, file_ids, target_id)
        grid_dir = storage_layout.grid_dir(self.workdir, target_id) if grids else None
        return ResolvedTarget(target_id=target_id, is_upload=upload_id is not None,
                              parts=tuple(parts), grid_dir=grid_dir, grid_parts=tuple(grids))

    # ── materialize ─────────────────────────────────────────────────────────
    def materialize(self, target: ResolvedTarget) -> ResolvedTarget:
        need = sum(p.size_bytes for p in target.parts) + sum(g.size_bytes for g in target.grid_parts)
        if need > self.max_bytes:
            raise WorkspaceExceeded(
                f"대상 {target.target_id} 가 {need} B 로 작업 디렉터리 상한 {self.max_bytes} 를 넘는다")
        with self._lock:
            parts = tuple(self._fetch(target.target_id, p, is_grid=False) for p in target.parts)
            grids = tuple(self._fetch(target.target_id, g, is_grid=True) for g in target.grid_parts)
            self._touch(target.target_id)
            self._evict(keep=target.target_id)
        return replace(target, parts=parts, grid_parts=grids)

    def _key_of(self, target_id: str, part: SourcePart, *, is_grid: bool) -> str:
        if is_grid:
            return storage_layout.storage_key(target_id, file_id="", kind=storage_layout.GRID_KIND,
                                              file_name=part.file_name)
        # 키는 **객체 이름**(`file_name`)으로 되짚는다 — `file_id` 는 이름이 ULID 가 아닐 때 파생값이라
        # 그것으로 키를 만들면 없는 객체를 가리킨다(실호출 증거에서 잡힌 자리).
        return storage_layout.storage_key(target_id, file_id=part.file_name, kind=storage_layout.BODY_KIND)

    def _fetch(self, target_id: str, part: SourcePart, *, is_grid: bool) -> SourcePart:
        key = self._key_of(target_id, part, is_grid=is_grid)
        size, etag = self.client.head_object(key)
        if size != part.size_bytes:
            raise SizeMismatch(f"{key}: 목록 크기 {part.size_bytes} ≠ HeadObject 크기 {size} — "
                               "413 판정 뒤 객체가 바뀌었다")
        path = part.path
        if path.is_file() and path.stat().st_size == size and self._etags.get(path) == etag:
            return replace(part, version=etag)
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(f".{path.name}.part")
        received = 0
        try:
            with partial.open("wb") as fh:
                for chunk in self.client.get_object_stream(key):
                    fh.write(chunk)
                    received += len(chunk)
            if received != size:
                raise SizeMismatch(f"{key}: HeadObject 크기 {size} ≠ 받은 바이트 {received} — 반쪽 파일을 쓰지 않는다")
            os.replace(partial, path)
        finally:
            if partial.exists():
                partial.unlink()
        self._etags[path] = etag
        return replace(part, version=etag)

    # ── 캐시 관리 ───────────────────────────────────────────────────────────
    def _touch(self, target_id: str) -> None:
        self._tick += 1.0
        self._last_used[target_id] = self._tick

    def _target_dirs(self) -> list[Path]:
        root = storage_layout.uploads_root(self.workdir)
        if not root.is_dir():
            return []
        return [d for d in root.iterdir() if d.is_dir()]

    @staticmethod
    def _dir_bytes(d: Path) -> int:
        return sum(p.stat().st_size for p in d.rglob("*") if p.is_file())

    def _evict(self, *, keep: str) -> None:
        if self.max_bytes == math.inf:
            return
        dirs = {d.name: d for d in self._target_dirs()}
        total = sum(self._dir_bytes(d) for d in dirs.values())
        # 오래 안 쓴 순 — 기록이 없는 디렉터리(재기동 전 것)가 가장 먼저 나간다
        order = sorted((t for t in dirs if t != keep), key=lambda t: self._last_used.get(t, 0.0))
        for t in order:
            if total <= self.max_bytes:
                break
            d = dirs[t]
            total -= self._dir_bytes(d)
            shutil.rmtree(d, ignore_errors=True)
            self._last_used.pop(t, None)
            self._etags = {p: e for p, e in self._etags.items() if d not in p.parents}
