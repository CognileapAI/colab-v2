"""dev S3 모드의 지도 타일 회수는 관측 전용이다 (BF-12).

로컬 볼륨용 회수기를 S3 배포에 그대로 붙이면 주체 0을 내고도 루프가 돈 것처럼 보인다.
여기서는 정확한 두 prefix만 읽고, 객체 바이트로 키를 재계산하며, 어떤 설정에서도 S3
삭제를 부르지 않는 경계를 잠근다.
"""
from __future__ import annotations

import hashlib

from colab_viz.app import main
from colab_viz.domains.d7_visualization import tile_liveness, tile_reclaim
from colab_viz.kernel import storage_layout
from colab_viz.kernel.config import Settings
from colab_viz.ports.source import S3SourcePort

TID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
FID = "01BX5ZZKBKACTAV9WEVGEMMVRZ"
TID2 = "01ARZ3NDEKTSV4RRFFQ69G5FBV"
FID2 = "01BX5ZZKBKACTAV9WEVGEMMWRZ"


def _tile_key(payload: bytes) -> str:
    kind = storage_layout.MAP_TILE_CONVERSION_KIND
    return storage_layout.map_tile_content_key(
        sourceDigest=hashlib.sha256(payload).hexdigest(),
        sourceByteSize=len(payload),
        gridDigest=storage_layout.GRID_DIGEST_EMBEDDED,
        conversionKind=kind,
        overviewResampling=storage_layout.MAP_TILE_OVERVIEW_RESAMPLING[kind],
        compression=storage_layout.MAP_TILE_COMPRESSION,
    )


class _ClosingChunks:
    def __init__(self, chunks: list[bytes]):
        self._chunks = iter(chunks)
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._chunks)

    def close(self):
        self.closed = True


class StubS3:
    def __init__(self, objects: dict[str, bytes], *, fail_prefix: str | None = None,
                 mutate_on_get: str | None = None, extra_on_get: str | None = None,
                 truncate_on_get: str | None = None):
        self.objects = dict(objects)
        self.fail_prefix = fail_prefix
        self.mutate_on_get = mutate_on_get
        self.extra_on_get = extra_on_get
        self.truncate_on_get = truncate_on_get
        self.list_calls: list[str] = []
        self.head_calls: list[str] = []
        self.stream_chunk_sizes: list[int] = []
        self.expected_etags: list[tuple[str, str | None]] = []
        self.streams: list[_ClosingChunks] = []
        self.delete_calls: list[list[str]] = []

    def list_objects(self, prefix: str):
        self.list_calls.append(prefix)
        if prefix == "":
            raise AssertionError("버킷 루트를 목록으로 열었다")
        if prefix == self.fail_prefix:
            raise OSError("목록 실패")
        for key in sorted(self.objects):
            if key.startswith(prefix):
                yield key, len(self.objects[key])

    def head_object(self, key: str):
        self.head_calls.append(key)
        payload = self.objects[key]
        return len(payload), f'"version-{hashlib.md5(payload).hexdigest()}"'

    def get_object_stream(self, key: str, *, chunk_size: int = 1 << 20,
                          expected_etag: str | None = None):
        self.stream_chunk_sizes.append(chunk_size)
        if key == self.mutate_on_get:
            self.objects[key] = bytes(reversed(self.objects[key]))
        current_etag = self.head_object(key)[1]
        self.expected_etags.append((key, expected_etag))
        if expected_etag is not None and expected_etag != current_etag:
            raise OSError("If-Match 불일치")
        payload = self.objects[key]
        if key == self.truncate_on_get:
            payload = payload[:-1]
        chunks = [payload[offset:offset + chunk_size]
                  for offset in range(0, len(payload), chunk_size)]
        if key == self.extra_on_get:
            chunks.append(b"too-many-bytes")
        stream = _ClosingChunks(chunks)
        self.streams.append(stream)
        return stream

    def delete_objects(self, keys: list[str]):
        self.delete_calls.append(list(keys))


def _objects() -> tuple[dict[str, bytes], str]:
    payload = b"dev-s3-source-bytes"
    live = _tile_key(payload)
    dead = "tile-" + "f" * 64
    return {
        f"uploads/{TID}/{FID}": payload,
        f"previews/{live}.tif": b"LIVE-COG",
        f"previews/{dead}.tif": b"OLD-COG",
        "previews/render-only.png": b"PNG",
    }, live


def test_s3_관측은_정확한_prefix와_객체_바이트로_생존을_판정한다(tmp_path):
    objects, _live = _objects()
    client = StubS3(objects)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=1024)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is True, result.reason
    assert (result.subjects, result.tiles, result.reachable, result.unreachable) == (1, 2, 1, 1)
    assert client.list_calls == ["uploads/", "previews/"]
    assert client.delete_calls == []
    assert result.applied is False and result.removed == ()


def test_s3_관측은_apply_true여도_삭제하지_않는다(tmp_path):
    objects, _live = _objects()
    client = StubS3(objects)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=1024)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=True)

    assert result.ready is True
    assert result.applied is False and result.removed == ()
    assert client.delete_calls == []
    assert "S3 관측 전용" in result.reason


def test_s3_목록_실패는_고아_0으로_접지_않고_준비_red다(tmp_path):
    objects, _live = _objects()
    client = StubS3(objects, fail_prefix="previews/")
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=1024)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is False
    assert result.unreachable == 0 and result.removed == ()
    assert "OSError" in result.reason
    assert client.delete_calls == []


