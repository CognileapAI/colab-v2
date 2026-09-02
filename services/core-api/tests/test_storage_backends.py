"""오라클 — 저장 백엔드 두 벌 (`kernel/storage_backends.py` · `〈276〉`).

로컬 백엔드는 기존 라우트 헬퍼의 이사라 동작 등가를, S3 백엔드는 가짜 전송으로
호출 형태(복사 후 삭제 · 원본 부재 건너뜀 · 실패 시 되돌림)를 못 박는다.
실제 S3 왕복은 `ops/s3_smoke.py` 몫이다.
"""
from __future__ import annotations

import dataclasses

import pytest

from colab_core.kernel.config import ENV_S3_BUCKET, ENV_S3_REGION, ENV_STORAGE_MODE, _storage_settings
from colab_core.kernel.s3 import S3Client
from colab_core.kernel.storage_backends import LocalFilesystemStorage, S3UploadStorage


@dataclasses.dataclass(frozen=True)
class _Row:
    file_id: str
    storage_key: str | None
    kind: str = "본체"
    file_name: str = "a.nc"


# ── 로컬 ────────────────────────────────────────────────────────────────────

def test_local_put_discard_roundtrip(tmp_path) -> None:
    st = LocalFilesystemStorage(tmp_path)
    st.put(key="uploads/U1/F1", payload=b"abc")
    assert (tmp_path / "uploads/U1/F1").read_bytes() == b"abc"
    st.discard(key="uploads/U1/F1")
    assert not (tmp_path / "uploads/U1/F1").exists()
    st.discard(key="uploads/U1/F1")  # 없는 것은 조용히 넘어간다


def test_local_relocate_moves_and_prunes(tmp_path) -> None:
    st = LocalFilesystemStorage(tmp_path)
    st.put(key="uploads/U1/F1", payload=b"abc")
    st.relocate(files=[_Row("F1", "uploads/U1/F1")], new_keys={"F1": "uploads/D1/F1"})
    assert (tmp_path / "uploads/D1/F1").read_bytes() == b"abc"
    assert not (tmp_path / "uploads/U1").exists()  # 빈 업로드 자리는 치운다


def test_local_relocate_skips_missing_source(tmp_path) -> None:
    st = LocalFilesystemStorage(tmp_path)
    st.relocate(files=[_Row("F1", "uploads/U1/F1")], new_keys={"F1": "uploads/D1/F1"})
    assert not (tmp_path / "uploads/D1/F1").exists()


# ── S3 (가짜 전송) ──────────────────────────────────────────────────────────

def _fake(responses):
    """(method, url) 를 기록하고 미리 정한 응답을 차례로 돌려주는 전송."""
    calls: list[tuple[str, str, dict[str, str], bytes]] = []

    def transport(method, url, headers, payload, timeout):
        calls.append((method, url, headers, payload))
        status, resp_headers, body = responses.pop(0)
        return status, resp_headers, body

    return calls, transport


def _client(responses) -> tuple[list, S3Client]:
    from colab_core.kernel.sigv4 import Credentials
    calls, transport = _fake(responses)
    return calls, S3Client(bucket="b", region="ap-northeast-2",
                           creds=Credentials(access_key="AK", secret_key="SK"),
                           transport=transport, backoff_base=0.0)


_COPY_OK = (200, {}, b"<CopyObjectResult><ETag>\"e\"</ETag></CopyObjectResult>")
_DELETE_OK = (200, {}, b"<DeleteResult/>")
_PUT_OK = (200, {"ETag": '"e"'}, b"")


def test_s3_put_uses_single_put_with_content_type() -> None:
    calls, client = _client([_PUT_OK])
    S3UploadStorage(client).put(key="uploads/U1/F1", payload=b"abc")
    method, url, headers, payload = calls[0]
    assert method == "PUT" and url.endswith("/uploads/U1/F1") and payload == b"abc"
    assert headers.get("content-type") == "application/octet-stream"


def test_s3_relocate_copies_then_deletes_sources() -> None:
    calls, client = _client([_COPY_OK, _DELETE_OK])
    S3UploadStorage(client).relocate(
        files=[_Row("F1", "uploads/U1/F1")], new_keys={"F1": "uploads/D1/F1"})
    assert [c[0] for c in calls] == ["PUT", "POST"]          # 복사 → 일괄 삭제
    assert calls[0][2].get("x-amz-copy-source") == "/b/uploads/U1/F1"
    assert b"uploads/U1/F1" in calls[1][3]                    # 삭제 본문에 원본 키


