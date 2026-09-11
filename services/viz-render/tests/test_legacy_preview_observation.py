from __future__ import annotations

import io
import json

import pytest

from colab_viz.domains.d7_visualization import legacy_preview_observation as obs
from colab_viz.domains.d7_visualization import ownership


class FakeS3:
    def __init__(self, objects):
        self.objects = objects
        self.closed = 0

    def list_objects(self, prefix):
        return iter((key, len(body)) for key, body in sorted(self.objects.items()))

    def head_object(self, key):
        return len(self.objects[key]), f'etag-{key}'

    def get_object_stream(self, key, *, chunk_size, expected_etag):
        owner = self
        class Stream(io.BytesIO):
            def __iter__(self):
                while chunk := self.read(chunk_size):
                    yield chunk
            def close(self):
                owner.closed += 1
                super().close()
        assert expected_etag == f'etag-{key}'
        return Stream(self.objects[key])


def _legacy(source=None):
    return json.dumps({"name": "old.png", "source": source}).encode()


def test_s3_구판관측은_333_형식파일을_내용으로분류하고_삭제하지_않는다():
    objects = {}
    for i in range(14):
        objects[f"previews/no-sidecar-{i}.{'png' if i < 7 else 'webp'}"] = b"image"
    for i in range(2):
        objects[f"previews/no-ledger-{i}.png"] = b"image"
        objects[f"previews/no-ledger-{i}.json"] = _legacy(f"gone-{i}")
    for i in range(3):
        objects[f"previews/known-{i}.png"] = b"image"
        objects[f"previews/known-{i}.json"] = _legacy("known")
    for i in range(154):
        doc = {"sidecarVersion": 2, "baked_for": {}, "source": "known", "sources": ["known"]}
        objects[f"previews/modern-{i}.png"] = b"image"
        objects[f"previews/modern-{i}.json"] = json.dumps(doc).encode()
    objects["previews/tile-current.tif"] = b"map-tile"
    assert len(objects) == 333
    client = FakeS3(objects)
    ledger = ownership.Ledger(frozenset({"known"}), frozenset())

    result = obs.observe(client, ledger, observed_at="2026-09-11T00:00:00Z")

    assert result["objects"] == 333
    assert result["legacy_counts"] == {
        ownership.LEGACY_SIDECAR_ABSENT: 14,
        ownership.LEGACY_SOURCE_LEDGER_ABSENT: 2,
        ownership.LEGACY_SOURCE_LEDGER_PRESENT: 3,
    }
    assert result["rebake_unreachable"] == 16
    assert result["deleted"] == 0
    assert len(result["key_sets"]["rebake_unreachable"]) == 16
    assert client.closed == 159


def test_s3_관측은_prefix이탈_중첩키_목록head크기불일치를_0으로접지않는다():
    ledger = ownership.Ledger(frozenset({"known"}), frozenset())
    with pytest.raises(obs.ObservationNotReady):
        obs.observe(FakeS3({"outside/x.png": b"x"}), ledger)
    with pytest.raises(obs.ObservationNotReady):
        obs.observe(FakeS3({"previews/nested/x.png": b"x"}), ledger)

    client = FakeS3({"previews/x.png": b"x", "previews/x.json": _legacy("known")})
    client.head_object = lambda _key: (999, "etag")
    with pytest.raises(obs.ObservationNotReady):
        obs.observe(client, ledger)

    duplicate_page = FakeS3({"previews/x.png": b"x"})
    duplicate_page.list_objects = lambda _prefix: iter([
        ("previews/x.png", 1), ("previews/x.png", 2)])
    with pytest.raises(obs.ObservationNotReady):
        obs.observe(duplicate_page, ledger)


def test_s3_관측은_빈원장과_깨진sidecar를_추측하지않는다():
    with pytest.raises(obs.ObservationNotReady):
        obs.observe(FakeS3({"previews/x.png": b"x"}), ownership.Ledger(frozenset(), frozenset()))
    broken = FakeS3({"previews/x.png": b"x", "previews/x.json": b"not-json"})
    with pytest.raises(obs.ObservationNotReady):
        obs.observe(broken, ownership.Ledger(frozenset({"known"}), frozenset()))
    assert broken.closed == 1

    invalid_modern = {"sidecarVersion": 2, "baked_for": {}, "source": "", "sources": []}
    with pytest.raises(obs.ObservationNotReady):
        obs.observe(FakeS3({"previews/m.png": b"x",
                            "previews/m.json": json.dumps(invalid_modern).encode()}),
                    ownership.Ledger(frozenset({"known"}), frozenset()))


def test_cli_관측준비실패는_exit78이다(tmp_path, monkeypatch, capsys):
    d3 = tmp_path / "d3.ids"; d3.write_text("known\n", encoding="utf-8")
    d5 = tmp_path / "d5.ids"; d5.write_text("", encoding="utf-8")
    client = FakeS3({"previews/x.png": b"x", "previews/x.json": b"null"})
    monkeypatch.setattr("colab_viz.kernel.s3.S3Client", lambda **_kwargs: client)

    rc = obs.main(["--bucket", "dev-bucket", "--region", "test-region",
                   "--d3-ids", str(d3), "--d5-ids", str(d5),
                   "--snapshot", str(tmp_path / "snapshot.json")])

    assert rc == 78
    assert "::관측준비실패::" in capsys.readouterr().out
