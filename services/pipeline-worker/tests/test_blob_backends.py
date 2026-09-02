"""업로드 바이트 읽기 어댑터 두 벌 (`kernel/blob_backends.py` · `PLAN-SoT §9 〈281〉-㉴` V-3).

로컬 어댑터는 `app/worker.py` 에 있던 `_storage_path`+`_named_view` 의 **이사**라 동작 등가를,
S3 어댑터는 스텁 클라이언트로 호출 형태(내려받기 → 임시파일 → rename · 크기 대조 · 처리 뒤 삭제)를
못 박는다. 실제 S3 왕복은 `sessions/ID-evidence-worker.txt` 의 실호출 몫이다.

geo 스택·DB 불필요 — `kernel`·`app.health` 만 import 한다. `app.worker` 는 numpy 를 끌어오므로
여기서 import 하지 않는다(그쪽은 `test_worker_blob_drive.py`).
"""
from __future__ import annotations

import json
import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from colab_pipeline.app import health
from colab_pipeline.kernel import storage_layout
from colab_pipeline.kernel.blob_backends import (
    ENV_S3_BUCKET,
    ENV_S3_REGION,
    ENV_STORAGE_MODE,
    ENV_UPLOAD_DIR,
    ENV_WORKDIR,
    BlobSizeMismatch,
    LocalUploadBlobs,
    S3UploadBlobs,
    blob_settings,
    build_blobs,
    declared_storage_mode,
    storage_mode,
)
from colab_pipeline.kernel.s3 import S3Error

_UPL = "01JQ0000000000000000000003"
_F1 = "01JQ00000000000000000000F1"
_G1 = "01JQ00000000000000000000G1"


# ── ① 로컬 — 기존 `_storage_path`+`_named_view` 와 등가 ────────────────────────

def _old_named_view(blob: Path, holder: Path, file_name: str) -> Path:
    """`app/worker.py::_named_view` 의 **이사 전 원문** — 오라클은 옮긴 코드가 아니라 옛 동작이다."""
    safe = Path(file_name).name or blob.name
    holder.mkdir(parents=True, exist_ok=True)
    view = holder / safe
    if view.exists():
        return view
    try:
        view.symlink_to(blob.resolve())
    except (OSError, NotImplementedError):
        import shutil
        shutil.copyfile(blob, view)
    return view


def _put_local(root: Path, *, kind: str, file_id: str, name: str, payload: bytes) -> str:
    key = storage_layout.storage_key(_UPL, file_id=file_id, kind=kind, file_name=name)
    blob = root / key
    blob.parent.mkdir(parents=True, exist_ok=True)
    blob.write_bytes(payload)
    return key


def test_local_body_is_the_same_path_and_bytes_as_the_old_named_view(tmp_path: Path) -> None:
    root, work = tmp_path / "store", tmp_path / "work"
    key = _put_local(root, kind=storage_layout.BODY_KIND, file_id=_F1, name="kwra.tif",
                     payload=b"II*\x00body")
    dest = work / _UPL / "inputs" / _F1
    got = LocalUploadBlobs(root).materialize(key=key, dest=dest, file_name="kwra.tif")

    expected = _old_named_view(
        storage_layout.storage_path(root, _UPL, file_id=_F1, kind=storage_layout.BODY_KIND,
                                    file_name="kwra.tif"),
        tmp_path / "oracle" / _UPL / "inputs" / _F1, "kwra.tif")
    assert got == dest / "kwra.tif"                       # 본체는 inputs/<fileId>/<이름>
    assert got.read_bytes() == expected.read_bytes() == b"II*\x00body"
    # 이름 붙은 뷰는 저장소의 바이트를 **그대로** 본다 — 링크거나 같은 바이트의 복사다
    assert got.resolve() == (root / key).resolve() or got.read_bytes() == (root / key).read_bytes()


