"""미리보기 출력 싱크 — 산출물을 데이터 버킷 `previews/{name}` 에 놓는다 (`〈281〉-㉮`).

순수 시험 — `put_object` 를 기록하는 스텁이다. numpy·conftest 불필요.
`../core-api/.venv/bin/python -m pytest tests/test_preview_sink.py -q --noconftest`

URL 은 바뀌지 않는다: `COLAB_VIZ_PREVIEW_URL_BASE=/previews` 그대로이고 CloudFront 가
`/previews/*` 를 데이터 버킷 `previews/` 오리진으로 보낸다 — 그래서 **키 = `{prefix}/{파일명}`**
이어야 하고 파일명은 `preview._write` 가 정한 `{cache_key}{suffix}` 그대로다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from colab_viz.kernel.preview_sinks import (
    CACHE_CONTROL, CONTENT_TYPES, LocalPreviewSink, S3PreviewSink,
)


@dataclass(frozen=True)
class _Artifact:
    """`preview.Artifact` 중 싱크가 보는 것 — `path` 뿐이다."""
    path: Path


class StubPut:
    def __init__(self) -> None:
        self.puts: list[dict] = []

    def put_object(self, key: str, payload: bytes,
                   content_type: str = "application/octet-stream",
                   cache_control: str | None = None) -> str:
        self.puts.append(dict(key=key, payload=payload, content_type=content_type,
                              cache_control=cache_control))
        return '"etag"'


def _four(tmp_path: Path) -> list[_Artifact]:
    key = "0" * 64
    blobs = {".webp": b"RIFF-webp", ".png": b"\x89PNG", ".json": b"{}", ".pgw": b"1\n0\n"}
    out = []
    for suffix, blob in blobs.items():
        p = tmp_path / f"{key}{suffix}"
        p.write_bytes(blob)
        out.append(_Artifact(path=p))
    return out


def test_산출물_4종이_키_content_type_cache_control_로_올라간다(tmp_path):
    client = StubPut()
    S3PreviewSink(client).publish(_four(tmp_path))

    assert [p["key"] for p in client.puts] == [
        f"previews/{'0' * 64}{s}" for s in (".webp", ".png", ".json", ".pgw")]
    assert [p["content_type"] for p in client.puts] == [
        "image/webp", "image/png", "application/json", "text/plain"]
    assert all(p["cache_control"] == "public, max-age=300" for p in client.puts)
    assert CACHE_CONTROL == "public, max-age=300"
    assert [p["payload"] for p in client.puts] == [b"RIFF-webp", b"\x89PNG", b"{}", b"1\n0\n"]


def test_접두사는_슬래시를_접고_기본은_previews_다(tmp_path):
    client = StubPut()
    S3PreviewSink(client, prefix="/stage/previews/").publish(_four(tmp_path)[:1])
    assert client.puts[0]["key"] == f"stage/previews/{'0' * 64}.webp"


def test_모르는_확장자는_거절하고_아무것도_올리지_않는다(tmp_path):
    p = tmp_path / "x.bmp"
    p.write_bytes(b"BM")
    client = StubPut()
    with pytest.raises(ValueError):
        S3PreviewSink(client).publish([_Artifact(path=p)])
    assert client.puts == []
    assert set(CONTENT_TYPES) == {".webp", ".png", ".json", ".pgw"}


def test_로컬_싱크는_아무것도_하지_않는다(tmp_path):
    assert LocalPreviewSink().publish(_four(tmp_path)) is None


def test_빈_목록은_호출이_없다():
    client = StubPut()
    S3PreviewSink(client).publish([])
    assert client.puts == []
