"""업로드 바이트를 **읽는** Port (`PLAN-SoT §9 〈281〉-㉴` V-3).

워커는 접수된 바이트를 어디서 가져오는지 몰라야 한다 — 로컬 모드는 core-api 와 같은 디스크,
s3 모드는 버킷이다. 두 경우 모두 `d5/` 의 감지·파싱은 **로컬 경로**를 전제한다(netCDF4·h5py·pyhdf 와
매직 바이트 try-open 전부 파일 전체·랜덤 액세스). 그래서 이 Port 의 계약은 「키 하나를 `dest` 아래
제 이름으로 놓고 경로를 돌려준다」이고, 스트림으로 흘려보내지 않는다.

`materialize` 가 돌려주는 경로는 `dest / basename(file_name)` 이다 — `basename` 만 쓰므로 경로 탈출이
성립하지 않는다(옛 `app/worker.py::_named_view` 와 같다). `discard` 는 그 업로드의 작업 디렉터리를
치운다 — s3 모드의 작업 디렉터리는 **캐시이지 상태가 아니다**(`〈279〉`). 로컬 모드의 바이트는
core-api 소유라 지우지 않는다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class UploadBlobPort(Protocol):
    def materialize(self, *, key: str, dest: Path, file_name: str) -> Path:
        """저장 키 `key` 의 바이트를 `dest / basename(file_name)` 에 놓고 그 경로를 돌려준다.

        없는 키는 어댑터의 예외(로컬 `FileNotFoundError` · s3 `S3Error`)를 그대로 낸다 — 반쪽 파일을
        남기지 않는다. 크기가 어긋나면 `BlobSizeMismatch`(`kernel/blob_backends.py`).
        """
        ...

    def discard(self, upload_id: str) -> None:
        """이 업로드의 작업 디렉터리를 치운다. 없는 것은 조용히 넘긴다."""
        ...