def test_s3_relocate_skips_missing_source() -> None:
    missing = (404, {}, b"<Error><Code>NoSuchKey</Code><Message>x</Message></Error>")
    calls, client = _client([missing])
    S3UploadStorage(client).relocate(
        files=[_Row("F1", "uploads/U1/F1")], new_keys={"F1": "uploads/D1/F1"})
    assert [c[0] for c in calls] == ["PUT"]                   # 삭제까지 가지 않는다


def test_s3_relocate_rolls_back_copies_on_failure() -> None:
    boom = (500, {}, b"<Error><Code>InternalError</Code><Message>x</Message></Error>")
    # 파일 2건: 첫 복사 성공, 둘째 복사는 재시도 끝에 실패 → 복사해 둔 첫 키를 지운다
    calls, client = _client([_COPY_OK, boom, boom, boom, boom, _DELETE_OK])
    with pytest.raises(Exception):
        S3UploadStorage(client).relocate(
            files=[_Row("F1", "uploads/U1/F1"), _Row("F2", "uploads/U1/F2")],
            new_keys={"F1": "uploads/D1/F1", "F2": "uploads/D1/F2"})
    assert calls[-1][0] == "POST" and b"uploads/D1/F1" in calls[-1][3]  # 되돌림 삭제


# ── 설정 스위치 ─────────────────────────────────────────────────────────────

def test_storage_mode_unknown_value_dies(monkeypatch) -> None:
    monkeypatch.setenv(ENV_STORAGE_MODE, "minio")
    with pytest.raises(RuntimeError, match="모르는 값"):
        _storage_settings()


def test_storage_mode_s3_requires_bucket_and_region(monkeypatch) -> None:
    monkeypatch.setenv(ENV_STORAGE_MODE, "s3")
    monkeypatch.delenv(ENV_S3_BUCKET, raising=False)
    monkeypatch.delenv(ENV_S3_REGION, raising=False)
    with pytest.raises(RuntimeError, match="반쪽 설정"):
        _storage_settings()


def test_storage_mode_defaults_to_local(monkeypatch) -> None:
    monkeypatch.delenv(ENV_STORAGE_MODE, raising=False)
    mode, _bucket, _region = _storage_settings()
    assert mode == "local"


# ── put_stream (`〈278〉` — 업로드 본문을 통째로 메모리에 올리지 않는다) ──────

def test_local_put_stream_copies_in_chunks_and_returns_the_size(tmp_path, monkeypatch) -> None:
    """청크 4 바이트로 10 바이트를 옮긴다 — 한 번의 read 로 다 읽는 구현이면 청크 크기가 뜻이 없다."""
    import io

    from colab_core.kernel import storage_backends
    monkeypatch.setattr(storage_backends, "STREAM_CHUNK", 4)

    class Counting(io.BytesIO):
        reads: list[int] = []

        def read(self, n=-1):  # noqa: D401
            self.reads.append(n)
            return super().read(n)

    src = Counting(b"0123456789")
    st = LocalFilesystemStorage(tmp_path)
    assert st.put_stream(key="uploads/U1/F1", stream=src) == 10
    assert (tmp_path / "uploads/U1/F1").read_bytes() == b"0123456789"
    assert all(n == 4 for n in src.reads), src.reads
    assert len(src.reads) >= 3


def test_local_put_stream_overwrites(tmp_path) -> None:
    import io
    st = LocalFilesystemStorage(tmp_path)
    st.put(key="uploads/U1/F1", payload=b"old-old-old")
    assert st.put_stream(key="uploads/U1/F1", stream=io.BytesIO(b"new")) == 3
    assert (tmp_path / "uploads/U1/F1").read_bytes() == b"new"


def test_s3_put_stream_is_a_read_fallback_that_sends_one_put() -> None:
    """SigV4 가 본문 전체 해시를 서명에 넣으므로 S3 쪽은 다 읽어 단일 PUT 이다 — 그 사실을 못 박는다."""
    import io
    calls, client = _client([_PUT_OK])
    n = S3UploadStorage(client).put_stream(key="uploads/U1/F1", stream=io.BytesIO(b"abc"))
    assert n == 3
    method, url, headers, payload = calls[0]
    assert method == "PUT" and url.endswith("/uploads/U1/F1") and payload == b"abc"
    assert headers.get("content-type") == "application/octet-stream"
    assert len(calls) == 1


