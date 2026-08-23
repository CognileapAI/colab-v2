"""**음성 ㉴** — `d5_*` 행이 **어느 읽기에도 비치지 않는다** + reaper 가 정리한다.

왜 이 시험이 완료 조건인가
  `〈64〉-ⓒ` 는 「`d5_*` 는 어느 사용자 읽기 경로에도 노출되지 않고, 만료되면 reaper 가
  지운다」를 못 박았는데 **DB 층은 이것을 강제하지 않는다.** `rls-allowlist.toml` 의
  주석 하나가 지고 있을 뿐이다. 이 파일이 없으면 그 보장은 **산문에만 있다.**

  ㉲(D3 에 한 행도 없다)와 짝이다 — ㉲ 를 D3 기준으로 좁힌 대신 **원래 보장을 여기서 되찾는다.**
"""
from __future__ import annotations

import json

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload

from colab_core.app.main import API_PREFIX

#: 사용자가 읽는 경로 전부. **새 읽기 op 이 생기면 여기 한 줄을 더한다.**
READ_PATHS = (
    "/datasets",
    "/datasets/facets",
    "/dashboard/summary",
    "/dashboard/data-map",
    "/dashboard/activities",
)


def test_ledger_identifiers_never_appear_in_any_read_path(p2_client) -> None:
    """카탈로그·검색·대시보드 어디에도 `uploadId`·`fileId` 가 비치지 않는다.

    **문자열로 훑는다** — 필드 이름을 미리 알고 그 자리만 보면, 다른 필드로 새는 것을 못 잡는다.
    """
    client = p2_client()
    receipt = make_upload(client)
    needles = [receipt["uploadId"]] + [f["fileId"] for f in receipt["files"]]

    for path in READ_PATHS:
        r = client.get(API_PREFIX + path, headers=auth(TOKEN_RES))
        assert r.status_code in (200, 501), f"{path} 가 {r.status_code} 다."
        if r.status_code != 200:
            continue                      # 아직 501 인 op — 200 으로 가짜 값을 내리지 않는다
        body = json.dumps(r.json(), ensure_ascii=False)
        for needle in needles:
            assert needle not in body, f"{path} 응답에 등록 전 원장의 식별자가 비쳤다: {needle}"


def test_the_ledger_row_is_not_visible_through_the_lineage_read(p2_client) -> None:
    """계보 읽기에도 비치지 않는다 — `upload.ready` 에 `datasetId` 가 없는 것이 그 계약 표현이다."""
    from conftest import DS_A2
    client = p2_client()
    receipt = make_upload(client)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/lineage/confirmation", headers=auth(TOKEN_RES))
    assert r.status_code == 200
    body = json.dumps(r.json(), ensure_ascii=False)
    assert receipt["uploadId"] not in body
    assert receipt["files"][0]["fileId"] not in body


def test_only_one_module_in_core_api_touches_the_d5_tables() -> None:
    """`d5_*` 로 가는 문이 **하나뿐**임을 코드가 지킨다 (`CLAUDE.md §3-1` · `〈63〉-㉱`).

    문이 둘이 되는 순간 「어느 읽기에도 안 비친다」를 사람이 매번 확인해야 하고,
    그 확인은 언젠가 빠진다.
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1] / "src" / "colab_core"
    tables = ("d5_upload_file", "d5_pipeline_event", "d5_upload")
    verbs = ("FROM", "INTO", "UPDATE", "DELETE", "JOIN")
    offenders = []
    for path in sorted(root.rglob("*.py")):
        if path.name == "d5_ingestion.py":
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not any(t in line for t in tables):
                continue
            # 표 이름이 SQL 절과 **같은 줄**에 있을 때만 접근으로 본다 — 산문 언급이 아니다.
            if any(v in line.upper() for v in verbs):
                offenders.append(f"{path.relative_to(root)}:{line_no}: {line.strip()}")
    assert offenders == [], f"`d5_*` 를 직접 만지는 곳이 더 있다:\n" + "\n".join(offenders)


def test_the_reaper_deletes_expired_rows_and_their_children(p2_client, sql) -> None:
    """`〈64〉-ⓒ` 의 나머지 절반 — **만료되면 reaper 가 지운다.**

    파일 행·이벤트 행까지 함께 사라져야 한다. 업로드만 지우고 자식이 남으면
    「아무도 지우자고 말하지 않는 행」이 원장에 눌러앉는다.
    """
    from colab_core.domains.d5_ingestion import UploadLedgerAdapter
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import scoped_session

    client = p2_client(ttl_hours=1)
    receipt = make_upload(client)
    upload_id = receipt["uploadId"]
    assert sql("SELECT count(*) AS n FROM d5_upload_file WHERE upload_id = :u",
               {"u": upload_id})[0]["n"] == 1
    sql("UPDATE d5_upload SET created_at = created_at - interval '2 hours',"
        "                     expires_at = expires_at - interval '2 hours' WHERE id = :u",
        {"u": upload_id})

    subject = Subject(account_id=Ulid("000000000000000000000000A1"),
                      lab_id=Ulid("0000000000000000000000000A"))
    with scoped_session(client.app.state.session_factory, subject) as session:
        reaped = UploadLedgerAdapter(session).reap_expired()

    assert upload_id in reaped
    assert sql("SELECT count(*) AS n FROM d5_upload WHERE id = :u", {"u": upload_id})[0]["n"] == 0
    assert sql("SELECT count(*) AS n FROM d5_upload_file WHERE upload_id = :u",
               {"u": upload_id})[0]["n"] == 0
    assert sql("SELECT count(*) AS n FROM d5_pipeline_event WHERE upload_id = :u",
               {"u": upload_id})[0]["n"] == 0


def test_the_reaper_does_not_reach_across_the_lab_boundary(p2_client, sql) -> None:
    """reaper 도 경계 안에서만 돈다 — RLS 가 이미 걸어 둔 위에서 지운다."""
    from colab_core.domains.d5_ingestion import UploadLedgerAdapter
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import scoped_session

    client = p2_client(ttl_hours=1)
    mine = make_upload(client)["uploadId"]
    sql("UPDATE d5_upload SET created_at = created_at - interval '2 hours',"
        "                     expires_at = expires_at - interval '2 hours' WHERE id = :u",
        {"u": mine})

    other = Subject(account_id=Ulid("00000000000000000000000BP1"),
                    lab_id=Ulid("0000000000000000000000000B"))
    with scoped_session(client.app.state.session_factory, other) as session:
        reaped = UploadLedgerAdapter(session).reap_expired()
    assert mine not in reaped, "다른 연구실의 reaper 가 남의 업로드를 지웠다."
    assert sql("SELECT count(*) AS n FROM d5_upload WHERE id = :u", {"u": mine})[0]["n"] == 1
