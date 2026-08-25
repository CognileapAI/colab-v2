"""`createUpload` · `getUploadStatus` — 접수와 상태, 그리고 **수명 세 규칙**.

수명은 `PLAN-SoT §9 〈67〉-ⓐ` 가 정본 규칙으로 못 박았다:
  ① 미등록 업로드는 **수명이 있다**
  ② **시계가 처리를 앞지르지 않는다** — 처리 중인 업로드는 만료로 지워지지 않는다
  ③ 만료 뒤에는 **없는 것으로 답한다** (404)

②를 단언하는 시험이 이 파일 아래쪽에 있다. **없으면 ㉳(만료 404)이 정상 동작에 404 를
내면서 green 을 보고한다** — `〈67〉` 이행 제약 ㉡ 이 요구한 그 시험이다.
"""
from __future__ import annotations

import datetime as dt

import pytest
from conftest import TOKEN_B, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

#: `.nc` 인데 실제로는 **HDF5 컨테이너**다 — 원천 파일이 실제로 이렇다 (`DR-3` · `SEED-DATA F-2`).
HDF5_MAGIC = b"\x89HDF\r\n\x1a\n" + b"\x00" * 32
#: `.hdf` 인데 실제로는 **HDF4** 라 `h5py` 로 안 열린다.
HDF4_MAGIC = b"\x0e\x03\x13\x01" + b"\x00" * 32


def _upload(client, *, files, kinds=None, token=TOKEN_RES):
    data = {} if kinds is None else {"fileKinds": kinds}
    return client.post(f"{API_PREFIX}/uploads", files=files, data=data, headers=auth(token))


def one_body(name="a.nc", payload=HDF5_MAGIC):
    return [("files", (name, payload, "application/octet-stream"))]


# ═══════════════════════════════ 접수 ═══════════════════════════════════════
def test_create_upload_issues_upload_id_and_file_id(p2_client) -> None:
    """`UploadReceipt` 가 `uploadId`·`fileId` 를 **FE 표면에 처음** 내리는 자리다
    (`SEAM-AUDIT` I-01·I-06 — 소비만 있고 생산이 없던 두 식별자)."""
    client = p2_client()
    r = _upload(client, files=one_body())
    assert r.status_code == 201, r.text
    body = r.json()
    assert set(body) == {"uploadId", "files"}
    assert len(body["uploadId"]) == 26
    assert len(body["files"]) == 1
    assert set(body["files"][0]) == {"fileId", "fileName", "kind", "byteSize"}
    assert body["files"][0]["kind"] == "본체"
    assert body["files"][0]["byteSize"] == len(HDF5_MAGIC)


def test_create_upload_emits_exactly_one_accepted_event(p2_client, sql) -> None:
    """**`upload.accepted` 를 내는 유일한 자리다.** 봉투가 `source` 를 const 로 못 박았다."""
    client = p2_client()
    upload_id = _upload(client, files=one_body()).json()["uploadId"]
    rows = sql("SELECT event_type, source, schema_version, idempotency_key, payload"
               "  FROM d5_pipeline_event WHERE upload_id = :u", {"u": upload_id})
    assert len(rows) == 1
    assert rows[0]["event_type"] == "upload.accepted"
    assert rows[0]["source"] == "core-api"
    assert rows[0]["idempotency_key"] == f"upload.accepted:{upload_id}"
    assert [f["kind"] for f in rows[0]["payload"]["files"]] == ["본체"]


def test_create_upload_requires_the_upload_edit_switch(p2_client, sql) -> None:
    """판정은 언제나 `업로드·편집` 스위치다 (`〈59〉-②` · `P-6`)."""
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'", {"a": "000000000000000000000000A1"},
        account_id="00000000000000000000000AP1")
    try:
        r = _upload(p2_client(), files=one_body())
        assert r.status_code == 403
        assert r.json()["code"] == "FORBIDDEN"
    finally:
        sql("UPDATE d2_permission_switch SET enabled = true"
            " WHERE account_id = :a AND switch = '업로드·편집'",
            {"a": "000000000000000000000000A1"}, account_id="00000000000000000000000AP1")


def test_create_upload_accepts_a_grid_only_bundle(p2_client) -> None:
    """**격자만 든 묶음도 접수된다** — 판정 자리가 접수에서 **등록 전환**으로 옮겨졌다.

    「본체 1건 이상」은 **데이터셋의 성질**이고(`DataModel §4.3`), 접수는 D3 에 아무것도
    만들지 않는다(`〈64〉-ⓐ`). 격자만 든 업로드는 **격자 후주입의 재료**로 정상 상태다
    (`attachUploadGridFiles` · Ted 2026-08-25 판정). 데이터셋이 되는 것은
    `tests/test_dataset_registration.py` 가 막는다.
    """
    r = _upload(p2_client(), files=one_body("grid.nc"), kinds=["기준 격자 파일"])
    assert r.status_code == 201, r.text


