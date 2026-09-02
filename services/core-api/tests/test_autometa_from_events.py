"""사건 → 장부 되쓰기 — **보류된 사건이 등록 전환에서 반영된다**.

## 왜 이 픽스처가 먼저인가

운영 원장의 업로드는 **전건 등록 전환이 끝나 있었다.** 그래서 「등록 전에 난 사건」의
경로에는 **대상이 한 건도 없다** — 그 상태에서 코드를 넣고 시험을 돌리면 아무것도
지나가지 않은 채 green 이 난다. 이 레포의 대표 실패가 정확히 그 모양이다
(`CLAUDE.md §4` green-by-skip).

그래서 이 파일은 **등록 전환 전 업로드**를 만들고 거기에 사건을 놓는다. 그 상태가
「보류」이고, 이 시험이 지나가는 길이 그 보류가 풀리는 길이다.

## 보류된 사건은 어디 사는가

**`d5_pipeline_event` 행 그 자체다.** 별도의 큐도, 프로세스 메모리도 아니다 —
메모리에 들고 있으면 재기동에서 사라지고, **사라진 사실은 「값이 원래 없었다」와
구분되지 않는다.** 사건 행은 이미 내구 저장이고 업로드와 함께 지워진다
(`ON DELETE CASCADE`). 그래서 「보류 목록」은 자료구조가 아니라 **질의**다.

세 상태 (`CLAUDE.md §4`):
  · 사건이 값을 나르면 → **반영한다**(㉮·㉯)
  · 사람이 이미 채운 칸이면 → **덮지 않는다**. 덮은 칸의 수를 0 으로 드러낸다(㉲)
  · 사건이 없으면 → **채우지 않는다.** 「불렀으니 통과」로 세지 않는다(㉱)
"""
from __future__ import annotations

import json

from sqlalchemy import text as sa_text

import pytest
from conftest import ACC_A_RES, LAB_A, TOKEN_RES, auth
from test_uploads import one_body

from colab_core.app.main import API_PREFIX

_FORMAT = "GeoTIFF"
_CRS = "EPSG:4326"
_GRID = "900x1200"
_VARIABLES = ["LST", "QC"]


