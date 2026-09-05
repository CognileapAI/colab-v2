"""WU-A4 · PRD-15 — **설명은 필수다. 그런데 DB 는 그대로 nullable 이다.**

rev1 축자 = 「연구자가 직접 쓴 맥락이 이 데이터의 값어치다」. 그 맥락이 없으면 남이 이
묶음을 다시 쓸 수 없다 — 그래서 필수 칸이 **이름 ＋ 설명 둘**이 된다(`VAL-001` 확장).

⛔ **`NOT NULL` 을 걸지 않고 일괄로 채우지도 않는다**(미결-5 ⓐ 확정 · 마이그레이션 0건).
막는 자리는 **쓰기 경로**뿐이고, 이미 비어 있는 행은 **그 행을 고칠 때** 채워진다.

여기서 재는 것 — 수용 기준 4건 그대로
  ⑴ 설명 없이 `createDataset` → **400**
  ⑵ 공백 세 칸만 → **400** (`minLength: 1` 이 못 막는 자리를 서버가 `strip` 으로 막는다)
  ⑶ 설명이 빈 **기존 행**의 상세 조회 → **200** 이고 `summary` 는 `null` 그대로다
     (화면이 「설명이 아직 없어요 — 수정에서 채워 주세요」를 그린다)
  ⑷ 그 행을 **설명을 비운 채** 다른 필드만 고쳐 저장 → **400**

⚠ ⑶ 과 ⑷ 이 한 벌이다 — **읽기는 종전대로 되고 쓰기만 막힌다.** 둘 중 하나만 재면
「일괄 채우기를 안 했다」가 증명되지 않는다.
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

#: 등록·수정 두 경로가 내는 **같은 문장**. 두 곳이 갈라지면 이 상수가 먼저 깨진다.
EMPTY = "설명을 적어 주세요."
#: 원래 비어 있던 행을 고칠 때의 문장 — 사용자가 지운 것이 아니라 없던 것이다.
BLANK_ON_UPDATE = "설명이 아직 없어요 — 수정에서 채워 주세요."


def _blank_summary_dataset(client, sql) -> str:
    """**설명이 빈 기존 행**을 만든다 — 등록 경로로는 더 이상 만들 수 없는 상태다.

    시드 13행이 그 상태이므로, 그 사실을 흉내 내려면 DB 를 직접 비우는 수밖에 없다.
    ⛔ 제품 코드가 이 길을 쓰지 않는다 — 시험이 **과거 상태를 재현**하는 자리다.
    """
    r = register(client, make_upload(client), summary="곧 비울 설명")
    assert r.status_code == 201, r.text
    dataset_id = r.json()["datasetId"]
    sql("UPDATE d3_dataset_description SET summary = NULL WHERE dataset_id = :d",
        {"d": dataset_id})
    return dataset_id


# ═══════════════════════════ ⑴⑵ 등록 경로 ═══════════════════════════════════
def test_create_without_summary_is_400(p2_client) -> None:
    """⑴ 설명 열쇠가 아예 없으면 **400** 이다 — 계약 `required` 를 서버가 집행한다."""
    client = p2_client()
    receipt = make_upload(client)
    r = client.post(f"{API_PREFIX}/datasets",
                    json={"uploadId": receipt["uploadId"], "name": "설명 없는 등록"},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert EMPTY in r.text


def test_create_with_null_summary_is_400(p2_client) -> None:
    """`summary: null` 은 「비워 둔다」였다 — 이제 **그 뜻이 없다**(`type: string`)."""
    client = p2_client()
    r = register(client, make_upload(client), summary=None)
    assert r.status_code == 400, r.text
    assert EMPTY in r.text


def test_create_with_only_whitespace_summary_is_400(p2_client) -> None:
    """⑵ 공백 세 칸 — `minLength: 1` 을 통과하지만 **맥락이 0글자**다."""
    client = p2_client()
    r = register(client, make_upload(client), summary="   ")
    assert r.status_code == 400, r.text
    assert EMPTY in r.text


def test_create_with_summary_succeeds_and_is_trimmed(p2_client) -> None:
    """**막기만 하고 못 올리게 되지 않았다** — 정상 경로가 살아 있음을 같이 잰다.

    앞뒤 공백은 저장하지 않는다 — 검사한 값과 저장한 값이 갈리면 다음 수정이 이유 없이 막힌다.
    """
    client = p2_client()
    r = register(client, make_upload(client), summary="  낙동강 유역 강수량  ")
    assert r.status_code == 201, r.text
    assert r.json()["summary"] == "낙동강 유역 강수량"


# ═══════════════════════════ ⑶ 기존 빈 행의 읽기 ════════════════════════════
def test_existing_blank_summary_row_still_reads_200(p2_client, sql) -> None:
    """⑶ **읽기는 종전대로다.** 여기가 red 면 「일괄 채우기 금지」가 깨진 것이다."""
    client = p2_client()
    dataset_id = _blank_summary_dataset(client, sql)
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    # 서버가 값을 지어내지도, 대신 채우지도 않는다 — 문면은 화면이 그린다.
    assert r.json()["summary"] is None, r.json()


def test_blank_summary_row_is_not_backfilled_in_db(p2_client, sql) -> None:
    """⛔ **행이 그대로 있다** — 미결-5 ⓐ 「일괄 채우기 금지」의 직접 증명."""
    client = p2_client()
    dataset_id = _blank_summary_dataset(client, sql)
    client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    rows = sql("SELECT summary FROM d3_dataset_description WHERE dataset_id = :d",
               {"d": dataset_id})
    assert rows and rows[0]["summary"] is None, rows


# ═══════════════════════════ ⑷ 기존 빈 행의 수정 ════════════════════════════
def test_updating_blank_summary_row_without_filling_it_is_400(p2_client, sql) -> None:
    """⑷ 이름만 고쳐도 **400** — 「그 행을 수정할 때 채우게 한다」(미결-5 ⓐ 축자)."""
    client = p2_client()
    dataset_id = _blank_summary_dataset(client, sql)
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"name": "이름만 고친다"}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert BLANK_ON_UPDATE in r.text


def test_updating_blank_summary_row_with_a_summary_succeeds(p2_client, sql) -> None:
    """**채우면 지나간다** — 막는 것이 목적이 아니라 채우게 하는 것이 목적이다."""
    client = p2_client()
    dataset_id = _blank_summary_dataset(client, sql)
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"name": "이름도 고친다", "summary": "이제 적었다"},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert r.json()["summary"] == "이제 적었다"


def test_update_cannot_blank_out_an_existing_summary(p2_client) -> None:
    """설명이 **있는** 행도 비울 수 없다 — `null` 도 공백도 400 이다."""
    client = p2_client()
    r = register(client, make_upload(client), summary="지우지 못한다")
    dataset_id = r.json()["datasetId"]
    for payload in ({"summary": None}, {"summary": "   "}):
        got = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json=payload,
                           headers=auth(TOKEN_RES))
        assert got.status_code == 400, (payload, got.text)
        assert EMPTY in got.text


def test_empty_patch_on_blank_summary_row_is_not_rejected(p2_client, sql) -> None:
    """**아무것도 안 고치는 요청은 수정이 아니다** — 400 을 남발하지 않는다.

    ⚠ 이 단언이 없으면 상세 화면의 「저장」 이 무변경으로 눌렸을 때 이유 없이 막힌다.
    """
    client = p2_client()
    dataset_id = _blank_summary_dataset(client, sql)
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json={},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
