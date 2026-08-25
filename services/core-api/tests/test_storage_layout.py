"""접수한 바이트가 **실제로 어디에 놓이는가** — 배치를 단언하는 시험.

`03-HANDOFF §4 #26` 이 적은 이 계열의 근본 원인은 한 줄이다: **저장 배치를 단언하는
시험이 0건이었다.** 그래서 세 단위가 서로 다른 배치를 쓰는데도 전 시험이 green 이었고,
사람이 올린 격자가 렌더러에 영영 닿지 않는 사실은 배포에서만 드러났다(`#20`).

여기서 보는 것은 응답이 아니라 **디스크**다. 응답은 `uploadId`·`fileId` 만 말하고
배치에 대해서는 아무 말도 하지 않는다 — 그것이 이 시험이 필요한 이유다.
정본 = `contracts/storage/layout.json` (생성물 `kernel/storage_layout.py`).
"""
from __future__ import annotations

import pathlib

from conftest import TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.kernel import storage_layout

BODY_BYTES = b"\x89HDF\r\n\x1a\n" + b"\x00" * 32
GRID_BYTES = b"\x93NUMPY\x01\x00" + b"\x00" * 40


def _root(tmp_path: pathlib.Path) -> pathlib.Path:
    """`p2_client` 가 `upload_storage_dir` 로 준 자리와 같은 곳."""
    return tmp_path / "uploads"


def _upload_body_and_grid(client):
    return client.post(
        f"{API_PREFIX}/uploads",
        files=[("files", ("hsr.bin", BODY_BYTES, "application/octet-stream")),
               ("files", ("LAT_HSR.npy", GRID_BYTES, "application/octet-stream"))],
        data={"fileKinds": ["본체", "기준 격자 파일"]},
        headers=auth(TOKEN_RES))


def test_본체는_저장_키_그대로_평평하게_놓인다(p2_client, tmp_path) -> None:
    """`974cf9f` 이 세운 규칙 — 「접수한 바이트를 저장 키 그대로 놓는다」."""
    r = _upload_body_and_grid(p2_client())
    assert r.status_code == 201, r.text
    body = r.json()
    upload_id = body["uploadId"]
    body_file = next(f for f in body["files"] if f["kind"] == "본체")

    expected = _root(tmp_path) / "uploads" / upload_id / body_file["fileId"]
    assert expected.is_file(), f"본체가 배치대로 놓이지 않았다: {expected}"
    assert expected.read_bytes() == BODY_BYTES


def test_기준_격자는_grid_아래_원래_이름으로_놓인다(p2_client, tmp_path) -> None:
    """**격자만 이름을 보존한다.**

    이름이 장식이 아니라 자료이기 때문이다 — 짝짓기(`§5.4.1` 가-2)와 축 판별 사다리 ④가
    파일명을 읽고, 격자 판독 자체가 확장자(`.npy`/`.nc`)로 갈린다. ULID 로 덮으면
    그 정보가 사라지고, 그 실패는 에러가 아니라 **「격자 없음」으로 위장**한다.
    """
    r = _upload_body_and_grid(p2_client())
    upload_id = r.json()["uploadId"]

    expected = _root(tmp_path) / "uploads" / upload_id / "grid" / "LAT_HSR.npy"
    assert expected.is_file(), f"격자가 grid/ 아래 이름 그대로 놓이지 않았다: {expected}"
    assert expected.read_bytes() == GRID_BYTES


def test_배치는_생성된_규약과_한_글자도_다르지_않다(p2_client, tmp_path) -> None:
    """**세 단위가 같은 규약을 쓰는지**를 시험이 본다 — 주석의 약속이 아니라 함수로."""
    r = _upload_body_and_grid(p2_client())
    body = r.json()
    upload_id = body["uploadId"]
    for f in body["files"]:
        key = storage_layout.storage_key(upload_id, file_id=f["fileId"],
                                         kind=f["kind"], file_name=f["fileName"])
        assert (_root(tmp_path) / key).is_file(), f"규약이 가리키는 자리에 바이트가 없다: {key}"


def test_격자와_본체가_같은_디렉터리에서_섞이지_않는다(p2_client, tmp_path) -> None:
    """종류가 **배치로 읽혀야** 한다 — 격자를 여는 마지막 소비자(D7)에는 원장이 없다."""
    r = _upload_body_and_grid(p2_client())
    upload_id = r.json()["uploadId"]
    target = _root(tmp_path) / "uploads" / upload_id
    flat = sorted(p.name for p in target.iterdir() if p.is_file())
    assert len(flat) == 1, f"본체 자리에 격자가 섞였다: {flat}"
    assert sorted(p.name for p in (target / "grid").iterdir()) == ["LAT_HSR.npy"]


# ══════════ 등록 전환 뒤의 배치 (`03-HANDOFF §4 #20` 계열 · 지도형 미리보기) ══════════
#
# ⚠ **이 계열이 전 시험 green 아래에서 존속했다.** 위 네 건은 전부 **등록 전** 배치만
# 봤고, 등록 전환은 저장 키를 그대로 승계해 바이트를 `uploads/{uploadId}/` 에 남겼다.
# 그리는 쪽(D7)에는 원장이 없어 **디렉터리가 곧 사실**이라, `datasetId` 로 오는 요청은
# 빈 자리를 보고 404 를 냈고 그 실패는 중계에서 **503 `RENDER_UNAVAILABLE`** 로 나왔다.
# 사용자에게 등록은 「데이터셋이 성립하는 사건」이므로 **자리도 데이터셋의 것**이어야 한다.
def _register(client, upload_id: str, *, name: str = "배치 시험 데이터셋"):
    return client.post(f"{API_PREFIX}/datasets", json={"uploadId": upload_id, "name": name},
                       headers=auth(TOKEN_RES))


