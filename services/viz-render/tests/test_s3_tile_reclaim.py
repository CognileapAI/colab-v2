"""dev S3 모드의 지도 타일 회수는 관측 전용이다 (BF-12).

로컬 볼륨용 회수기를 S3 배포에 그대로 붙이면 주체 0을 내고도 루프가 돈 것처럼 보인다.
여기서는 정확한 두 prefix만 읽고, 객체 바이트로 키를 재계산하며, 어떤 설정에서도 S3
삭제를 부르지 않는 경계를 잠근다.
"""
from __future__ import annotations

import hashlib

from colab_viz.app import main
from colab_viz.domains.d7_visualization import tile_reclaim
from colab_viz.kernel import storage_layout
from colab_viz.kernel.config import Settings
from colab_viz.ports.source import S3SourcePort

TID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
FID = "01BX5ZZKBKACTAV9WEVGEMMVRZ"


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


class StubS3:
    def __init__(self, objects: dict[str, bytes], *, fail_prefix: str | None = None):
        self.objects = dict(objects)
        self.fail_prefix = fail_prefix
        self.list_calls: list[str] = []
        self.head_calls: list[str] = []
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
        # ETag는 의도적으로 내용과 무관하다. 생존 키 재료로 쓰면 시험이 red다.
        self.head_calls.append(key)
        return len(self.objects[key]), '"not-a-content-digest"'

    def get_object_stream(self, key: str, *, chunk_size: int = 1 << 20):
        return iter((self.objects[key],))

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
    assert client.list_calls == ["uploads/", f"uploads/{TID}/", "previews/"]
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


def test_s3_관측_총량이_workdir_상한을_넘으면_다운로드_전에_준비_red다(tmp_path):
    objects, _live = _objects()
    client = StubS3(objects)
    source = S3SourcePort(client, workdir=tmp_path / "work", max_bytes=4)

    result = tile_reclaim.run_s3_observation(
        client=client, source=source, uploads_prefix="uploads",
        previews_prefix="previews", apply=False)

    assert result.ready is False
    assert client.list_calls == ["uploads/"]
    assert client.head_calls == []
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
