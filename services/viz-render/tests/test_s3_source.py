"""`S3SourcePort` — 객체 저장소의 대상을 **작업 디렉터리로 내려받아** 그린다 (`PLAN-SoT §9 〈342〉-㉴`).

순수 시험이다 — S3 클라이언트는 스텁이고 numpy·rasterio·conftest 가 필요 없다.
`../core-api/.venv/bin/python -m pytest tests/test_s3_source.py -q --noconftest` 로 돈다.

**이 파일이 막는 것** — ① 같은 객체를 두 번 내려받으면 캐시 키가 두 번 나오는 결함
(`_source_digest` 가 `st_mtime_ns` 를 쓰고, 내려받은 파일은 매번 새 mtime 이다 → `previews/`
가 렌더마다 는다) ② 크기 불일치를 조용히 통과시키는 것 ③ 작업 디렉터리가 상한 없이 자라는 것.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest

from colab_viz.domains.d7_visualization.source_digest import source_digest
from colab_viz.kernel import storage_layout
from colab_viz.ports.source import (
    FilesystemSourcePort, S3SourcePort, SizeMismatch, SourcePart, TargetNotFound,
    WorkspaceExceeded,
)

TID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
BODY_A = "01BX5ZZKBKACTAV9WEVGEMMVRZ"
BODY_B = "01BX5ZZKBKACTAV9WEVGEMMVS0"


def _key(target_id: str, file_id: str) -> str:
    return storage_layout.storage_key(target_id, file_id=file_id, kind=storage_layout.BODY_KIND)


def _grid_key(target_id: str, name: str) -> str:
    return storage_layout.storage_key(target_id, file_id="", kind=storage_layout.GRID_KIND,
                                      file_name=name)


class StubS3:
    """`S3Client` 의 네 호출만 흉내 낸다 — 시그니처는 `kernel/s3.py` 그대로."""

    def __init__(self, objects: dict[str, bytes], *, chunk: int = 3,
                 truncate: set[str] | None = None) -> None:
        self.objects = dict(objects)
        self.etags: dict[str, str] = {}
        self.calls: list[tuple[str, str]] = []
        self._chunk = chunk
        self._truncate = truncate or set()

    def etag(self, key: str) -> str:
        return self.etags.get(key) or f'"{hashlib.md5(self.objects[key]).hexdigest()}"'

    def list_objects(self, prefix: str):
        self.calls.append(("list", prefix))
        for k in sorted(self.objects):
            if k.startswith(prefix):
                yield k, len(self.objects[k])

    def head_object(self, key: str) -> tuple[int, str]:
        self.calls.append(("head", key))
        return len(self.objects[key]), self.etag(key)

    def get_object_stream(self, key: str, *, chunk_size: int = 1 << 20):
        self.calls.append(("get", key))
        data = self.objects[key]
        if key in self._truncate:
            data = data[:-1]

        def chunks():
            for i in range(0, len(data), self._chunk):
                yield data[i:i + self._chunk]
        return chunks()

    def gets(self, key: str) -> int:
        return sum(1 for c in self.calls if c == ("get", key))


def _objects(target_id: str = TID, *, grid: bool = True) -> dict[str, bytes]:
    objs = {_key(target_id, BODY_A): b"AAAAAAAAAA", _key(target_id, BODY_B): b"BBBBB"}
    if grid:
        objs[_grid_key(target_id, "Lat_HSR.npy")] = b"lat-lat"
        objs[_grid_key(target_id, "Lon_HSR.npy")] = b"lon-lon-lon"
    return objs


def _port(client, tmp_path, max_bytes=math.inf) -> S3SourcePort:
    return S3SourcePort(client, workdir=tmp_path / "work", max_bytes=max_bytes)


# ── ① resolve — 목록에서 parts / grid 를 가른다 ─────────────────────────────

def test_resolve_는_본체와_격자를_키_배치로_가르고_크기는_목록_값이다(tmp_path):
    client = StubS3(_objects())
    port = _port(client, tmp_path)
    target = port.resolve(dataset_id=TID, upload_id=None, file_ids=None)

    assert target.target_id == TID and target.is_upload is False
    assert [p.file_id for p in target.parts] == [BODY_A, BODY_B]
    assert [p.size_bytes for p in target.parts] == [10, 5]
    # 경로는 **작업 디렉터리 예정 경로**다 — 아직 내려받지 않았다
    expect = storage_layout.storage_path(tmp_path / "work", TID, file_id=BODY_A,
                                         kind=storage_layout.BODY_KIND)
    assert target.parts[0].path == expect and not expect.exists()
    assert target.grid_dir == storage_layout.grid_dir(tmp_path / "work", TID)
    assert sorted(g.file_name for g in target.grid_parts) == ["Lat_HSR.npy", "Lon_HSR.npy"]
    assert [g.size_bytes for g in sorted(target.grid_parts, key=lambda g: g.file_name)] == [7, 11]
    # 목록은 접두사 하나로 한 번 — 키 규약은 생성물(`storage_layout`)이 준 것이다
    assert client.calls == [("list", f"{storage_layout.UPLOADS_PREFIX}/{TID}/")]
    # resolve 는 바이트를 만지지 않는다
    assert not any(c[0] in ("get", "head") for c in client.calls)


def test_격자가_없으면_grid_dir_은_None_이다(tmp_path):
    target = _port(StubS3(_objects(grid=False)), tmp_path).resolve(
        dataset_id=None, upload_id=TID, file_ids=None)
    assert target.is_upload is True
    assert target.grid_dir is None and target.grid_parts == ()


def test_빈_접두사는_TargetNotFound_다(tmp_path):
    with pytest.raises(TargetNotFound):
        _port(StubS3({}), tmp_path).resolve(dataset_id=TID, upload_id=None, file_ids=None)


def test_fileIds_로_조각을_고르고_없는_id_는_TargetNotFound_다(tmp_path):
    port = _port(StubS3(_objects()), tmp_path)
    picked = port.resolve(dataset_id=TID, upload_id=None, file_ids=[BODY_B])
    assert [p.file_id for p in picked.parts] == [BODY_B]
    with pytest.raises(TargetNotFound):
        port.resolve(dataset_id=TID, upload_id=None, file_ids=["01BX5ZZKBKACTAV9WEVGEMMVS9"])


def test_다른_대상의_키는_섞이지_않는다(tmp_path):
    other = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
    client = StubS3({**_objects(), **_objects(other)})
    target = _port(client, tmp_path).resolve(dataset_id=other, upload_id=None, file_ids=None)
    assert target.target_id == other
    assert all(p.path.parts.count(other) == 1 and TID not in p.path.parts for p in target.parts)


# ── ② materialize — 바이트가 같고, 크기가 다르면 예외 ────────────────────────

def test_materialize_는_본체와_격자를_같은_바이트로_내려받는다(tmp_path):
    client = StubS3(_objects())
    port = _port(client, tmp_path)
    resolved = port.resolve(dataset_id=TID, upload_id=None, file_ids=None)
    got = port.materialize(resolved)

    for p in got.parts:
        assert p.path.read_bytes() == client.objects[_key(TID, p.file_id)]
        assert p.path.stat().st_size == p.size_bytes
        # ETag 가 조각의 판본이다 — 이것이 캐시 키로 들어간다
        assert p.version == client.etag(_key(TID, p.file_id))
    assert got.grid_dir is not None and got.grid_dir.is_dir()
    assert sorted(x.name for x in got.grid_dir.iterdir()) == ["Lat_HSR.npy", "Lon_HSR.npy"]
    assert (got.grid_dir / "Lon_HSR.npy").read_bytes() == b"lon-lon-lon"
    # 임시 파일이 남지 않는다
    assert not [x for x in (tmp_path / "work").rglob("*") if ".part" in x.name]


def test_내려받은_바이트가_head_크기와_다르면_SizeMismatch_이고_파일을_남기지_않는다(tmp_path):
    client = StubS3(_objects(grid=False), truncate={_key(TID, BODY_A)})
    port = _port(client, tmp_path)
    resolved = port.resolve(dataset_id=TID, upload_id=None, file_ids=None)
    with pytest.raises(SizeMismatch):
        port.materialize(resolved)
    assert not resolved.parts[0].path.exists()


def test_목록_크기와_head_크기가_다르면_SizeMismatch_다(tmp_path):
    """413 이 목록 크기로 판정됐다 — 그 사이 객체가 바뀌었으면 그 판정은 무효다."""
    client = StubS3(_objects(grid=False))
    port = _port(client, tmp_path)
    resolved = port.resolve(dataset_id=TID, upload_id=None, file_ids=None)
    client.objects[_key(TID, BODY_A)] = b"AAAAAAAAAAAAAAAAAAAA"      # 목록 뒤 교체
    with pytest.raises(SizeMismatch):
        port.materialize(resolved)


# ── ③ 캐시 키 — 같은 객체 두 번 = 같은 디지스트 ─────────────────────────────

def test_같은_객체를_두_번_materialize_하면_source_digest_가_같다(tmp_path):
    client = StubS3(_objects(grid=False))
    port = _port(client, tmp_path)
    first = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    d1 = source_digest(first.parts)
    # 두 번째 — 캐시 적중이라 내려받지 않는다
    second = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    assert source_digest(second.parts) == d1
    assert client.gets(_key(TID, BODY_A)) == 1


def test_캐시_파일이_지워졌으면_다시_내려받아도_디지스트는_같다(tmp_path):
    """mtime 이 새로 찍혀도 키가 안 바뀐다 — 이것이 `〈342〉` 어드바이저 정정이 요구한 성질이다."""
    client = StubS3(_objects(grid=False))
    port = _port(client, tmp_path)
    first = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    d1 = source_digest(first.parts)
    for p in first.parts:
        p.path.unlink()
    second = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    assert client.gets(_key(TID, BODY_A)) == 2
    assert source_digest(second.parts) == d1


def test_객체가_바뀌면_디지스트가_바뀌고_다시_내려받는다(tmp_path):
    client = StubS3(_objects(grid=False))
    port = _port(client, tmp_path)
    first = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    d1 = source_digest(first.parts)

    # 같은 크기, 다른 내용 → ETag 만 다르다
    client.objects[_key(TID, BODY_A)] = b"aaaaaaaaaa"
    second = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    assert second.parts[0].path.read_bytes() == b"aaaaaaaaaa"
    assert client.gets(_key(TID, BODY_A)) == 2
    assert source_digest(second.parts) != d1


def test_파일시스템_조각의_디지스트_규칙은_종전_그대로다(tmp_path):
    """Filesystem 어댑터는 `version` 이 없고 `(이름, 크기, mtime_ns)` 다 — 배포된 미리보기의
    캐시 키가 이 변경으로 바뀌면 staging 의 산출물이 전부 무효화된다."""
    f = tmp_path / BODY_A
    f.write_bytes(b"hello")
    part = SourcePart(file_id=BODY_A, file_name=BODY_A, path=f, size_bytes=5)
    assert part.version is None
    st = f.stat()
    legacy = hashlib.sha256(f"{BODY_A}|{st.st_size}|{st.st_mtime_ns}|".encode()).hexdigest()
    assert source_digest([part]) == legacy


def test_Filesystem_의_materialize_는_항등이다(tmp_path):
    root = tmp_path / "src"
    body = storage_layout.storage_path(root, TID, file_id=BODY_A, kind=storage_layout.BODY_KIND)
    body.parent.mkdir(parents=True)
    body.write_bytes(b"x")
    port = FilesystemSourcePort(root)
    resolved = port.resolve(dataset_id=TID, upload_id=None, file_ids=None)
    assert port.materialize(resolved) is resolved


# ── ④ 작업 디렉터리 상한 — LRU ───────────────────────────────────────────────

def _dir_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def test_상한을_넘으면_가장_오래_안_쓴_대상부터_지운다(tmp_path):
    other = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
    client = StubS3({**_objects(grid=False), **_objects(other, grid=False)})
    port = _port(client, tmp_path, max_bytes=20)          # 대상 하나 = 15 B

    a = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    b = port.materialize(port.resolve(dataset_id=other, upload_id=None, file_ids=None))
    assert not a.parts[0].path.parent.exists(), "오래된 대상이 지워져야 한다"
    assert all(p.path.is_file() for p in b.parts), "방금 내려받은 대상은 남는다"

    # 다시 A 를 쓰면 이번엔 B 가 나간다 — 최근 사용 순이다
    a2 = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    assert all(p.path.is_file() for p in a2.parts)
    assert not b.parts[0].path.parent.exists()


def test_상한_안이면_아무것도_지우지_않는다(tmp_path):
    other = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
    client = StubS3({**_objects(grid=False), **_objects(other, grid=False)})
    port = _port(client, tmp_path, max_bytes=100)
    a = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    b = port.materialize(port.resolve(dataset_id=other, upload_id=None, file_ids=None))
    assert all(p.path.is_file() for p in a.parts + b.parts)


def test_대상_하나가_상한보다_크면_내려받기_전에_거절한다(tmp_path):
    client = StubS3(_objects())                              # 본체 15 + 격자 18 = 33 B
    port = _port(client, tmp_path, max_bytes=32)
    resolved = port.resolve(dataset_id=TID, upload_id=None, file_ids=None)
    with pytest.raises(WorkspaceExceeded):
        port.materialize(resolved)
    assert not any(c[0] == "get" for c in client.calls)


def test_명시_무제한이면_지우지_않는다(tmp_path):
    other = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
    client = StubS3({**_objects(grid=False), **_objects(other, grid=False)})
    port = _port(client, tmp_path, max_bytes=math.inf)
    a = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    b = port.materialize(port.resolve(dataset_id=other, upload_id=None, file_ids=None))
    assert all(p.path.is_file() for p in a.parts + b.parts)
    assert _dir_bytes(tmp_path / "work") >= 30


def test_상한은_숫자여야_한다(tmp_path):
    with pytest.raises((TypeError, ValueError)):
        S3SourcePort(StubS3({}), workdir=tmp_path, max_bytes=None)  # type: ignore[arg-type]


def test_객체_이름이_ULID_모양이_아니어도_키는_이름으로_되짚는다(tmp_path):
    """실호출 증거에서 잡힌 결함 — 파생 `file_id` 로 키를 만들면 없는 객체를 가리켜 404 였다."""
    key = f"{storage_layout.UPLOADS_PREFIX}/{TID}/not-a-ulid.nc"
    client = StubS3({key: b"payload"})
    port = _port(client, tmp_path)
    got = port.materialize(port.resolve(dataset_id=TID, upload_id=None, file_ids=None))
    assert got.parts[0].file_name == "not-a-ulid.nc" and got.parts[0].file_id != "not-a-ulid.nc"
    assert got.parts[0].path.read_bytes() == b"payload"
    assert ("get", key) in client.calls
