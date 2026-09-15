"""표식 백필 — `DL-2` 이전에 구운 산출물에 파일별 표식을 놓는다 (회부문 ⓓ5).

표식(`preview-index/by-file/{fileId}/{contentKey}`)은 **이 회차부터** 찍힌다. 그 전에 구운
산출물은 표식이 없어 회수 때 목록 조회로 찾히지 않고, 로컬 훑기로만 보충된다(`unindexed`).
dev 의 로컬 캐시는 LRU 라 밀려난 벌은 **어느 쪽으로도 안 잡힌다** — 그 구멍을 이 스크립트가
한 번 메운다.

여기서 재는 것 넷.
  ⑴ **기본은 dry-run** — `--apply` 없이는 PUT 이 0건이다. 「돌려 보고 나서 결정한다」가
     이 스크립트의 기본 자세이고, Ted ⓓ5 GO 가 `--apply` 의 전제다.
  ⑵ **사이드카만 읽는다** — `previews/` 아래 `.json` 만 GET 하고 그림은 건드리지 않는다.
  ⑶ **구판·`sources` 없음은 건너뛴다** — 못 읽은 것에 표식을 지어 놓지 않는다.
  ⑷ **삭제 0건** — 이 스크립트에는 지우는 문이 없다.
"""
from __future__ import annotations

import json

from colab_viz.ops import backfill_preview_index as backfill

_F1 = "01JQ0000000000000000000FA1"
_F2 = "01JQ0000000000000000000FA2"


def _key(tag: str) -> str:
    return (tag * 64)[:64]


class _StubS3:
    """`previews/` 접두의 목록·HEAD·본문을 들고 있는 최소 대역."""

    def __init__(self, docs: dict[str, bytes]) -> None:
        #: `{키: 본문}` — 사이드카가 아닌 키(그림)도 목록에는 들어간다.
        self.objects = dict(docs)
        self.puts: list[tuple[str, bytes]] = []
        self.deleted: list[str] = []

    def list_objects(self, prefix: str):
        for key, blob in sorted(self.objects.items()):
            if key.startswith(prefix):
                yield (key, len(blob))

    def head_object(self, key: str):
        return len(self.objects[key]), '"etag"'

    def get_object_stream(self, key: str, *, chunk_size=65536, expected_etag=None):
        yield self.objects[key]

    def put_object(self, key: str, payload: bytes, content_type: str, **kw) -> None:
        self.puts.append((key, payload))

    def delete_objects(self, keys) -> None:          # 부르면 시험이 잡는다
        self.deleted.extend(keys)


def _sidecar(sources, *, version: int = 2) -> bytes:
    doc = {"sidecarVersion": version, "name": "x.png", "layer": "detail",
           "source": sources[0] if sources else "", "sources": list(sources),
           "baked_for": {"target_id": "01JQ00000000000000000000D1", "is_upload": False}}
    return json.dumps(doc).encode("utf-8")


def _store() -> _StubS3:
    good, legacy, empty = _key("a"), _key("b"), _key("c")
    return _StubS3({
        f"previews/{good}.json": _sidecar([_F1, _F2]),
        f"previews/{good}.png": b"\x89PNG",
        f"previews/{good}.webp": b"RIFF",
        # 구판 — `sidecarVersion` 1 · `baked_for` 유무와 무관하게 판정 불가다.
        f"previews/{legacy}.json": json.dumps({"sidecarVersion": 1,
                                               "source": _F1}).encode("utf-8"),
        # v2 인데 `sources` 가 비었다 — 표식을 놓을 파일이 없다.
        f"previews/{empty}.json": _sidecar([]),
        # 지도 타일은 이 접두 밖이 아니라 **이름**으로 갈린다.
        f"previews/tile-{_key('d')}.json": _sidecar([_F1]),
    })


def test_dry_run_is_the_default_and_writes_nothing() -> None:
    store = _store()
    report = backfill.run(client=store, previews_prefix="previews")
    assert store.puts == [], "dry-run 인데 객체를 썼다."
    assert store.deleted == [], "이 스크립트에는 지우는 문이 없다."
    assert report.pairs == 2, report          # 좋은 벌 하나 × 원천 둘
    assert report.sidecars == 4               # `.json` 넷 (타일 포함)
    assert report.skipped == 2                # 구판 1 ＋ `sources` 빈 것 1
    assert report.tiles == 1
    assert report.applied is False


def test_apply_puts_one_marker_per_source() -> None:
    store = _store()
    report = backfill.run(client=store, previews_prefix="previews", apply=True)
    assert report.applied is True
    good = _key("a")
    assert sorted(k for k, _ in store.puts) == sorted([
        f"preview-index/by-file/{_F1}/{good}",
        f"preview-index/by-file/{_F2}/{good}",
    ])
    assert all(payload == b"" for _, payload in store.puts), "표식은 0바이트다 — 담을 값이 없다."
    assert store.deleted == []


def test_it_never_touches_keys_outside_the_previews_prefix() -> None:
    """접두 밖은 **목록에도 안 든다** — 버킷 전체 스캔을 하지 않는다."""
    store = _store()
    store.objects["uploads/somewhere/x.json"] = _sidecar([_F1])
    backfill.run(client=store, previews_prefix="previews", apply=True)
    assert all(k.startswith("preview-index/") for k, _ in store.puts)
    assert report_keys_listed(store) == ["previews/"]


def report_keys_listed(store: _StubS3) -> list[str]:
    """`list_objects` 가 받은 접두를 되묻는다 — 대역이 기록하지 않으므로 재실행해 확인한다."""
    seen: list[str] = []
    original = store.list_objects

    def spy(prefix: str):
        seen.append(prefix)
        return original(prefix)

    store.list_objects = spy                               # type: ignore[assignment]
    backfill.run(client=store, previews_prefix="previews")
    return seen
