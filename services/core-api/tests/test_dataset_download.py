"""`ST-1` 원본 내려받기 (`downloadDataset`) — **열리는가**와 **안 열리는가**를 둘 다 못 박는다.

Ted 판정 2026-09-02 「파일 저장처는 지금 볼륨을 그대로 쓴다」의 집행 시험이다.
`CT-1` 의 남은 한 칸(**권한 있는 행의 다운로드가 실제로 열리는가**)도 여기서 닫는다 —
그 칸은 양성만으로 닫지 않는다. **잠긴 행·다른 연구실 행이 안 열리는 것이 같은 무게의 증거다.**

red 만드는 법 — `routes/catalog.py` `_dataset_for_download` 의 `body_accessible` 두 줄을
지운다(그러면 잠긴 행이 열린다) · `?deliver=1` 분기에서 그 함수 호출을 지운다
(그러면 표식이 자격증명이 되어 판정을 건너뛴다).
"""
from __future__ import annotations

import io
import zipfile

from conftest import DS_A1, DS_A2, TOKEN_B, TOKEN_PROF, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.kernel import file_store

BODY_A1 = b"date,rain\n2026-01-01,12\n"
KEY_A1 = "k/a1"        # seed.sql `d3_file.storage_key` 축자
KEY_A2 = "k/a2"


def _place(tmp_path, key: str, payload: bytes) -> None:
    """접수 볼륨 위에 바이트를 놓는다 — **키가 곧 경로다**(`kernel/file_store`)."""
    path = tmp_path / "uploads" / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _downloads(sql, dataset_id: str) -> int:
    return sql("SELECT count(*) AS n FROM d8_download WHERE dataset_id = :d",
               {"d": dataset_id})[0]["n"]


# ── 양성 — 권한 있는 행은 실제로 열린다 (`CT-1` 남은 한 칸) ────────────────────

def test_a_permitted_row_download_actually_opens(p2_client, tmp_path, sql) -> None:
    _place(tmp_path, KEY_A1, BODY_A1)
    client = p2_client()
    before = _downloads(sql, DS_A1)

    hop = client.get(f"{API_PREFIX}/datasets/{DS_A1}/download", headers=auth(TOKEN_PROF),
                     follow_redirects=False)
    assert hop.status_code == 302, hop.text          # 계약이 요구하는 응답
    location = hop.headers["location"]
    assert f"{file_store.DELIVER_MARK}=1" in location

    bytes_hop = client.get(location, headers=auth(TOKEN_PROF))
    assert bytes_hop.status_code == 200, bytes_hop.text
    assert bytes_hop.content == BODY_A1               # **바이트가 실제로 온다**
    assert "attachment" in bytes_hop.headers["content-disposition"]

    # 이력은 302 시점에 쌓인다 (계약 산문 축자). 바이트 hop 이 또 쌓지 않는다.
    assert _downloads(sql, DS_A1) == before + 1


def test_pieces_come_bundled_in_one_archive(p2_client, tmp_path, sql) -> None:
    """조각 묶음이면 **묶어서 한 번에** 받는다 (`Policy_데이터셋_상세 §2` 축자)."""
    _place(tmp_path, KEY_A1, BODY_A1)
    _place(tmp_path, "k/a1b", b"second piece")
    sql("""INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes,
                                storage_key, carries_lat, carries_lon)
           VALUES ('00000000000000000000000FA9', current_lab_id(), :d, '본체',
                   'a1-body-2.csv', 12, 'k/a1b', false, false)""", {"d": DS_A1})
    client = p2_client()
    hop = client.get(f"{API_PREFIX}/datasets/{DS_A1}/download", headers=auth(TOKEN_PROF),
                     follow_redirects=False)
    got = client.get(hop.headers["location"], headers=auth(TOKEN_PROF))
    assert got.status_code == 200, got.text
    with zipfile.ZipFile(io.BytesIO(got.content)) as bundle:
        assert sorted(bundle.namelist()) == ["a1-body-2.csv", "a1-body.csv"]
        assert bundle.read("a1-body.csv") == BODY_A1


# ── 음성 — 잠긴 행 · 다른 연구실 행 (둘 다 필수 증거) ─────────────────────────

def test_a_locked_row_download_is_refused(p2_client, tmp_path, sql) -> None:
    """잠긴 데이터의 본체는 403 이다. **404 가 아니다** — 존재는 인정한다(P-13·P-34)."""
    _place(tmp_path, KEY_A2, b"locked bytes")
    client = p2_client()
    before = _downloads(sql, DS_A2)

    refused = client.get(f"{API_PREFIX}/datasets/{DS_A2}/download", headers=auth(TOKEN_PROF),
                         follow_redirects=False)
    assert refused.status_code == 403, refused.text
    assert _downloads(sql, DS_A2) == before          # 거절에는 이력을 쌓지 않는다


def test_the_deliver_mark_is_not_a_credential(p2_client, tmp_path, sql) -> None:
    """표식을 손으로 붙여도 판정을 건너뛰지 못한다 — 그러면 그것이 green-by-skip 이다."""
    _place(tmp_path, KEY_A2, b"locked bytes")
    client = p2_client()
    direct = client.get(
        f"{API_PREFIX}/datasets/{DS_A2}/download?{file_store.DELIVER_MARK}=1",
        headers=auth(TOKEN_RES))
    assert direct.status_code == 403, direct.text


def test_a_cross_lab_row_download_is_not_found(p2_client, tmp_path) -> None:
    """다른 연구실의 행은 **404** 다 — RLS 가 행을 지우므로 존재조차 알리지 않는다."""
    _place(tmp_path, KEY_A1, BODY_A1)
    client = p2_client()
    for url in (f"{API_PREFIX}/datasets/{DS_A1}/download",
                f"{API_PREFIX}/datasets/{DS_A1}/download?{file_store.DELIVER_MARK}=1"):
        got = client.get(url, headers=auth(TOKEN_B), follow_redirects=False)
        assert got.status_code == 404, got.text


def test_download_without_a_token_is_unauthorized(p2_client) -> None:
    got = p2_client().get(f"{API_PREFIX}/datasets/{DS_A1}/download", follow_redirects=False)
    assert got.status_code == 401, got.text


def test_missing_bytes_do_not_become_an_empty_success(p2_client, tmp_path) -> None:
    """원장에는 있는데 저장처에 바이트가 없으면 **500 이다.** 빈 200 으로 위장하지 않는다."""
    client = p2_client()      # 바이트를 놓지 않는다
    got = client.get(f"{API_PREFIX}/datasets/{DS_A1}/download?{file_store.DELIVER_MARK}=1",
                     headers=auth(TOKEN_PROF))
    assert got.status_code == 500, got.text
    assert got.json()["code"] == "STORAGE_OBJECT_MISSING"
