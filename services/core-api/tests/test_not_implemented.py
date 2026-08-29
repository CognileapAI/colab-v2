"""오라클 — 어떤 오퍼레이션이 501 을 내는가, 그리고 **어떤 code 로** 내는가.

이 표가 없으면 나중에 누군가 501 을 가짜 200 으로 바꿔도 아무도 모른다.
"""
from __future__ import annotations

import json
import pathlib
import tempfile

import pytest
from fastapi.testclient import TestClient

from colab_core.app.main import API_PREFIX, create_app
from colab_core.app.routes.not_implemented import OPERATIONS
from colab_core.kernel.config import Settings

# 실동작 **22 개**. P1 이 넷을, **P2 가 열둘을** 501 표에서 빼 왔고(P2-EXEC §4 W2 P2-api ⑸),
# **S1 이 `searchDatasets` 를 신설과 동시에 구현했다** — 계약에 op 을 열어 두고 안 만들면
# 501 이 24 → 25 가 된다. 그래서 여는 회차에 함께 만들었다 (`〈80〉-㉯ 5` · `〈74〉-㉱`).
P1_REAL = {"getCurrentAccount", "getLab", "listLabMembers", "saveLabMemberPermissions",
           "listDatasets", "listDatasetFacets", "getDataset", "listDatasetFiles",
           "createProject"}
#: P2 가 가져간 열둘. **뺀 자리마다 실동작 시험이 있다** — 옆 칸이 그 시험 파일이다.
P2_REAL = {
    "createUpload":                 "tests/test_uploads.py",
    "getUploadStatus":              "tests/test_uploads.py",
    "createDataset":                "tests/test_dataset_registration.py",
    "updateDataset":                "tests/test_dataset_update.py",
    "updateLab":                    "tests/test_lab_and_project_update.py",
    "updateProject":                "tests/test_lab_and_project_update.py",
    "listDatasetFieldSuggestions":  "tests/test_field_suggestions.py",
    "addDatasetFile":               "tests/test_dataset_files.py",
    "replaceDatasetGridFile":       "tests/test_dataset_files.py",
    "deleteDatasetGridFile":        "tests/test_dataset_files.py",
    "addLineageParent":             "tests/test_lineage_confirm.py",
    "removeLineageParent":          "tests/test_lineage_confirm.py",
    "confirmLineage":               "tests/test_lineage_confirm.py",
    "createPreviewRender":          "tests/test_preview_relay.py",
    "getPreviewRender":             "tests/test_preview_relay.py",
    "listUploadLineageSuggestions": "tests/test_lineage_suggestions.py",
}
#: S1 이 동결 해제 회차에 신설과 동시에 구현한 **둘**. **뺀 자리마다 실동작 시험이 있다**는
#: 규칙이 「신설한 자리」에도 그대로 걸린다 — 그래야 501 이 안 늘어난 것이 증명된다.
#: ⭑ `listPalettes` 는 **4차 해제**(`〈88〉` 묶음 4)가 신설과 동시에 구현했다. 이것 없이는
#: 실서버에서 `createRender` 가 한 번도 안 불렸다 — 계약만 열고 501 로 두면 그 구멍이
#: 그대로 남는다.
S1_REAL = {"searchDatasets": "tests/test_search_relay.py",
           "listPalettes": "tests/test_palettes_relay.py"}
