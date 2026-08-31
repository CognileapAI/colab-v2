"""⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 2·3⟩ — 구조화된 격자 거절 · 성공 응답의 세 층.

이 파일이 못 박는 것 둘. 둘 다 **에러를 내지 않던 부류**다.

**⑴ 격자 거절 사유가 숫자와 enum 으로 나간다** (`묶음 1·2` · 스윕 `C-1`).
  지금까지 사다리 1·2·3단이 전부 `REFERENCE_GRID_MISSING` 한 코드 아래 **한국어 문장**으로
  나갔고 FE 가 정규식으로 갈랐다. 복합 문장(「형상이 안 맞는다 (…축을 판별하지 못했다…)」)에서
  **먼저 맞는 정규식이 이겨** 실제로 오분류했다. 여기서 그 복합 문장을 그대로 만들어
  **바깥 사유가 이긴다**는 것을 단언한다.

**⑵ ①썸네일·②비지도형이 성공 응답에 실린다** (`묶음 3` · 스윕 `A-1`).
  `build_value_layers` 가 ①②를 **항상 함께 굽는데** 성공 응답에는 `imageUrl` 한 자리뿐이라
  ③이 있으면 ②가, ③이 없으면 ①이 버려졌다. **렌더가 성공할수록 썸네일이 안 보였다.**
"""
from __future__ import annotations

import numpy as np
import pytest
from conftest import AUTH


def _render(client, target: dict) -> dict:
    r = client.post("/viz/v1/renders",
                    json={"target": target, "style": {"palette": "단색-파랑"}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    return r.json()


# ── ⑴ 구조화된 거절 ────────────────────────────────────────────────────────

def test_형상_불일치는_사유_enum_과_숫자_형상으로_나간다(client, put_target):
    """본체와 형상이 다른 격자를 붙인다 — 사다리 1단(`§E.2-⑥`).

    ⚠ 본체는 **좌표를 스스로 말하지 않는 `.npy`** 여야 한다. GeoTIFF 는 파일 안에서 격자가
    계산돼(`has_position`) 격자 파일을 아예 보지 않는다 — 그 본체로는 이 단에 못 온다.
    """
    tid = put_target({"values.npy": _npy_bytes(np.arange(64, dtype="float32").reshape(8, 8))},
                     grid={"LAT_x.npy": np.linspace(30.0, 40.0, 100).reshape(10, 10),
                           "LON_x.npy": np.linspace(120.0, 130.0, 100).reshape(10, 10)})
    job = _render(client, {"datasetId": tid})

    rej = job.get("gridRejection")
    assert rej is not None, "거절 사실이 구조화된 필드로 나와야 한다 — 문장만으로는 화면이 못 가른다"
    assert rej["reason"] == "형상 불일치"
    # **숫자다.** 문자열로 나르면 화면이 되파싱하고, 두 서비스의 인자 순서가 갈린다.
    assert rej["shapes"]["dataShape"] == [8, 8]
    assert rej["shapes"]["gridShape"] == [10, 10]


def test_복합_문장에서도_바깥_사유가_이긴다_정규식_순서가_뒤집지_않는다(client, put_target):
    """⚠ **실측된 오분류의 재발 방지.** 형상 불일치 메시지에는 사다리 아랫단의 사유
    (「축을 판별하지 못했다」)가 **괄호 안에 딸려 붙는다.** FE 의 정규식은 그 안쪽을 먼저
    맞혀 `축 판별 실패` 로 갈랐다 — 사용자는 「형상을 맞춘 격자를 올리라」 대신 엉뚱한
    안내를 받았고 **에러는 안 났다.** 구조화된 `reason` 은 바깥 판정이다.
    """
    # 쌍 `a` — 축은 잘 갈리지만 **형상이 본체와 다르다**(후보로 선다)
    # 쌍 `b` — 둘 다 ±90 안이라 **축을 못 가른다**(사다리 아랫단 사유가 `errors` 에 쌓인다)
    # → 바깥 메시지가 「형상이 안 맞는다: … (축을 판별하지 못했다 …)」로 **겹쳐 나간다.**
    tid = put_target({"values.npy": _npy_bytes(np.arange(64, dtype="float32").reshape(8, 8))},
                     grid={"LAT_a.npy": np.linspace(30.0, 40.0, 100).reshape(10, 10),
                           "LON_a.npy": np.linspace(120.0, 130.0, 100).reshape(10, 10),
                           "LAT_b.npy": np.full((8, 8), 30.0),
                           "LON_b.npy": np.full((8, 8), 40.0)})
    job = _render(client, {"datasetId": tid})
    rej = job.get("gridRejection")
    assert rej is not None
    detail = (job.get("failure") or {}).get("details", {}).get("detail", "")
    assert "축을 판별하지 못했다" in detail, \
        "이 시험이 재현하려는 복합 문장이 실제로 만들어져야 한다 — 아니면 회귀를 못 막는다"
    assert rej["reason"] == "형상 불일치", \
        "바깥 판정은 「이 격자는 이 파일의 것이 아니다」다 — 안쪽 사유가 이기면 안 된다"


def test_축_판별_실패는_그_사유로_나간다(client, put_target):
    """두 배열 모두 ±90 안이라 위도·경도를 못 가른다 — 사다리 3단(`§E.2-⑦`).

    **형상은 본체와 맞춘다** — 안 맞추면 바깥의 `형상 불일치` 가 먼저 서고 이 단에 못 온다.
    """
    tid = put_target({"values.npy": _npy_bytes(np.arange(64, dtype="float32").reshape(8, 8))},
                     grid={"LAT_x.npy": np.full((8, 8), 30.0),
                           "LON_x.npy": np.full((8, 8), 40.0)})
    job = _render(client, {"datasetId": tid})
    rej = job.get("gridRejection")
    assert rej is not None
    assert rej["reason"] == "축 판별 실패"


def test_짝_불일치는_그_사유로_나간다(client, put_target):
    """위도 파일과 경도 파일의 형상이 서로 다르다 — 사다리 2단(`§E.2-⑧`)."""
    tid = put_target({"values.npy": _npy_bytes(np.arange(64, dtype="float32").reshape(8, 8))},
                     grid={"LAT_x.npy": np.linspace(30.0, 40.0, 64).reshape(8, 8),
                           "LON_x.npy": np.linspace(120.0, 130.0, 100).reshape(10, 10)})
    job = _render(client, {"datasetId": tid})
    rej = job.get("gridRejection")
    assert rej is not None
    assert rej["reason"] == "짝 불일치"
    assert rej["shapes"]["latShape"] == [8, 8]
    assert rej["shapes"]["lonShape"] == [10, 10]


def test_사유_값은_계약의_세_값_밖으로_나가지_않는다():
    """**네 번째를 만들지 않는다** (`common.json#GridRejectionReason`)."""
    from colab_viz.domains.d7_visualization.grid import GRID_REJECTION_REASONS

    assert GRID_REJECTION_REASONS == ("형상 불일치", "짝 불일치", "축 판별 실패")


def test_격자를_잘_붙인_렌더에는_거절_필드가_없다(client, put_target, tiny_geotiff):
    """선택 속성이다 — 없는 것을 `null` 로 만들지 않는다."""
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"datasetId": tid})
    assert job["status"] == "완료", job.get("failure")
    assert "gridRejection" not in job