@pytest.mark.parametrize("seekable", [True, False])
def test_s3_put_stream_over_the_single_put_limit_is_413_before_any_request(
        monkeypatch, seekable) -> None:
    """5 GiB 상한 — 탐색 가능하면 읽기 전에 재고, 아니면 읽은 뒤 잰다. 어느 쪽도 S3 에 닿지 않는다."""
    import io

    from colab_core.kernel import errors, storage_backends
    monkeypatch.setattr(storage_backends, "S3_SINGLE_PUT_MAX", 2)

    class NotSeekable(io.BytesIO):
        def seekable(self):
            return False

    stream = io.BytesIO(b"abc") if seekable else NotSeekable(b"abc")
    calls, client = _client([])
    with pytest.raises(errors.ApiError) as exc:
        S3UploadStorage(client).put_stream(key="uploads/U1/F1", stream=stream)
    assert exc.value.status_code == 413
    assert calls == []


# ── 다운로드 (`〈278〉-(다)`) — `open` · `presign_get` ─────────────────────────

def test_local_open_streams_in_chunks_and_a_missing_key_is_file_not_found(tmp_path, monkeypatch) -> None:
    """읽기도 청크다 — 한 번에 다 읽는 구현이면 청크 크기가 뜻이 없다. 없는 키는 **열 때** 예외다
    (스트림을 시작한 뒤가 아니라) — 라우트가 200 헤더를 보내기 전에 404 를 낼 수 있어야 한다."""
    from colab_core.kernel import storage_backends
    monkeypatch.setattr(storage_backends, "READ_CHUNK", 4)
    st = LocalFilesystemStorage(tmp_path)
    st.put(key="uploads/D1/F1", payload=b"0123456789")
    chunks = list(st.open(key="uploads/D1/F1"))
    assert b"".join(chunks) == b"0123456789"
    assert [len(c) for c in chunks] == [4, 4, 2]
    with pytest.raises(FileNotFoundError):
        st.open(key="uploads/D1/none")


def test_local_presign_get_is_none_because_bytes_go_through_core(tmp_path) -> None:
    import datetime as dt
    st = LocalFilesystemStorage(tmp_path)
    assert st.presign_get(key="uploads/D1/F1", file_name="a.nc", expires_seconds=600,
                          now=dt.datetime.now(dt.timezone.utc)) is None


def _stream_fake(responses):
    """스트림 전송 대역 — (status, headers, body) 를 차례로. 2xx 본문은 읽기 객체로 감싼다."""
    import io
    calls: list[tuple[str, str, dict[str, str]]] = []

    def transport(method, url, headers, timeout):
        calls.append((method, url, headers))
        status, resp_headers, body = responses.pop(0)
        return status, resp_headers, (io.BytesIO(body) if status < 400 else body)

    return calls, transport


def _stream_client(responses) -> tuple[list, S3Client]:
    from colab_core.kernel.sigv4 import Credentials
    calls, transport = _stream_fake(responses)
    return calls, S3Client(bucket="b", region="ap-northeast-2",
                           creds=Credentials(access_key="AK", secret_key="SK"),
                           stream_transport=transport, backoff_base=0.0)


def test_s3_open_is_a_get_object_stream() -> None:
    calls, client = _stream_client([(200, {"Content-Length": "5"}, b"hello")])
    out = b"".join(S3UploadStorage(client).open(key="uploads/D1/F1"))
    assert out == b"hello"
    method, url, headers = calls[0]
    assert method == "GET" and url.endswith("/uploads/D1/F1")
    assert "Authorization" in headers               # 헤더 서명 — 본문 없는 GET


def test_s3_open_of_a_missing_key_is_file_not_found_at_open_time() -> None:
    missing = (404, {}, b"<Error><Code>NoSuchKey</Code><Message>x</Message></Error>")
    _calls, client = _stream_client([missing])
    with pytest.raises(FileNotFoundError):
        S3UploadStorage(client).open(key="uploads/D1/none")


def test_s3_presign_get_carries_the_disposition_and_the_ttl() -> None:
    """저장 이름은 프리사인드 URL 의 `response-content-disposition` 에 실린다 — 브라우저가
    S3 에서 직접 받아도 `DownloadTicket.fileName` 으로 저장된다."""
    import datetime as dt
    import urllib.parse
    _calls, client = _stream_client([])
    now = dt.datetime(2026, 8, 29, 12, 0, tzinfo=dt.timezone.utc)
    got = S3UploadStorage(client).presign_get(key="uploads/D1/F1", file_name="강우 2026.nc",
                                             expires_seconds=600, now=now)
    assert got is not None
    assert got.url.startswith("https://b.s3.ap-northeast-2.amazonaws.com/uploads/D1/F1?")
    assert got.expires_at == now + dt.timedelta(seconds=600)
    query = dict(urllib.parse.parse_qsl(got.url.split("?", 1)[1]))
    assert query["X-Amz-Expires"] == "600"
    assert query["X-Amz-Signature"]
    assert query["response-content-disposition"] == \
        "attachment; filename*=UTF-8''" + urllib.parse.quote("강우 2026.nc", safe="")