#: **S1 의 `P5` 레인이 표에서 뺀 셋** (24 → 21). 앞의 둘은 S-02·S-02b 화면 본체이고,
#: `linkProjectDataset` 은 `S1-PLAN.md §4.2` P5 행이 「여기서 열린다」고 지목한 op 이다.
P5_REAL = {
    "listProjects":        "tests/test_project_screens.py",
    "getProject":          "tests/test_project_screens.py",
    "linkProjectDataset":  "tests/test_project_screens.py",
}
#: **`P3` 이 표에서 뺀 하나** (20 → 19) — `getDatasetLineage`. **그래프를 그리는 함수는
#: P2 가 만들어 두었고**(`routes/lineage.py:lineage_graph`), 없던 것은 그 함수를 부를 GET
#: 라우트 하나였다. 종전 산문은 「이 조회 op 자체는 P1 배정」이었는데 **`P1` 이 닫힌 뒤에도
#: op 은 501 로 남아 있었다** — 산문이 낡은 자리다. 계보 그래프 화면(`P3`)은 이 op 없이
#: 설 수 없다. **뺀 자리에 실동작 시험이 있다**는 규칙은 여기에도 그대로 걸린다.
P3_REAL = {"getDatasetLineage": "tests/test_lineage_graph_read.py"}
#: **`P6` 승인 처리가 표에서 뺀 여덟** (16 → 8). 접근 요청 4 ＋ Verified 4.
#: 앞의 여섯은 `NOT_IMPLEMENTED_NO_STORE` 였고 그 사유(「저장처 자체가 P0 스키마에 없다」)를
#: 마이그레이션 `0010` 이 없앴다 — `d2_dataset_access_request`·`d2_verification_request`.
#: 뒤의 둘은 `NOT_IMPLEMENTED_P1` 이었다. **여덟이 한 회차에 나가는 이유** = 요청 op 만 열고
#: 처리 op 을 남기면 정본 §7.1·§7.2 의 전이표가 반만 서고, 그 회차의 산출은 「쌓이기만 하는
#: 대기줄」이 된다 (`CLAUDE.md §5` 부분 완료 금지).
#: **뺀 자리마다 실동작 시험이 있다** — 여덟 다 `tests/test_approval.py` 가 부르고,
#: 그 파일은 음성 다섯(경계 누출·미승인 개방·만료·일괄 승인 표면·권한 없는 처리)을 함께 든다.
P6_REAL = {
    "createAccessRequest":             "tests/test_approval.py",
    "listPendingAccessRequests":       "tests/test_approval.py",
    "approveAccessRequest":            "tests/test_approval.py",
    "rejectAccessRequest":             "tests/test_approval.py",
    "requestVerification":             "tests/test_approval.py",
    "listPendingVerificationRequests": "tests/test_approval.py",
    "approveVerification":             "tests/test_approval.py",
    "cancelVerification":              "tests/test_approval.py",
}
#: **`P7` 연구실 대시보드가 표에서 뺀 셋** (8 → 5). D8 집계 셋이다.
#: **계약 개정이 0 건이다** — 계약은 처음부터 이 셋을 들고 있었고 라우트만 없었다.
#: **셋이 한 회차에 나가는 이유** = 지표·맵·활동은 한 화면의 세 구획이고, 하나라도 501 이면
#: 그 화면은 「불러오지 못했어요」로만 선다 (`CLAUDE.md §5` 부분 완료 금지).
#: **뺀 자리마다 실동작 시험이 있다** — 셋 다 `tests/test_dashboard.py` 가 부르고,
#: 그 파일은 **연구실 경계 음성**(B 주체로 같은 세 op 을 불러 A 의 값이 하나도 안 보이는 것)을
#: 함께 든다. 대시보드는 숫자로 접힌 화면이라 누출이 숫자 안에 숨는다.
P7_REAL = {
    "getDashboardSummary": "tests/test_dashboard.py",
    "getDataMap":          "tests/test_dashboard.py",
    "listActivities":      "tests/test_dashboard.py",
}
P2_REAL = {**P2_REAL, **S1_REAL, **P5_REAL, **P3_REAL, **P6_REAL, **P7_REAL}
REAL = P1_REAL | set(P2_REAL)
NO_STORE = {
    # ⭑ **승인 요청 여섯이 여기서 빠졌다** (`P6` · 마이그레이션 `0010`). 남은 하나는
    #    `downloadDataset` 이고 그 저장처(파일 저장소)는 아직 없다 — `CT-1` 의 마지막 한 칸이다.
    "downloadDataset",
    # ⭑ `updateDataset` 이 여기서 빠졌다 (2026-08-27 · `〈127〉` Ted 판정 ㈎ ＋ ㈏ 범위).
    #    `#36`(설명 결손 2건)을 채울 **공개 경로가 그것뿐이었다.**
}
TOKEN = "a1-test-token"
ACCOUNT = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
LAB = "01ARZ3NDEKTSV4RRFFQ69G5FAW"


@pytest.fixture(scope="module")
def client() -> TestClient:
    tmp = pathlib.Path(tempfile.mkdtemp()) / "subjects.json"
    tmp.write_text(json.dumps({TOKEN: {"accountId": ACCOUNT, "labId": LAB}}), encoding="utf-8")
    app = create_app(Settings(database_url="postgresql+psycopg://unused/unused",
                              subjects_file=str(tmp)))
    return TestClient(app, raise_server_exceptions=False)