# ── ⑵ 성공 응답이 세 층을 다 말한다 ────────────────────────────────────────

def test_지도형_성공에도_썸네일과_값미리보기_URL_이_실린다(client, put_target, tiny_geotiff):
    """③이 주 화면이다. 그때 ①②는 **버려지지 않고** 자기 필드로 간다.

    ⭑ **⟨재개정 2026-08-31 · Ted 판정 ⑬ · `〈240〉`⟩ 갈래가 스위치가 되어 ③의 자리가
    기본값에서 다시 `imageUrl` 이다.** ／ 종전 문면 ~~`〈238〉` 으로 `tileUrlTemplate` 으로
    옮겨졌다~~ — 정본(260826 델타 · POL-021)이 타일을 축자로 배제하고 있어 **기본은
    「한 장」**이 됐다. 타일을 켠 쪽은 `test_tile_branch_switch.py` 가 잰다.
    **재는 성질은 두 갈래 어디서나 그대로다 — ①②가 주 화면 자리를 차지하지 않는다.**
    """
    tid = put_target(copy_from=[tiny_geotiff])
    res = _render(client, {"datasetId": tid})["result"]
    assert res["thumbnailUrl"], "①썸네일이 성공 응답에 실릴 자리가 있어야 한다"
    assert res["valuePreviewUrl"], "②비지도형이 성공 응답에 실릴 자리가 있어야 한다"
    # ③이 주 화면이다 — 주 화면 자리가 ①②를 가리키면 지도를 안 그린 것이 된다
    주화면 = res["imageUrl"]
    assert 주화면 != res["valuePreviewUrl"]
    assert 주화면 != res["thumbnailUrl"]


def test_비지도형_성공에도_썸네일_URL_이_실린다(client, put_target):
    """③이 없으면 `imageUrl` 은 ②다. **그때 ①이 버려지던 자리다.**"""
    raw = np.arange(64, dtype="float32").reshape(8, 8)
    tid = put_target({"values.npy": _npy_bytes(raw)})
    job = _render(client, {"datasetId": tid})
    assert job["status"] == "완료", job.get("failure")
    res = job["result"]
    assert res["precisionBadge"] == "격자 없음 — 지도형 보류"
    assert res["thumbnailUrl"], "①썸네일이 성공 응답에서 사라지면 안 된다"
    assert res["valuePreviewUrl"] == res["imageUrl"], \
        "②가 주 화면인 갈래다 — 같은 자리를 가리키는 것이 정상이다"


def _npy_bytes(arr: np.ndarray) -> bytes:
    import io
    buf = io.BytesIO()
    np.save(buf, arr)
    return buf.getvalue()
