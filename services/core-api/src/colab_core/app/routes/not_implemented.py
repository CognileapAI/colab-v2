"""아직 구현하지 않은 23 개 오퍼레이션 — **501 + ErrorEnvelope**.

두 종으로 나눈다 (NIGHT-20260823 §3).
  · `NOT_IMPLEMENTED_NO_STORE` — 저장처 자체가 P0 스키마에 없다(접근 요청 4 · Verified 요청 2 ·
    다운로드 1). 구현 전에 스키마가 먼저 필요하다는 사실을 코드가 말한다.
  · `NOT_IMPLEMENTED_P1` — 저장 자리는 있고 로직이 P1 이다.

**200 으로 가짜 값을 내리지 않는다.** 하나 구현할 때마다 이 표가 한 줄씩 줄고,
그 줄어듦이 진척의 계측이 된다. **뺀 자리마다 실동작 시험이 있어야 한다** (`P2.md §2-19`).

P2 가 열둘을 가져갔다 (36 → 24) —
  업로드 6 `createUpload` `getUploadStatus` `createDataset` `addDatasetFile`
          `replaceDatasetGridFile` `deleteDatasetGridFile`
  계보 3  `addLineageParent` `removeLineageParent` `confirmLineage`
  중계 3  `createPreviewRender` `getPreviewRender` `listUploadLineageSuggestions`

**남긴 것과 이유** (`P2-EXEC §4 W2 P2-api`)
  · ~~`updateDataset`~~ — **구현했다 (2026-08-27 · `〈127〉` Ted 판정 ㈎).**
    `#36`(설명 결손 2건)을 채울 **공개 경로가 이것뿐이었다** — 나머지 셋은 막혀 있다:
    `deleteDataset` 501 · 재적재는 12 → 14 를 만들고 · DB 직접 UPDATE 는 `㊾-③` 위반.
    Ted 판정 ㈏(2026-08-27)로 대상이 넓어졌다 — 원천 표기·가공 단계·대표 조각·변수·
    좌표계·기간까지. **표가 23 → 22 로 준다.**
  · ~~`getDatasetLineage`~~ — **구현했다 (P3 · 계보 그래프).** 그래프를 그리는 함수는
    P2 가 만들어 두었고(`routes/lineage.py:lineage_graph`), 없던 것은 그 함수를 부를
    GET 라우트 하나였다. 종전 기재는 「이 조회 op 자체는 P1 배정이라 범위를 늘리지
    않는다」였는데, **`P1` 이 닫힌 뒤에도 op 은 501 로 남아 있었다** — 산문이 낡은
    자리다. 계보 그래프 화면(`P3`)은 이 op 없이 설 수 없다. **표가 23 → 22 로 준다.**

**S1 의 `P5` 레인이 셋을 가져갔다 (24 → 21)** — `listProjects` · `getProject` ·
`linkProjectDataset`. 앞의 둘은 S-02·S-02b 화면 본체이고, 셋째는 `S1-PLAN.md §4.2` 의
P5 행이 「여기서 열린다」고 지목한 op 이다. **셋 다 실동작 시험이 뒤에 있다**
(`tests/test_project_screens.py`) — 그 규칙이 없으면 501 을 200 으로 바꾼 것과 다르지 않다.

**`P5` 잔여 회차가 남은 프로젝트 op 을 전부 가져갔다 (23 → 20)** — `deleteProject` ·
`setProjectStatus` · `unlinkProjectDataset`. ⭑ **위 문단의 「넷」은 낡은 수였다** —
`updateProject` 는 그 뒤 `〈150〉` 으로 이미 열렸는데 이 산문이 안 따라갔다. 셋이 맞다.

**왜 배정을 넘었는가.** 셋 다 `NOT_IMPLEMENTED_P1` 로 적혀 있었으나 **정본은 셋 다
E-05 화면의 동작으로 적었다** — `PRD_프로젝트:65` 가 S-02b 를 「… 소속 해제 · 프로젝트
닫기」로 정의하고, `Policy_프로젝트 §6` 의 허용 행동이 「만들기 · 정보 수정 · 소속 해제 ·
닫기 · 다시 열기」이며, `§8` 삭제 버튼 행이 그 자리를 「상세 · 데이터셋 0건」으로 못 박는다.
**낡은 배정 표기를 실물에 맞춘 것이지 범위를 늘린 것이 아니다** (`CLAUDE.md §5`).
셋 다 실동작 시험이 뒤에 있다 (`tests/test_project_screens.py`).
"""
from __future__ import annotations

import dataclasses

from fastapi import Depends, FastAPI

from ...kernel import errors
from ...kernel.auth import Subject
from ..deps import current_subject


@dataclasses.dataclass(frozen=True)
class Op:
    operation_id: str
    method: str
    path: str
    code: str