def test_local_grid_keeps_its_name_in_one_grid_dir(tmp_path: Path) -> None:
    """격자는 `grid/<이름>` 그대로 — 축 판별 사다리가 `.npy` 접미사·파일명을 읽는다."""
    root, work = tmp_path / "store", tmp_path / "work"
    key = _put_local(root, kind=storage_layout.GRID_KIND, file_id=_G1, name="Lon_HSR.npy",
                     payload=b"\x93NUMPY-fake")
    dest = work / _UPL / storage_layout.GRID_DIRNAME
    got = LocalUploadBlobs(root).materialize(key=key, dest=dest, file_name="Lon_HSR.npy")
    assert got == dest / "Lon_HSR.npy"
    assert got.read_bytes() == (root / key).read_bytes()


def test_local_strips_the_file_name_to_its_basename(tmp_path: Path) -> None:
    """경로 탈출이 성립하지 않는다 — `basename` 만 쓴다(옛 `_named_view` 와 같다)."""
    root, work = tmp_path / "store", tmp_path / "work"
    key = _put_local(root, kind=storage_layout.BODY_KIND, file_id=_F1, name="a.nc", payload=b"x")
    dest = work / _UPL / "inputs" / _F1
    got = LocalUploadBlobs(root).materialize(key=key, dest=dest, file_name="../../evil.nc")
    assert got == dest / "evil.nc"


def test_local_discard_is_a_no_op_the_bytes_belong_to_core_api(tmp_path: Path) -> None:
    root, work = tmp_path / "store", tmp_path / "work"
    key = _put_local(root, kind=storage_layout.BODY_KIND, file_id=_F1, name="a.nc", payload=b"x")
    view = LocalUploadBlobs(root).materialize(key=key, dest=work / _UPL / "inputs" / _F1,
                                             file_name="a.nc")
    LocalUploadBlobs(root).discard(_UPL)
    assert (root / key).exists() and view.exists()


# ── ② S3 — 스텁 클라이언트 ───────────────────────────────────────────────────

class _StubS3:
    """`get_object_stream` 이 청크 iterator, `head_object` 가 (크기, etag). 실물은 `kernel/s3.S3Client`."""

    def __init__(self, objects: dict[str, bytes], *, head_size: dict[str, int] | None = None,
                 chunk: int = 4) -> None:
        self.objects = objects
        self.head_size = head_size or {}
        self.chunk = chunk
        self.calls: list[tuple[str, str]] = []

    def head_object(self, key: str) -> tuple[int, str]:
        self.calls.append(("head", key))
        if key not in self.objects:
            raise S3Error(404, "NoSuchKey", key)
        return self.head_size.get(key, len(self.objects[key])), '"etag"'

    def get_object_stream(self, key: str, *, chunk_size: int = 0):
        self.calls.append(("get", key))
        if key not in self.objects:
            raise S3Error(404, "NoSuchKey", key)
        body = self.objects[key]

        def chunks():
            for i in range(0, len(body), self.chunk):
                yield body[i:i + self.chunk]
        return chunks()


def _s3_keys() -> tuple[str, str]:
    body = storage_layout.storage_key(_UPL, file_id=_F1, kind=storage_layout.BODY_KIND,
                                      file_name="kwra.tif")
    grid = storage_layout.storage_key(_UPL, file_id=_G1, kind=storage_layout.GRID_KIND,
                                      file_name="Lon_HSR.npy")
    return body, grid


def test_s3_materialize_downloads_the_same_bytes_under_dest(tmp_path: Path) -> None:
    body_key, grid_key = _s3_keys()
    payload = bytes(range(256)) * 3 + b"tail"
    client = _StubS3({body_key: payload, grid_key: b"\x93NUMPY"})
    work = tmp_path / "work"
    blobs = S3UploadBlobs(client, work)

    got = blobs.materialize(key=body_key, dest=work / _UPL / "inputs" / _F1, file_name="kwra.tif")
    assert got == work / _UPL / "inputs" / _F1 / "kwra.tif"
    assert got.read_bytes() == payload
    grid = blobs.materialize(key=grid_key, dest=work / _UPL / storage_layout.GRID_DIRNAME,
                             file_name="Lon_HSR.npy")
    assert grid == work / _UPL / storage_layout.GRID_DIRNAME / "Lon_HSR.npy"
    assert grid.read_bytes() == b"\x93NUMPY"
    # 임시파일이 남지 않는다 — 작업 디렉터리는 캐시이지 상태가 아니다
    assert [p.name for p in got.parent.iterdir()] == ["kwra.tif"]
    assert ("head", body_key) in client.calls and ("get", body_key) in client.calls


