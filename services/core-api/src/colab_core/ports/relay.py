"""내부 표면 두 곳으로 나가는 **중계 Port** — viz-render(D7) · ai-service(D10).

왜 Port 인가
  둘 다 **다른 배포 단위**다. core-api 는 그쪽 코드를 import 하지 않고(`import-boundary`
  계약 1 — 배포 단위는 서로를 import 하지 않는다) HTTP seam 으로만 말한다.
  이 파일은 그 표면이고, 구현(전송)은 조립 루트 `app/relay.py` 에 있다.

**중계는 해석하지 않는다.**
  · 요청/응답은 `core-viz.yaml#RenderRequest`/`RenderJob` · `core-ai.yaml#LineageSuggestionResponse`
    를 **그대로** 지난다. 스키마를 재선언하지 않는다 — 같은 모양의 두 번째 선언은 갈라질 표면이다.
  · **타일 URL 을 중계하지 않는다** — 결과의 `tileUrlTemplate` 을 FE 가 직접 소비한다
    (`fe-core.yaml createPreviewRender` 산문 · `core-viz.yaml` 상단 주석).
  · **core-api 에 geo 라이브러리를 import 하지 않는다** (`CLAUDE.md §3-4` · `banned-import`).
    그리는 일은 전부 viz-render 안이다.
"""
from __future__ import annotations

from typing import Any, Protocol


