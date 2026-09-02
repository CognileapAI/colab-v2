"""`createDataset` — 등록 전환. **여기서 D3 에 첫 행이 선다.**

담는 음성 시험 (`P2.md §6-2` · `P2-EXEC §4 W2 ⑷`)
  ㉮ 사람이 올린 파일이 우리 산출물로 기록되지 않는다 · 계보에 파생물로 서지 않는다
  ㉰ **등록 원자성** — 중간 실패 시 D3 에 반쪽 행이 남지 않는다
  ㉱ **재전달·재요청 멱등** — 같은 업로드로 데이터셋이 둘 생기지 않는다
  ㉲ 등록하지 않고 나간 파일이 D3 에 한 행도 남기지 않는다
  ㉳ **만료된 업로드는 전환되지 않는다** (404)
그리고 `NB-A` — **등록 뒤 `d3_file.id` 가 업로드가 발급한 `fileId` 와 같다.**
"""
from __future__ import annotations

import pytest
from conftest import DS_A1, PRJ_B, TOKEN_RES, auth
from test_uploads import HDF5_MAGIC, one_body

from colab_core.app.main import API_PREFIX

PRJ_A = "0000000000000000000000PRJA"


def make_upload(client, *, files=None, token=TOKEN_RES) -> dict:
    r = client.post(f"{API_PREFIX}/uploads", files=files or one_body(), headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def register(client, receipt, **extra):
    body = {"uploadId": receipt["uploadId"], "name": "등록 시험 데이터셋", **extra}
    return client.post(f"{API_PREFIX}/datasets", json=body, headers=auth(TOKEN_RES))


# ═════════════════════════ 전환의 성질 ══════════════════════════════════════
def test_registration_is_a_conversion_not_a_new_creation(p2_client, sql) -> None:
    """의미는 「새로 만든다」가 아니라 **「uploadId 를 D3 데이터셋으로 등록 전환한다」**다."""
    client = p2_client()
    receipt = make_upload(client)
    r = register(client, receipt, topic="강우·강수", summary="한 줄")
    assert r.status_code == 201, r.text
    detail = r.json()
    assert detail["name"] == "등록 시험 데이터셋"
    assert detail["topic"] == "강우·강수"
    rows = sql("SELECT registered_at FROM d5_upload WHERE id = :u", {"u": receipt["uploadId"]})
    assert rows[0]["registered_at"] is not None, "원장에 전환 도장이 안 찍혔다."


def test_file_id_identity_is_preserved(p2_client, sql) -> None:
    """**`NB-A` 동일성 — 이 단언이 유일한 방어선이다.**

    `d5_upload_file.id → d3_file.id` 에는 FK 가 없다(불변규칙 1 이 금지한다). 등록 코드가
    ULID 를 새로 뽑아도 **DB 는 아무 말도 하지 않는다** — 동일성이 조용히 깨지고, 그 뒤로
    업로드 세계의 `fileId` 로는 아무것도 찾을 수 없게 된다.
    """
    client = p2_client()
    receipt = make_upload(client, files=[
        ("files", ("a.nc", HDF5_MAGIC, "application/octet-stream")),
        ("files", ("b.nc", HDF5_MAGIC + b"x", "application/octet-stream")),
    ])
    issued = sorted(f["fileId"] for f in receipt["files"])
    dataset_id = register(client, receipt).json()["datasetId"]

    stored = sorted(r["id"] for r in
                    sql("SELECT id FROM d3_file WHERE dataset_id = :d", {"d": dataset_id}))
    assert stored == issued, (
        "등록이 `fileId` 를 새로 뽑았다 — NB-A 동일성이 깨졌다. "
        f"발급 {issued} vs 저장 {stored}")

    listed = client.get(f"{API_PREFIX}/datasets/{dataset_id}/files", headers=auth(TOKEN_RES))
    assert sorted(f["fileId"] for f in listed.json()["items"]) == issued


def test_lineage_parents_and_project_ids_come_in_one_request(p2_client, sql) -> None:
    """등록 폼 한 화면이 **한 번에** 제출하는 값이다 — 등록 후 N 회 호출이 아니다."""
    client = p2_client()
    receipt = make_upload(client)
    r = register(client, receipt,
                 lineageParents=[{"parentDatasetId": DS_A1, "parentRole": "주입력",
                                  "method": "역거리가중", "origin": "manual"}],
                 projectIds=[PRJ_A])
    assert r.status_code == 201, r.text
    dataset_id = r.json()["datasetId"]
    edges = sql("SELECT parent_dataset_id, parent_role, method, origin"
                "  FROM d4_lineage_edge WHERE child_dataset_id = :d", {"d": dataset_id})
    assert len(edges) == 1
    assert edges[0]["parent_dataset_id"] == DS_A1
    assert edges[0]["origin"] == "manual"
    links = sql("SELECT project_id FROM d6_project_dataset WHERE dataset_id = :d",
                {"d": dataset_id})
    assert [x["project_id"] for x in links] == [PRJ_A]
    assert r.json()["processingLevel"] == 1, "주입력 부모가 Lv0 이면 자식은 Lv1 이다."


def test_registering_without_parents_is_recorded_as_unknown_not_as_a_guess(p2_client) -> None:
    """비어 있으면 **`기록 없음`으로 등록된다** — 등록을 막지 않고, 부모를 지어내지도 않는다."""
    client = p2_client()
    detail = register(p2_client_alias := client, make_upload(client)).json()
    assert detail["lineageState"] == "기록 없음"
    assert detail["processingLevel"] == 0
    assert p2_client_alias is client


def test_the_level_cannot_be_chosen_at_registration(p2_client) -> None:
    """**`LV-1` · `〈194〉` 「예외 없음」** — 등록 요청에도 사람이 고르는 칸이 없다.

    계약 `DatasetCreate` 에서 `processingLevel` 을 지웠고, 런타임의 강제 자리는
    `_ALLOWED_CREATE_FIELDS` 다. 조용히 무시하지 않고 **400 으로 드러낸다.**
    """
    client = p2_client()
    r = register(client, make_upload(client), processingLevel=1)
    assert r.status_code == 400, r.text
    assert "processingLevel" in r.text


# ══════════════ 음성 ㉮ — 우리 산출물로 기록되지 않는다 ═════════════════════
def test_a_human_uploaded_file_is_never_recorded_as_our_product(p2_client, sql) -> None:
    """**음성 ㉮** — 사람이 올린 파일이 우리 산출물(COG)로 기록되지 않고, 계보에 파생물로
    서지 않는다.

    core-api 쪽 형태는 둘이다 — ⓐ 등록이 **계보 관계를 스스로 만들지 않는다**(사람이 실어
    보낸 것만 선다) ⓑ 요청에 「이건 우리가 만든 것」을 적을 자리가 아예 없다.
    되돌릴 수 없는 오염은 **첫 쓰기보다 늦게 막을 수 없다** (`P2.md §8-A`).
    """
    client = p2_client()
    receipt = make_upload(client, files=[("files", ("real-cog.tif", b"II*\x00" + b"\x00" * 60,
                                                    "application/octet-stream"))])
    dataset_id = register(client, receipt).json()["datasetId"]

    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id = :d",
               {"d": dataset_id})[0]["n"] == 0, "등록이 계보 관계를 스스로 만들었다."
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE parent_dataset_id = :d",
                {"d": dataset_id})[0]["n"] == 0

    # ⓑ 「우리 산출물」·「파생」을 적을 자리가 요청에 없다 — 있으면 400 이다.
    for forged in ({"derived": True}, {"cog": True}, {"isOurProduct": True}):
        r = client.post(f"{API_PREFIX}/datasets",
                        json={"uploadId": make_upload(client)["uploadId"], "name": "x", **forged},
                        headers=auth(TOKEN_RES))
        assert r.status_code == 400, f"계약에 없는 필드 {forged} 가 통과했다."


