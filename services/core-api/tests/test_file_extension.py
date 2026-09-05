"""WU-A5 · PRD-21 — **확장자는 확장자로만 적는다.**

화면이 보이는 값은 판별 결과 문자열(`format`)이 아니라 **조각의 확장자**다.
`.hdf` 하나가 서로 호환되지 않는 두 포맷을 가리키므로(`P-10` · `R-09`), 매직 넘버를
읽지 않는 한 단정할 수 없다 — 그래서 화면은 단정하지 않고 확장자를 그대로 쓴다.

여기서 재는 것
  ⑴ `.nc` 조각 → `basicInfo.fileExtension = "nc"` (화면이 `*.nc` 로 조립한다)
  ⑵ `.hdf` 조각 → `"hdf"` (HDF4/HDF5 를 단정하지 않는다)
  ⑶ 확장자 없는 파일명 → `None` 이고 상세가 **200 이다**(화면은 `format` 으로 퇴행한다)
  ⑷ 대소문자는 접힌다 — `.NC` 와 `.nc` 는 같은 종류다 (PRD-32 · `_extension_of`)

⛔ **「`nc` 로도 찾는다」는 여기서 재지 않는다** — 색인 재정의(부록 B `M-10`)는 R-B 에서
   한 번만 돈다. R-A 는 컬럼만 세우고 검색은 종전대로 `format` 으로 잡힌다.
저장값은 **점이 없는 소문자**(`nc`)다. 별표와 점은 화면의 문법이지 저장의 값이 아니다.
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register
from test_uploads import HDF5_MAGIC

from colab_core.app.main import API_PREFIX


def body(name: str, salt: bytes = b"") -> tuple:
    return ("files", (name, HDF5_MAGIC + salt, "application/octet-stream"))


def _register_and_read(client, names: list[str]) -> dict:
    receipt = make_upload(client, files=[body(n, bytes([i])) for i, n in enumerate(names)])
    r = register(client, receipt)
    assert r.status_code == 201, r.text
    detail = r.json()
    again = client.get(f"{API_PREFIX}/datasets/{detail['datasetId']}", headers=auth(TOKEN_RES))
    assert again.status_code == 200, again.text
    return again.json()


def test_netcdf_slice_reports_the_extension_not_the_detected_format(p2_client) -> None:
    """⑴ `nakdong_precip_2025.nc` → `fileExtension = "nc"`. `NetCDF-4` 를 화면에 보내지 않는다."""
    detail = _register_and_read(p2_client(), ["nakdong_precip_2025.nc"])
    assert detail["basicInfo"]["fileExtension"] == "nc", detail["basicInfo"]


def test_hdf_is_not_resolved_into_hdf4_or_hdf5(p2_client) -> None:
    """⑵ `.hdf` 는 `hdf` 다 — 둘 중 어느 쪽인지 **단정하지 않는다**."""
    detail = _register_and_read(p2_client(), ["swath.hdf"])
    assert detail["basicInfo"]["fileExtension"] == "hdf", detail["basicInfo"]


def test_file_without_extension_falls_back_and_does_not_break(p2_client) -> None:
    """⑶ 확장자가 없으면 **NULL 이고 화면이 안 깨진다** — 지어내지 않는다."""
    detail = _register_and_read(p2_client(), ["nakdong_precip_2025"])
    assert detail["basicInfo"]["fileExtension"] is None, detail["basicInfo"]
    # 퇴행 표시의 재료가 남아 있다 — 화면은 이 자리에서 `format` 을 그대로 보인다.
    assert "format" in detail["basicInfo"]


def test_extension_is_lowercased(p2_client) -> None:
    """⑷ `.NC` 와 `.nc` 는 같은 종류다 (PRD-32) — 저장도 한 값으로 접힌다."""
    detail = _register_and_read(p2_client(), ["A.NC", "b.nc"])
    assert detail["basicInfo"]["fileExtension"] == "nc", detail["basicInfo"]


def test_extension_is_stored_on_the_dataset_row(p2_client, sql) -> None:
    """데이터셋당 **1값**이다 (`P-5`) — 조각마다 세지 않는다. 저장 자리는 autometa 다."""
    client = p2_client()
    receipt = make_upload(client, files=[body("a.nc"), body("b.nc", b"x")])
    dataset_id = register(client, receipt).json()["datasetId"]
    rows = sql("SELECT file_extension, format FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": dataset_id})
    assert rows[0]["file_extension"] == "nc"


def test_grid_file_extension_does_not_decide_the_dataset_extension(p2_client, sql) -> None:
    """조각(**본체**)이 정한다 — 기준 격자 파일은 확장자가 달라도 값을 흔들지 않는다."""
    client = p2_client()
    r = client.post(
        f"{API_PREFIX}/uploads",
        files=[body("a.nc"), body("grid.tif", b"g")],
        data={"fileKinds": ["본체", "기준 격자 파일"]},
        headers=auth(TOKEN_RES),
    )
    assert r.status_code == 201, r.text
    dataset_id = register(client, r.json()).json()["datasetId"]
    rows = sql("SELECT file_extension FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": dataset_id})
    assert rows[0]["file_extension"] == "nc"