class PreviewRenderPort(Protocol):
    """viz-render 중계. 실패하면 예외가 아니라 **호출자가 판정할 결과**를 돌려준다."""

    def create(self, *, lab_id: str, account_id: str, request: dict[str, Any]) -> dict[str, Any]:
        ...

    def get(self, *, lab_id: str, account_id: str, render_id: str) -> dict[str, Any] | None:
        ...

    def screenshot(self, *, lab_id: str, account_id: str,
                   request: dict[str, Any]) -> tuple[int, bytes, str | None]:
        """`createScreenshot` 중계 (`〈231〉` · 11차 해제). **JSON 이 아닌 답을 지난다** —
        200 은 `image/png` 바이트다. 상태·본문·`Content-Type` 셋을 그대로 돌려주고
        core-api 는 그림을 해석하지 않는다."""
        ...

    def lookup_value(self, *, lab_id: str, account_id: str,
                     request: dict[str, Any]) -> dict[str, Any]:
        """`lookupValue` 중계 (`〈294〉` · 15차 해제 · `V-2` 값 조회).

        **값을 지어내지 않는다** — 못 닿으면 예외이고 라우트가 503 으로 낸다.
        `available: false` 는 저쪽이 **읽어 보고 낸 사실**이지 못 물어봤을 때의 기본값이
        아니다. 둘을 같은 모양으로 접으면 「없다」가 「모른다」를 덮는다.
        """
        ...

    def lookup_value_timed(self, *, lab_id: str, account_id: str,
                           request: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
        """`lookup_value` ＋ **저쪽이 낸 `Server-Timing`** (`VL-1` · `PLAN-SoT §9 〈311〉`).

        몸통은 `lookup_value` 와 **한 글자도 다르지 않다.** 둘째 값은 viz-render 의 구간
        문자열이고 없으면 `None` 이다 — **해석하지 않고 지나 보낸다**(중계의 규율).
        `〈304〉` 가 「서버 단독 p95 `[미확인]`」으로 남긴 자리를 푸는 재료다.
        """
        ...

    def palettes(self, *, lab_id: str, account_id: str) -> dict[str, Any]:
        """`RenderStyle.palette` 값 집합 (`〈88〉` 묶음 4). **못 닿으면 예외다** —
        빈 목록은 「고를 것이 없다」는 답이지 「물어보지 못했다」가 아니다."""
        ...

    def reclaim_previews(self, *, lab_id: str, account_id: str, target_id: str,
                         file_ids: list[str]) -> dict[str, Any]:
        """`reclaimPreviews` 중계 (`DL-2` · 22차 해제 ㉯).

        **core 는 무엇을 지울지 고르지 않는다.** 넘기는 것은 방금 지워진 `d3_file.id`
        전부이고, `sources ⊆ fileIds` 판정도 산출물 자리도 viz-render 안이다 — 여기서
        키를 짓는 순간 D7 의 사실이 D3 코드로 옮겨 앉는다.

        ⚠ **못 닿으면 예외다.** 「지울 것이 없었다」와 「물어보지 못했다」를 같은 값으로
        접으면 삭제가 미리보기를 남긴 채 204 로 끝난다 — 계약 산문(「파일과 미리보기만
        지워져요」)이 거짓이 되는 자리다. 호출자는 그 예외에 삭제 전체를 되돌린다.
        """
        ...


class LineageSuggestionPort(Protocol):
    """ai-service 중계. **못 찾으면 정직한 빈 상태**다 — 억지 제안을 만들지 않는다
    (`CLAUDE.md §3 AI 응답 규격`). 0건도 `degraded` 와 `scope` 를 달고 온다.

    ⭑ **`upload_id` 가 아니라 `file_meta` 를 넘긴다.** 계약
    (`core-ai.yaml LineageSuggestionRequest`)이 `file`(`UploadedFileMeta`)을 required 로
    두고 `additionalProperties: false` 다. 업로드 식별자는 그 계약 어디에도 없다 —
    ai-service 는 업로드 원장을 읽지 못하므로 식별자만으로는 아무것도 할 수 없다.
    **읽는 것은 core-api 의 일이고, 넘기는 것은 읽은 값이다.**

    ⭑ **⟨K3 `WU1b` 2026-09-24⟩ `candidates` 도 읽은 값이다.** ai-service 는 카탈로그에
    닿지 못하므로(`CLAUDE.md §3-1`) 스스로 후보를 찾을 수 없다 — **찾는 것은 D3 의 주인인
    core-api 이고 매기는 것만 저쪽 일이다**(`〈72〉-㉮` 검색과 같은 분담). 그래서 되받은
    제안의 `parentDatasetId` 가 **보낸 후보 밖**이면 구현이 그것을 버린다: 신뢰하지 않는
    쪽에서 거르는 것이 계약 표류를 잡는 유일한 자리다(응답 `scope` 를 버리는 그 자리와 같다).

    ⭑ **⟨K3 `WU-S1b` 2026-09-24⟩ `processing_level` 은 사람이 고른 값이다.** 「부모 Lv ≤ 자기
    Lv」의 기준값이고 **거르는 것은 core-api 다**(`〈72〉-㉮` 분담) — 저쪽은 해석 단서로만 쓴다.
    ⚠ 안 골랐으면 **이 표면에 오지 않는다**: 기준값이 없으면 적격을 가를 수 없어 라우트가
    중계를 부르지 않고 정직한 빈 상태로 답한다(`routes/ingestion.LEVEL_REQUIRED_REASON`).

    ⭑ **⟨K3 `WU-S2` 2026-09-24⟩ `upload_axes`·`candidate_axes` 는 요청을 만든 그 값들이다.**
    되받은 제안의 `evidence` 를 **실제 값에 대조**하는 데 쓴다 — 중계가 DB 를 다시 읽지
    않는다(읽으면 「보낸 값」과 「검증에 쓴 값」이 갈려 인용 검증이 오라클 구실을 못 한다).
    ⚠ **타입을 `Any` 로 적는다.** 구체 타입은 `domains.d3_lineage_signals` 의
    `UploadAxes`·`CandidateAxes` 인데, Port 는 domains **아래 층**이라 그 모듈을 import 하면
    층 계약(`gates/config/importlinter.ini` core-layers)이 깨진다. 이름을 여기 적어 두는 것으로
    갈음한다 — 조립 루트(`app/relay.py`)는 그 타입을 그대로 부른다.
    """

    def suggest(self, *, lab_id: str, lab_name: str, account_id: str,
                file_meta: dict[str, Any], candidates: list[dict[str, Any]],
                searched_count: int, dataset_name_draft: str | None,
                subject: str | None, processing_level: int,
                upload_axes: Any, candidate_axes: dict[str, Any]) -> dict[str, Any]:
        ...


class QueryInterpretationPort(Protocol):
    """ai-service **질의 해석** 중계 (`core-ai.yaml searchDatasets` · `〈80〉-㉯ 5`).

    ⚠ **2026-08-25 판정 ㈎ 로 이 표면의 몫이 줄었다.** `K4-a` 까지는 저쪽이 `tsvector` 를
    직접 던져 후보·순위를 돌려줬다 — D10 이 D3 테이블에 붙는 `CLAUDE.md §3-1` 위반이었다.
    **AI 는 이제 검색어·주제·해석 출처만 돌려준다.** 찾고 매기는 일도, 카드 값을 붙이는
    일도 D3·D2 의 주인인 core-api 가 한다 (`〈72〉-㉮`).

    **못 읽으면 정직한 빈 상태**다 — 검색어를 지어내지 않는다. 뒤진 범위(`scope`)는
    호출자가 D3 에서 세어 붙인다: 세는 일이 이쪽 도메인이기 때문이다.
    """

    def interpret(self, *, lab_id: str, lab_name: str, account_id: str, query: str,
                  limit: int, cursor: str | None, searched_count: int) -> dict[str, Any]:
        ...
