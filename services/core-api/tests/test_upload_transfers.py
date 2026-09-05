"""오라클 — 프리사인드 전송 9 op (`routes/upload_transfers.py` · 동결 해제 8차 `〈338〉`).

S3 는 가짜 클라이언트를 앱 상태에 꽂아 검증한다 — 실전 S3 왕복은 `ops/s3_smoke.py` 와
동결 해제 증거의 실호출이 한다. 핵심 오라클 다섯:
① local 모드에서 아홉 전부 501 (FE 폴백 신호) ② 완결 전에는 d5_upload 도
upload.accepted 도 없다 ③ 완결은 실측(ListParts·Head)이 전부 확인된 뒤에만, 그때
같은 ULID 로 접수가 선다 ④ 재개 정보(uploadedParts)는 S3 실측이다 ⑤ 만료 전송의
지연 정리는 원장이 아는 것만 지운다.
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.kernel.config import Settings
from colab_core.kernel.s3 import Part, S3Error


class FakeS3:
    """전송 라우트가 부르는 표면만 흉내 낸다. 파트의 정본 노릇을 한다."""

    def __init__(self) -> None:
        self.parts: dict[str, list[Part]] = {}      # ref -> 올라간 파트
        self.objects: dict[str, int] = {}           # key -> 크기
        self.aborted: list[str] = []
        self.deleted: list[str] = []
        self._seq = 0

    # 라우트 표면
    def url_ttl(self, configured, now):
        return configured

    def presign_put(self, key, *, query=None, expires, now):
        q = "&".join(f"{k}={v}" for k, v in (query or {}).items())
        return f"https://fake/{key}" + (f"?{q}" if q else "")

    def create_multipart_upload(self, key, content_type=None):
        self._seq += 1
        ref = f"mp-{self._seq}"
        self.parts[ref] = []
        return ref

    def list_parts(self, key, ref):
        if ref not in self.parts:
            raise S3Error(404, "NoSuchUpload", ref)
        return list(self.parts[ref])

    def complete_multipart_upload(self, key, ref, parts):
        self.objects[key] = sum(p.size for p in parts)
        del self.parts[ref]
        return '"etag"'

    def abort_multipart_upload(self, key, ref):
        if ref not in self.parts:
            raise S3Error(404, "NoSuchUpload", ref)
        del self.parts[ref]
        self.aborted.append(ref)

    def head_object(self, key):
        if key not in self.objects:
            raise S3Error(404, "NoSuchKey", key)
        return self.objects[key], '"etag"'

    def delete_objects(self, keys):
        for k in keys:
            self.objects.pop(k, None)
            self.deleted.append(k)


class FakeStorage:
    """저장 Port(`ports/storage.py`)의 가짜 — **등록 전환이 부르는 `relocate` 가 여기 있다.**

    ⚠ 이걸 안 꽂으면 s3 모드에서 `POST /datasets` 가 **진짜 S3** 를 두드려 500 이 된다
      (`routes/ingestion.py:458` → `_storage()` 가 실제 `S3Client` 를 만든다).
      전송 라우트의 가짜(`upload_transfer_s3`)와 **다른 객체**라 둘 다 꽂아야 한다.
    """

    def __init__(self, fake: FakeS3) -> None:
        self.s3 = fake
        self.relocated: list[tuple[str, str]] = []

    def relocate(self, *, files, new_keys) -> None:
        for f in files:
            new_key = new_keys[f.file_id]
            if not f.storage_key or f.storage_key == new_key:
                continue
            size = self.s3.objects.pop(f.storage_key, None)
            if size is None:      # 원본이 이미 없으면 건너뛴다 — Port 규약 그대로
                continue
            self.s3.objects[new_key] = size
            self.relocated.append((f.storage_key, new_key))


def s3_client(p2_client_factory, fake: FakeS3):
    client = p2_client_factory()
    app = client.app
    settings = app.state.settings
    app.state.settings = Settings(**{**settings.__dict__,
                                     "storage_mode": "s3",
                                     "s3_bucket": "test-bucket",
                                     "s3_region": "ap-northeast-2"})
    app.state.upload_transfer_s3 = fake
    app.state.upload_storage = FakeStorage(fake)
    return client


def _initiate(client, files, token=TOKEN_RES, label="시험 묶음"):
    return client.post(f"{API_PREFIX}/uploads/transfers",
                       json={"sourceLabel": label, "files": files},
                       headers=auth(token))


SMALL = {"fileName": "작은.nc", "byteSize": 1024}
BIG = {"fileName": "큰.nc", "byteSize": 20 * 1024 * 1024}


# ═══════════════════════════ local 모드 = 501 ═══════════════════════════════
def test_local_mode_answers_501_everywhere(p2_client) -> None:
    """저장 모드 local 에서 아홉 전부 501 — FE 가 form-data 경로로 폴백하는 신호다."""
    client = p2_client()
    u = "01JXXXXXXXXXXXXXXXXXXXXXX0"
    calls = [
        ("post", "/uploads/transfers", {"json": {"files": [SMALL]}}),
        ("get", "/uploads/transfers/incomplete", {}),
        ("get", f"/uploads/transfers/{u}", {}),
        ("delete", f"/uploads/transfers/{u}", {}),
        ("post", f"/uploads/transfers/{u}/put-urls", {"json": {"fileIds": [u]}}),
        ("post", f"/uploads/transfers/{u}/files/{u}/multipart", {}),
        ("post", f"/uploads/transfers/{u}/files/{u}/part-urls", {"json": {"partNumbers": [1]}}),
        ("post", f"/uploads/transfers/{u}/files/{u}/complete", {}),
        ("post", f"/uploads/transfers/{u}/complete", {}),
    ]
    for method, path, kw in calls:
        r = getattr(client, method)(f"{API_PREFIX}{path}", headers=auth(TOKEN_RES), **kw)
        assert r.status_code == 501, (path, r.status_code, r.text)


# ═══════════════════════════════ 계획 ═══════════════════════════════════════
def test_initiate_plans_strategy_and_preserves_relative_path(p2_client) -> None:
    client = s3_client(p2_client, FakeS3())
    r = _initiate(client, [
        {**SMALL, "relativePath": "기상/작은.nc"},
        {**BIG, "kind": "본체"},
    ])
    assert r.status_code == 201, r.text
    body = r.json()
    small, big = body["files"]
    assert small["strategy"] == "단일" and small["partSize"] is None
    assert small["relativePath"] == "기상/작은.nc"
    assert big["strategy"] == "멀티파트" and big["partSize"] == 8 * 1024 * 1024
    assert big["partCount"] == 3
    assert body["rejected"] == []


def test_initiate_rejects_path_in_file_name(p2_client) -> None:
    """경로는 relativePath 로만 — fileName 에 '/' 가 오면 사유와 함께 거절된다."""
    client = s3_client(p2_client, FakeS3())
    r = _initiate(client, [{"fileName": "폴더/속.nc", "byteSize": 10}, SMALL])
    assert r.status_code == 201
    assert len(r.json()["rejected"]) == 1
    assert "relativePath" in r.json()["rejected"][0]["reason"]


def test_rejection_reason_names_which_field_failed(p2_client) -> None:
    """거부 사유가 `fileName` 실패와 `relativePath` 실패를 **가른다**.

    둘을 한 `try` 로 묶어 「이름을 정규화할 수 없다」로 뭉개면, 폴더 경로가 문제인데
    화면은 「이름」이라고 답한다 — 사람이 파일 이름을 고치며 시간을 쓴다.
    이 사유는 FE 가 **그대로 화면에 올리는 문장**이다.
    """
    client = s3_client(p2_client, FakeS3())
    r = _initiate(client, [
        {"fileName": "..", "byteSize": 10},                       # 이름이 정규화 불가
        {"fileName": "좋은.nc", "byteSize": 10, "relativePath": ".."},  # 경로가 정규화 불가
        SMALL,                                                    # 성한 것 하나 — 전체 400 을 피한다
    ])
    assert r.status_code == 201, r.text
    reasons = [x["reason"] for x in r.json()["rejected"]]
    assert len(reasons) == 2, reasons
    assert "fileName" in reasons[0], reasons
    assert "relativePath" in reasons[1], reasons
    assert reasons[0] != reasons[1], "두 실패가 같은 문장으로 답하면 가른 것이 아니다"


def test_no_upload_row_and_no_event_before_complete(p2_client, sql) -> None:
    """완결 전에는 d5_upload 도 upload.accepted 도 없다 — 접수는 완결의 효과다."""
    client = s3_client(p2_client, FakeS3())
    upload_id = _initiate(client, [SMALL]).json()["uploadId"]
    assert sql("SELECT 1 FROM d5_upload WHERE id = :u", {"u": upload_id}) == []
    assert sql("SELECT 1 FROM d5_pipeline_event WHERE upload_id = :u", {"u": upload_id}) == []
    assert len(sql("SELECT 1 FROM d5_upload_transfer WHERE id = :u", {"u": upload_id})) == 1


# ═══════════════════════ 실측 검증 → 완결 = 접수 ════════════════════════════
def _finish_single(client, fake, upload_id, file_):
    fake.objects[_storage_key_of(client, upload_id, file_)] = file_["byteSize"]
    r = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/files/{file_['fileId']}/complete",
                    headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def _storage_key_of(client, upload_id, file_):
    return f"uploads/{upload_id}/{file_['fileId']}"


def test_complete_verifies_size_and_then_accepts_with_same_ulid(p2_client, sql) -> None:
    fake = FakeS3()
    client = s3_client(p2_client, fake)
    plan = _initiate(client, [{**SMALL, "relativePath": "기상/작은.nc"}]).json()
    upload_id, f = plan["uploadId"], plan["files"][0]

    # 크기 불일치 → 실패로 남고 완결은 409
    fake.objects[_storage_key_of(client, upload_id, f)] = 7
    r = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/files/{f['fileId']}/complete",
                    headers=auth(TOKEN_RES))
    assert r.json()["outcome"] == "실패" and "크기 불일치" in r.json()["detail"]
    r = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/complete", headers=auth(TOKEN_RES))
    assert r.status_code == 409

    # 실측 일치 → 올라감 → 완결 = 같은 ULID 로 d5_upload + accepted 1건
    out = _finish_single(client, fake, upload_id, f)
    assert out["outcome"] == "올라감"
    r = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/complete", headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    assert r.json()["uploadId"] == upload_id
    assert len(sql("SELECT 1 FROM d5_upload WHERE id = :u", {"u": upload_id})) == 1
    rows = sql("SELECT relative_path FROM d5_upload_file WHERE upload_id = :u", {"u": upload_id})
    assert [row["relative_path"] for row in rows] == ["기상/작은.nc"]
    events = sql("SELECT event_type FROM d5_pipeline_event WHERE upload_id = :u", {"u": upload_id})
    assert [e["event_type"] for e in events] == ["upload.accepted"]
    # 두 번째 완결은 409 — 접수는 한 번이다
    r = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/complete", headers=auth(TOKEN_RES))
    assert r.status_code == 409


def test_multipart_resume_reads_parts_from_s3(p2_client) -> None:
    """uploadedParts 는 S3 실측이다 — DB 를 믿으면 이미 올린 파트를 다시 올린다."""
    fake = FakeS3()
    client = s3_client(p2_client, fake)
    plan = _initiate(client, [BIG]).json()
    upload_id, f = plan["uploadId"], plan["files"][0]
    r = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/files/{f['fileId']}/multipart",
                    headers=auth(TOKEN_RES))
    assert r.status_code == 200 and r.json()["partCount"] == 3
    ref = next(iter(fake.parts))
    fake.parts[ref] = [Part(number=1, etag='"a"', size=8 * 1024 * 1024)]
    r = client.get(f"{API_PREFIX}/uploads/transfers/{upload_id}", headers=auth(TOKEN_RES))
    assert r.json()["files"][0]["uploadedParts"] == [1]
    # 파트 URL 발급은 쿼리에 partNumber·uploadId 를 싣는다
    r = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/files/{f['fileId']}/part-urls",
                    json={"partNumbers": [2, 3]}, headers=auth(TOKEN_RES))
    urls = r.json()["urls"]
    assert [u["partNumber"] for u in urls] == [2, 3]
    assert f"uploadId={ref}" in urls[0]["url"]


def test_incomplete_list_and_abort_cleans_s3(p2_client) -> None:
    fake = FakeS3()
    client = s3_client(p2_client, fake)
    plan = _initiate(client, [SMALL, BIG]).json()
    upload_id = plan["uploadId"]
    small, big = plan["files"]
    client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/files/{big['fileId']}/multipart",
                headers=auth(TOKEN_RES))
    _finish_single(client, fake, upload_id, small)

    r = client.get(f"{API_PREFIX}/uploads/transfers/incomplete", headers=auth(TOKEN_RES))
    mine = [i for i in r.json()["items"] if i["uploadId"] == upload_id]  # DB 는 시험 간 공유다
    assert len(mine) == 1
    assert mine[0]["uploadedFiles"] == 1 and mine[0]["plannedFiles"] == 2
    assert mine[0]["sourceLabel"] == "시험 묶음"

    r = client.delete(f"{API_PREFIX}/uploads/transfers/{upload_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 204
    assert len(fake.aborted) == 1                       # 미완 멀티파트 Abort
    assert _storage_key_of(client, upload_id, small) in fake.deleted  # 올라간 객체 삭제
    r = client.get(f"{API_PREFIX}/uploads/transfers/incomplete", headers=auth(TOKEN_RES))
    assert [i for i in r.json()["items"] if i["uploadId"] == upload_id] == []


def test_permission_gate_blocks_initiate(p2_client) -> None:
    from conftest import TOKEN_PROF  # 업로드·편집 스위치가 꺼진 역할이 아닐 수 있어 확인용
    client = s3_client(p2_client, FakeS3())
    r = _initiate(client, [SMALL], token="a1-guest-token")
    assert r.status_code in (401, 403)


# ═════════════════ s3 폴더 종단 — 전송 → 완결 → 등록 → d3_file ═══════════════
def test_s3_folder_survives_to_d3_file(p2_client, sql) -> None:
    """폴더째 올린 구조가 **등록 뒤에도** 산다 (`〈339〉`-(나) · `0009`).

    ⚠ **이 시험은 red 로 시작하지 않는다.** 승계 코드가 이미 있어 지금도 통과한다.
       오라클이 아니라 **사각지대의 봉인**이다 — `d5→d3` 승계는 form-data 로만 시험됐고
       (`test_dataset_registration.py`), s3(프리사인드) 경로의 종단은 **0건**이었다.
       WU F-3(구 `F-2`) 완료 정의도 s3 는 「프리사인드 GET 1건」만 요구했다(`WORK-UNITS.md`).

    ⚠ `ready` 를 기다리지 않는다 — s3 모드에서 worker·viz 는 로컬 경로만 읽는다(`S3.md §4`).
       기다리면 dev 실물에서 영원히 안 끝나는 조건을 시험이 정답으로 박는다.
    """
    from tests.test_dataset_registration import register

    fake = FakeS3()
    client = s3_client(p2_client, fake)
    plan = _initiate(client, [
        {"fileName": "서울.nc", "byteSize": 1024, "relativePath": "기상/2025/서울.nc"},
        # **같은 이름·다른 폴더** — 중복 판정이 `relativePath` 우선이라 거부되지 않는다
        {"fileName": "서울.nc", "byteSize": 2048, "relativePath": "기상/2024/서울.nc"},
        {"fileName": "낱개.nc", "byteSize": 512},                      # 경로 없는 것도 섞는다
    ]).json()
    assert plan["rejected"] == [], plan["rejected"]
    upload_id = plan["uploadId"]

    for f in plan["files"]:
        assert _finish_single(client, fake, upload_id, f)["outcome"] == "올라감"
    receipt = client.post(f"{API_PREFIX}/uploads/transfers/{upload_id}/complete",
                          headers=auth(TOKEN_RES))
    assert receipt.status_code == 201, receipt.text

    r = register(client, receipt.json())
    assert r.status_code == 201, r.text

    rows = sql(
        "SELECT f.relative_path FROM d3_file f"
        " JOIN d3_dataset d ON d.id = f.dataset_id"
        " WHERE d.id = :d ORDER BY f.relative_path NULLS LAST",
        {"d": r.json()["datasetId"]},
    )
    assert [row["relative_path"] for row in rows] == [
        "기상/2024/서울.nc", "기상/2025/서울.nc", None,
    ], rows
