"""WU-B1 · PRD-01 · PRD-02 · PRD-03 — 분류 3축(분류 · 유형 · 사람이 고른 가공 단계).

여기서 재는 것 (`dev-package/prd/rounds/R-B-1-db.md` §2 WU-B1 수용 기준 그대로)

  PRD-01 · 분류 `category` (`M-1` · `d3_dataset_description` 한 칸 · 국문 5값)
    ⑴ 5값 밖 문자열은 **400** 이고 응답에 `allowed` 5값이 실린다 (IntegrityError 500 이 아니다)
    ⑵ 5값이 그대로 저장되고 그대로 돌아온다
  PRD-02 · 유형 `dataType` (`M-2` · 같은 표 한 칸 · 국문 6값 · 컬럼명은 `type` 을 피한다)
    ⑶ 6값 밖은 **400** ＋ `allowed` 6값
    ⑷ 유형 `관측 기반 산출물` ＋ 가공 단계 `Lv1` 이 **성공**한다 (조합 제약 없음 — 미결-14 ⓐ)
  PRD-03 · 사람이 고른 가공 단계 `processingLevelUserSet` (`M-3` · `d3_dataset` 재신설 · 4값)
    ⑸ 4값 밖은 **400** ＋ `allowed` 4값
    ⑹ `Lv3` 이 저장된다 (상한 Lv3 — 미결-7 ⓐ)
    ⑺ 사람 값과 파생값이 어긋나도 **성공**한다 (경고만 — 미결-2 ⓐ)
  공통
    ⑻ 세 칸을 안 실으면 전부 `null` 이고 등록이 성공한다 (선택 입력 · 기존 행의 상태)
    ⑼ 사람 값이 없는 행의 `processingLevel` 은 **파생값 그대로**다 (`자동` 표기는 화면 몫)
    ⑽ 수정 경로가 세 칸을 받는다 — 계약만 열고 서버 수용을 미루지 않는다(§5-㉰-4)

⚠ **여기서 재지 않는 것**
  · 화면 문면(「분류를 아직 안 골랐어요」 · `자동` 칩 · 국문＋영문 병기) → **WU-B3**.
  · `processingLevelDerived`·`processingLevelMismatch` 두 열쇠와 응답 `processingLevel`
    의 사람 값 우선 → **WU-B5**(PRD-10 · `R-B-2-server.md`). 이 회차는 세 열쇠만 연다.
  · 3축 질의 파라미터·`DatasetRow` 확장·색인 → **WU-B7**(`M-10`).
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX

CATEGORIES = ("수문 인자", "기상·기후 인자", "식생·탄소 인자", "사회·경제 인자", "환경 인자")
DATA_TYPES = ("지상관측자료", "위성자료", "재분석자료",
              "수치모형자료", "합성자료", "관측 기반 산출물")
PROCESSING_LEVELS = ("Lv0", "Lv1", "Lv2", "Lv3")


def _read(client, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def _register(client, **extra):
    return register(client, make_upload(client), **extra)


# ═══════════════════════════ PRD-01 · 분류 ═══════════════════════════
def test_category_outside_the_five_values_is_400_with_allowed(p2_client) -> None:
    """⑴ 5값 밖은 **400** 이고 `allowed` 5값이 실린다 — 500 으로 새지 않는다."""
    r = _register(p2_client(), category="강우·강수")
    assert r.status_code == 400, r.text
    assert sorted(r.json()["details"]["allowed"]) == sorted(CATEGORIES), r.text


def test_every_category_round_trips(p2_client) -> None:
    """⑵ 5값이 **전부** 저장되고 그대로 돌아온다 — 한 값이라도 빠지면 화면과 갈린다."""
    client = p2_client()
    for value in CATEGORIES:
        r = _register(client, category=value)
        assert r.status_code == 201, r.text
        assert _read(client, r.json()["datasetId"])["basicInfo"]["category"] == value


# ═══════════════════════════ PRD-02 · 유형 ═══════════════════════════
def test_data_type_outside_the_six_values_is_400_with_allowed(p2_client) -> None:
    """⑶ 6값 밖은 **400** ＋ `allowed` 6값."""
    r = _register(p2_client(), dataType="ERA5")
    assert r.status_code == 400, r.text
    assert sorted(r.json()["details"]["allowed"]) == sorted(DATA_TYPES), r.text


def test_every_data_type_round_trips(p2_client) -> None:
    """⑶-b 6값이 전부 담긴다."""
    client = p2_client()
    for value in DATA_TYPES:
        r = _register(client, dataType=value)
        assert r.status_code == 201, r.text
        assert _read(client, r.json()["datasetId"])["basicInfo"]["dataType"] == value


def test_derived_observation_product_with_lv1_succeeds(p2_client) -> None:
    """⑷ `관측 기반 산출물` ＋ `Lv1` 이 **성공**한다 — 조합 검증을 만들지 않는다(미결-14 ⓐ)."""
    client = p2_client()
    r = _register(client, dataType="관측 기반 산출물", processingLevelUserSet="Lv1")
    assert r.status_code == 201, r.text
    basic = _read(client, r.json()["datasetId"])["basicInfo"]
    assert basic["dataType"] == "관측 기반 산출물"
    assert basic["processingLevelUserSet"] == "Lv1"


# ═════════════════ PRD-03 · 사람이 고른 가공 단계 ═════════════════
def test_processing_level_user_set_outside_the_four_values_is_400(p2_client) -> None:
    """⑸ 4값 밖은 **400** ＋ `allowed` 4값 — `Lv4`·`2` 같은 값이 CHECK 로 떨어지지 않는다."""
    r = _register(p2_client(), processingLevelUserSet="Lv4")
    assert r.status_code == 400, r.text
    assert sorted(r.json()["details"]["allowed"]) == sorted(PROCESSING_LEVELS), r.text


def test_lv3_is_open(p2_client) -> None:
    """⑹ 상한은 `Lv3` 이다(미결-7 ⓐ) — 4값이 전부 담긴다."""
    client = p2_client()
    for value in PROCESSING_LEVELS:
        r = _register(client, processingLevelUserSet=value)
        assert r.status_code == 201, r.text
        assert _read(client, r.json()["datasetId"])["basicInfo"]["processingLevelUserSet"] == value


def test_mismatch_between_human_and_derived_level_still_succeeds(p2_client) -> None:
    """⑺ 사람 `Lv3` ↔ 파생 `0` 이 어긋나도 **등록이 성공**한다 — 경고만이다(미결-2 ⓐ).

    ⚠ 불일치를 알리는 응답 열쇠(`processingLevelMismatch`)는 **WU-B5** 몫이라 여기서
       만들지 않는다. 이 시험이 붙잡는 것은 **400 이 아니다**라는 사실 하나다.
    """
    client = p2_client()
    r = _register(client, processingLevelUserSet="Lv3")
    assert r.status_code == 201, r.text
    detail = _read(client, r.json()["datasetId"])
    assert detail["basicInfo"]["processingLevelUserSet"] == "Lv3"
    # 파생값은 종전 그대로 계산된다 — 부모가 없으므로 0 이다.
    assert detail["processingLevel"] == 0, detail["processingLevel"]


# ═══════════════════════════ 공통 ═══════════════════════════
def test_three_axes_are_optional_and_default_to_null(p2_client) -> None:
    """⑻·⑼ 세 칸을 안 실으면 전부 `null` 이고 `processingLevel` 은 **파생값 그대로**다.

    이것이 마이그레이션 뒤 기존 13행의 상태다 — 재선택을 강제하지 않는다(미결-3 ⓐ).
    """
    client = p2_client()
    r = _register(client)
    assert r.status_code == 201, r.text
    detail = _read(client, r.json()["datasetId"])
    basic = detail["basicInfo"]
    assert basic["category"] is None and basic["dataType"] is None, basic
    assert basic["processingLevelUserSet"] is None, basic
    assert detail["processingLevel"] == 0, detail


def test_update_path_accepts_the_three_keys(p2_client) -> None:
    """⑽ 수정 경로가 세 칸을 받는다 — 등록만 열고 수정을 미루지 않는다."""
    client = p2_client()
    dataset_id = _register(client).json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"category": "수문 인자", "dataType": "위성자료",
                           "processingLevelUserSet": "Lv2"},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    basic = _read(client, dataset_id)["basicInfo"]
    assert basic["category"] == "수문 인자"
    assert basic["dataType"] == "위성자료"
    assert basic["processingLevelUserSet"] == "Lv2"


def test_update_rejects_values_outside_the_sets_with_400(p2_client) -> None:
    """수정 경로도 **같은 400** 을 낸다 — 검사기를 등록에만 두면 수정이 500 을 낸다."""
    client = p2_client()
    dataset_id = _register(client).json()["datasetId"]
    for key, bad in (("category", "강우·강수"), ("dataType", "ERA5"),
                     ("processingLevelUserSet", "Lv9")):
        r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}", json={key: bad},
                         headers=auth(TOKEN_RES))
        assert r.status_code == 400, (key, r.text)


def test_topic_still_works_alongside_category(p2_client) -> None:
    """`topic` 열은 **남는다** — 되돌림 경로이자 이관 대조 근거다(§3-㉴)."""
    client = p2_client()
    r = _register(client, topic="강우·강수", category="기상·기후 인자")
    assert r.status_code == 201, r.text
    detail = _read(client, r.json()["datasetId"])
    assert detail["topic"] == "강우·강수", detail
    assert detail["basicInfo"]["category"] == "기상·기후 인자"


def test_update_path_accepts_null_to_clear_category(p2_client) -> None:
    """`category` 를 이미 가진 데이터셋에 `null` 을 실으면 되돌려진다(advisor ② 회귀 고정)."""
    client = p2_client()
    dataset_id = _register(client, category="수문 인자").json()["datasetId"]
    r = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                     json={"category": None},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    basic = _read(client, dataset_id)["basicInfo"]
    assert basic["category"] is None, basic
