"""D8 Insight — 활동 기록(바꾼 일만) · 다운로드 이력 · 홈 대시보드 집계.

P0 은 저장 자리만 만들었고 **WU-P7 이 집계 3종을 열었다** —
`getDashboardSummary`·`getDataMap`·`listActivities`. 조립은 `app/routes/insight.py` 가 한다.

**이 파일은 자기 표(`d8_activity`)만 읽고 쓴다.** 요약·맵의 재료(데이터셋·계보·Verified·
프로젝트)는 D3·D4·D2·D6 의 사실이라 여기서 한 줄도 질의하지 않는다 — 조립 루트가
각 도메인의 모듈 함수로 받아 합친다 (`CLAUDE.md §3-1` · `routes/catalog.py` 와 같은 무늬).

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


#: 활동 문자열 — **정본이 값 집합을 안 닫았으므로 여기서 하나로 고정한다**
#: (`DataModel §6.1` 은 다섯을 예시로 열거할 뿐이고 `d8_activity.action` 에도 CHECK 가 없다).
#: 계약 `listActivities` 산문이 적은 다섯(올림 · 계보 고침 · 승인 · 프로젝트 만듦 · 지움)에
#: `ACTION_GRID_CHANGED`(P2 가 먼저 쓴 것)를 더한 것이 지금 쌓이는 전부다.
#: ⚠ **열람은 여기 없다** — 서버에 남기지 않는다(`Policy_홈_대시보드 §10`). 없는 것이 규칙의 실물이다.
ACTION_DATASET_ADDED = "데이터셋 등록"
ACTION_LINEAGE_CONFIRMED = "계보 확정"
ACTION_VERIFIED_APPROVED = "Verified 승인"
ACTION_PROJECT_CREATED = "프로젝트 만듦"
ACTION_PROJECT_DELETED = "프로젝트 지움"

_RECENT = text("""
    SELECT id, actor_account_id, action, target_kind, target_id, occurred_at
      FROM d8_activity
     ORDER BY occurred_at DESC, id DESC
""")


def recent_activities(session: Session) -> list[dict]:
    """활동 전체를 **시점 최신순**으로 (`Policy_홈_대시보드 §5`).

    연구실 경계는 RLS 가 이미 걸었다 — 여기에 `lab_id` 조건을 다시 적지 않는다
    (`routes/catalog.py:list_dataset_cores` 와 같은 규칙).

    **이름을 여기서 붙이지 않는다.** 행위자는 D1, 대상은 D3·D6 의 사실이고 이 표에는
    식별자만 있다. 붙이는 자리는 조립 루트다.
    """
    return [dict(r) for r in session.execute(_RECENT).mappings()]


# ── 다운로드 이력 ────────────────────────────────────────────────────────────
#: `ST-1`. 자리는 P0 이 만들어 두었고(`d8_download` · 마이그레이션 0건) 쓰는 자리가 없었다.
#: **append-only 트리거가 걸린 표다** — 한 번 쌓으면 고치지도 지우지도 못한다.
_INSERT_DOWNLOAD = text("""
    INSERT INTO d8_download (id, lab_id, account_id, dataset_id)
    VALUES (:id, current_lab_id(), :account, :dataset_id)
    RETURNING id
""")


def record_download(session: Session, *, account_id: Ulid, dataset_id: Ulid) -> str:
    """누가 언제 받았는지 한 줄 (`DataModel §6.2` · `Policy_데이터셋_상세 §8` 다운로드 행).

    **받은 횟수는 어느 화면에도 내리지 않는다** — 쌓기만 한다(정본 1.3 확정 ④).
    """
    return session.execute(_INSERT_DOWNLOAD, {
        "id": str(Ulid.generate()), "account": str(account_id),
        "dataset_id": str(dataset_id),
    }).scalar_one()
