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


class LineageSuggestionPort(Protocol):
    """ai-service 중계. **못 찾으면 정직한 빈 상태**다 — 억지 제안을 만들지 않는다
    (`CLAUDE.md §3 AI 응답 규격`). 0건도 `degraded` 와 `scope` 를 달고 온다."""

    def suggest(self, *, lab_id: str, lab_name: str, account_id: str,
                upload_id: str, searched_count: int,
                dataset_name_draft: str | None, subject: str | None) -> dict[str, Any]:
        ...
