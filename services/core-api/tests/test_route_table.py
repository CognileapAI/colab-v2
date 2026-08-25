"""오라클 — 앱의 라우트 표 ↔ 계약(fe-core.yaml)을 diff 한다.

이 테스트가 오라클이다. 사람이 세지 않는다. 계약이 34 개면 앱도 34 개여야 하고,
경로·메서드가 한 글자라도 다르면 여기서 red 가 난다.
"""
from __future__ import annotations

import yaml
from conftest import CONTRACT

from colab_core.app.main import API_PREFIX, create_app
from colab_core.kernel.config import Settings

METHODS = {"get", "post", "put", "patch", "delete"}
SETTINGS = Settings(database_url="postgresql+psycopg://unused/unused", subjects_file=None)


def contract_operations() -> dict[str, tuple[str, str]]:
    doc = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    out: dict[str, tuple[str, str]] = {}
    for path, item in doc["paths"].items():
        for method, op in item.items():
            if method in METHODS:
                out[op["operationId"]] = (method.upper(), path)
    return out


def app_operations() -> dict[str, tuple[str, str]]:
    app = create_app(SETTINGS)
    out: dict[str, tuple[str, str]] = {}
    for route in app.routes:
        methods = getattr(route, "methods", None) or set()
        methods = {m for m in methods if m != "HEAD"}
        if not methods or not route.path.startswith(API_PREFIX):
            continue
        assert len(methods) == 1, f"라우트 하나에 메서드가 여럿이다: {route.path}"
        out[route.name] = (next(iter(methods)), route.path[len(API_PREFIX):])
    return out


def test_operation_count_is_50() -> None:
    """45 → 46 → 49 → **50.**

    ⭑ **50 의 하나는 `attachUploadGridFiles`** — 격자 후주입의 집행 경로다
    (Ted 2026-08-25 판정 · 사용자 관점 우선). **신설과 동시에 구현했다** — 그래서
    501 표는 23 에 머문다(`searchDatasets`·`listPalettes` 때 세운 규칙 그대로).


    46 의 하나는 `searchDatasets`(`〈80〉-㉯ 5`)였다. **49 의 셋은 4차 동결 해제**다
    (`PLAN-SoT §9-〈88〉` 묶음 4·5·6) — `listPalettes` · `addUploadFile` ·
    `replaceUploadGridFile`. 셋 다 **등록 전 세계**의 표면이고, 셋이 함께 있어야
    `S1-PLAN-REFOUND §E` 의 11 상태가 닫힌다.

    ⚠ 이전 판의 주석은 「동결 해제는 이 회차 한 번뿐이다 — 이 수가 또 늘면 `〈80〉` 이
    실패했다는 뜻이다」였다. **실제로 네 번 늘었고, 그것이 `〈88〉` 이 존재하는 이유다.**
    세 회차가 각각 직전 묶음이 세지 않은 축에서 구멍을 남겼다 — 마지막 축이
    **「그 응답을 부를 op 이 있는가」**였다(`sessions/S1-CONTRACT-GAP-SWEEP.md`).
    """
    assert len(contract_operations()) == 50, "계약의 오퍼레이션이 50 개가 아니다 — 발췌가 잘렸다."


def test_app_route_table_equals_contract() -> None:
    contract, app = contract_operations(), app_operations()
    assert set(app) - set(contract) == set(), "계약에 없는 라우트를 앱이 열었다."
    assert set(contract) - set(app) == set(), "계약에 있는 오퍼레이션을 앱이 등록하지 않았다."
    mismatched = {oid: (contract[oid], app[oid]) for oid in contract if contract[oid] != app[oid]}
    assert mismatched == {}, f"경로·메서드가 계약과 다르다: {mismatched}"


def test_no_duplicate_paths() -> None:
    app = create_app(SETTINGS)
    seen = set()
    for route in app.routes:
        for m in (getattr(route, "methods", None) or set()) - {"HEAD"}:
            key = (m, route.path)
            assert key not in seen, f"라우트가 중복 등록됐다: {key}"
            seen.add(key)