def test_s3_materialize_refuses_a_size_mismatch_and_leaves_no_file(tmp_path: Path) -> None:
    """HeadObject 크기 ≠ 받은 바이트 — 반쪽 파일을 「형식 인식 실패」로 위장시키지 않는다."""
    body_key, _ = _s3_keys()
    client = _StubS3({body_key: b"0123456789"}, head_size={body_key: 11})
    work = tmp_path / "work"
    dest = work / _UPL / "inputs" / _F1
    with pytest.raises(BlobSizeMismatch) as e:
        S3UploadBlobs(client, work).materialize(key=body_key, dest=dest, file_name="kwra.tif")
    assert "11" in str(e.value) and "10" in str(e.value)
    assert not (dest / "kwra.tif").exists()
    assert not list(dest.glob("*partial*")), "임시파일이 남았다"


def test_s3_materialize_propagates_a_missing_key_without_a_file(tmp_path: Path) -> None:
    body_key, _ = _s3_keys()
    work = tmp_path / "work"
    dest = work / _UPL / "inputs" / _F1
    with pytest.raises(S3Error):
        S3UploadBlobs(_StubS3({}), work).materialize(key=body_key, dest=dest, file_name="kwra.tif")
    assert not (dest / "kwra.tif").exists()


def test_s3_materialize_uses_the_basename_only(tmp_path: Path) -> None:
    body_key, _ = _s3_keys()
    work = tmp_path / "work"
    dest = work / _UPL / "inputs" / _F1
    got = S3UploadBlobs(_StubS3({body_key: b"x"}), work).materialize(
        key=body_key, dest=dest, file_name="../../evil.nc")
    assert got == dest / "evil.nc"


# ── ③ discard — `workdir/<uploadId>` 만 지운다 ───────────────────────────────

def test_s3_discard_removes_only_that_upload_dir(tmp_path: Path) -> None:
    work = tmp_path / "work"
    mine = work / _UPL / "inputs" / _F1
    sibling = work / "01JQ0000000000000000000004" / "inputs" / _F1
    for d in (mine, sibling):
        d.mkdir(parents=True)
        (d / "a.nc").write_bytes(b"x")
    (work / "unrelated.txt").write_text("keep", encoding="utf-8")

    S3UploadBlobs(_StubS3({}), work).discard(_UPL)

    assert not (work / _UPL).exists()
    assert (sibling / "a.nc").exists() and (work / "unrelated.txt").exists()


def test_s3_discard_is_quiet_when_nothing_is_there(tmp_path: Path) -> None:
    S3UploadBlobs(_StubS3({}), tmp_path / "work").discard(_UPL)   # 없는 것은 조용히


@pytest.mark.parametrize("bad", ["", ".", "..", "../x", "a/b", "/abs"])
def test_s3_discard_refuses_an_upload_id_that_is_not_one_segment(tmp_path: Path, bad: str) -> None:
    """`rmtree` 에 넣을 경로는 **한 조각**이어야 한다 — 형제·상위 디렉터리를 지우는 길을 두지 않는다."""
    work = tmp_path / "work"
    (work / "keep").mkdir(parents=True)
    with pytest.raises(ValueError):
        S3UploadBlobs(_StubS3({}), work).discard(bad)
    assert (work / "keep").exists()


# ── ④ 환경 판정 — `run_once` 가 DB 에 붙기 전에 부르는 순수 함수 ─────────────

def _env(**kw: str) -> dict[str, str]:
    return {k: v for k, v in kw.items()}


