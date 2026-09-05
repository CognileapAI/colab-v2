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


def test_operation_count_is_66() -> None:
    """45 → 46 → 49 → 50 → 52 → 53 → 54 → 63 → 65 → **66.**

    ⭑ **병합(창 8-a) 실측 = 66.** 두 줄기가 각자 더한 op 이 겹치지 않아 합이 그대로 는다 —
    PR #1 줄기 **65**(`〈337〉`~`〈342〉` · 저장 Port · 파일 관리 · 다운로드 셋) ＋ `main` 줄기가
    더한 **`lookupDatasetValue` 하나**(15차 동결 해제 · `PLAN-SoT §9 〈294〉` · Ted 승인
    2026-09-03 · 등급 ㉯ op 신설 · `V-2` 값 조회) = **66**.
    ⛔ **이 수를 손으로 고르지 않는다** — `contracts/seams/fe-core.yaml` 을 세어 적은 값이다.

    ⚠ **`lookupDatasetValue` 회차는 seam 둘이 함께 늘었다** — `core-viz.yaml` 도 5 → 6
    (`lookupValue`). **seam 마다 총계를 따로 센다**: 이 시험이 세는 것은 `fe-core.yaml`
    하나이고, 두 seam 의 op 을 합쳐 읽으면 이 못이 무엇을 잠그는지가 흐려진다.
    **신설과 동시에 구현했다**(`routes/preview.py` `lookupDatasetValue` ·
    `services/viz-render/src/colab_viz/app/routes/values.py`) — 집행 없는 신설 금지
    (`X2-FREEZE-PROTOCOL §5-㉰-4`). 그래서 501 표는 그대로다.
    `contract-breaking` = 파괴적 변경 없음(순수 추가).

    ⭑ **54 의 하나는 `createPreviewScreenshot`** — **11차 동결 해제**
    (`PLAN-SoT §9 〈231〉` · Ted 승인 2026-08-30 · 등급 ㉯ op 신설). 정본이 스크린샷을
    편집 권한자 컨트롤로 요구하는데(`Policy_데이터셋_상세 §6`·`§8`) `fe-core.yaml` 에
    중계가 **0건**이라 화면이 서버 `createScreenshot` 에 닿을 길이 없었다
    (`sessions/P3-DETAIL-PREVIEW-20260830.md` 남은 차단 ㈎). **신설과 동시에 구현했다**
    (`routes/preview.py` — 집행 없는 신설 금지 `X2-FREEZE-PROTOCOL §5-㉰-4`) — 그래서
    501 표는 그대로다. `contract-breaking` = 파괴적 변경 없음(순수 추가).

    ⭑ **54 → 63 은 프리사인드 전송 9 op** — 8차 동결 해제. 두 레인이 각자 계약을 열었고
    병합에서 **둘 다 남았다**(순수 추가끼리라 겹치는 op 이 없다).

    ⭑ **63 → 65 는 9차 동결 해제**(`PLAN-SoT §9 〈339〉-(다)` · 회의 2026-08-23 Ted·phj ·
    [사용자 승인 2026-08-29]) — 파일 단위 다운로드 티켓(`downloadDatasetFile`)과 서명 티켓
    바이트(`getDownloadBytes`). 같은 회차에 `downloadDataset` 이 302 → 200 `DownloadTicket` 으로,
    `DatasetFile` 에 `byteSize`·`createdAt`(필수)·`relativePath` 가, `createUpload` 에
    `relativePaths` 가 붙었다. 302 삭제는 `response-non-success-status-removed` INFO 다
    (소비자 0건 · 집행 0건이던 응답).
    ⚠ **신설 둘은 이 커밋에서 구현하지 않는다** — 501 표에 **임시 등재**(5 → 7)하고 다운로드
    집행 커밋(C2)이 뺀다. 「신설과 동시에 구현」 규칙의 예외이고, 예외인 이유가 표에 적혀 있다.

    ---

    ⭑ **53 의 하나는 `listDatasetFieldSuggestions`** — **6차 동결 해제**
    (`PLAN-SoT §9 〈138〉` · 결정 2-10 · Ted 판정 ㈏ 2026-08-27). **신설과 동시에
    구현했다** — 그래서 501 표는 그대로다. 이 회차의 개정은 **순수 추가**였고
    `contract-breaking` 이 「파괴적 변경 없음, 다만 스펙이 다르다」로 그것을 확인했다.

    ⚠ **기대값을 결과에 맞춘 것이 아니다** — 계약이 실제로 커졌고, 그 개정을 Ted 가
    범위까지 정해 승인했다(㈏ 「올리고 고친다를 한 벌로」).

    ⭑ **52 의 둘은 `createSession`·`endSession`** — **5차 동결 해제**
    (`PLAN-SoT §9 〈90〉` · Ted 2026-08-26 지시). **신설과 동시에 구현했다**(`routes/session.py`)
    — 그래서 501 표는 23 에 머문다. 기존 50 op 의 요청·응답·`security` 는 한 글자도 안 바뀐다.

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

    **53 → 62 는 8차 동결 해제**(`PLAN-SoT §9 〈338〉`) — 프리사인드 전송 9 op.
    **신설과 동시에 구현했다**(㉰-4) — 저장 모드 local 에서는 아홉 전부 정직한 501 을
    내고, FE 는 그 신호로 form-data 경로에 폴백한다. 501 표는 24 그대로다.
    """
    assert len(contract_operations()) == 66, "계약의 오퍼레이션이 66 개가 아니다 — 발췌가 잘렸다."


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
