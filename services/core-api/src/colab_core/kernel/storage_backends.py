"""`ports/storage.py` 의 두 구현 — 로컬 디스크(local) · S3(s3).

어느 쪽이 서는지는 `Settings.storage_mode` 가 정한다 (`kernel/config.py` · `〈173〉`).
로컬 개발은 local 이 기본이고, dev/prod 배포가 s3 를 켠다. 저장 키는 두 구현이
**완전히 같다** — `kernel/storage_layout.storage_key()` 가 POSIX 상대 키를 주므로
로컬에서는 경로로 접고, S3 에서는 오브젝트 키로 그대로 쓴다.
"""
from __future__ import annotations

import os
import pathlib
import shutil
from collections.abc import Sequence
from typing import Any, BinaryIO

from colab_core.kernel import errors, storage_layout
from colab_core.kernel.s3 import S3Client, S3Error

# 파일 인자의 모양은 `ports/ingestion.UploadFileRecord`(file_id·storage_key)다.
# 층 규칙(app > domains > ports > kernel)상 kernel 은 ports 를 import 하지 않으므로
# 여기서는 덕 타이핑으로 받는다 — 계약 검사는 Protocol(`ports/storage.py`)이 한다.

#: 스트림 복사 청크. 업로드 본문을 통째로 메모리에 올리지 않는다 (`〈175〉`).
STREAM_CHUNK = 8 * 1024 * 1024

#: S3 단일 PutObject 의 하드 리밋. 그 위는 멀티파트뿐이고, 서버 경유 경로는 멀티파트를
#: 하지 않는다 — 큰 파일의 정문은 프리사인드 전송(`〈174〉`)이다.
S3_SINGLE_PUT_MAX = 5 * 1024 ** 3


def _stream_size(stream: BinaryIO) -> int | None:
    """탐색 가능한 스트림이면 위치를 건드리지 않고 남은 길이를 잰다. 아니면 None."""
    try:
        if not stream.seekable():
            return None
        here = stream.tell()
        end = stream.seek(0, os.SEEK_END)
        stream.seek(here)
        return end - here
    except (OSError, ValueError, AttributeError):
        return None


class LocalFilesystemStorage:
    """지금까지의 동작 그대로 — `routes/ingestion.py` 에 살던 헬퍼 4개의 이사.

    ⚠ 키가 곧 배치다. 예전에는 `sha256(key)` 한 덩이를 루트에 평평하게 깔았는데,
    바이트를 여는 쪽(pipeline-worker)은 키를 경로로 그대로 읽어 실제로 갈라졌고,
    그 실패는 에러가 아니라 「형식 인식 실패」로 위장했다. 그 뒤 세 번째 소비자
    (viz-render)까지 드러나 규칙을 정본(`contracts/storage/layout.json`)으로 옮겼다
    (`03-HANDOFF §4 #20`). 이 구현은 그 정본 키를 경로로 접기만 한다.
    """

    def __init__(self, root: pathlib.Path):
        self._root = root
        root.mkdir(parents=True, exist_ok=True)

    def put(self, *, key: str, payload: bytes) -> None:
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def put_stream(self, *, key: str, stream: BinaryIO) -> int:
        """청크 복사 — 파일 크기와 무관하게 메모리는 청크 하나다."""
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            shutil.copyfileobj(stream, fh, length=STREAM_CHUNK)
            return fh.tell()

    def discard(self, *, key: str | None, keep: str | None = None) -> None:
        if not key or key == keep:
            return
        try:
            (self._root / key).unlink()
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            return

    def relocate(self, *, files: Sequence[Any],
                 new_keys: dict[str, str]) -> None:
        # 같은 볼륨 안의 이름 바꾸기(os.replace)라 바이트를 복사하지 않는다.
        # 도중 실패하면 옮긴 것을 역순으로 되돌린다 — 반쪽 이동을 남기지 않는다.
        done: list[tuple[pathlib.Path, pathlib.Path]] = []
        try:
            for f in files:
                new_key = new_keys[f.file_id]
                if not f.storage_key or f.storage_key == new_key:
                    continue
                src, dst = self._root / f.storage_key, self._root / new_key
                if not src.is_file():
                    continue  # 바이트가 이미 없다. 원장은 새 자리를 적는다
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.replace(src, dst)
                done.append((src, dst))
        except OSError:
            for src, dst in reversed(done):
                src.parent.mkdir(parents=True, exist_ok=True)
                os.replace(dst, src)
            raise
        self._prune_upload_dirs([f.storage_key for f in files])

    def _prune_upload_dirs(self, old_keys: Sequence[str | None]) -> None:
        """옮기고 남은 빈 자리를 치운다. 비어 있지 않으면 건드리지 않는다."""
        stop = storage_layout.uploads_root(self._root)
        for key in old_keys:
            if not key:
                continue
            node = (self._root / key).parent
            while stop in node.parents:
                try:
                    node.rmdir()
                except OSError:
                    break
                node = node.parent