def test_storage_mode_defaults_to_local_and_normalizes() -> None:
    assert storage_mode({}) == "local"
    assert storage_mode({ENV_STORAGE_MODE: " S3 "}) == "s3"


def test_unknown_storage_mode_is_refused_not_folded_into_local() -> None:
    with pytest.raises(RuntimeError) as e:
        storage_mode({ENV_STORAGE_MODE: "minio"})
    assert ENV_STORAGE_MODE in str(e.value) and "minio" in str(e.value)
    with pytest.raises(RuntimeError):
        blob_settings({ENV_STORAGE_MODE: "minio", ENV_UPLOAD_DIR: "/x"})


def test_s3_mode_requires_bucket_region_and_workdir(tmp_path: Path) -> None:
    base = {ENV_STORAGE_MODE: "s3", ENV_S3_BUCKET: "b", ENV_S3_REGION: "ap-northeast-2",
            ENV_WORKDIR: str(tmp_path / "w")}
    for missing in (ENV_S3_BUCKET, ENV_S3_REGION, ENV_WORKDIR):
        env = {k: v for k, v in base.items() if k != missing}
        with pytest.raises(RuntimeError) as e:
            blob_settings(env)
        assert missing in str(e.value), f"{missing} 이 빠졌는데 그 이름을 말하지 않는다"


def test_s3_mode_does_not_need_an_upload_dir(tmp_path: Path) -> None:
    """s3 모드에서 `COLAB_WORKER_UPLOAD_DIR` 부재는 **정상**이다 — 바이트는 버킷에 있다."""
    s = blob_settings({ENV_STORAGE_MODE: "s3", ENV_S3_BUCKET: "b", ENV_S3_REGION: "r",
                       ENV_WORKDIR: str(tmp_path / "w")})
    assert (s.mode, s.bucket, s.region, s.upload_dir, s.workdir) == (
        "s3", "b", "r", None, tmp_path / "w")


def test_local_mode_keeps_requiring_the_upload_dir(tmp_path: Path) -> None:
    """현행 유지 — 바이트를 못 여는 워커는 「형식 인식 실패」를 내면서 돈다. 뜨지 않는 쪽을 고른다."""
    with pytest.raises(RuntimeError) as e:
        blob_settings({})
    assert ENV_UPLOAD_DIR in str(e.value)
    s = blob_settings({ENV_UPLOAD_DIR: str(tmp_path / "u")})
    assert (s.mode, s.upload_dir, s.workdir) == ("local", tmp_path / "u", tmp_path / "u" / "_work")
    s2 = blob_settings({ENV_UPLOAD_DIR: str(tmp_path / "u"), ENV_WORKDIR: str(tmp_path / "w")})
    assert s2.workdir == tmp_path / "w"


def test_build_blobs_picks_the_adapter_by_mode(tmp_path: Path) -> None:
    local = build_blobs(blob_settings({ENV_UPLOAD_DIR: str(tmp_path / "u")}))
    assert isinstance(local, LocalUploadBlobs)

    made: list[dict] = []

    def _factory(**kw):
        made.append(kw)
        return _StubS3({})

    s3 = build_blobs(blob_settings({ENV_STORAGE_MODE: "s3", ENV_S3_BUCKET: "b",
                                    ENV_S3_REGION: "r", ENV_WORKDIR: str(tmp_path / "w")}),
                     client_factory=_factory)
    assert isinstance(s3, S3UploadBlobs)
    # core 의 `routes/upload_transfers.py::_s3` 와 같은 모양 — 버킷·리전만, 자격증명은 호출 시점(`load_credentials`)
    assert made == [{"bucket": "b", "region": "r"}]


# ── ⑤ healthz 본문 — `storageMode` (deploy_doctor 가 읽는 키 이름) ───────────

@pytest.fixture()
def base_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), health._Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def _healthz(base_url: str) -> dict:
    with urllib.request.urlopen(f"{base_url}{health.PATH}") as response:
        assert response.status == 200
        return json.loads(response.read().decode("utf-8"))


