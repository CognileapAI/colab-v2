"""업로드 바이트 읽기 어댑터 두 벌 — 로컬 디스크 · S3 (`ports/blobs.py` · `PLAN-SoT §9 〈342〉-㉴`).

로컬 어댑터는 `app/worker.py` 에 있던 `_storage_path`+`_named_view` 의 **이사**다 — 동작이 같다
(이름 붙은 뷰 = 링크, 안 되면 복사 · `basename` 만). S3 어댑터는 키를 **통째로 내려받는다** —
`d5/` 의 감지·파싱이 로컬 경로·랜덤 액세스를 전제하므로 스트림으로 흘려보내지 않는다(`DR-11`).

작업 디렉터리(`COLAB_WORKER_WORKDIR`)는 s3 모드에서 **캐시이지 상태가 아니다**(`〈340〉`) — 처리가
끝나면 `discard` 가 그 업로드 디렉터리를 지운다. 상한은 두지 않는다: 동시 처리 1 이라 그 크기는
업로드 한 건이고, EBS 사이징 규칙은 Ted 판정 항목이다.

표준 라이브러리 + 복제 커널(`kernel/s3.py`)만 쓴다 — geo 스택을 여기서 끌어오지 않는다
(`app/health.py` 가 정적 판정을 위해 이 모듈을 import 한다).
"""
from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import storage_layout

#: `local`(기본) | `s3`. 모르는 값은 기동 거부 — core-api `kernel/config.py::_storage_settings` 와 같은 규칙.
ENV_STORAGE_MODE = "COLAB_WORKER_STORAGE_MODE"
ENV_S3_BUCKET = "COLAB_WORKER_S3_BUCKET"
ENV_S3_REGION = "COLAB_WORKER_S3_REGION"
#: 접수한 바이트가 놓인 자리(로컬 모드). **core-api 의 `COLAB_CORE_UPLOAD_DIR` 과 같은 곳**이어야 한다 —
#: 워커가 파일을 못 열면 감지가 통째로 실패하고, 그 실패는 「형식 인식 실패」로 위장한다.
ENV_UPLOAD_DIR = "COLAB_WORKER_UPLOAD_DIR"
#: 워커가 산출물·이름 붙은 뷰·(s3) 내려받은 바이트를 두는 자리.
ENV_WORKDIR = "COLAB_WORKER_WORKDIR"

STORAGE_MODES = ("local", "s3")


class BlobSizeMismatch(RuntimeError):
    """HeadObject 크기 ≠ 받은 바이트. 반쪽 파일을 「형식 인식 실패」로 위장시키지 않는다."""


def declared_storage_mode(env: Mapping[str, str]) -> str:
    """env 에 **선언된** 모드 — 정적 판정(버킷·자격증명·네트워크를 안 본다). 헬스 본문용."""
    raw = (env.get(ENV_STORAGE_MODE) or "local").strip().lower()
    return raw or "local"


def storage_mode(env: Mapping[str, str]) -> str:
    mode = declared_storage_mode(env)
    if mode not in STORAGE_MODES:
        raise RuntimeError(
            f"{ENV_STORAGE_MODE} 가 모르는 값이다: {mode!r} — {'|'.join(STORAGE_MODES)} 중 하나. "
            "모르는 값을 local 로 접지 않는다"
        )
    return mode


@dataclass(frozen=True)
class BlobSettings:
    mode: str
    upload_dir: Path | None
    workdir: Path
    bucket: str | None = None
    region: str | None = None


def blob_settings(env: Mapping[str, str]) -> BlobSettings:
    """`run_once` 가 DB 에 붙기 전에 부르는 순수 판정. 반쪽 설정은 그 이름을 말하며 거부한다."""
    mode = storage_mode(env)
    if mode == "s3":
        missing = [k for k in (ENV_S3_BUCKET, ENV_S3_REGION, ENV_WORKDIR) if not env.get(k)]
        if missing:
            raise RuntimeError(
                f"{ENV_STORAGE_MODE}=s3 인데 {' · '.join(missing)} 가 없다 — 반쪽 설정으로 돌지 않는다"
            )
        return BlobSettings(mode="s3", upload_dir=None, workdir=Path(env[ENV_WORKDIR]),
                            bucket=env[ENV_S3_BUCKET], region=env[ENV_S3_REGION])
    upload_dir = env.get(ENV_UPLOAD_DIR)
    if not upload_dir:
        # 바이트를 못 여는 워커는 **감지를 못 하면서 「형식 인식 실패」를 낸다** —
        # 없는 것을 있는 척하지 않고 뜨지 않는 쪽을 고른다 (core-api 의 업로드 저장처와 같은 규칙).
        raise RuntimeError(f"{ENV_UPLOAD_DIR} 가 없다 — 접수한 바이트를 못 여는 워커는 안 돈다")
    workdir = Path(env.get(ENV_WORKDIR) or (Path(upload_dir) / "_work"))
    return BlobSettings(mode="local", upload_dir=Path(upload_dir), workdir=workdir)