# ══════════════════ 음성 ㉰ — 등록 원자성 ═══════════════════════════════════
def test_a_mid_way_failure_leaves_no_half_row_in_d3(p2_client, sql) -> None:
    """**음성 ㉰** — `createDataset` 은 전환+파일+계보+프로젝트를 한 요청에서 한다.
    그 중간에서 실패하면 **D3 에 반쪽 행이 남지 않는다.**

    실패를 마지막 단계(프로젝트 연결)에서 일으킨다 — 앞의 데이터셋·파일·계보가 이미 다
    써진 뒤라, 롤백이 진짜로 도는지가 여기서만 드러난다.
    """
    client = p2_client()
    before = sql("SELECT count(*) AS n FROM d3_dataset")[0]["n"]
    receipt = make_upload(client)
    r = register(client, receipt,
                 lineageParents=[{"parentDatasetId": DS_A1, "origin": "manual"}],
                 projectIds=[PRJ_B])          # 남의 연구실 프로젝트 → 마지막 단계에서 실패
    assert r.status_code == 400, r.text

    assert sql("SELECT count(*) AS n FROM d3_dataset")[0]["n"] == before, "반쪽 데이터셋이 남았다."
    assert sql("SELECT count(*) AS n FROM d3_file WHERE id = :f",
               {"f": receipt["files"][0]["fileId"]})[0]["n"] == 0, "반쪽 파일 행이 남았다."
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE parent_dataset_id = :d",
               {"d": DS_A1})[0]["n"] == 1, "실패한 등록의 계보 관계가 남았다(시드 1건이 전부여야 한다)."
    # 원장의 전환 도장도 함께 되돌아간다 — 안 그러면 다시 등록할 수 없게 된다.
    assert sql("SELECT registered_at FROM d5_upload WHERE id = :u",
               {"u": receipt["uploadId"]})[0]["registered_at"] is None
    assert register(client, receipt).status_code == 201, "실패한 등록이 업로드를 태워 버렸다."