#: 계약(`contracts/seams/fe-core.yaml`) 의 오퍼레이션 중 실동작을 뺀 나머지.
#: ⭑ **23 → 22** — `getDatasetLineage` 구현 (P3 · 계보 그래프. 윗 문단이 이유를 적었다).
#: ⭑ 종전 기재는 「49 개 중 26 개」였다 — **둘 다 1 씩 낮았고 차 23 만 우연히 맞았다**
#: (2026-08-26 실측 정정: 계약 `operationId` 고유 50 · 이 표 23). 같은 자리의 네 번째 오기다.
#: 차만 맞아서 `test_route_table.py` 도 `len(OPERATIONS)` 단언도 red 를 내지 않았다 —
#: **산문이 조용히 틀려 있던 자리**이고, 그래서 실물 대조로만 잡힌다.
#: 25 → 36(D2c 신설 11) → **24**(P2 구현 12) → **24 유지**(S1 W3 — `searchDatasets` 를
#: 신설과 동시에 구현했으므로 표에 더할 행이 없다. `〈80〉-㉯ 5` · `〈74〉-㉱`)
#: → **21**(S1 W5 `P5` — 프로젝트 목록·상세·연결 셋)
#: → **23**(S1 4차 동결 해제 — `addUploadFile`·`replaceUploadGridFile` 신설.
#:    `listPalettes` 는 신설과 동시에 구현해 표에 안 든다. `〈88〉` 묶음 4·5·6).
#: → **20**(`P5` 잔여 — `deleteProject`·`setProjectStatus`·`unlinkProjectDataset`.
#:    윗 문단이 배정을 넘은 이유를 적었다).
#: → **9**(`P7` 연구실 대시보드 — D8 집계 셋 `getDashboardSummary`·`getDataMap`·
#:    `listActivities`). **계약 개정이 0 건이다** — 계약은 처음부터 이 셋을 들고 있었고
#:    라우트만 없었다(`routes/insight.py`). **셋이 한 회차에 나가는 이유** = 지표·맵·활동은
#:    한 화면의 세 구획이고, 하나라도 501 이면 그 화면은 「불러오지 못했어요」로만 선다
#:    (`CLAUDE.md §5` 부분 완료 금지). 셋 다 실동작 시험이 뒤에 있다
#:    (`tests/test_dashboard.py` — **연구실 경계 음성 포함**).
#: → **12**(`P6` 승인 처리 — 접근 요청 4 ＋ Verified 4. **여덟이 한 회차에 나간다**).
#:    앞의 여섯은 `NOT_IMPLEMENTED_NO_STORE` 였고 그 사유(「저장처 자체가 P0 스키마에 없다」)를
#:    마이그레이션 `0010` 이 없앴다 — `d2_dataset_access_request`·`d2_verification_request`.
#:    뒤의 둘(`approveVerification`·`cancelVerification`)은 `NOT_IMPLEMENTED_P1` 이었다.
#:    **함께 뺀 이유** — 검토 대기를 만들 수 있는데 승인할 수 없으면 그 회차의 산출은
#:    「쌓이기만 하는 대기줄」이다. 요청 op 만 열고 처리 op 을 남기는 절단은 정본 §7.1·§7.2 의
#:    전이표를 반만 세우는 것이라 부분 완료가 된다 (`CLAUDE.md §5`).
#:    여덟 다 실동작 시험이 뒤에 있다 (`tests/test_approval.py` — 음성 다섯 포함).
#: 이 표와 계약의 대조는 `tests/test_route_table.py` 가 오라클로 검사한다.
OPERATIONS: tuple[Op, ...] = (
    Op("deleteDataset", "DELETE", "/datasets/{datasetId}", "NOT_IMPLEMENTED_P1"),
    Op("getDatasetDeletionImpact", "GET", "/datasets/{datasetId}/deletion-impact",
       "NOT_IMPLEMENTED_P1"),
    Op("downloadDataset", "GET", "/datasets/{datasetId}/download", "NOT_IMPLEMENTED_NO_STORE"),
    # ── D2c 신설 11 중 P2 가 안 가져간 둘 (윗 문단이 이유를 적었다) ──
    # ── ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 5·6⟩ 등록 **전** 세계의 파일 조작 둘 ──
    #    **표가 21 → 23 으로 는다. 퇴행이 아니다** — 두 op 은 지금 화면이 필요로 하는데
    #    계약이 침묵해서 표에도 없던 것이고, 그 침묵이 `D-2`·`D-4` 를 세 회차 동안 감췄다.
    #    `P2.md §2-19` 의 「목록이 줄어드는 것이 진척의 계측」은 **표에 이미 있던 행**에
    #    대한 말이다. 없는 줄이 줄어들 수는 없다.
    #    ⚠ 셋째(`listPalettes`)는 여기 없다 — **신설과 동시에 구현했다**(`routes/preview.py`).
    #    `searchDatasets` 때와 같은 규칙이다(`〈80〉-㉯ 5`): 계약에 열어 두고 안 만들면 표가 는다.
    Op("addUploadFile", "POST", "/uploads/{uploadId}/files", "NOT_IMPLEMENTED_P1"),
    Op("replaceUploadGridFile", "PUT", "/uploads/{uploadId}/files/{fileId}",
       "NOT_IMPLEMENTED_P1"),
)

_MESSAGE = {
    "NOT_IMPLEMENTED_NO_STORE": "아직 저장처가 없다 — P0 스키마에 이 기록의 자리가 없다.",
    "NOT_IMPLEMENTED_P1": "아직 구현하지 않았다 — P1 범위다.",
}


def _handler(op: Op):
    # 미구현이어도 **인증은 건다.** 인증 없이 501 을 내리면 경계 밖에서 오퍼레이션 목록을 읽게 된다.
    def endpoint(_subject: Subject = Depends(current_subject)) -> None:
        raise errors.ApiError(501, op.code, _MESSAGE[op.code], {"operationId": op.operation_id})

    endpoint.__name__ = op.operation_id
    return endpoint


def register(app: FastAPI, *, prefix: str) -> None:
    for op in OPERATIONS:
        app.add_api_route(
            prefix + op.path,
            _handler(op),
            methods=[op.method],
            name=op.operation_id,
            include_in_schema=False,
        )
