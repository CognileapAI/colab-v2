"""WU-B6 · PRD-19 — Lv0 출처 두 칸(출처 주소 `sourceUrl` · 내려받은 날 `sourceDownloadedOn`).

여기서 재는 것 (`dev-package/prd/rounds/R-B-1-db.md` §2 WU-B6 수용 기준 그대로)

  ⑴ Lv0 이고 출처 주소가 빔 → `createDataset` **성공** (선택 입력)
  ⑵ Lv1 인데 `sourceUrl` 을 실어 보냄 → **성공하고 값이 저장된다** (거절하지 않는다)
  ⑶ 두 칸을 안 실으면 둘 다 `null` 이고 등록이 성공한다 — 그것이 기존 전 행의 상태다
  ⑷ 두 칸이 상세 `basicInfo` 로 그대로 돌아온다 (Lv 를 안 가린다)
  ⑸ 수정 경로가 두 칸을 받는다 — 계약만 열고 서버 수용을 미루지 않는다(§5-㉰-4)
  ⑹ 수정으로 두 칸을 **비울 수 있다** (`null` 은 「비워라」)
  ⑺ 날짜가 아닌 문자열은 **400** 이다 — 캐스트에 맡기면 사용자의 오타가 500 이 된다
  ⑻ `sourceLabel` 은 **Lv 무관 상시** 그대로다 (미결-11 ⓐ) — 두 칸이 그 값을 대신하지 않는다

⛔ **여기서 재지 않는 것 — 폐기된 판정**
  「Lv0 이면 두 칸 필수 · 비면 400」·「Lv1 이상에서 값이 오면 400」은 **폐기됐다**
  (PRD-19 · 미결-11 ⓐ). 목업 배지를 근거로 400 을 세우지 않는다. 아래 ⑴⑵ 가 그 폐기의
  회귀 시험이다 — 400 이 되살아나면 두 시험이 red 를 낸다.

⚠ **여기서 재지 않는 것 — 다른 층**
  · 화면의 Lv0 전용 블록 표시·숨김과 숨은 값 미전송 → `frontend/test/lv0-source-20260907.test.tsx`.
  · 파생 Lv 가 Lv0 인 기존 행의 상세 안내 문면 → 같은 프런트 시험.
  · DB 층의 「CHECK 도 NOT NULL 도 없다」 → `db/platform/tests/0018-drift.sh`.
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

URL = "https://cds.climate.copernicus.eu/datasets/reanalysis-era5"


def _read(client, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def _register(client, **extra):
    return register(client, make_upload(client), **extra)


# ═══════════════════ 선택 입력이다 — 비어도 등록된다 ═══════════════════
def test_lv0_with_empty_source_url_registers(p2_client) -> None:
    """⑴ Lv0 이고 출처 주소가 비어도 **성공**한다.

    ⛔ 종전 완료 판정(「Lv0 이면 두 칸 필수 · 비면 400」)의 **회귀 시험**이다.
    """
    r = _register(p2_client(), processingLevelUserSet="Lv0")
    assert r.status_code == 201, r.text
    basic = r.json()["basicInfo"]
    assert basic["sourceUrl"] is None
    assert basic["sourceDownloadedOn"] is None


def test_lv0_with_both_fields_stores_them(p2_client) -> None:
    """⑷ Lv0 에서 두 칸을 실으면 그대로 저장되고 상세로 돌아온다."""
    client = p2_client()
    r = _register(client, processingLevelUserSet="Lv0",
                  sourceUrl=URL, sourceDownloadedOn="2026-08-20")
    assert r.status_code == 201, r.text
    basic = _read(client, r.json()["datasetId"])["basicInfo"]
    assert basic["sourceUrl"] == URL
    assert basic["sourceDownloadedOn"] == "2026-08-20"


def test_fields_absent_means_null_and_registration_succeeds(p2_client) -> None:
    """⑶ 두 칸을 안 실으면 둘 다 `null` — 그것이 마이그레이션 뒤 기존 전 행의 상태다."""
    client = p2_client()
    r = _register(client)
    assert r.status_code == 201, r.text
    basic = _read(client, r.json()["datasetId"])["basicInfo"]
    assert basic["sourceUrl"] is None
    assert basic["sourceDownloadedOn"] is None


# ═════════════ Lv 로 갈리지 않는다 — 저장은 Lv 를 보지 않는다 ═════════════
def test_lv1_with_source_url_succeeds_and_stores(p2_client) -> None:
    """⑵ `Lv1` 인데 `sourceUrl` 을 실어 보내도 **성공하고 값이 저장된다**.

    ⛔ 종전 완료 판정(「Lv1 이상에서 값이 오면 400」)의 **회귀 시험**이다.
       Lv 로 갈리는 것은 두 칸의 **화면 표시뿐**이고, 서버는 Lv 를 보지 않는다.
    """
    client = p2_client()
    r = _register(client, processingLevelUserSet="Lv1",
                  sourceUrl=URL, sourceDownloadedOn="2026-08-20")
    assert r.status_code == 201, r.text
    basic = _read(client, r.json()["datasetId"])["basicInfo"]
    assert basic["sourceUrl"] == URL
    assert basic["sourceDownloadedOn"] == "2026-08-20"


def test_every_level_accepts_the_two_fields(p2_client) -> None:
    """⑵-b 네 단계 **전부**에서 저장된다 — 한 단계라도 막히면 Lv 게이팅이 서버에 남은 것이다."""
    client = p2_client()
    for level in ("Lv0", "Lv1", "Lv2", "Lv3"):
        r = _register(client, processingLevelUserSet=level, sourceUrl=f"{URL}#{level}")
        assert r.status_code == 201, f"{level}: {r.text}"
        basic = _read(client, r.json()["datasetId"])["basicInfo"]
        assert basic["sourceUrl"] == f"{URL}#{level}", level


# ═══════════════════════════ 수정 경로 ═══════════════════════════
def test_update_accepts_both_fields(p2_client) -> None:
    """⑸ 수정 경로가 두 칸을 받는다 — 등록만 열고 수정을 미루지 않는다(§5-㉰-4).

    「Lv0 인데 비어 있어요 — 수정에서 채워 주세요」가 실행 가능한 안내가 되는 자리다.
    """
    client = p2_client()
    dataset_id = _register(client, processingLevelUserSet="Lv0").json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"sourceUrl": URL, "sourceDownloadedOn": "2026-08-20"},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    basic = _read(client, dataset_id)["basicInfo"]
    assert basic["sourceUrl"] == URL
    assert basic["sourceDownloadedOn"] == "2026-08-20"


def test_update_can_clear_both_fields(p2_client) -> None:
    """⑹ `null` 은 **비우라**는 뜻이다 — 열쇠 생략(그대로 두라)과 다르다."""
    client = p2_client()
    dataset_id = _register(client, sourceUrl=URL,
                           sourceDownloadedOn="2026-08-20").json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"sourceUrl": None, "sourceDownloadedOn": None},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    basic = _read(client, dataset_id)["basicInfo"]
    assert basic["sourceUrl"] is None
    assert basic["sourceDownloadedOn"] is None


# ═════════════════════ 날짜 형상 — 400 이지 500 이 아니다 ═════════════════════
def test_invalid_download_date_is_400_on_create(p2_client) -> None:
    """⑺ 날짜가 아닌 문자열은 **400** 이다.

    검사하지 않으면 `date` 캐스트가 DB 에서 죽어 **사용자의 오타가 500** 이 된다
    (`CODE-REVIEW-20260903` #12 와 같은 자리).
    """
    r = _register(p2_client(), sourceDownloadedOn="어제")
    assert r.status_code == 400, r.text


def test_invalid_download_date_is_400_on_update(p2_client) -> None:
    """⑺-b 수정 경로도 같은 검사를 탄다 — 검사기를 두 벌 두지 않는다."""
    client = p2_client()
    dataset_id = _register(client).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"sourceDownloadedOn": "2026-13-40"},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


# ═══════════ 원천 표기는 다른 축이다 — Lv 무관 상시 노출 (미결-11 ⓐ) ═══════════
def test_source_label_stays_visible_at_every_level(p2_client) -> None:
    """⑻ `sourceLabel` 은 Lv 와 무관하게 상시 그대로다 — 두 칸이 그 값을 대신하지 않는다."""
    client = p2_client()
    for level in ("Lv0", "Lv2"):
        r = _register(client, processingLevelUserSet=level, sourceLabel="ECMWF ERA5")
        assert r.status_code == 201, r.text
        basic = _read(client, r.json()["datasetId"])["basicInfo"]
        assert basic["sourceLabel"] == "ECMWF ERA5", level
