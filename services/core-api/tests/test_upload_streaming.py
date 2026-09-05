"""업로드가 **바이트를 어떻게 다루는가** (`CODE-REVIEW-20260903` #10 · 부록).

두 가지를 잰다.

ⓐ **거절된 격자 파일이 디스크에 남지 않는다** (부록 — `ingestion.py:624`).
   `add_dataset_file` 이 `_store` 를 `kind == GRID` 400 **앞에서** 불러, 거절된 격자 파일이
   `uploads/{id}/grid/` 에 그대로 남았다. 격자를 읽는 쪽(viz-render)에는 원장이 없어
   **폴더가 곧 사실**이라, 거절했다면서 그 파일로 그리거나 짝이 셋이 되어 통째로 거절된다.

ⓑ **파일 전체를 메모리에 올리지 않는다** (#10).
   세 업로드 라우트만 `async def` 인데 `await upload_file.read()` 로 전체를 읽고
   `path.write_bytes` 와 동기 SQLAlchemy 를 이벤트 루프에서 돌렸다 — nginx 상한 8g 까지
   RSS 가 파일 크기를 따라가고, 그동안 이 프로세스의 **모든 요청(`/healthz` 포함)이 멈춘다.**
   바이트 무결성 시험 셋이 그 전환의 **회귀 그물**이다: 잘리거나 청크가 섞이는 것이 가장
   무서운 회귀다. 마지막 시험 하나가 **구조 자체**를 못으로 박는다.

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


def test_the_upload_routes_do_not_read_whole_files_into_memory() -> None:
    """**구조를 못으로 박는다** — 결과만 재면 다음 사람이 `read()` 로 되돌려도 green 이다.

    세 라우트는 `def`(스레드풀)이고 바이트는 저장 Port 의 `put_stream` → `shutil.copyfileobj`
    로 흘러야 한다 (병합 창 8-a 로 그 호출이 `kernel/storage_backends` 로 옮겼다).
    `async def` 로 되돌리면 **동기 SQLAlchemy 까지** 이벤트 루프에서 돌아 `/healthz` 가
    같이 멈춘다 — 그 정지는 업로드한 사람이 아니라 **다른 모든 사람**에게 보인다.

    ⚠ **문자열이 아니라 구문을 본다.** 산문에 `async def` 라는 낱말이 나오는 것과 코드가
    `async def` 인 것은 다르다 — 문자열로 재면 주석 한 줄이 시험을 뒤집는다.
    """
    import ast

    src = (pathlib.Path(__file__).resolve().parents[1]
           / "src" / "colab_core" / "app" / "routes" / "ingestion.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    coroutines = [n.name for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)]
    assert coroutines == [], f"업로드 라우트가 다시 `async def` 가 됐다: {coroutines}"
    awaits = [n for n in ast.walk(tree) if isinstance(n, ast.Await)]
    assert awaits == [], "이벤트 루프에서 파일을 읽고 있다."
    calls = {ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "upload_file.read" not in calls and "file.read" not in calls, \
        "파일 전체를 한 번에 읽는 호출이 남아 있다."

    # ⭑ ⟨병합 창 8-a⟩ **흘려 보내는 자리가 옮겼다 — 못은 그 자리를 따라간다.**
    #   종전에는 `ingestion.py` 안에 `shutil.copyfileobj` 가 있었다. PR #1 의 저장 Port
    #   (`〈337〉`)가 바이트를 만지는 자리를 `kernel/storage_backends` 하나로 모으면서
    #   그 호출이 `LocalFilesystemStorage.put_stream` 으로 갔다. **약하게 만든 것이 아니다** —
    #   재는 것은 그대로 「전체를 메모리에 올리지 않는가」이고, 자리만 실물을 따라 옮겼다.
    #   ⛔ 라우트 쪽 못(`async def` 0 · `await` 0 · 전체 `read()` 0)은 **위에서 그대로 잰다.**
    backend_src = (pathlib.Path(__file__).resolve().parents[1]
                   / "src" / "colab_core" / "kernel" / "storage_backends.py"
                   ).read_text(encoding="utf-8")
    backend_calls = {ast.unparse(n.func) for n in ast.walk(ast.parse(backend_src))
                     if isinstance(n, ast.Call)}
    assert "shutil.copyfileobj" in backend_calls, \
        "저장 Port 가 바이트를 흘려 보내지 않는다 — 전체를 메모리에 올린다."

    # 라우트가 그 Port 를 실제로 부르는가 — Port 가 스트리밍이어도 라우트가 안 쓰면 뜻이 없다.
    assert any(c.endswith(".put_stream") for c in calls), \
        "업로드 라우트가 저장 Port 의 `put_stream` 을 부르지 않는다."
