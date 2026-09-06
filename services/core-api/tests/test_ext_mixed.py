"""WU-A13 · PRD-32 — 확장자 혼합의 **최종 방어선**.

화면(`FileDropCard`)이 놓는 순간 걸러도 그것이 유일한 방어선이 되면 안 된다.
API 로 2종 확장자 조각을 실어 보내면 **등록 전환이 400** 이다.

⛔ 접수(`createUpload`)는 막지 않는다 — 접수는 D3 에 아무것도 만들지 않고
(`〈64〉-ⓐ`), 격자 후주입의 재료로 정상 상태다. 「본체 1건 이상」과 **같은 자리**,
같은 이유로 판정은 `createDataset` 에 선다.
"""
from __future__ import annotations

from conftest import TOKEN_RES, auth
from test_dataset_registration import make_upload, register
from test_uploads import HDF5_MAGIC

from colab_core.app.main import API_PREFIX


def body(name: str, salt: bytes = b"") -> tuple:
    return ("files", (name, HDF5_MAGIC + salt, "application/octet-stream"))


def test_mixed_extensions_are_rejected_at_registration(p2_client) -> None:
    """`.nc` 2 + `.tif` 1 → **400**. 데이터셋의 `file_extension` 이 1값인 근거가 이 규칙이다."""
    client = p2_client()
    receipt = make_upload(client, files=[body("a.nc"), body("b.nc", b"x"), body("c.tif", b"y")])
    r = register(client, receipt)
    assert r.status_code == 400, r.text
    assert "확장자" in r.text


def test_single_extension_registers(p2_client) -> None:
    """한 종류만이면 그대로 등록된다 — 회귀 방지."""
    client = p2_client()
    receipt = make_upload(client, files=[body("a.nc"), body("b.nc", b"x")])
    r = register(client, receipt)
    assert r.status_code == 201, r.text


def test_extension_comparison_ignores_case(p2_client) -> None:
    """`.NC` 와 `.nc` 는 **같은 종류**다 — 화면 규칙과 서버 규칙이 어긋나지 않는다."""
    client = p2_client()
    receipt = make_upload(client, files=[body("A.NC"), body("b.nc", b"x")])
    r = register(client, receipt)
    assert r.status_code == 201, r.text


def test_grid_file_extension_does_not_count(p2_client) -> None:
    """조각(**본체**)만 센다 — 기준 격자 파일은 다른 확장자여도 막지 않는다."""
    client = p2_client()
    r = client.post(
        f"{API_PREFIX}/uploads",
        files=[body("a.nc"), body("grid.tif", b"g")],
        data={"fileKinds": ["본체", "기준 격자 파일"]},
        headers=auth(TOKEN_RES),
    )
    assert r.status_code == 201, r.text
    assert register(client, r.json()).status_code == 201