def test_the_5_unimplemented_operations_are_exactly_these() -> None:
    """**목록이 줄어드는 것이 진척의 계측이다** (P2.md §2-19). 25 → 36 → 24 → 21 → **23**.

    ⭑ **이번에는 늘었고, 그것이 옳다** (`PLAN-SoT §9-〈88〉` 묶음 5·6 · 4차 동결 해제).
    `addUploadFile`·`replaceUploadGridFile` 은 **지금 화면이 필요로 하는데 계약이 침묵해서
    표에도 없던** op 이다 — 격자를 붙일 때마다 본체 전체가 재전송되고 `uploadId` 가
    바뀌었고(`D-2`), 등록 전 축 뒤집기 버튼이 아예 서지 못했다(`D-4`). **그 침묵이 세
    회차 동안 구멍을 감췄다.** `§2-19` 의 「줄어드는 것이 진척」은 **표에 이미 있던 행**에
    대한 말이고, 없는 줄이 줄어들 수는 없다.

    ⭑ **셋째(`listPalettes`)는 표에 안 들었다** — 신설과 동시에 구현했다(`S1_REAL`).
    스윕은 21 → 24 를 예상했지만 **24 는 세 op 을 전부 501 로 두었을 때의 수**이고,
    그러면 `D-1`(실서버에서 렌더가 시작조차 안 된다)이 **그대로 남는다.**
    `searchDatasets` 때 세운 규칙 그대로다: 여는 회차에 만든다 (`〈80〉-㉯ 5` · `〈74〉-㉱`).

    ⭑ **S1 의 `W3` 는 이 수를 바꾸지 않았다** (`〈74〉-㉱` · `C1` 통과 조건 2) — 계약이 하나
    늘어난 `searchDatasets` 를 **여는 회차에 구현**해 표에 행을 더하지 않았다.
    ⭑ **`W5` 의 `P5` 레인이 셋을 뺐다** — `listProjects` · `getProject` ·
    `linkProjectDataset`. 이번에는 **줄어드는 것이 정상이다**: `S1-PLAN.md §4.2` 의 P5 행이
    「`linkProjectDataset` 이 여기서 열린다」고 미리 적었고, 화면 본체 두 op 이 함께 열렸다.
    남은 프로젝트 op 넷(`updateProject`·`deleteProject`·`setProjectStatus`·
    `unlinkProjectDataset`)은 P1 배정이라 그대로 있다 — 범위를 늘리지 않았다.
    ⚠ **그중 `updateProject` 는 `〈150〉` 으로 빠졌다** — 남은 셋만 P1 이다.

    ⭑ **2026-08-27 — `updateDataset` 이 빠져 23 → 22.** `〈127〉` Ted 판정 ㈎ 가 예고한
    수 그대로다(「구현하면 501 표가 23 → 22 로 준다」). **줄어드는 것이 진척의 계측이다.**
    같은 회차에 `listDatasetFieldSuggestions` 가 신설됐지만 **여는 회차에 구현**해
    표에 행을 더하지 않았다 — `searchDatasets`·`listPalettes` 때 세운 규칙 그대로다.

    ⭑ **2026-08-27 — `updateLab`·`updateProject` 가 빠져 22 → 20** (`〈150〉`).
    `〈149〉-㉱` 가 남긴 결손 2건이고, 둘 다 **「올린 뒤 고칠 길이 없다」의 잔여**였다.
    계약은 이미 완비라 **개정 없이 501 만 걷었다.**

    ⭑ **`P3` — `getDatasetLineage` 가 빠져 20 → 19.** 계보 그래프 화면의 조회 op 이고,
    **계약 개정이 0 건이다** — 계약은 처음부터 이 op 을 들고 있었고 라우트만 없었다.
    **줄어드는 것이 진척의 계측이다** (`P2.md §2-19`).

    ⭑ **`P5` 잔여 — 프로젝트 op 셋이 빠져 19 → 16.** `deleteProject`·`setProjectStatus`·
    `unlinkProjectDataset`. 위 문단의 「남은 프로젝트 op 넷 … P1 배정이라 그대로 있다」는
    **두 겹으로 낡았다** — ⑴ `updateProject` 는 `〈150〉` 으로 이미 열려 넷이 아니라 셋이었고,
    ⑵ 셋의 `P1` 배정은 정본과 어긋났다: `PRD_프로젝트:65` 가 S-02b 를 「… 소속 해제 ·
    프로젝트 닫기」로 정의하고 `Policy_프로젝트 §6`·`§8` 이 삭제·닫기·해제를 전부 E-05
    화면의 동작으로 적는다. **배정 표기를 실물에 맞춘 것이지 범위를 늘린 것이 아니다.**
    **줄어드는 것이 진척의 계측이다** (`P2.md §2-19`).
    
    ⭑ **병합 2026-09-02 — 5 → 7.** 다른 레인이 `downloadDatasetFile`·`getDownloadBytes` 를
    **임시 등재**했다(`〈278〉`-(다) 9차 동결 해제). 이 회차(C1b)는 계약 동결 + 파일 메타만이고,
    다운로드 집행 커밋(C2)이 둘을(그리고 `downloadDataset` 까지) 뺀다.
    **이 수가 7 에 머문 채 C2 가 닫히면 그것이 red 다.**
    """
    assert len(OPERATIONS) == 7
    assert REAL & {op.operation_id for op in OPERATIONS} == set()


