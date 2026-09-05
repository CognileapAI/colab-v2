"""다운로드 집행 — `downloadDataset` · `downloadDatasetFile` · `getDownloadBytes` (`PLAN-SoT §9 〈339〉-(다)`).

오라클 열하나. 티켓 발급이 곧 이력이고(`d8_download` — 파일 단위는 `file_id`, 묶음은 NULL),
바이트는 서명 티켓만으로 받되 **바이트 시점에 판정을 다시 한다**(경계 · `body_access`).
만료는 410, 위조·회수·경계 밖은 전부 404 — 존재를 흘리지 않는다 (P-9·P-10).

시험 간 간섭을 줄이려고 **자기가 만든 데이터셋 id 로만 필터한다** — 같은 시험 DB 를 다른
세션이 동시에 쓴다. 전역 count 를 단언하지 않는다.


⭑ **⟨병합 창 8-a⟩ `tests/test_dataset_download.py` 를 걷고 그 못을 여기로 옮겼다.**
그 파일은 `main` 줄기의 **302 ＋ `Location` ＋ `?deliver=1`** 판(`routes/catalog.py`)을 재던 것이고,
그 판은 Ted 판정 `〈334〉`-㉳-⑥(「다운로드 = 200 티켓 ＋ 바이트 op」)과 병합된 계약(200 `DownloadTicket`)
으로 **사라졌다.** ⛔ **덮지 않고 옮겼다** — 걷은 시험 하나하나가 여기 어디로 갔는지 적는다:

| 걷은 시험 (`test_dataset_download.py`) | 대신 서는 자리 (이 파일) |
|---|---|
| `test_a_permitted_row_download_actually_opens` | `test_getDownloadBytes_streams_the_original_bytes_of_a_single_file` |
| `test_pieces_come_bundled_in_one_archive` | `test_getDownloadBytes_bundle_is_a_zip_named_by_relative_path_and_grid_dir` |
| `test_the_bundle_carries_the_reference_grid_files_too` | 같은 묶음 시험(격자 디렉터리 항목을 함께 단언한다) |
| `test_missing_bytes_do_not_become_an_empty_success` | `test_bytes_missing_from_storage_is_404_for_a_single_file` |
| `test_a_locked_row_download_is_refused` · `test_a_locked_rows_grid_file_is_refused_too` | `test_a_locked_dataset_without_a_grant_is_403_for_both_ticket_ops` |
| `test_a_cross_lab_row_download_is_not_found` | `test_another_labs_dataset_is_404_for_the_ticket_ops` |
| `test_download_without_a_token_is_unauthorized` | `test_ticket_ops_require_a_subject_but_the_bytes_op_does_not` |
| `test_the_bundle_is_streamed_and_never_fully_buffered` · `test_the_download_route_never_calls_a_full_buffer_path` | `test_getDownloadBytes_bundle_…` ＋ `zip_stream` 구조(`routes/download.py`) |
| `test_the_deliver_mark_is_not_a_credential` | **대응 없음 — 잴 대상이 없어졌다.** `?deliver=1` 표식은 302 판의 것이고 티켓 판에는 그 개념이 없다(티켓 자체가 자격이다). |

⚠ **원문은 `git show 5a9d9f8:services/core-api/tests/test_dataset_download.py` 에 있다.**
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import pathlib
import urllib.parse
import zipfile

from conftest import ACC_A_RES, DS_A1, DS_A2, LAB_A, TOKEN_B, TOKEN_RES, auth
from test_upload_transfers import FakeS3

from colab_core.app.main import API_PREFIX
from colab_core.kernel.auth import Subject
from colab_core.kernel.config import Settings
from colab_core.kernel.ids import Ulid
from colab_core.kernel.s3 import S3Error
from colab_core.kernel.storage_backends import S3UploadStorage

SECRET = "download-ticket-test-secret"
BODY_A = b"lat,lon,rain\n37.5,127.0,3.2\n"
BODY_B = b"\x89HDF\r\n\x1a\n" + b"\x00" * 32
GRID = "기준 격자 파일"


def _client(p2_client, **kw):
    return p2_client(session_secret=SECRET, **kw)


def _dataset(client, *, name="다운로드 시험", paths=("기상/a.csv", "기상/하위/b.nc"),
             token=TOKEN_RES) -> tuple[str, dict]:
    """본체 둘을 폴더 경로와 함께 올려 등록한다. (datasetId, {fileName: UploadFileRef})."""
    files = [("files", ("a.csv", BODY_A, "text/csv")),
             ("files", ("b.nc", BODY_B, "application/octet-stream"))]
    r = client.post(f"{API_PREFIX}/uploads", files=files, data={"relativePaths": list(paths)},
                    headers=auth(token))
    assert r.status_code == 201, r.text
    receipt = r.json()
    r = client.post(f"{API_PREFIX}/datasets", json={"uploadId": receipt["uploadId"], "name": name},
                    headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()["datasetId"], {f["fileName"]: f for f in receipt["files"]}


def _ticket(client, dataset_id: str, file_id: str | None = None, token=TOKEN_RES):
    path = (f"{API_PREFIX}/datasets/{dataset_id}/download" if file_id is None
            else f"{API_PREFIX}/datasets/{dataset_id}/files/{file_id}/download")
    return client.get(path, headers=auth(token))


def _downloads(sql, dataset_id: str) -> list[dict]:
    return sql("SELECT account_id, dataset_id, file_id FROM d8_download"
               " WHERE dataset_id = :d ORDER BY downloaded_at, id", {"d": dataset_id})


def _disposition(name: str) -> str:
    return "attachment; filename*=UTF-8''" + urllib.parse.quote(name, safe="")


# ═══════════════════════ 발급 = 이력 (`d8_download`) ═══════════════════════
def test_downloadDatasetFile_records_a_download_row_with_the_file_id(p2_client, sql) -> None:
    """① 파일 단위 티켓 → `d8_download` 한 행, `file_id` 가 그 조각. 주체·데이터셋도 그대로."""
    client = _client(p2_client)
    dataset_id, files = _dataset(client)
    file_id = files["a.csv"]["fileId"]
    assert _downloads(sql, dataset_id) == []

    r = _ticket(client, dataset_id, file_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"url", "expiresAt", "fileName", "byteSize", "scope"}
    assert body["scope"] == "파일"
    assert body["fileName"] == "a.csv"
    assert body["byteSize"] == len(BODY_A)
    assert body["url"].startswith(f"{API_PREFIX}/downloads/"), body["url"]
    rows = _downloads(sql, dataset_id)
    assert len(rows) == 1
    assert rows[0]["account_id"].strip() == ACC_A_RES
    assert rows[0]["dataset_id"].strip() == dataset_id
    assert (rows[0]["file_id"] or "").strip() == file_id


def test_downloadDataset_records_a_download_row_with_file_id_null(p2_client, sql) -> None:
    """② 묶음 티켓 → `file_id` NULL(= 데이터셋 묶음). 이름은 `<데이터셋 이름>.zip`,
    크기는 **null** — zip 을 만들어 봐야 아는 값을 지어내지 않는다 (계약 산문)."""
    client = _client(p2_client)
    dataset_id, _files = _dataset(client, name="묶음 시험")

    r = _ticket(client, dataset_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scope"] == "묶음"
    assert body["fileName"] == "묶음 시험.zip"
    assert body["byteSize"] is None
    expires = dt.datetime.fromisoformat(body["expiresAt"].replace("Z", "+00:00"))
    ahead = expires - dt.datetime.now(dt.timezone.utc)
    assert dt.timedelta(minutes=9) < ahead <= dt.timedelta(minutes=10), ahead
    rows = _downloads(sql, dataset_id)
    assert len(rows) == 1 and rows[0]["file_id"] is None


# ═══════════════════════════ 바이트 (`getDownloadBytes`) ═══════════════════
def test_getDownloadBytes_streams_the_original_bytes_of_a_single_file(p2_client) -> None:
    """③ 단일 파일 — 원본과 **같은 바이트**. Bearer 없이, 티켓만으로.
    `Content-Disposition` 은 계약 형태 그대로, `Content-Length` 는 원장의 크기다."""
    client = _client(p2_client)
    dataset_id, files = _dataset(client)
    url = _ticket(client, dataset_id, files["b.nc"]["fileId"]).json()["url"]

    r = client.get(url)   # 인증 헤더 없음 — `security: []`
    assert r.status_code == 200, r.text
    assert hashlib.sha256(r.content).hexdigest() == hashlib.sha256(BODY_B).hexdigest()
    assert r.headers["content-type"].startswith("application/octet-stream")
    assert r.headers["content-disposition"] == _disposition("b.nc")
    assert r.headers["content-length"] == str(len(BODY_B))


def test_getDownloadBytes_bundle_is_a_zip_named_by_relative_path_and_grid_dir(
        p2_client, sql, tmp_path) -> None:
    """④ 묶음 zip — 엔트리 이름은 `relative_path`(없으면 `file_name`), 격자는 `grid/<이름>`.
    저장은 `ZIP_STORED` 다(압축 없음 — 스트리밍이 메모리 상수인 이유)."""
    client = _client(p2_client)
    # 본체 둘(폴더 경로) + 워커가 축을 확정한 격자 하나 — 격자는 등록 전환이 원장에서 그대로 옮긴다.
    files = [("files", ("a.csv", BODY_A, "text/csv")),
             ("files", ("b.nc", BODY_B, "application/octet-stream"))]
    r = client.post(f"{API_PREFIX}/uploads", files=files,
                    data={"relativePaths": ["기상/a.csv", "기상/하위/b.nc"]}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    upload_id = r.json()["uploadId"]
    grid_id = str(Ulid.generate())
    sql("INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, byte_size,"
        "  storage_key, carries_lat, carries_lon)"
        " VALUES (:i, :l, :u, :k, 'g.nc', 8, :s, true, true)",
        {"i": grid_id, "l": LAB_A, "u": upload_id, "k": GRID, "s": f"uploads/{upload_id}/grid/g.nc"})
    r = client.post(f"{API_PREFIX}/datasets", json={"uploadId": upload_id, "name": "격자 묶음"},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    dataset_id = r.json()["datasetId"]
    # 격자 바이트는 원장이 아니라 저장소가 안다 — 데이터셋 자리에 심는다 (`layout.json` 키 그대로).
    grid_path = tmp_path / "uploads" / "uploads" / dataset_id / "grid" / "g.nc"
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    grid_path.write_bytes(b"GRIDGRID")

    ticket = _ticket(client, dataset_id)
    assert ticket.status_code == 200, ticket.text
    r = client.get(ticket.json()["url"])
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/zip")
    assert r.headers["content-disposition"] == _disposition("격자 묶음.zip")

    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert zf.testzip() is None
        names = {i.filename: i for i in zf.infolist()}
        assert set(names) == {"기상/a.csv", "기상/하위/b.nc", "grid/g.nc"}
        assert zf.read("기상/a.csv") == BODY_A
        assert zf.read("기상/하위/b.nc") == BODY_B
        assert zf.read("grid/g.nc") == b"GRIDGRID"
        assert all(i.compress_type == zipfile.ZIP_STORED for i in names.values())


def test_bundle_entry_name_collisions_get_a_file_id_suffix(p2_client) -> None:
    """같은 이름의 본체 둘(경로 없음) — 두 번째는 `<stem>.<fileId 앞 8자>.<ext>` 로 갈라진다.
    zip 안에서 이름이 겹치면 한 조각이 조용히 사라진다."""
    client = _client(p2_client)
    files = [("files", ("same.csv", BODY_A, "text/csv")),
             ("files", ("same.csv", BODY_B, "text/csv"))]
    r = client.post(f"{API_PREFIX}/uploads", files=files, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    receipt = r.json()
    r = client.post(f"{API_PREFIX}/datasets", json={"uploadId": receipt["uploadId"], "name": "중복"},
                    headers=auth(TOKEN_RES))
    dataset_id = r.json()["datasetId"]
    url = _ticket(client, dataset_id).json()["url"]
    with zipfile.ZipFile(io.BytesIO(client.get(url).content)) as zf:
        names = sorted(zf.namelist())
    assert len(names) == 2 and "same.csv" in names
    other = next(n for n in names if n != "same.csv")
    ids = {f["fileId"] for f in receipt["files"]}
    assert other.startswith("same.") and other.endswith(".csv")
    assert any(other == f"same.{i[:8]}.csv" for i in ids), (other, ids)


# ═════════════════════════════ 만료 · 위조 ══════════════════════════════════
def test_an_expired_ticket_is_410_gone(p2_client) -> None:
    """⑤ 수명이 지났으면 410 — 「있었는데 창이 닫혔다」. 시계는 발급기의 `now` 로 심는다."""
    client = _client(p2_client)
    dataset_id, _ = _dataset(client)
    signer = client.app.state.download_tickets
    stale = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=11)
    issued = signer.issue(dataset_id=Ulid(dataset_id), file_id=None,
                          subject=Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A)),
                          now=stale)
    r = client.get(f"{API_PREFIX}/downloads/{issued.ticket}")
    assert r.status_code == 410, r.text
    assert r.json()["code"] == "GONE"


def test_a_tampered_ticket_is_404_not_401(p2_client) -> None:
    """⑥ 서명이 어긋나면 404 — 401 도 400 도 아니다. 존재를 흘리지 않는다."""
    client = _client(p2_client)
    dataset_id, _ = _dataset(client)
    url = _ticket(client, dataset_id).json()["url"]
    ticket = url.rsplit("/", 1)[1]
    assert client.get(url).status_code == 200      # 대조 — 원본 티켓은 산다

    prefix, payload, mac = ticket.split(".")
    flipped = ("A" if mac[-1] != "A" else "B")
    assert client.get(f"{API_PREFIX}/downloads/{prefix}.{payload}.{mac[:-1]}{flipped}").status_code == 404
    # 본문을 바꿔도(다른 데이터셋을 가리키게) 서명이 안 맞는다
    assert client.get(f"{API_PREFIX}/downloads/{prefix}.{payload[:-2]}AA.{mac}").status_code == 404
    assert client.get(f"{API_PREFIX}/downloads/not-a-ticket").status_code == 404
    assert client.get(f"{API_PREFIX}/downloads/{prefix}..").status_code == 404


# ═════════════════════════ 잠김 · 회수 · 경계 ══════════════════════════════
def test_a_locked_dataset_without_a_grant_is_403_for_both_ticket_ops(p2_client, sql) -> None:
    """⑦ 잠긴 데이터셋(DSA2)에 허용 목록 밖 주체 — 본체를 주는 op 이라 403 (P-34).
    상세(`getDataset`)는 200 이지만 바이트는 아니다. 이력도 남지 않는다."""
    client = _client(p2_client)
    before = _downloads(sql, DS_A2)
    r = _ticket(client, DS_A2)
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "FORBIDDEN"
    r = _ticket(client, DS_A2, "00000000000000000000000FA3")
    assert r.status_code == 403, r.text
    assert _downloads(sql, DS_A2) == before


def test_access_revoked_after_issue_makes_the_bytes_404(p2_client, sql) -> None:
    """⑧ 발급 뒤 잠기면 바이트는 404 — 티켓이 서명은 맞아도 **바이트 시점에 다시 판정**한다.
    RLS `body_access` 가 행을 지우므로 라우트가 잠금을 따로 묻지 않아도 그렇다."""
    client = _client(p2_client)
    dataset_id, files = _dataset(client)
    file_url = _ticket(client, dataset_id, files["a.csv"]["fileId"]).json()["url"]
    bundle_url = _ticket(client, dataset_id).json()["url"]
    assert client.get(file_url).status_code == 200      # 대조 — 잠그기 전에는 산다
    sql("INSERT INTO d2_dataset_access (dataset_id, lab_id, state)"
        " VALUES (:d, current_lab_id(), '잠김')", {"d": dataset_id})
    try:
        assert client.get(file_url).status_code == 404
        assert client.get(bundle_url).status_code == 404
    finally:
        sql("DELETE FROM d2_dataset_access WHERE dataset_id = :d", {"d": dataset_id})


def test_another_labs_dataset_is_404_for_the_ticket_ops(p2_client, sql) -> None:
    """⑩ 다른 연구실의 데이터셋은 **없는 것**이다 — 403 이 아니라 404 (P-9·P-10)."""
    client = _client(p2_client)
    before = _downloads(sql, DS_A1)
    assert _ticket(client, DS_A1, token=TOKEN_B).status_code == 404
    assert _ticket(client, DS_A1, "00000000000000000000000FA1", token=TOKEN_B).status_code == 404
    assert _downloads(sql, DS_A1) == before


def test_a_file_of_another_dataset_is_404(p2_client) -> None:
    """파일 단위 — `fileId` 가 그 데이터셋의 조각이 아니면 404. FK 는 이것을 못 막는다."""
    client = _client(p2_client)
    ds1, files1 = _dataset(client, name="첫째")
    ds2, _ = _dataset(client, name="둘째")
    assert _ticket(client, ds2, files1["a.csv"]["fileId"]).status_code == 404


# ═════════════════════════ 서명 비밀값 없음 = 500 ═══════════════════════════
def test_without_a_session_secret_the_download_ops_are_500(p2_client) -> None:
    """⑨ 비밀값이 없으면 서명할 수 없다 — **조용한 기본값을 두지 않는다.** 발급도 바이트도
    500 + 명시 메시지. 다른 op 은 그대로 돈다(`createUpload`·`createDataset` 이 위에서 그랬다)."""
    client = p2_client()   # session_secret=None
    dataset_id, files = _dataset(client)
    for path in (f"/datasets/{dataset_id}/download",
                 f"/datasets/{dataset_id}/files/{files['a.csv']['fileId']}/download"):
        r = client.get(f"{API_PREFIX}{path}", headers=auth(TOKEN_RES))
        assert r.status_code == 500, r.text
        assert r.json()["code"] == "DOWNLOAD_UNAVAILABLE"
        assert "COLAB_CORE_SESSION_SECRET" in r.json()["message"]
    r = client.get(f"{API_PREFIX}/downloads/anything")
    assert r.status_code == 500 and r.json()["code"] == "DOWNLOAD_UNAVAILABLE"


def test_ticket_ops_require_a_subject_but_the_bytes_op_does_not(p2_client) -> None:
    """발급 둘은 Bearer 필수(401), 바이트는 `security: []` — 티켓이 곧 자격이다."""
    client = _client(p2_client)
    dataset_id, files = _dataset(client)
    assert client.get(f"{API_PREFIX}/datasets/{dataset_id}/download").status_code == 401
    assert client.get(f"{API_PREFIX}/datasets/{dataset_id}/files/{files['a.csv']['fileId']}/download"
                      ).status_code == 401


# ═══════════════════════════════ s3 모드 ═══════════════════════════════════
class FakeS3Download(FakeS3):
    """전송 가짜에 **저장 백엔드 + 다운로드 표면**을 얹는다 — 바이트를 기억한다."""

    def __init__(self) -> None:
        super().__init__()
        self.blobs: dict[str, bytes] = {}
        self.presigned: list[tuple[str, dict, int]] = []

    def put_object(self, key, payload, content_type="application/octet-stream"):
        self.blobs[key] = bytes(payload)
        self.objects[key] = len(payload)
        return '"etag"'

    def copy_object(self, src_key, dst_key):
        if src_key not in self.blobs:
            raise S3Error(404, "NoSuchKey", src_key)
        self.blobs[dst_key] = self.blobs[src_key]
        self.objects[dst_key] = self.objects[src_key]

    def delete_objects(self, keys):
        for k in keys:
            self.blobs.pop(k, None)
        super().delete_objects(keys)

    def presign_get(self, key, *, query=None, expires, now):
        self.presigned.append((key, dict(query or {}), expires))
        q = "&".join(f"{k}={urllib.parse.quote(v, safe='')}" for k, v in (query or {}).items())
        return f"https://fake.s3/{key}?{q}&X-Amz-Expires={expires}&X-Amz-Signature=sig"

    def get_object_stream(self, key):
        if key not in self.blobs:
            raise S3Error(404, "NoSuchKey", key)
        data = self.blobs[key]
        return iter([data[:5], data[5:]])


def _s3_client(p2_client, fake: FakeS3Download):
    client = _client(p2_client)
    app = client.app
    app.state.settings = Settings(**{**app.state.settings.__dict__, "storage_mode": "s3",
                                     "s3_bucket": "test-bucket", "s3_region": "ap-northeast-2"})
    app.state.upload_storage = S3UploadStorage(fake)   # 업로드·등록·다운로드가 같은 저장소를 본다
    return client


def test_s3_mode_file_ticket_is_an_absolute_presigned_get(p2_client, sql) -> None:
    """⑪-가 s3 모드 파일 단위 = 프리사인드 GET **절대 URL** — 바이트가 core 를 안 거친다.
    키와 `response-content-disposition`(저장 이름)이 실리고, 수명은 티켓 TTL 이다. 이력은 그대로 쌓인다."""
    fake = FakeS3Download()
    client = _s3_client(p2_client, fake)
    dataset_id, files = _dataset(client)
    r = _ticket(client, dataset_id, files["a.csv"]["fileId"])
    assert r.status_code == 200, r.text
    body = r.json()
    key = f"uploads/{dataset_id}/{files['a.csv']['fileId']}"
    assert body["url"].startswith(f"https://fake.s3/{key}?"), body["url"]
    assert body["scope"] == "파일" and body["fileName"] == "a.csv"
    assert len(fake.presigned) == 1
    p_key, p_query, p_expires = fake.presigned[0]
    assert p_key == key and p_expires == 600
    assert p_query["response-content-disposition"] == _disposition("a.csv")
    assert fake.blobs[key] == BODY_A                      # 등록 전환이 데이터셋 자리로 옮겼다
    assert len(_downloads(sql, dataset_id)) == 1


def test_s3_mode_bundle_is_relative_and_streams_each_object_into_the_zip(p2_client) -> None:
    """⑪-나 s3 모드 묶음 = 상대 경로 티켓, core-api 가 S3 GET 을 **`ZIP_STORED` 로 흘려보낸다**
    (「컨트롤 플레인만」의 예외 — `〈339〉-(다)`)."""
    fake = FakeS3Download()
    client = _s3_client(p2_client, fake)
    dataset_id, _ = _dataset(client, name="s3 묶음")
    r = _ticket(client, dataset_id)
    assert r.status_code == 200, r.text
    assert r.json()["url"].startswith(f"{API_PREFIX}/downloads/")
    assert fake.presigned == []
    r = client.get(r.json()["url"])
    assert r.status_code == 200, r.text
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert zf.testzip() is None
        assert zf.read("기상/a.csv") == BODY_A
        assert zf.read("기상/하위/b.nc") == BODY_B
        assert sorted(zf.namelist()) == ["기상/a.csv", "기상/하위/b.nc"]


def test_bytes_missing_from_storage_is_404_for_a_single_file(p2_client, tmp_path) -> None:
    """원장은 있는데 바이트가 없다 — 500 이 아니라 404(「없다」). 스트림을 열기 **전에** 판정한다."""
    client = _client(p2_client)
    dataset_id, files = _dataset(client)
    key = pathlib.Path(tmp_path / "uploads" / "uploads" / dataset_id / files["a.csv"]["fileId"])
    assert key.is_file()
    key.unlink()
    url = _ticket(client, dataset_id, files["a.csv"]["fileId"]).json()["url"]
    assert client.get(url).status_code == 404
