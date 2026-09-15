"""미리보기 출력 싱크 — 산출물을 데이터 버킷 `previews/{name}` 에 놓는다 (`〈342〉-㉮`).

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
        #: `DL-2` — 삭제 호출을 **한 번씩** 기록한다. 「몇 번 불렀는가」가 판정의 일부다.
        self.deletes: list[list[str]] = []

    def put_object(self, key: str, payload: bytes,
                   content_type: str = "application/octet-stream",
                   cache_control: str | None = None) -> str:
        self.puts.append(dict(key=key, payload=payload, content_type=content_type,
                              cache_control=cache_control))
        return '"etag"'

    def delete_objects(self, keys: list[str]) -> None:
        self.deletes.append(list(keys))


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


# ── `index`·`remove` — `DL-2` ⓓ2 ────────────────────────────────────────────
# 산출물 키는 내용 주소라 fileId 를 담지 않는다. 발행 시점에 파일별 **표식 객체**를
# 하나 놓아 두면 삭제 때 지워진 fileId 마다 목록 조회 1회로 산출물을 되찾는다 —
# 버킷 접두 전체 스캔 0.

_FILE_A = "01J00000000000000000FILEA"
_FILE_B = "01J00000000000000000FILEB"
_KEY = "0" * 64


def test_index_는_파일별_표식을_0바이트로_놓는다():
    client = StubPut()
    S3PreviewSink(client).index([(_FILE_A, _KEY), (_FILE_B, _KEY)])

    assert [p["key"] for p in client.puts] == [
        f"preview-index/by-file/{_FILE_A}/{_KEY}",
        f"preview-index/by-file/{_FILE_B}/{_KEY}",
    ]
    # 본문 0바이트 — 자리 자체가 사실이고 담을 값이 없다.
    assert all(p["payload"] == b"" for p in client.puts)
    assert all(p["content_type"] == "application/json" for p in client.puts)
    # 표식은 CloudFront 가 노출하지 않는다 — 캐시 수명을 붙일 대상이 아니다.
    assert all(p["cache_control"] is None for p in client.puts)


def test_index_는_산출물_접두를_타지_않는다():
    """싱크 접두(`previews`)를 바꿔도 표식 자리는 **형제 접두** 그대로다."""
    client = StubPut()
    S3PreviewSink(client, prefix="stage/previews").index([(_FILE_A, _KEY)])
    assert client.puts[0]["key"] == f"preview-index/by-file/{_FILE_A}/{_KEY}"


def test_index_빈_목록은_호출이_없다():
    client = StubPut()
    S3PreviewSink(client).index([])
    assert client.puts == []


def test_remove_는_산출물과_표식을_한_번의_삭제로_보낸다():
    client = StubPut()
    S3PreviewSink(client).remove([f"{_KEY}.png", f"{_KEY}.json"],
                                 index_pairs=[(_FILE_A, _KEY)])

    assert len(client.deletes) == 1, "삭제는 한 번이다 — 반쯤 지우고 멈추지 않는다"
    assert client.deletes[0] == [
        f"previews/{_KEY}.png",
        f"previews/{_KEY}.json",
        f"preview-index/by-file/{_FILE_A}/{_KEY}",
    ]


def test_remove_는_아무것도_없으면_부르지_않는다():
    client = StubPut()
    S3PreviewSink(client).remove([], index_pairs=[])
    assert client.deletes == []


def test_remove_는_경로가_섞인_이름을_거절하고_아무것도_지우지_않는다():
    """**관대하게 무시하지 않는다** — 이름 한 조각이 아닌 것은 지울 자리를 모른다."""
    client = StubPut()
    with pytest.raises(ValueError):
        S3PreviewSink(client).remove([f"sub/{_KEY}.png"], index_pairs=[])
    assert client.deletes == []


def test_로컬_싱크의_index_remove_는_아무것도_하지_않는다():
    sink = LocalPreviewSink()
    assert sink.index([(_FILE_A, _KEY)]) is None
    assert sink.remove([f"{_KEY}.png"], index_pairs=[(_FILE_A, _KEY)]) is None