def test_every_op_p2_took_out_has_a_behavioural_test_behind_it() -> None:
    """뺀 자리에 시험이 없으면 501 을 200 으로 바꾼 것과 다르지 않다 (P2-EXEC §4 W2 ⑸)."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    for operation_id, test_file in sorted(P2_REAL.items()):
        path = root / test_file
        assert path.is_file(), f"{operation_id} 를 501 표에서 뺐는데 시험 파일이 없다: {test_file}"
        assert operation_id in path.read_text(encoding="utf-8"), \
            f"{test_file} 이 {operation_id} 를 부르지 않는다 — 그 자리는 증명되지 않았다."


def test_codes_are_the_two_kinds() -> None:
    no_store = {op.operation_id for op in OPERATIONS if op.code == "NOT_IMPLEMENTED_NO_STORE"}
    p1 = {op.operation_id for op in OPERATIONS if op.code == "NOT_IMPLEMENTED_P1"}
    assert no_store == NO_STORE
    # 15 → 13: P5 가 `listProjects`·`getProject` 를 가져갔다
    # 13 → 15: `〈88〉` 묶음 5·6 이 등록 전 파일 조작 둘을 신설했다(저장 자리는 있고 로직이 P1)
    # 15 → 13: `〈150〉` 이 `updateLab`·`updateProject` 를 가져갔다 — **둘 다 P1 계열이었다.**
    #          `〈149〉-㉱` 가 남긴 결손 2건이고 둘 다 「올린 뒤 고칠 길이 없다」의 잔여다.
    #          **줄어드는 것이 진척의 계측이다** (`P2.md §2-19`).
    # 13 → 12: `P3` 이 `getDatasetLineage` 를 가져갔다 — 계보 그래프 화면의 조회 op 이다.
    # 12 →  9: `P5` 잔여가 프로젝트 op 셋을 가져갔다 (삭제·닫기·소속 해제).
    #  9 →  7: `P6` 이 `approveVerification`·`cancelVerification` 을 가져갔다.
    #          **둘은 저장 자리가 있었고 로직만 없던 쪽이다** — 검토 대기 표가 서면서
    #          「요청은 받는데 승인은 못 한다」가 될 자리라 같은 회차에 함께 열었다.
    #  7 →  4: `P7` 이 D8 집계 셋(`getDashboardSummary`·`getDataMap`·`listActivities`)을
    #          가져갔다. **셋 다 저장 자리는 있었고 집계만 없던 쪽이다** — `d8_activity` 는
    #          P0 이 세웠고 지표·맵의 재료는 D3·D4·D2·D6 에 이미 다 있었다.
    #  4 →  6: `〈278〉`-(다) 다운로드 둘의 **임시 등재**(C2 가 뺀다). `NO_STORE` 가 아닌 이유 —
    #          저장 자리는 `0009`(`d8_download.file_id`)가 이미 만들었다. ⚠ 같은 이유로
    #          `downloadDataset` 의 `NO_STORE` 도 낡았다 — C2 가 셋을 함께 걷는다.
    assert len(p1) == 6
    assert no_store & p1 == set()


@pytest.mark.parametrize("op", OPERATIONS, ids=lambda o: o.operation_id)
def test_returns_501_with_envelope(client: TestClient, op) -> None:
    url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{uploadId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{fileId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{renderId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{ticket}", "not-a-real-ticket")
    r = client.request(op.method, url, headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 501, f"{op.operation_id} 가 501 이 아니다 — 가짜 200 은 거짓말이다."
    body = r.json()
    assert body["code"] == op.code
    assert body["message"]
    assert body["details"]["operationId"] == op.operation_id


@pytest.mark.parametrize("op", OPERATIONS, ids=lambda o: o.operation_id)
def test_requires_subject(client: TestClient, op) -> None:
    url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{uploadId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{fileId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{renderId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{ticket}", "not-a-real-ticket")
    r = client.request(op.method, url)
    assert r.status_code == 401, "미구현이어도 인증은 건다 — 경계 밖에 오퍼레이션 목록을 열지 않는다."
    assert r.json()["code"] == "UNAUTHORIZED"


def test_404_is_never_used_for_unimplemented(client: TestClient) -> None:
    """404 는 「경계 밖」의 뜻으로 예약돼 있다 (PLAN-SoT §9-㊱)."""
    for op in OPERATIONS:
        url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{uploadId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{fileId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{renderId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{ticket}", "not-a-real-ticket")
        r = client.request(op.method, url, headers={"Authorization": f"Bearer {TOKEN}"})
        assert r.status_code != 404