# ═════════════ 음성 ㉱ — 같은 업로드로 둘을 만들지 않는다 ═══════════════════
def test_registering_the_same_upload_twice_is_409_and_creates_one_dataset(
        p2_client, sql) -> None:
    """**음성 ㉱ 의 동기 절반** — 같은 사실이 두 번 와도 D3·D4 에 중복이 생기지 않는다."""
    client = p2_client()
    receipt = make_upload(client)
    first = register(client, receipt)
    assert first.status_code == 201
    second = register(client, receipt)
    assert second.status_code == 409, second.text
    assert second.json()["code"] == "CONFLICT"
    rows = sql("SELECT id FROM d3_file WHERE id = :f", {"f": receipt["files"][0]["fileId"]})
    assert len(rows) == 1, "같은 파일이 D3 에 두 번 들어갔다."


def test_delivering_the_accepted_event_twice_creates_one_outbox_row(p2_client, sql) -> None:
    """**음성 ㉱ 의 이벤트 절반** — 같은 이벤트를 두 번 기입해도 행은 하나다.

    **제약이 있다는 사실을 증거로 세지 않는다** — 실제로 두 번 부르고 센다.
    """
    from colab_core.domains.d5_ingestion import UploadLedgerAdapter
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import scoped_session
    from colab_core.ports.ingestion import UploadFileRecord

    client = p2_client()
    receipt = make_upload(client)
    upload_id = Ulid(receipt["uploadId"])
    record = UploadFileRecord(file_id=receipt["files"][0]["fileId"], file_name="a.nc",
                             kind="본체", byte_size=1, storage_key="k", carries_lat=False,
                             carries_lon=False, detected_format=None)
    subject = Subject(account_id=Ulid("000000000000000000000000A1"),
                      lab_id=Ulid("0000000000000000000000000A"))
    with scoped_session(client.app.state.session_factory, subject) as session:
        again = UploadLedgerAdapter(session).publish_accepted(
            upload_id=upload_id, actor_account_id=subject.account_id, files=[record])
    assert again is False, "두 번째 기입이 새 행을 만들었다 — 재전달 멱등이 아니다."
    assert sql("SELECT count(*) AS n FROM d5_pipeline_event"
               " WHERE upload_id = :u AND event_type = 'upload.accepted'",
               {"u": receipt["uploadId"]})[0]["n"] == 1


# ═══════ 음성 ㉲ — 등록하지 않고 나간 파일은 D3 에 한 행도 없다 ═════════════
def test_a_file_that_left_without_registering_leaves_no_row_in_d3(p2_client, sql) -> None:
    """**음성 ㉲** (`〈64〉-ⓐ` 경계) — 「저장되지 않는다」의 대상은 **D3 카탈로그**다."""
    client = p2_client()
    before_datasets = sql("SELECT count(*) AS n FROM d3_dataset")[0]["n"]
    before_files = sql("SELECT count(*) AS n FROM d3_file")[0]["n"]
    receipt = make_upload(client)          # 접수만 하고 등록을 누르지 않는다

    assert sql("SELECT count(*) AS n FROM d3_dataset")[0]["n"] == before_datasets
    assert sql("SELECT count(*) AS n FROM d3_file")[0]["n"] == before_files
    assert sql("SELECT count(*) AS n FROM d3_file WHERE id = :f",
               {"f": receipt["files"][0]["fileId"]})[0]["n"] == 0
    # 원장에는 있다 — 그것이 `〈64〉-ⓑ` 다. 없으면 이벤트 ②~⑦ 이 갈 곳을 잃는다.
    assert sql("SELECT count(*) AS n FROM d5_upload_file WHERE upload_id = :u",
               {"u": receipt["uploadId"]})[0]["n"] == 1


