"""**사용자 지시 삭제**로 미리보기 산출물을 회수한다 (`DL-2` · 회부문 ⓓ3·ⓓ6).

배경 — `DL-1` 은 데이터셋을 묘비로 바꾸고 원장이 알던 저장 키를 지운다. 그런데 그 파일로
그린 **미리보기 산출물은 아무도 지우지 않았다.** 배경 회수 루프의 등급 판정
(`ownership.grade`)은 묘비 데이터셋의 `fileId` 를 `d5_upload_file` 잔존 때문에
「접수분에만 닿는다」로 읽고, 그것은 **고아가 아니다** ⟹ 영원히 회수되지 않는다.

그래서 판정 입력을 **원장 등급이 아니라 「지워진 `fileId` 집합 `D`」** 로 바꾼 넷째 래퍼를
둔다. 계산기(`invalidation.plan`)도 집행 문(`invalidation.apply`)도 늘리지 않는다 —
`reclaim_plan`·`supersede_plan`·`tile_reclaim_plan` 과 같은 모양이다.

순수 시험 — numpy·conftest 불필요.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from colab_viz.domains.d7_visualization import invalidation, reclaim_on_delete
from colab_viz.kernel.storage_layout import PREVIEW_INDEX_PREFIX, preview_index_key

_EXTS = (".webp", ".png", ".json", ".pgw")
_F1 = "01J0000000000000000FILE1"
_F2 = "01J0000000000000000FILE2"
_TARGET = "01J000000000000000DATASET"


def _key(tag: str) -> str:
    """내용 키 자리 — 길이·모양만 실물과 같으면 된다(다이제스트를 여기서 만들지 않는다)."""
    return (tag * 64)[:64]


def _sidecar(sources, *, version: int = 2, baked: bool = True) -> dict:
    doc: dict = {"sidecarVersion": version, "name": "x.png", "layer": "detail",
                 "source": sources[0] if sources else "", "sources": list(sources)}
    if baked:
        doc["baked_for"] = {"target_id": _TARGET, "is_upload": False}
    return doc


def _lay(root: Path, key: str, *, sidecar: dict | None, on_disk: bool = True) -> None:
    """한 벌을 자리에 놓는다. `on_disk=False` 면 사이드카만 두고 그림은 두지 않는다."""
    root.mkdir(parents=True, exist_ok=True)
    if on_disk:
        (root / f"{key}.png").write_bytes(b"\x89PNG")
        (root / f"{key}.webp").write_bytes(b"RIFF")
    if sidecar is not None:
        (root / f"{key}.json").write_text(json.dumps(sidecar), encoding="utf-8")


class StubClient:
    """`list_objects` 로 표식을 돌려주고 삭제는 싱크가 진다 — 여기서는 목록만 센다."""

    def __init__(self, index: dict[str, list[str]] | None = None) -> None:
        self.index = index or {}
        self.listed: list[str] = []

    def list_objects(self, prefix: str):
        self.listed.append(prefix)
        file_id = prefix.rstrip("/").rsplit("/", 1)[-1]
        for content_key in self.index.get(file_id, []):
            yield (f"{prefix}{content_key}", 0)


class StubSink:
    def __init__(self) -> None:
        self.removes: list[tuple[list[str], list[tuple[str, str]]]] = []

    def publish(self, artifacts) -> None:
        return None

    def index(self, pairs) -> None:
        return None

    def remove(self, names, *, index_pairs) -> None:
        self.removes.append((list(names), list(index_pairs)))


def _run(tmp_path, client, sink, file_ids):
    return reclaim_on_delete.run(client=client, sink=sink, previews_root=tmp_path,
                                 target_id=_TARGET, file_ids=file_ids)


# ── 판정 ────────────────────────────────────────────────────────────────────

def test_원천이_전부_지워진_벌은_회수한다(tmp_path):
    key = _key("a")
    _lay(tmp_path, key, sidecar=_sidecar([_F1]))
    client = StubClient({_F1: [key]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.stale == 1 and result.kept == 0
    assert sorted(result.removed) == sorted(f"{key}{e}" for e in _EXTS)
    # 로컬 파일은 사라진다 — 집행은 `invalidation.apply()` 한 자리다.
    assert not (tmp_path / f"{key}.png").exists()
    assert not (tmp_path / f"{key}.json").exists()
    # 목록 조회는 지워진 파일 수에만 비례한다 — 버킷 접두 전체 스캔 0.
    assert client.listed == [f"{PREVIEW_INDEX_PREFIX}/by-file/{_F1}/"]


def test_원천이_일부만_지워진_벌은_남긴다(tmp_path):
    """한 그림이 파일 둘에서 왔고 하나만 지워졌으면 **그 그림은 아직 살아 있다.**"""
    key = _key("b")
    _lay(tmp_path, key, sidecar=_sidecar([_F1, _F2]))
    client = StubClient({_F1: [key]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.stale == 0 and result.kept == 1
    assert result.removed == ()
    assert result.kept_reasons[invalidation.DELETION_KEEP_PARTIAL] == 1
    assert (tmp_path / f"{key}.png").exists()
    assert sink.removes == [], "지울 것이 없으면 삭제 문을 부르지 않는다"


def test_지도_타일은_손대지_않는다(tmp_path):
    """`tile-` 은 D5 가 구운 것이고 사이드카가 없다 — 이 문의 대상이 아니다."""
    key = "tile-" + _key("c")[:59]
    _lay(tmp_path, key, sidecar=_sidecar([_F1]))
    client = StubClient({_F1: [key]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.stale == 0 and result.kept == 1
    assert result.kept_reasons[invalidation.DELETION_KEEP_MAP_TILE] == 1
    assert (tmp_path / f"{key}.png").exists()


def test_사이드카가_없거나_구판이면_남긴다(tmp_path):
    """**없는 근거로 지우면 그것이 오삭제다**(`ownership` 덫 ②)."""
    absent, legacy = _key("d"), _key("e")
    _lay(tmp_path, absent, sidecar=None)
    _lay(tmp_path, legacy, sidecar=_sidecar([_F1], version=1, baked=False))
    client = StubClient({_F1: [absent, legacy]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.stale == 0 and result.kept == 2
    assert result.kept_reasons[invalidation.DELETION_KEEP_NO_SIDECAR] == 1
    assert result.kept_reasons[invalidation.DELETION_KEEP_LEGACY] == 1
    assert (tmp_path / f"{absent}.png").exists()
    assert (tmp_path / f"{legacy}.png").exists()


def test_지워진_파일_집합이_비면_계획을_세우지_않는다(tmp_path):
    """`D = ∅` 은 「전부 지워라」가 아니다 — 조용히 걸러내지 않고 멈춘다."""
    with pytest.raises(invalidation.OutOfScope):
        _run(tmp_path, StubClient(), StubSink(), [])


# ── 집행 ────────────────────────────────────────────────────────────────────

def test_로컬에_없어도_S3_이름은_계산해_지운다(tmp_path):
    """dev 의 로컬 캐시는 LRU 라 **밀려난 벌이 S3 에만 남는다.** 이름은 키에서 나온다."""
    key = _key("f")
    # 사이드카만 로컬에 있고 그림은 이미 캐시에서 밀려났다.
    _lay(tmp_path, key, sidecar=_sidecar([_F1]), on_disk=False)
    client = StubClient({_F1: [key]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.stale == 1
    assert sorted(result.removed) == sorted(f"{key}{e}" for e in _EXTS)
    assert len(sink.removes) == 1
    names, pairs = sink.removes[0]
    assert sorted(names) == sorted(f"{key}{e}" for e in _EXTS)


def test_인덱스_표식도_같은_삭제_목록에_실린다(tmp_path):
    """표식을 남겨 두면 다음 회수가 없는 산출물을 찾아 헤맨다."""
    key = _key("g")
    _lay(tmp_path, key, sidecar=_sidecar([_F1, _F2]))
    client = StubClient({_F1: [key], _F2: [key]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1, _F2])

    assert result.stale == 1
    _names, pairs = sink.removes[0]
    assert sorted(pairs) == sorted([(_F1, key), (_F2, key)])
    assert sorted(preview_index_key(f, k) for f, k in pairs) == sorted(
        [preview_index_key(_F1, key), preview_index_key(_F2, key)])


def test_표식_없이_로컬에만_있는_벌은_회수하고_unindexed_로_센다(tmp_path):
    """이 회차 **이전** 산출물에는 표식이 없다. 세지 않으면 얼마나 남았는지 아무도 모른다."""
    indexed, old = _key("h"), _key("i")
    _lay(tmp_path, indexed, sidecar=_sidecar([_F1]))
    _lay(tmp_path, old, sidecar=_sidecar([_F1]))
    client = StubClient({_F1: [indexed]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.stale == 2 and result.unindexed == 1
    assert not (tmp_path / f"{old}.png").exists()


def test_클라이언트가_없으면_로컬_자리만_본다(tmp_path):
    """싱크가 로컬인 배포에는 표식 자리가 없다 — 목록 조회를 시도하지 않는다."""
    key = _key("j")
    _lay(tmp_path, key, sidecar=_sidecar([_F1]))
    sink = StubSink()

    result = reclaim_on_delete.run(client=None, sink=sink, previews_root=tmp_path,
                                   target_id=_TARGET, file_ids=[_F1])

    assert result.stale == 1 and result.unindexed == 1
    assert not (tmp_path / f"{key}.png").exists()


def test_두_번째_호출은_지울_것이_없다(tmp_path):
    """멱등 — core 가 삭제를 재시도해도 두 번째는 stale 0 이다."""
    key = _key("k")
    _lay(tmp_path, key, sidecar=_sidecar([_F1]))
    client = StubClient({_F1: [key]})
    sink = StubSink()

    first = _run(tmp_path, client, sink, [_F1])
    client.index = {}                       # 표식은 첫 회수가 지웠다
    second = _run(tmp_path, client, sink, [_F1])

    assert first.stale == 1 and second.stale == 0
    assert second.removed == ()


# ── 음성 — 삭제를 부르는 자리는 하나다 (`DL-2` ⓓ6) ──────────────────────────

def test_S3_삭제를_부르는_자리는_회수_모듈_하나다():
    """**음성.** 자동 회수 루프의 「S3 를 0건 지운다」는 여전히 참이어야 한다.

    ⚠ 이름만 늘리지 않는다 — 이 시험이 늘어난 자리를 곧바로 red 로 낸다.
    """
    root = Path(invalidation.__file__).resolve().parents[2]     # colab_viz/
    allowed = {"preview_sinks.py", "s3.py", "reclaim_on_delete.py"}
    offenders = []
    for p in sorted(root.rglob("*.py")):
        text = p.read_text(encoding="utf-8")
        for token in ("delete_objects(", ".remove("):
            if token in text and p.name not in allowed:
                offenders.append(f"{p.name}:{token}")
    assert offenders == [], f"S3 삭제를 부르는 자리가 늘었다: {offenders}"


def test_자동_회수_루프의_문면이_범위를_말한다():
    """`tile_reclaim` 의 잠금은 **없어진 것이 아니라 범위가 적힌 것**이다."""
    from colab_viz.domains.d7_visualization import tile_reclaim

    for doc in (tile_reclaim.__doc__,
                tile_reclaim.run_s3_observation.__doc__,
                tile_reclaim.S3ReclaimJob.__doc__):
        assert "자동 회수 루프" in doc, doc[:80]
        assert "reclaim_on_delete" in doc, doc[:80]


# ── 고아 표식 — 렌더-삭제 경합이 남긴 자리 (prod 임시 검증 2026-09-13 21:35) ──────

class OrphanClient(StubClient):
    """표식은 돌려주되 **원격 객체는 하나도 없다.** `head_object` 가 전건 없음을 낸다."""

    def __init__(self, index=None, present=()) -> None:
        super().__init__(index)
        self.present = set(present)
        self.headed: list[str] = []

    def head_object(self, key: str):
        self.headed.append(key)
        if key in self.present:
            return 4, '"etag"'
        raise FileNotFoundError(key)


def test_객체도_사이드카도_없는_표식은_표식만_걷는다(tmp_path):
    """**렌더가 표식을 먼저 쓰고 죽으면 그 표식이 고아로 남는다.**

    실측(2026-09-13 21:35 · prod 임시 검증) — 등록 직후 자동 렌더가 삭제와 겹쳐
    `RENDER_UNKNOWN_ERROR` 로 죽었고, 그 렌더가 `sink.index` 로 **먼저** 써 둔 표식 10개가
    산출물 없이 남았다. 표식만 남으면 다음 회수가 매번 같은 후보를 되짚고, 그 후보는
    「사이드카 부재」로 영원히 `kept` 다 — **자정되지 않는다.**

    ⛔ **산출물 삭제 판정은 한 글자도 바뀌지 않는다** — 지우는 것은 표식뿐이고, 그것도
    **지워진 파일(`D`)의 표식만**이다. 사이드카가 있으면 기존 규칙 그대로다.
    """
    key = _key("o")
    client = OrphanClient({_F1: [key]})          # 표식은 있다
    sink = StubSink()                            # 로컬에는 아무것도 놓지 않는다

    result = _run(tmp_path, client, sink, [_F1])

    assert result.orphan_index == 1, result
    # 산출물 판정은 무변 — 사이드카가 없으므로 `kept` 다.
    assert result.stale == 0 and result.kept == 1
    assert result.kept_reasons[invalidation.DELETION_KEEP_NO_SIDECAR] == 1
    assert result.removed == (), "고아 정리는 산출물을 지우지 않는다"
    names, pairs = sink.removes[0]
    assert names == [], f"산출물 삭제가 섞였다: {names}"
    assert pairs == [(_F1, key)], pairs


def test_객체가_남아_있으면_표식을_걷지_않는다(tmp_path):
    """**고아는 「아무것도 없다」일 때만이다.** 한 확장자라도 서 있으면 손대지 않는다 —
    사이드카를 아직 못 읽었을 뿐인 벌의 표식을 지우면 그 산출물은 영영 못 찾는다."""
    key = _key("p")
    client = OrphanClient({_F1: [key]}, present=[f"previews/{key}.webp"])
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.orphan_index == 0, result
    assert result.kept == 1
    assert sink.removes == [], "지울 것이 없으면 삭제 문을 부르지 않는다"


def test_사이드카가_있으면_고아로_세지_않는다(tmp_path):
    """기존 규칙 그대로 — 원천이 전부 지워졌으면 산출물째 회수하고 `orphan_index` 는 0 이다."""
    key = _key("q")
    _lay(tmp_path, key, sidecar=_sidecar([_F1]))
    client = OrphanClient({_F1: [key]})
    sink = StubSink()

    result = _run(tmp_path, client, sink, [_F1])

    assert result.orphan_index == 0, result
    assert result.stale == 1 and result.kept == 0