def _safe_name(file_name: str, fallback: str) -> str:
    return Path(file_name).name or fallback


class LocalUploadBlobs:
    """로컬 디스크 — 바이트는 core-api 소유(같은 볼륨). 이름 붙은 뷰만 만든다."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def materialize(self, *, key: str, dest: Path, file_name: str) -> Path:
        """⚠ **없는 바이트에 여기서 예외를 내지 않는다** — 옛 `_named_view` 와 같은 자리를 지킨다.

        `symlink_to` 는 대상이 없어도 링크를 만든다. 그 「끊어진 링크」를 `process_upload` 가 열다
        실패하면 그 업로드 **한 건만** `upload.failed` 로 닫힌다. 여기서 던지면 그 예외가
        `drive_uploads` 를 뚫고 나가 **워커 루프가 죽고 프로세스가 통째로 내려간다**
        (2026-08-31 컨테이너 실행 시험에서 실제로 그렇게 죽었다 — 바이트가 없는 업로드 한 건 때문에).
        """
        blob = self.root / key
        safe = _safe_name(file_name, blob.name)
        dest.mkdir(parents=True, exist_ok=True)
        view = dest / safe
        if view.exists():
            return view
        try:
            view.symlink_to(blob.resolve())
        except (OSError, NotImplementedError):
            shutil.copyfile(blob, view)
        return view

    def discard(self, upload_id: str) -> None:
        # 로컬 모드의 이름 붙은 뷰는 core-api 볼륨 곁의 `_work` 에 남는다 — 현행 동작 유지(지우지 않는다).
        return None


class S3UploadBlobs:
    """S3 — 키를 통째로 내려받아 `dest/<이름>` 에 놓는다. 작업 디렉터리는 캐시다."""

    def __init__(self, client: Any, workdir: Path) -> None:
        self.client = client
        self.workdir = Path(workdir)

    def materialize(self, *, key: str, dest: Path, file_name: str) -> Path:
        expected, _etag = self.client.head_object(key)
        safe = _safe_name(file_name, Path(key).name)
        dest.mkdir(parents=True, exist_ok=True)
        final = dest / safe
        partial = dest / f".{safe}.partial"
        received = 0
        try:
            with partial.open("wb") as fh:
                for chunk in self.client.get_object_stream(key):
                    fh.write(chunk)
                    received += len(chunk)
            if received != expected:
                raise BlobSizeMismatch(
                    f"{key}: HeadObject 크기 {expected} ≠ 받은 바이트 {received} — 반쪽 파일을 쓰지 않는다"
                )
            os.replace(partial, final)
        finally:
            if partial.exists():
                partial.unlink()
        return final

    def discard(self, upload_id: str) -> None:
        # `rmtree` 에 넣을 경로는 **한 조각**이어야 한다 — 형제·상위 디렉터리를 지우는 길을 두지 않는다.
        if (not upload_id or upload_id in (".", "..") or "/" in upload_id or "\\" in upload_id
                or Path(upload_id).name != upload_id):
            raise ValueError(f"업로드 id 가 한 조각이 아니다: {upload_id!r}")
        target = self.workdir / upload_id
        if target.is_dir():
            shutil.rmtree(target)


def _default_client_factory(*, bucket: str, region: str) -> Any:
    # core 의 `routes/upload_transfers.py::_s3` 와 같은 모양 — 버킷·리전만 여기서, 자격증명은
    # 호출 시점에 `load_credentials`(env→ECS→IMDSv2)가 준다. 액세스 키를 env 에 두지 않는다.
    from .s3 import S3Client

    return S3Client(bucket=bucket, region=region)


def build_blobs(settings: BlobSettings,
                client_factory: Callable[..., Any] | None = None):
    if settings.mode == "s3":
        factory = client_factory or _default_client_factory
        return S3UploadBlobs(factory(bucket=settings.bucket, region=settings.region), settings.workdir)
    assert settings.upload_dir is not None
    return LocalUploadBlobs(settings.upload_dir)


__all__ = [
    "ENV_S3_BUCKET", "ENV_S3_REGION", "ENV_STORAGE_MODE", "ENV_UPLOAD_DIR", "ENV_WORKDIR",
    "BlobSettings", "BlobSizeMismatch", "LocalUploadBlobs", "S3UploadBlobs",
    "blob_settings", "build_blobs", "declared_storage_mode", "storage_mode",
]
