"""D8 Insight — 활동 기록(바꾼 일만) · 다운로드 이력 · 홈 대시보드 집계.

P0 은 저장 자리만 만들었다. 집계 3종(`getDashboardSummary`·`getDataMap`·`listActivities`)은
P1 이며 지금은 501(NOT_IMPLEMENTED_P1) 로 응답한다 — 200 으로 빈 집계를 내리면 그건 거짓말이다.

**P2 가 쓰는 자리 하나** — `〈60〉` 좌표계·격자 변경 활동 기록.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid

#: `〈60〉-③` 이 못 박은 **그 문자열 그대로**.
#: `d8_activity.action` 에 CHECK 가 없는 것은 「아무 문자열이나 써도 된다」가 아니라
#: **정본 §6.1 이 값 집합을 안 닫았다**는 뜻이다. 레인마다 다른 문자열을 쓰면 활동 화면이
#: 뒤죽박죽이 되므로 여기서 하나로 고정한다.
ACTION_GRID_CHANGED = "좌표계·격자 변경"

_INSERT = text("""
    INSERT INTO d8_activity (id, lab_id, actor_account_id, action, target_kind, target_id)
    VALUES (:id, current_lab_id(), :actor, :action, :target_kind, :target_id)
    RETURNING id
""")


def record_activity(session: Session, *, actor_id: Ulid, action: str,
                    target_kind: str, target_id: Ulid) -> str:
    """활동 한 줄. **append-only 트리거가 걸린 표라 고치거나 지울 수 없다** — 그래서
    누가 언제 바꿨는지가 지워지지 않는 기록으로 남는다 (`〈60〉`). 스키마 변경 없음.
    """
    if target_kind not in ("데이터셋", "프로젝트"):
        raise ValueError(f"활동 대상 종류가 둘 중 하나가 아니다: {target_kind!r}")
    return session.execute(_INSERT, {
        "id": str(Ulid.generate()), "actor": str(actor_id), "action": action,
        "target_kind": target_kind, "target_id": str(target_id),
    }).scalar_one()