def test_healthz_reports_storage_mode_local_by_default(base_url, monkeypatch) -> None:
    monkeypatch.delenv(ENV_STORAGE_MODE, raising=False)
    body = _healthz(base_url)
    assert body["storageMode"] == "local"
    assert body["implemented"] is True and body["unit"] == "pipeline-worker"


def test_healthz_reports_storage_mode_s3_from_env_without_touching_the_network(base_url,
                                                                              monkeypatch) -> None:
    monkeypatch.setenv(ENV_STORAGE_MODE, "s3")
    monkeypatch.delenv(ENV_S3_BUCKET, raising=False)      # 정적 판정 — 버킷·자격증명을 안 본다
    assert _healthz(base_url)["storageMode"] == "s3"
    assert declared_storage_mode(os.environ) == "s3"


# ── ⑥ 없는 바이트 — 워커를 죽이지 않는다 (2026-08-31 컨테이너 실행 시험이 잡은 회귀) ──────

def test_local_materialize_does_not_raise_when_the_blob_is_missing(tmp_path: Path) -> None:
    """옛 `_named_view` 와 같은 자리 — 끊어진 링크를 만들고, 실패는 `process_upload` 가 한 건으로 닫는다.

    여기서 던지면 예외가 `drive_uploads` 를 뚫고 `serve()` 까지 올라가 **프로세스가 죽는다.**
    실제로 그렇게 죽었다(로컬 PG 에 바이트 없는 업로드 한 건이 남아 있었다).
    """
    root, work = tmp_path / "store", tmp_path / "work"
    key = storage_layout.storage_key(_UPL, file_id=_F1, kind=storage_layout.BODY_KIND,
                                     file_name="gone.nc")
    dest = work / _UPL / "inputs" / _F1
    got = LocalUploadBlobs(root).materialize(key=key, dest=dest, file_name="gone.nc")
    assert got == dest / "gone.nc"
    assert not got.exists(), "대상이 없으므로 끊어진 링크다 — 열면 그때 실패한다"


def test_drive_uploads_skips_an_upload_whose_bytes_are_gone(tmp_path: Path) -> None:
    """한 건의 바이트 사고가 **나머지 업로드와 워커 프로세스**를 멈추게 하지 않는다.

    `app.worker` 는 geo 스택을 끌어오므로 **의존이 선 곳에서만** 돈다(이미지 안 · 실 venv).
    건너뛰는 것을 통과로 세지 않으려고 이유를 남긴다 — CI·컨테이너에서는 실제로 돈다.
    """
    pytest.importorskip("numpy", reason="geo 스택이 없는 환경 — 이 시험은 이미지 안에서 돈다")
    from colab_pipeline.app import worker as W

    class _Blobs:
        def __init__(self): self.discarded = []
        def materialize(self, *, key, dest, file_name):
            if "BAD" in key:
                raise FileNotFoundError(key)
            dest.mkdir(parents=True, exist_ok=True)
            p = dest / file_name
            p.write_bytes(b"x")
            return p
        def discard(self, upload_id): self.discarded.append(upload_id)

    bad, good = "01JQ000000000000000000BAD1", "01JQ00000000000000000GOOD1"

    class _Ledger:
        def pending_uploads(self, *, limit):
            return [{"id": bad, "lab_id": "L", "uploader_account_id": "A"},
                    {"id": good, "lab_id": "L", "uploader_account_id": "A"}]
        def accepted_files(self, upload_id):
            return [{"fileId": "01JQ00000000000000000000F1", "kind": storage_layout.BODY_KIND,
                     "fileName": "a.nc"}]

    class _Service:
        def __init__(self): self.seen = []
        def process_upload(self, work, *, stage1): self.seen.append(work.upload_id)

    blobs, service = _Blobs(), _Service()
    done = W.drive_uploads(_Ledger(), workdir=tmp_path / "w", blobs=blobs, service=service)

    assert done == [good], "나쁜 건은 건너뛰고 좋은 건은 처리한다"
    assert service.seen == [good]
    assert bad in blobs.discarded, "건너뛴 건의 작업 디렉터리도 치운다"