def _make_unregistered_upload(client) -> dict:
    """**등록 전환 전** 업로드 — 사건이 나는 시점의 실제 상태다."""
    r = client.post(f"{API_PREFIX}/uploads", files=one_body(), headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    return r.json()


def _hold_event(sql, upload_id: str, event_type: str, payload: dict) -> None:
    """워커가 냈을 사건을 원장에 놓는다 — **보류 상태를 실물로 만드는 자리**.

    멱등 키는 발행자의 규칙(`<타입>:<uploadId>`)을 그대로 쓴다. 시험이 다른 규칙을
    적으면 그 시험은 실물이 아니라 자기가 적은 규칙을 확인하게 된다.
    """
    from colab_core.kernel.ids import Ulid

    sql("""
        INSERT INTO d5_pipeline_event
          (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
           idempotency_key, payload)
        VALUES (:id, :lab, :acc, :u, :t, '1.0', 'pipeline-worker', :k, CAST(:p AS jsonb))
    """, {"id": str(Ulid.generate()), "lab": LAB_A, "acc": ACC_A_RES,
          "u": upload_id, "t": event_type, "k": f"{event_type}:{upload_id}",
          "p": json.dumps(payload, ensure_ascii=False)})


def _format_detected(**over) -> dict:
    return {"format": _FORMAT, "renderable": True, "uniform": True, **over}


def _header_parsed(**over) -> dict:
    return {"variables": _VARIABLES, "period": {"start": "2024-01-01T00:00:00Z",
                                                "end": "2024-01-31T00:00:00Z"},
            "crs": _CRS, "grid": _GRID, "byteSizeTotal": 4096,
            "unreadableFiles": [], **over}


def _autometa(sql, dataset_id: str) -> dict:
    rows = sql("SELECT format, crs, grid, variables, period_start, period_end,"
               "       total_size_bytes"
               "  FROM d3_dataset_autometa WHERE dataset_id = :d", {"d": dataset_id})
    assert len(rows) == 1
    return rows[0]


def _register(client, receipt, **extra):
    body = {"uploadId": receipt["uploadId"], "name": "자동 정보 반영 시험", **extra}
    return client.post(f"{API_PREFIX}/datasets", json=body, headers=auth(TOKEN_RES))


# ═════════════════ ㉮ 보류 → 반영 (이번 회차가 여는 길) ══════════════════════
def test_events_held_before_registration_are_applied_at_registration(p2_client, sql) -> None:
    """**대상 행이 아직 없는 사건**이 등록 전환에서 장부에 들어간다.

    이 시험이 red 였던 이유가 실물의 상태다 — 소비자가 0 건이라 사건이 나도 장부가
    그대로였고, 그 상태는 「값이 원래 없다」와 화면에서 구분되지 않았다.
    """
    client = p2_client()
    receipt = _make_unregistered_upload(client)
    upload_id = receipt["uploadId"]

    # 등록 전이다 — 장부 행 자체가 아직 없다. **이것이 「보류」의 정의다.**
    assert sql("SELECT registered_at FROM d5_upload WHERE id = :u",
               {"u": upload_id})[0]["registered_at"] is None
    _hold_event(sql, upload_id, "file.format-detected", _format_detected())
    _hold_event(sql, upload_id, "file.header-parsed", _header_parsed())

    dataset_id = _register(client, receipt).json()["datasetId"]

    meta = _autometa(sql, dataset_id)
    assert meta["format"] == _FORMAT
    assert meta["crs"] == _CRS
    assert meta["grid"] == _GRID
    assert list(meta["variables"]) == _VARIABLES
    assert meta["period_start"] is not None and meta["period_end"] is not None


def test_the_hold_survives_a_restart_because_it_lives_in_the_ledger(p2_client, sql) -> None:
    """**보류함이 프로세스 밖에 있다** — 사건을 놓은 프로세스와 반영하는 프로세스가 다르다.

    클라이언트를 새로 세워 요청 경계를 갈아 끼운다. 보류가 메모리였다면 여기서 값이
    사라진다 — 그리고 그 사라짐은 아무 에러도 내지 않는다.
    """
    receipt = _make_unregistered_upload(p2_client())
    upload_id = receipt["uploadId"]
    _hold_event(sql, upload_id, "file.format-detected", _format_detected())
    _hold_event(sql, upload_id, "file.header-parsed", _header_parsed())

    dataset_id = _register(p2_client(), receipt).json()["datasetId"]
    assert _autometa(sql, dataset_id)["crs"] == _CRS


# ═════════════════ ㉯ 두 사건이 서로 다른 칸을 채운다 ════════════════════════
def test_the_two_events_fill_different_columns(p2_client, sql) -> None:
    """`format` 은 ② 가, `crs`·`grid` 는 ③ 이 나른다 — **한 사건이 아니다.**"""
    client = p2_client()
    receipt = _make_unregistered_upload(client)
    _hold_event(sql, receipt["uploadId"], "file.header-parsed", _header_parsed())

    meta = _autometa(sql, _register(client, receipt).json()["datasetId"])
    assert meta["crs"] == _CRS and meta["grid"] == _GRID
    assert meta["format"] is None, "②가 없는데 포맷이 채워졌다 — 지어낸 값이다"


# ═════════════════ ㉰ 값 집합 밖·불확정은 옮기지 않는다 ══════════════════════
def test_non_uniform_format_is_not_carried_over(p2_client, sql) -> None:
    """**조각마다 포맷이 다르면 아직 모르는 것이다** — 등록 경로의 기존 규칙과 같다."""
    client = p2_client()
    receipt = _make_unregistered_upload(client)
    _hold_event(sql, receipt["uploadId"], "file.format-detected",
                _format_detected(uniform=False))

    assert _autometa(sql, _register(client, receipt).json()["datasetId"])["format"] is None


# ═════════════════ ㉱ 사건이 없으면 채우지 않는다 (대상 0건 = 통과 아님) ══════
def test_no_events_means_no_values_invented(p2_client, sql) -> None:
    """**「불렀다」를 「채웠다」로 세지 않는다.** 사건이 0 건이면 칸은 비어 있어야 하고,
    그 비어 있음은 유실 감지 게이트가 건수로 읽는다."""
    client = p2_client()
    receipt = _make_unregistered_upload(client)
    meta = _autometa(sql, _register(client, receipt).json()["datasetId"])
    assert meta["crs"] is None and meta["grid"] is None
    assert list(meta["variables"]) == []


# ═════════════════ ㉲ 사람이 고친 값을 덮지 않는다 ══════════════════════════
def test_a_value_set_by_a_person_is_not_overwritten(p2_client, sql, session_factory) -> None:
    """사람이 고친 칸을 사건이 덮으면 **그 수정은 아무 말 없이 사라진다.**"""
    from conftest import scoped_ro

    from colab_core.domains import d3_catalog
    from colab_core.kernel.ids import Ulid

    client = p2_client()
    receipt = _make_unregistered_upload(client)
    _hold_event(sql, receipt["uploadId"], "file.header-parsed", _header_parsed())
    dataset_id = _register(client, receipt).json()["datasetId"]

    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"crs": "사람이 고친 좌표계"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text

    # 같은 사건을 한 번 더 반영해도(재전달) **사람이 적은 값이 남는다.**
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        filled = d3_catalog.apply_autometa(session, dataset_id=Ulid(dataset_id), crs=_CRS)
        assert "crs" in filled, "칸이 채워져 있다는 사실 자체는 보고돼야 한다"
        row = session.execute(
            sa_text("SELECT crs FROM d3_dataset_autometa WHERE dataset_id = :d"),
            {"d": dataset_id}).mappings().first()
        assert row["crs"] == "사람이 고친 좌표계"


@pytest.mark.parametrize("event_type", ["file.crs-normalized", "preview.cog-built"])
def test_progress_only_events_do_not_write_ledger_columns(p2_client, sql, event_type) -> None:
    """**진행 사실은 장부 값이 아니다** — 이 둘은 채우는 칸이 하나도 없다."""
    client = p2_client()
    receipt = _make_unregistered_upload(client)
    _hold_event(sql, receipt["uploadId"], event_type,
                {"fileIds": [receipt["files"][0]["fileId"]], "overviewLevels": 2,
                 "sourceCrs": "WGS84", "targetCrs": "EPSG:4326", "transformed": False})
    meta = _autometa(sql, _register(client, receipt).json()["datasetId"])
    assert meta["crs"] is None and meta["grid"] is None


# ═══════ ㉵ 등록 요청이 실은 사람 값이 파이프라인 사건에 안 덮인다 (`#62`) ═══════
def test_human_values_sent_at_registration_survive_the_header_parsed_event(
        p2_client, sql) -> None:
    """**`#62` 의 핵심 단언** — 등록 요청에 사람이 적은 값과 헤더 파싱 사건이 **같은 회차에**
    만난다. 이기는 쪽은 **사람**이다.

    `〈138〉`(정본 `VAL-006`)이 변수·좌표계·기간을 「사람이 적는 값」으로 옮겼다. 그런데
    등록 전환은 `apply_autometa` 로 보류 사건을 같은 트랜잭션에서 반영한다(`〈190〉`).
    두 값이 한 요청 안에서 겹치므로 **순서가 곧 규칙**이다 — 사람 값을 먼저 쓰고, 사건은
    `COALESCE` 로 **빈 칸만** 채운다. 순서가 뒤집히면 사용자의 입력이 화면에 아무 말도
    남기지 않고 사라진다.

    사건이 나른 `format`·`grid` 는 사람이 안 적는 값이라 **그대로 들어와야 한다** —
    「사람 값을 지켰다」를 「사건을 통째로 버렸다」로 바꿔 통과시키지 않는다.
    """
    client = p2_client()
    receipt = _make_unregistered_upload(client)
    _hold_event(sql, receipt["uploadId"], "file.format-detected", _format_detected())
    _hold_event(sql, receipt["uploadId"], "file.header-parsed", _header_parsed())

    r = _register(client, receipt,
                  variables=["사람이 적은 변수"], crs="EPSG:5179",
                  period={"start": "1999-01-01T00:00:00Z", "end": "1999-12-31T00:00:00Z"})
    assert r.status_code == 201, r.text
    dataset_id = r.json()["datasetId"]

    meta = _autometa(sql, dataset_id)
    assert list(meta["variables"]) == ["사람이 적은 변수"], "사건이 사람이 적은 변수를 덮었다."
    assert meta["crs"] == "EPSG:5179", "사건이 사람이 적은 좌표계를 덮었다."
    assert meta["period_start"].year == 1999 and meta["period_end"].year == 1999, \
        "사건이 사람이 적은 기간을 덮었다."
    # 사람이 안 적는 칸은 사건이 그대로 채운다 — 반영 자체를 껐는지 여기서 갈린다.
    assert meta["format"] == _FORMAT
    assert meta["grid"] == _GRID


def test_empty_form_defaults_are_not_stored_as_human_values(p2_client, sql) -> None:
    """**폼 기본값 통과 ≠ 사람이 적었다** (`〈140〉`-㉱ 와 같은 실패형).

    빈 배열·빈 문자열을 값으로 저장하면 `_APPLY_AUTOMETA` 의 「빈 칸만 채운다」가 영영
    막혀 그 세 칸이 **영구 공란**이 된다. 그래서 등록은 빈 값을 **안 보낸 것으로 다룬다.**
    """
    client = p2_client()
    receipt = _make_unregistered_upload(client)
    _hold_event(sql, receipt["uploadId"], "file.header-parsed", _header_parsed())

    r = _register(client, receipt, variables=[], crs="", period=None)
    assert r.status_code == 201, r.text
    meta = _autometa(sql, r.json()["datasetId"])
    assert list(meta["variables"]) == _VARIABLES, "빈 배열이 저장돼 사건 반영을 막았다."
    assert meta["crs"] == _CRS, "빈 문자열이 저장돼 사건 반영을 막았다."
    assert meta["period_start"] is not None