# ═══════════════ 음성 ㉳ — 만료된 업로드는 전환되지 않는다 ══════════════════
def test_an_expired_upload_does_not_convert(p2_client, sql) -> None:
    """**음성 ㉳** — 404. 짝이 되는 시험(`처리 중이면 살아 있다`)이 `test_uploads.py` 에 있다."""
    client = p2_client(ttl_hours=1)
    receipt = make_upload(client)
    before = sql("SELECT count(*) AS n FROM d3_dataset")[0]["n"]
    sql("UPDATE d5_upload SET created_at = created_at - interval '2 hours',"
        "                     expires_at = expires_at - interval '2 hours' WHERE id = :u",
        {"u": receipt["uploadId"]})

    r = register(client, receipt)
    assert r.status_code == 404, r.text
    assert sql("SELECT count(*) AS n FROM d3_dataset")[0]["n"] == before


# ═════════ 정본 §192 — 그릴 수 없는 것과 등록할 수 없는 것은 다르다 ════════
@pytest.mark.parametrize("reason", ["형식 인식 실패", "헤더 인식 실패", "미리보기 준비 실패"])
def test_a_failed_pipeline_does_not_block_registration(p2_client, sql, reason) -> None:
    """정본 `Policy_업로드와_계보_확정:192` · `P2.md §2-12`·`§2-21`.

    「감지 실패·그릴 수 없음·헤더 못 읽음은 **등록을 막지 않는다**」. 기준 격자가 없어
    파이프라인이 `upload.failed` 로 끝나도 **등록·다운로드·계보 확정은 그대로 된다.**
    """
    client = p2_client()
    receipt = make_upload(client)
    sql("UPDATE d5_upload SET failed_at = now(), failure_class = '영구', failure_reason = :r"
        " WHERE id = :u", {"u": receipt["uploadId"], "r": reason})

    status = client.get(f"{API_PREFIX}/uploads/{receipt['uploadId']}", headers=auth(TOKEN_RES))
    assert status.status_code == 200
    assert status.json()["failure"] == {"reason": reason}
    assert register(client, receipt).status_code == 201, \
        f"실패({reason})한 업로드가 등록을 막았다 — 정본 :192 위반이다."


# ═════════ 변수·좌표계·기간 — 등록 요청이 받는다 (`#62` · 정본 `VAL-006`) ═════════
def test_the_three_free_input_fields_are_accepted_at_registration(p2_client, sql) -> None:
    """**`〈138〉` 의 나머지 절반** — 계약 `DatasetCreate` 가 선언한 셋을 서버가 받는다.

    종전에는 `_ALLOWED_CREATE_FIELDS` 에 없어 **400** 이었다(`#62`). 계약은 그대로다 —
    바뀐 것은 런타임뿐이고, 저장은 `updateDataset` 이 쓰는 **그 경로 하나**를 쓴다.
    """
    client = p2_client()
    r = register(client, make_upload(client),
                 variables=["tp", "t2m"], crs="EPSG:5179",
                 period={"start": "2025-06-01T00:00:00Z", "end": "2025-09-30T00:00:00Z"})
    assert r.status_code == 201, r.text
    basics = r.json()["basicInfo"]
    assert basics["variables"] == ["tp", "t2m"]
    assert basics["crs"] == "EPSG:5179"
    assert basics["period"]["start"].startswith("2025-06-01")

    rows = sql("SELECT variables, crs, period_start, period_end"
               "  FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": r.json()["datasetId"]})
    assert list(rows[0]["variables"]) == ["tp", "t2m"]
    assert rows[0]["crs"] == "EPSG:5179"
    assert rows[0]["period_start"].month == 6


def test_the_registration_and_update_paths_share_one_validator(p2_client) -> None:
    """**검사기가 한 벌이다** — 같은 어긋난 값을 두 경로에 넣으면 같은 400 이 난다.

    두 벌을 두면 한쪽만 고쳐지는 날이 오고, 그날 생성 경로는 500 을 낸다.
    """
    client = p2_client()
    bad = {"variables": ["", "tp"]}
    created = register(client, make_upload(client), **bad)
    assert created.status_code == 400, created.text

    dataset_id = register(client, make_upload(client)).json()["datasetId"]
    patched = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json=bad,
                           headers=auth(TOKEN_RES))
    assert patched.status_code == 400, patched.text
    assert created.json()["message"] == patched.json()["message"]


def test_a_malformed_period_is_a_400_on_both_paths(p2_client) -> None:
    """기간의 **형상**만 본다 (`VAL-006` 「형식 검사는 하지 않는다」).

    형상을 안 보면 저장 코드가 `AttributeError` 로 죽어 **500** 이 난다 — 사용자에게
    「우리 잘못」으로 보이는 자리에 사용자의 오타가 앉는다.
    """
    client = p2_client()
    created = register(client, make_upload(client), period="2025-06 ~ 2025-09")
    assert created.status_code == 400, created.text

    dataset_id = register(client, make_upload(client)).json()["datasetId"]
    patched = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                           json={"period": "2025-06 ~ 2025-09"}, headers=auth(TOKEN_RES))
    assert patched.status_code == 400, patched.text


