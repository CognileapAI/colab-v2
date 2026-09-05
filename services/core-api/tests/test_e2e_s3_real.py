"""`S3` 완료 정의의 **둘째 조항** — 5종 실파일이 **계보 확정 상태로 남는가**.

**이 파일이 재는 것과 재지 않는 것을 먼저 가른다.**
  · **재는 것** = 지원 목록 5종의 **실파일이 업로드를 통과해 등록되고, 계보가 `확정` 으로 남는다.**
  · **재지 않는 것** = 「그려진다」. 그 조항은 `services/viz-render/tests/test_e2e_real.py` 의
    `e2e_format` 표식 5건이 지고, 게이트 `e2e-format-coverage` 가 그 5건을 센다.
    **여기서 그리기를 다시 재지 않는다** — 두 곳에 적으면 갈라진다.

**왜 실파일인가.** 계보 확정 자체는 포맷과 무관한 계산이라(`d3_catalog.lineage_state`)
합성 바이트로도 초록이 난다. 그러나 `S3` 가 묻는 것은 「계산식이 옳은가」가 아니라
**「그 5종의 실물이 실제로 이 경로를 통과했는가」**다. 합성 픽스처로 바꾸면 그 질문이 사라진다.
(`M-4` 의 무늬 — 부분 검증이 통과하면 전체가 통과한 것으로 착각한다.)

**확장자로 포맷을 정하지 않는다**(`DR-3`·`M-1`) — core-api 는 접수만 하고 판정하지 않는다.
그 성질을 여기서도 음성으로 확인한다(`d5_upload_file.detected_format` 이 NULL).

원천 위치는 환경변수 `COLAB_REFERENCE_DATA` 로 받는다(절대경로 금지와 같은 이유).
**미지정·미마운트면 skip 이 아니라 fail** — green-by-skip 을 금지한다(`CLAUDE.md §4`).
마운트 없이 단위 시험만 돌릴 때는 `-m "not e2e"` 로 **명시적으로** 뺀다.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload

from colab_core.app.main import API_PREFIX

pytestmark = pytest.mark.e2e

_ENV = "COLAB_REFERENCE_DATA"

#: **GeoTIFF 를 가장 먼저 돌린다**(`WORK-UNITS §7` `S3` 행 축자). 목록의 정본은
#: `gates/config/e2e-format-coverage.toml` `[required].formats` 하나이고, 여기서는
#: 그 다섯 이름에 **실파일 자리**만 붙인다. 숫자가 아니라 목록으로 읽는다.
_REAL_FILES: list[tuple[str, str, str]] = [
    ("GeoTIFF", "02.File-format/file_format_4_tif/00.Data", "HLS.S30.*.tif"),
    ("NetCDF", "02.File-format/file_format_2_nc/00.Data", "gk2a_*.nc"),
    ("Binary", "02.File-format/file_format_3_bin/00.Data", "RDR_CMP_HSR_*.bin.gz"),
    # 폴더명이 거짓말한다 — 실체는 HDF4 다(`DR-3`·`M-1`). 폴더 이름을 포맷 근거로 쓰지 않는다.
    ("HDF4", "02.File-format/file_format_5_HDF5/00.Data", "*h27v05*.hdf"),
    # ⚠ **격자 파일이 아니라 본체다** — `04.Lat_Lon_info` 의 `.npy` 는 좌표 기준 격자이고
    #   (`DATA-REFERENCE §1`), 여기서 올리는 것은 `01.level-data` 의 산출 값 배열이다.
    ("NumPy", "01.level-data/02.vegetation/02.vegetation/Lv.2", "Prediction_*.npy"),
]


def _root() -> Path:
    v = os.environ.get(_ENV)
    if not v or not Path(v).is_dir():
        pytest.fail(f"{_ENV} 가 원천 디렉터리를 가리키지 않는다 — E2E 는 skip 하지 않는다")
    return Path(v)


def _real_file(subdir: str, pattern: str) -> Path:
    d = _root() / subdir
    if not d.is_dir():
        pytest.fail(f"원천 폴더 없음: {subdir}")
    files = sorted(p for p in d.glob(pattern) if p.name != "desktop.ini")
    if not files:
        pytest.fail(f"{subdir} 에 {pattern} 없음")
    return files[0]


def _upload_real(client, path: Path) -> dict:
    """실파일 바이트를 그대로 올린다. **접수 영수증이 실물 크기를 말해야 한다.**"""
    payload = path.read_bytes()
    receipt = make_upload(client, files=[
        ("files", (path.name, payload, "application/octet-stream"))])
    assert receipt["files"][0]["byteSize"] == len(payload) == path.stat().st_size, \
        f"{path.name}: 접수한 바이트 수가 실파일과 다르다 — 실물이 통과하지 않았다"
    return receipt


def _register(client, receipt, name: str) -> str:
    r = client.post(f"{API_PREFIX}/datasets",
                    json={"uploadId": receipt["uploadId"], "name": name, "summary": "시험용 설명 한 줄"},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    return r.json()["datasetId"]


@pytest.mark.parametrize("fmt,subdir,pattern", _REAL_FILES,
                         ids=[f[0] for f in _REAL_FILES])
def test_실파일이_업로드를_통과해_등록되고_계보가_확정으로_남는다(
        p2_client, sql, fmt, subdir, pattern) -> None:
    """`S3` 완료 정의 — 「**각각 최소 1건** … 계보가 **확정 상태로 남는다**」.

    `확정` 은 부모가 있어야 성립한다(`d3_catalog.lineage_state` 판정 순서 1·2) —
    부모가 없으면 `원천` 이다. 그래서 실파일 데이터셋에 **부모를 붙이고 확인까지** 한다.
    부모도 같은 실파일로 만든다 — 합성 부모를 붙이면 「실데이터 계보」가 아니게 된다.
    """
    client = p2_client()
    src = _real_file(subdir, pattern)

    parent_id = _register(client, _upload_real(client, src), f"S3 {fmt} 부모")
    child_id = _register(client, _upload_real(client, src), f"S3 {fmt} 파생")

    # ── core-api 는 확장자로도 매직바이트로도 포맷을 적지 않는다 (`DR-3` 음성 확인)
    rows = sql("SELECT detected_format FROM d5_upload_file "
               "WHERE file_name = :n ORDER BY created_at DESC LIMIT 1", {"n": src.name})
    assert rows and rows[0]["detected_format"] is None, \
        f"core-api 가 {src.name} 의 포맷을 스스로 적었다 — 판정은 pipeline-worker 몫이다"

    r = client.post(f"{API_PREFIX}/datasets/{child_id}/lineage/parents",
                    json={"parentDatasetId": parent_id, "parentRole": "주입력"},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text

    # 부모를 막 붙였으니 아직 `확인 필요` 다 — 사람이 확인하기 전에 `확정` 이 되면 안 된다.
    before = client.get(f"{API_PREFIX}/datasets/{child_id}", headers=auth(TOKEN_RES)).json()
    assert before["lineageState"] == "확인 필요", before["lineageState"]

    r = client.post(f"{API_PREFIX}/datasets/{child_id}/lineage/confirmation",
                    headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text

    after = client.get(f"{API_PREFIX}/datasets/{child_id}", headers=auth(TOKEN_RES)).json()
    assert after["lineageState"] == "확정", \
        (f"{fmt}: 실파일 데이터셋의 계보가 확정으로 남지 않았다", after["lineageState"])
    assert after["lineageConfirmedAt"], f"{fmt}: 확정일이 비어 있다 — 확정 상태의 근거가 없다"

    # 계보 상세도 같은 값을 말한다 — 화면이 읽는 자리가 상세라 여기서 갈리면 화면이 갈린다.
    graph = client.get(f"{API_PREFIX}/datasets/{child_id}/lineage",
                       headers=auth(TOKEN_RES)).json()
    assert graph["lineageState"] == "확정", graph["lineageState"]
    assert any(n.get("datasetId") == parent_id for n in graph["nodes"]), \
        f"{fmt}: 확정된 계보에 부모 노드가 없다"


def test_지원_목록은_게이트_설정을_정본으로_삼는다() -> None:
    """**목록이 두 곳에서 갈리는 것을 막는다** — 정본은 `.toml` 하나다(`〈248〉`).

    여기 다섯을 손으로 적어 두고 정본이 여섯이 되면, 이 파일은 조용히 **다섯만** 재고
    통과한다. 그 조용함이 이 레포의 대표 실패 유형이다(`CLAUDE.md §4` green-by-skip).
    """
    import tomllib

    config = (Path(__file__).resolve().parents[3]
              / "gates" / "config" / "e2e-format-coverage.toml")
    assert config.is_file(), f"목록 정본을 못 찾았다: {config}"
    required = tomllib.loads(config.read_text(encoding="utf-8"))["required"]["formats"]
    assert [f[0] for f in _REAL_FILES] == required, \
        ("이 파일의 포맷 목록이 정본과 갈렸다 — 정본을 따라 고친다", required)