def test_s3_빈_prefix는_목록을_부르기_전에_거부한다(tmp_path):
    objects, _live = _objects()
    client = StubS3(objects)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=1024)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="",
        previews_prefix="previews", apply=False)

    assert result.ready is False
    assert client.list_calls == []
    assert client.delete_calls == []


def test_s3_관측_streaming은_단일객체가_workdir_상한보다_커도_판정한다(tmp_path):
    objects, _live = _objects()
    client = StubS3(objects)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=4)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is True, result.reason
    assert result.subjects == 1
    assert client.list_calls == ["uploads/", "previews/"]
    assert client.head_calls
    assert client.delete_calls == []


def test_s3_관측은_전체합계가_상한보다_커도_cache를_건드리지_않고_전수_판정한다(tmp_path):
    first = b"first-subject-bytes"
    second = b"second-subject-bytes"
    first_live = _tile_key(first)
    second_live = _tile_key(second)
    dead = "tile-" + "f" * 64
    objects = {
        f"uploads/{TID}/{FID}": first,
        f"uploads/{TID2}/{FID2}": second,
        f"previews/{first_live}.tif": b"FIRST",
        f"previews/{second_live}.tif": b"SECOND",
        f"previews/{dead}.tif": b"OLD",
    }
    workdir = tmp_path / "work"
    sentinel = workdir / "uploads" / "render-in-progress" / "source.bin"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"render-cache-must-survive")
    client = StubS3(objects)
    source = S3SourcePort(client, workdir=workdir, max_bytes=32)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=True)

    assert result.ready is True, result.reason
    assert (result.subjects, result.tiles, result.reachable, result.unreachable) == (2, 3, 2, 1)
    assert client.stream_chunk_sizes and max(client.stream_chunk_sizes) <= 1 << 20
    assert list(workdir.rglob("*")) == [
        workdir / "uploads", workdir / "uploads" / "render-in-progress", sentinel]
    assert sentinel.read_bytes() == b"render-cache-must-survive"
    assert client.delete_calls == []
    assert result.applied is False and result.removed == ()


def test_s3_관측은_head뒤_같은크기_객체교체를_준비_red로_막는다(tmp_path):
    objects, _live = _objects()
    second = b"second-subject-bytes"
    objects[f"uploads/{TID2}/{FID2}"] = second
    objects[f"previews/{_tile_key(second)}.tif"] = b"SECOND"
    body_key = f"uploads/{TID2}/{FID2}"
    client = StubS3(objects, mutate_on_get=body_key)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=1024)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is False
    assert result.rows == () and result.unreachable == 0
    assert "주체 2건" in result.reason and "계산 불가 1건" in result.reason
    assert all(etag for _key, etag in client.expected_etags)
    assert client.delete_calls == []


def test_s3_관측은_초과수신을_즉시_준비_red로_막고_stream을_닫는다(tmp_path):
    objects, _live = _objects()
    body_key = f"uploads/{TID}/{FID}"
    client = StubS3(objects, extra_on_get=body_key)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=1024)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is False
    assert result.rows == () and result.unreachable == 0
    assert client.streams[0].closed is True
    assert client.delete_calls == []


def test_s3_관측은_부족수신도_준비_red로_막고_stream을_닫는다(tmp_path):
    objects, _live = _objects()
    body_key = f"uploads/{TID}/{FID}"
    client = StubS3(objects, truncate_on_get=body_key)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=1024)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is False
    assert result.rows == () and result.unreachable == 0
    assert client.streams[0].closed is True
    assert client.delete_calls == []


def test_s3_streaming_후보키는_기존_materialize_후보키와_같다(tmp_path):
    objects, _live = _objects()
    objects[f"uploads/{TID}/grid/Lat.npy"] = b"latitude-grid"
    objects[f"uploads/{TID}/grid/Lon.npy"] = b"longitude-grid"
    local_client = StubS3(objects)
    local_source = S3SourcePort(
        local_client, workdir=tmp_path / "materialized", max_bytes=1024)
    materialized = local_source.materialize(local_source.resolve(
        dataset_id=TID, upload_id=None, file_ids=None))
    expected = {key for key, _used in tile_liveness.candidate_tile_keys(
        materialized.parts[0].path, grid_dir=materialized.grid_dir)}
    preview_objects = {
        **objects,
        **{f"previews/{key}.tif": b"TILE" for key in expected},
    }
    client = StubS3(preview_objects)
    source = S3SourcePort(client, workdir=tmp_path / "untouched", max_bytes=1)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is True, result.reason
    assert result.reachable == len(expected)
    assert result.unreachable == result.tiles - len(expected)
    assert not source.workdir.exists()
    assert client.delete_calls == []


def test_app_조립은_s3_s3에_관측_job을_붙인다(tmp_path):
    objects, _live = _objects()
    client = StubS3(objects)
    settings = Settings(
        source_root=tmp_path / "unused", service_token="token",
        tile_signing_secret="secret", execution="inline",
        preview_dir=tmp_path / "preview-cache", source_mode="s3",
        s3_bucket="bucket", s3_region="ap-northeast-2",
        workdir=tmp_path / "work", work_max_bytes=1024,
        preview_sink="s3", preview_s3_prefix="previews",
        trigger_spool=tmp_path / "events", tile_reclaim_apply=True,
    )
    source = S3SourcePort(client, workdir=settings.workdir, max_bytes=1024)

    job = main._build_reclaim_job(settings=settings, client=client, source=source)

    assert isinstance(job, tile_reclaim.S3ReclaimJob)
    assert job.apply_requested is True