class S3UploadStorage:
    """비로컬 벌(dev/prod)의 저장 — 키를 S3 오브젝트 키로 그대로 쓴다.

    이동은 CopyObject + DeleteObject (서버사이드 — 바이트가 core-api 를 오가지
    않는다). 도중 실패하면 복사해 둔 새 키를 지워 되돌린다 — 원본은 삭제를
    **모든 복사가 끝난 뒤**에만 하므로 반쪽 이동이 남지 않는다.

    ⚠ 이 백엔드가 켜져도 pipeline-worker·viz-render 는 아직 로컬 경로만 읽는다 —
    전송·접수는 되지만 파이프라인·미리보기는 미동작이다 (열린 갭, `S3.md §4`).
    """

    def __init__(self, client: S3Client):
        self._client = client

    def put(self, *, key: str, payload: bytes) -> None:
        self._client.put_object(key, payload)

    def put_stream(self, *, key: str, stream: BinaryIO) -> int:
        """**read() 폴백이다 — 진짜 스트리밍이 아니다.**

        SigV4(`kernel/sigv4.py`)가 `x-amz-content-sha256` 에 **본문 전체 해시**를 넣어
        서명하므로 본문을 다 읽기 전에는 요청을 시작할 수 없다(청크 서명·UNSIGNED-PAYLOAD
        는 자작 서명기가 지원하지 않는다). 그래서 여기서 전부 읽어 `put_object` 로 보낸다.
        단일 PUT 상한(5 GiB)을 넘는 본문은 **413** 이다 — 그 크기의 정문은 프리사인드 전송이다.
        """
        size = _stream_size(stream)
        if size is not None and size > S3_SINGLE_PUT_MAX:
            raise errors.payload_too_large(
                f"S3 단일 PUT 상한(5 GiB)을 넘는다 ({size}B) — 프리사인드 전송으로 올릴 것.")
        payload = stream.read()
        if len(payload) > S3_SINGLE_PUT_MAX:
            raise errors.payload_too_large(
                f"S3 단일 PUT 상한(5 GiB)을 넘는다 ({len(payload)}B) — 프리사인드 전송으로 올릴 것.")
        self._client.put_object(key, payload)
        return len(payload)

    def discard(self, *, key: str | None, keep: str | None = None) -> None:
        if not key or key == keep:
            return
        self._client.delete_objects([key])  # DeleteObjects 는 없는 키에도 조용하다

    def relocate(self, *, files: Sequence[Any],
                 new_keys: dict[str, str]) -> None:
        copied: list[str] = []
        moved_src: list[str] = []
        try:
            for f in files:
                new_key = new_keys[f.file_id]
                if not f.storage_key or f.storage_key == new_key:
                    continue
                try:
                    self._client.copy_object(f.storage_key, new_key)
                except S3Error as e:
                    if e.status == 404 or e.code == "NoSuchKey":
                        continue  # 바이트가 이미 없다 — 로컬 구현과 같은 규칙
                    raise
                copied.append(new_key)
                moved_src.append(f.storage_key)
        except S3Error:
            if copied:
                self._client.delete_objects(copied)
            raise
        if moved_src:
            self._client.delete_objects(moved_src)