def test_create_upload_rejects_a_third_file_kind(p2_client) -> None:
    """파일 종류는 **둘뿐이다** — 여기서 값 집합을 늘리지 않는다 (`common.json#FileKind`)."""
    r = _upload(p2_client(), files=one_body(), kinds=["보조 파일"])
    assert r.status_code == 400


# ══════════════════════════════ 상태 조회 ═══════════════════════════════════
def test_get_upload_status_reads_events_and_creates_no_new_fact(p2_client, sql) -> None:
    """이벤트 ②~⑦ 의 **결과를 읽기만** 한다."""
    client = p2_client()
    upload_id = _upload(client, files=one_body()).json()["uploadId"]
    before = sql("SELECT count(*) AS n FROM d5_pipeline_event")[0]["n"]

    r = client.get(f"{API_PREFIX}/uploads/{upload_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["uploadId"] == upload_id
    assert body["ready"] is False
    # **아직 모르면 null 이다.** 0 이나 false 로 채우면 「모른다」가 「아니다」가 된다.
    assert body["renderable"] is None
    assert body["metadataComplete"] is None
    assert body["failure"] is None
    assert sql("SELECT count(*) AS n FROM d5_pipeline_event")[0]["n"] == before


def test_get_upload_status_is_404_across_the_lab_boundary(p2_client) -> None:
    """남의 연구실 업로드는 **없는 것**이다 — 403 이 아니라 404 (P-9·P-10)."""
    upload_id = _upload(p2_client(), files=one_body()).json()["uploadId"]
    r = p2_client().get(f"{API_PREFIX}/uploads/{upload_id}", headers=auth(TOKEN_B))
    assert r.status_code == 404


# ═══════════ 수명 — 규칙 ①②③ (`〈67〉-ⓐ` · 이행 제약 ㉠㉡) ═══════════════
def test_expires_at_comes_from_the_operations_setting_not_a_constant(p2_client) -> None:
    """규칙 ① — 수명이 있다. **숫자는 운영 설정에서 온다**(정본에 숫자가 없다).

    설정을 1시간으로 바꾸면 `expiresAt` 이 1시간 뒤가 된다. 코드에 24 가 박혀 있으면 red 다.
    """
    client = p2_client(ttl_hours=1)
    upload_id = _upload(client, files=one_body()).json()["uploadId"]
    body = client.get(f"{API_PREFIX}/uploads/{upload_id}", headers=auth(TOKEN_RES)).json()
    delta = dt.datetime.fromisoformat(body["expiresAt"]) - dt.datetime.now(dt.timezone.utc)
    assert dt.timedelta(minutes=55) < delta < dt.timedelta(minutes=65)


def test_the_default_operations_value_is_24_hours(p2_client) -> None:
    """초기값 24 — Ted 승인 (`〈67〉-ⓐ`). ⚠ **재 본 적 없는 최악 처리 시간 위에 얹힌 값**이다."""
    from colab_core.kernel.config import DEFAULT_UPLOAD_TTL_HOURS
    assert DEFAULT_UPLOAD_TTL_HOURS == 24
    client = p2_client()
    upload_id = _upload(client, files=one_body()).json()["uploadId"]
    body = client.get(f"{API_PREFIX}/uploads/{upload_id}", headers=auth(TOKEN_RES)).json()
    delta = dt.datetime.fromisoformat(body["expiresAt"]) - dt.datetime.now(dt.timezone.utc)
    assert dt.timedelta(hours=23) < delta < dt.timedelta(hours=25)


def _age(sql, upload_id: str, *, hours: int) -> None:
    """수명 시계를 앞당긴다 — **잠들지 않고** 만료를 만든다."""
    sql("UPDATE d5_upload SET created_at = created_at - make_interval(hours => :h),"
        "                     expires_at = expires_at - make_interval(hours => :h)"
        " WHERE id = :u", {"u": upload_id, "h": hours})


def test_an_expired_upload_answers_404(p2_client, sql) -> None:
    """규칙 ③ — **만료 뒤에는 없는 것으로 답한다.** (음성 시험 ㉳ 의 조회 쪽 절반)"""
    client = p2_client(ttl_hours=1)
    upload_id = _upload(client, files=one_body()).json()["uploadId"]
    _age(sql, upload_id, hours=2)
    r = client.get(f"{API_PREFIX}/uploads/{upload_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


def test_an_upload_still_being_processed_survives_its_expiry_time(p2_client, sql) -> None:
    """규칙 ② — **시계가 처리를 앞지르지 않는다** (`〈67〉` 이행 제약 ㉡).

    이 시험이 없으면 위 ㉳ 이 green 인 채로 **정상 처리 중인 업로드에 404 를 낸다.**
    「에러 없이 그럴듯한 값」의 정확한 재발이다 (`DATA-REFERENCE §0`).
    """
    client = p2_client(ttl_hours=1)
    upload_id = _upload(client, files=one_body()).json()["uploadId"]
    _age(sql, upload_id, hours=2)                 # 만료 시각을 이미 지났다
    assert client.get(f"{API_PREFIX}/uploads/{upload_id}",
                      headers=auth(TOKEN_RES)).status_code == 404, "전제 확인 — 지금은 만료다"

    # 파이프라인이 **방금** 한 발짝 나갔다. 그러면 이 업로드는 처리 중이다.
    sql("INSERT INTO d5_pipeline_event"
        "  (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,"
        "   idempotency_key, payload)"
        " VALUES ('01ARZ3NDEKTSV4RRFFQ69G5F01', current_lab_id(), :a, :u,"
        "         'file.header-parsed', '1.0', 'pipeline-worker',"
        "         :k, '{}'::jsonb)",
        {"a": "000000000000000000000000A1", "u": upload_id,
         "k": f"file.header-parsed:{upload_id}"})

    r = client.get(f"{API_PREFIX}/uploads/{upload_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, "처리 중인 업로드가 만료 시각을 지났다는 이유로 사라졌다."


def test_the_reaper_skips_uploads_that_are_still_processing(p2_client, sql) -> None:
    """`〈67〉` 이행 제약 ㉠ — **reaper 는 처리 중 상태를 건너뛴다.** 산문이 아니라 삭제 질의 조건이다."""
    from colab_core.domains.d5_ingestion import UploadLedgerAdapter

    client = p2_client(ttl_hours=1)
    idle = _upload(client, files=one_body()).json()["uploadId"]
    busy = _upload(client, files=one_body()).json()["uploadId"]
    _age(sql, idle, hours=2)
    _age(sql, busy, hours=2)
    sql("INSERT INTO d5_pipeline_event"
        "  (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,"
        "   idempotency_key, payload)"
        " VALUES ('01ARZ3NDEKTSV4RRFFQ69G5F02', current_lab_id(), :a, :u,"
        "         'file.crs-normalized', '1.0', 'pipeline-worker', :k, '{}'::jsonb)",
        {"a": "000000000000000000000000A1", "u": busy,
         "k": f"file.crs-normalized:{busy}"})

    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import scoped_session
    factory = client.app.state.session_factory
    subject = Subject(account_id=Ulid("000000000000000000000000A1"),
                      lab_id=Ulid("0000000000000000000000000A"))
    with scoped_session(factory, subject) as session:
        reaped = UploadLedgerAdapter(session).reap_expired()

    assert idle in reaped, "만료됐고 아무도 처리하지 않는 업로드가 안 지워졌다."
    assert busy not in reaped, "처리 중인 업로드를 reaper 가 지웠다 — 시계가 처리를 앞질렀다."


# ═════════════ 음성 ② — 확장자와 실제 포맷이 어긋나는 파일 ══════════════════
@pytest.mark.parametrize("file_name,payload,real_format", [
    ("gk2a.nc", HDF5_MAGIC, "HDF5"),      # `.nc` 인데 HDF5 컨테이너다 (`DR-3`)
    ("modis.hdf", HDF4_MAGIC, "HDF4"),    # `.hdf` 는 HDF4 라 h5py 로 안 열린다
])
def test_core_api_never_infers_a_format_from_the_extension(
        p2_client, sql, file_name, payload, real_format) -> None:
    """**음성 ②** — 확장자 기반 감지가 red 를 내야 한다.

    core-api 에서 그 red 의 형태는 「확장자를 보고 포맷을 적어 넣지 않는다」다.
    접수 직후 `detected_format` 은 **NULL** 이다 — 매직바이트 판정은 pipeline-worker 의
    일이고(`P2.md §2-10`·`§2-14`), 여기서 확장자로 채우면 `.nc` 가 NetCDF 로 **에러 없이
    그럴듯하게** 기록된다. `M-1`(확장자로 싸잡아 분류)이 실제로 저지른 실수다.
    """
    upload_id = _upload(p2_client(),
                        files=[("files", (file_name, payload, "application/octet-stream"))]
                        ).json()["uploadId"]
    rows = sql("SELECT file_name, detected_format FROM d5_upload_file WHERE upload_id = :u",
               {"u": upload_id})
    assert rows[0]["file_name"] == file_name
    assert rows[0]["detected_format"] is None, \
        f"core-api 가 확장자를 보고 포맷을 적었다 — 실제 포맷은 {real_format} 다."


def test_no_extension_to_format_table_exists_in_core_api() -> None:
    """위 시험의 짝 — **그런 표가 코드에 아예 없다.**

    행동 시험은 「지금 안 한다」를 말하고, 이 시험은 「할 수단이 없다」를 말한다.
    둘 중 하나만 있으면 다음 사람이 손쉽게 되돌린다.
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1] / "src" / "colab_core"
    suspicious = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in (".nc\":", ".nc':", "endswith(\".nc\")", "endswith('.nc')",
                      "splitext", "NetCDF\"", "'NetCDF'"):
            if token in text:
                suspicious.append(f"{path.name}: {token}")
    assert suspicious == [], f"확장자→포맷 매핑으로 보이는 것이 있다: {suspicious}"