def _worker_resolved_grid(sql, receipt) -> None:
    """**워커 자리를 시험이 대신한다** — 축이 정해진 뒤에야 격자 원장 행이 선다 (`〈66〉`).

    저장 키는 접수가 실제로 쓴 값과 같아야 한다 — 워커도 이벤트가 실은 그 키를 그대로 옮긴다.
    """
    upload_id = receipt["uploadId"]
    for f in receipt["files"]:
        if f["kind"] != "기준 격자 파일":
            continue
        key = storage_layout.storage_key(upload_id, file_id=f["fileId"], kind=f["kind"],
                                         file_name=f["fileName"])
        sql("""INSERT INTO d5_upload_file
                 (id, lab_id, upload_id, kind, file_name, byte_size, storage_key,
                  carries_lat, carries_lon)
               VALUES (:id, current_lab_id(), :u, '기준 격자 파일', :n, :b, :k, true, false)""",
            {"id": f["fileId"], "u": upload_id, "n": f["fileName"],
             "b": f["byteSize"], "k": key})


def test_등록_전환은_바이트를_데이터셋_자리로_모은다(p2_client, tmp_path, sql) -> None:
    """본체도 격자도 `uploads/{datasetId}/` 아래로 온다 — 규약 함수가 가리키는 자리다."""
    client = p2_client()
    receipt = _upload_body_and_grid(client).json()
    upload_id = receipt["uploadId"]
    _worker_resolved_grid(sql, receipt)
    r = _register(client, upload_id)
    assert r.status_code == 201, r.text
    dataset_id = r.json()["datasetId"]

    for f in receipt["files"]:
        key = storage_layout.storage_key(dataset_id, file_id=f["fileId"],
                                         kind=f["kind"], file_name=f["fileName"])
        assert (_root(tmp_path) / key).is_file(), f"등록 뒤 규약 자리에 바이트가 없다: {key}"

    old = _root(tmp_path) / "uploads" / upload_id
    if old.exists():
        assert not [p for p in old.rglob("*") if p.is_file()], \
            "업로드 자리에 바이트가 남았다 — 데이터셋 디렉터리가 갈라진다."


def test_등록_뒤_원장이_적은_저장_키가_실물을_가리킨다(p2_client, tmp_path, sql) -> None:
    """`d3_file.storage_key` 는 **바이트를 여는 유일한 좌표**다 — 실물과 어긋나면 red."""
    client = p2_client()
    receipt = _upload_body_and_grid(client).json()
    _worker_resolved_grid(sql, receipt)
    dataset_id = _register(client, receipt["uploadId"]).json()["datasetId"]

    rows = sql("SELECT id, storage_key FROM d3_file WHERE dataset_id = :d", {"d": dataset_id})
    assert len(rows) == 2, rows
    for row in rows:
        assert (_root(tmp_path) / row["storage_key"]).is_file(), \
            f"원장이 적은 자리에 바이트가 없다: {row['storage_key']}"
        assert row["storage_key"].startswith(f"uploads/{dataset_id}/"), row["storage_key"]


def test_등록_전_업로드의_배치는_그대로다(p2_client, tmp_path) -> None:
    """음성 — 등록하지 않은 업로드(S-08)는 **업로드 자리에서** 그려진다."""
    client = p2_client()
    receipt = _upload_body_and_grid(client).json()
    upload_id = receipt["uploadId"]
    for f in receipt["files"]:
        key = storage_layout.storage_key(upload_id, file_id=f["fileId"],
                                         kind=f["kind"], file_name=f["fileName"])
        assert (_root(tmp_path) / key).is_file(), key


def test_후주입_격자는_데이터셋_grid_아래로_온다(p2_client, tmp_path, sql) -> None:
    """격자 후주입도 같은 규칙이다 — 본체와 격자가 **한 디렉터리**에 모여야 D7 이 짝을 본다.

    ⚠ 워커 자리를 시험이 대신한다 — 축이 확정된 원장 행을 만드는 것이 워커의 일이다.
    """
    client = p2_client()
    body_receipt = client.post(
        f"{API_PREFIX}/uploads",
        files=[("files", ("hsr.bin", BODY_BYTES, "application/octet-stream"))],
        data={"fileKinds": ["본체"]}, headers=auth(TOKEN_RES)).json()
    dataset_id = _register(client, body_receipt["uploadId"]).json()["datasetId"]

    grid_receipt = client.post(
        f"{API_PREFIX}/uploads",
        files=[("files", ("LON_HSR.npy", GRID_BYTES, "application/octet-stream"))],
        data={"fileKinds": ["기준 격자 파일"]}, headers=auth(TOKEN_RES)).json()
    grid_upload = grid_receipt["uploadId"]
    _worker_resolved_grid(sql, grid_receipt)

    r = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                    json={"uploadId": grid_upload}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text

    target = _root(tmp_path) / "uploads" / dataset_id
    assert (target / "grid" / "LON_HSR.npy").is_file(), \
        "후주입 격자가 데이터셋의 grid/ 아래로 오지 않았다 — 렌더러가 짝을 못 본다."
    assert len([p for p in target.iterdir() if p.is_file()]) == 1, "본체 자리에 격자가 섞였다."
