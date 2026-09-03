"""업로드가 **바이트를 어떻게 다루는가** (`CODE-REVIEW-20260903` #10 · 부록).

두 가지를 잰다.

ⓐ **거절된 격자 파일이 디스크에 남지 않는다** (부록 — `ingestion.py:624`).
   `add_dataset_file` 이 `_store` 를 `kind == GRID` 400 **앞에서** 불러, 거절된 격자 파일이
   `uploads/{id}/grid/` 에 그대로 남았다. 격자를 읽는 쪽(viz-render)에는 원장이 없어
   **폴더가 곧 사실**이라, 거절했다면서 그 파일로 그리거나 짝이 셋이 되어 통째로 거절된다.

ⓑ **바이트가 온전히 도착한다** — 여러 메가바이트 · 묶음 · 교체.
   이 시험들은 **회귀 그물**이다: 업로드가 파일 전체를 메모리에 올리는 대신 흘려 보내도록
   바뀔 때(#10), 잘리거나 청크가 섞이는 것이 가장 무서운 회귀다. 지금 구현에서도 통과하며,
   그것이 요점이다 — 그물은 바꾸기 **전에** 쳐 둔다.

⚠ 메모리 사용량 자체는 여기서 재지 않는다 (`[미확인]`).
"""
from __future__ import annotations

import hashlib
import io
import pathlib

from conftest import DS_A1, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

#: 여러 청크로 갈리는 크기. 한 번에 다 읽는 구현과 흘려 보내는 구현을 **결과로** 가른다.
BIG = 5 * 1024 * 1024 + 12345


def _payload(seed: bytes, size: int) -> bytes:
    """반복이 아니라 **자리마다 다른** 바이트 — 청크 순서가 바뀌면 해시가 달라진다."""
    out = bytearray()
    block = 0
    while len(out) < size:
        out += hashlib.sha256(seed + block.to_bytes(4, "big")).digest()
        block += 1
    return bytes(out[:size])


def _upload_root(client) -> pathlib.Path:
    from colab_core.kernel import file_store
    app = client.app
    return file_store.resolve_upload_root(app.state.settings, app.state)


def _files_on_disk(root: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def _body_path(root: pathlib.Path, target_id: str, file_id: str) -> pathlib.Path:
    """**자리는 `kernel/storage_layout` 이 정한다** — 시험이 배치를 다시 짜지 않는다."""
    from colab_core.kernel import storage_layout
    return root / storage_layout.storage_key(target_id, file_id=file_id, kind="본체")


def _grid_path(root: pathlib.Path, target_id: str, file_id: str,
               file_name: str) -> pathlib.Path:
    from colab_core.kernel import storage_layout
    return root / storage_layout.storage_key(target_id, file_id=file_id,
                                             kind="기준 격자 파일", file_name=file_name)


# ══════════ ⓐ 거절된 격자 파일은 디스크에 닿지 않는다 ════════════════════════
def test_a_rejected_grid_file_never_lands_on_disk(p2_client) -> None:
    """**거절은 저장 앞에 온다.** 폴더가 곧 사실인 소비자가 있기 때문이다."""
    client = p2_client()
    root = _upload_root(client)
    before = {p for p in _files_on_disk(root)}

    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                    files={"file": ("거절될격자.npy", b"\x93NUMPY" + b"x" * 4096,
                                    "application/octet-stream")},
                    data={"kind": "기준 격자 파일"}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text

    after = {p for p in _files_on_disk(root)}
    assert after == before, \
        f"거절한 격자 파일의 바이트가 남았다: {sorted(str(p) for p in after - before)}"


def test_an_accepted_body_file_still_lands_on_disk(p2_client) -> None:
    """**넓히지도 좁히지도 않았음**을 함께 잰다 — 받아들인 본체는 그대로 저장된다."""
    client = p2_client()
    root = _upload_root(client)
    payload = _payload(b"body", 4096)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                    files={"file": ("본체조각.csv", payload, "text/csv")},
                    data={"kind": "본체"}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    written = _body_path(root, DS_A1, r.json()["fileId"])
    assert written.is_file(), "받아들인 조각의 바이트가 없다."
    assert written.read_bytes() == payload


# ══════════ ⓑ 큰 파일이 온전히 도착한다 (스트리밍 경로) ══════════════════════
def test_a_multi_megabyte_upload_is_written_byte_for_byte(p2_client) -> None:
    """청크로 흘려 보내도 **바이트가 하나도 어긋나지 않는다.**"""
    client = p2_client()
    root = _upload_root(client)
    payload = _payload(b"createUpload", BIG)

    r = client.post(f"{API_PREFIX}/uploads",
                    files={"files": ("큰파일.nc", io.BytesIO(payload),
                                     "application/octet-stream")},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["files"][0]["byteSize"] == len(payload), \
        "원장이 적은 크기가 실제와 다르다 — 스트리밍이 길이를 잃었다."

    written = _body_path(root, body["uploadId"], body["files"][0]["fileId"])
    assert written.is_file(), "업로드한 바이트가 디스크에 없다."
    on_disk = written.read_bytes()
    assert len(on_disk) == len(payload), f"{len(on_disk)} != {len(payload)} — 잘렸다."
    assert hashlib.sha256(on_disk).hexdigest() == hashlib.sha256(payload).hexdigest(), \
        "바이트가 섞였다 — 청크 순서가 어긋났다."


def test_two_files_in_one_upload_do_not_bleed_into_each_other(p2_client) -> None:
    """묶음 업로드에서 **청크가 서로 섞이지 않는다.**"""
    client = p2_client()
    root = _upload_root(client)
    first = _payload(b"first", 2 * 1024 * 1024 + 7)
    second = _payload(b"second", 3 * 1024 * 1024 + 11)

    r = client.post(
        f"{API_PREFIX}/uploads",
        files=[("files", ("첫째.bin", io.BytesIO(first), "application/octet-stream")),
               ("files", ("둘째.bin", io.BytesIO(second), "application/octet-stream"))],
        headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    body = r.json()
    sizes = {f["fileName"]: f["byteSize"] for f in body["files"]}
    assert sizes == {"첫째.bin": len(first), "둘째.bin": len(second)}

    written = {f["fileName"]: _body_path(root, body["uploadId"], f["fileId"])
               for f in body["files"]}
    for name, payload in (("첫째.bin", first), ("둘째.bin", second)):
        assert written[name].is_file(), f"{name} 이 디스크에 없다."
        assert written[name].read_bytes() == payload, f"{name} 의 바이트가 어긋났다."


def test_replacing_a_grid_file_streams_too(p2_client) -> None:
    """`replaceDatasetGridFile` 도 같은 경로를 쓴다 — 한 자리만 고치면 나머지가 다르게 산다."""
    from test_dataset_files import GRID_FILE

    client = p2_client()
    root = _upload_root(client)
    payload = _payload(b"grid", 2 * 1024 * 1024 + 3)
    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
                   files={"file": ("교체격자.nc", io.BytesIO(payload),
                                   "application/octet-stream")},
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    found = _grid_path(root, DS_A1, GRID_FILE, "교체격자.nc")
    assert found.is_file(), "교체한 격자의 바이트가 없다."
    assert found.read_bytes() == payload