def test_the_update_path_can_write_a_period(p2_client, sql) -> None:
    """`_UPDATABLE` 에 `period` 가 없어 **수정 경로의 기간이 통째로 죽어 있었다**
    (`KeyError` → 500). 시험이 없어 아무도 몰랐다."""
    client = p2_client()
    dataset_id = register(client, make_upload(client)).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"period": {"start": "2020-01-01T00:00:00Z",
                                      "end": "2020-02-01T00:00:00Z"}},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    rows = sql("SELECT period_start FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": dataset_id})
    assert rows[0]["period_start"].year == 2020


# ═══════ 무기한 기간 — 끝은 조건부다 (14차 해제 · Ted 판정 2026-09-02) ═══════
@pytest.mark.parametrize("period,label", [
    ({"start": "2025-06-01T00:00:00Z", "end": None}, "끝을 null 로 명시"),
    ({"start": "2025-06-01T00:00:00Z"}, "끝을 아예 안 보냄"),
])
def test_a_period_without_an_end_is_accepted_and_comes_back_open(
        p2_client, sql, period, label) -> None:
    """**끝이 없으면 무기한이다.** 계약 `DataPeriod.end` 는 `[string, "null"]` 이다.

    종전에는 `end` 가 `required` ＋ 비-nullable 이라 **진행 중인 데이터를 적을 자리가
    없었다** — 사용자는 있지도 않은 종료일을 지어내야 했다(`P4X` ㉮).

    ⭑ 열쇠를 아예 뺀 요청도 받는다 — 계약은 `end` 를 required-but-nullable 로 두지만
    (`ProjectPeriod` 와 같은 모양), 서버가 **빠진 열쇠를 `null` 과 같이 다루는 것**은
    계약보다 넓은 쪽이라 어떤 계약 문면도 깨지 않는다.
    """
    client = p2_client()
    r = register(client, make_upload(client), period=period)
    assert r.status_code == 201, f"{label}: {r.text}"

    basics = r.json()["basicInfo"]
    assert basics["period"] is not None, f"{label}: 시작이 있는데 기간이 통째로 사라졌다."
    assert basics["period"]["start"].startswith("2025-06-01")
    assert basics["period"]["end"] is None, f"{label}: 없는 끝을 지어냈다."

    rows = sql("SELECT period_start, period_end FROM d3_dataset_autometa "
               " WHERE dataset_id = :d", {"d": r.json()["datasetId"]})
    assert rows[0]["period_start"] is not None and rows[0]["period_end"] is None


def test_an_end_without_a_start_is_a_400_on_both_paths(p2_client) -> None:
    """**시작 없는 끝은 기간이 아니다.** 끝만 조건부이지 시작은 조건부가 아니다.

    문구 규약은 형제 검사(`variables`·`crs`)와 같다 — 형상 한 줄, 400.
    """
    client = p2_client()
    bad = {"period": {"end": "2025-09-30T00:00:00Z"}}
    created = register(client, make_upload(client), **bad)
    assert created.status_code == 400, created.text

    dataset_id = register(client, make_upload(client)).json()["datasetId"]
    patched = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json=bad,
                           headers=auth(TOKEN_RES))
    assert patched.status_code == 400, patched.text
    assert created.json()["message"] == patched.json()["message"]


def test_the_project_dataset_table_carries_an_open_ended_period(p2_client) -> None:
    """소속 데이터셋 표의 기간도 열려 있을 수 있다.

    `d3_catalog.periods_of` 가 `period_end IS NOT NULL` 로 걸러 **끝 없는 기간을 통째로
    떨어뜨리고 있었다** — 화면에는 「기간 없음」으로 보이는데 시작은 저장돼 있다.
    """
    client = p2_client()
    dataset_id = register(client, make_upload(client),
                          period={"start": "2025-06-01T00:00:00Z", "end": None}
                          ).json()["datasetId"]
    assert client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{dataset_id}",
                      json={"usageNote": None}, headers=auth(TOKEN_RES)).status_code == 204

    body = client.get(f"{API_PREFIX}/projects/{PRJ_A}", headers=auth(TOKEN_RES)).json()
    row = next(d for d in body["datasets"] if d["datasetId"] == dataset_id)
    assert row["period"] is not None, "끝이 없다고 기간을 통째로 떨어뜨렸다."
    assert row["period"]["end"] is None
