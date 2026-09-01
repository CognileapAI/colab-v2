"""D8 조립 — 연구실 대시보드 (WU-P7). `getDashboardSummary` · `getDataMap` · `listActivities`.

**정본은 `Policy_홈_대시보드` v1.5 하나다.** 이 파일이 계산하는 것은 전부 거기 축자로 있다 —
지표 구성(§5 「네 개를 넘기지 않는다」) · 계보 확정 = `확정` + `원천`(§5) · 미확정 =
`확인 필요` + `기록 없음`(§4) · 계보 네 값 전부 내림(§5 · 계약 산문) · 최신순 활동(§5).

**퍼센트를 만들지 않는다** (§5 축자 「퍼센트로 바꿔 적지 않는다」). 비율 막대는 화면이
`totalCount` 로 나눠 그린다 — 서버가 나누면 「59% 채웠다」가 값으로 굳는다.

**경계를 어떻게 건너나** (`CLAUDE.md §3-1`). 대시보드 한 화면은 D3(데이터셋·주제) ·
D4(계보) · D2(Verified) · D6(프로젝트) · D8(활동)의 사실을 합쳐야 그려진다. 도메인끼리
붙이지 않고 **이 조립 루트가 각 도메인의 모듈 함수로 받아 합친다** — `routes/catalog.py`
와 같은 무늬이고, 그래서 **새 Port 가 필요 없다.**

⭑ **계산을 다시 쓰지 않는다.** 계보 상태 판정(`d3_catalog.lineage_state`)과 카탈로그 한 행의
조립(`catalog._compose`)은 이미 있고, 데이터 맵의 묶는 기준은 **카탈로그 필터와 같아야 한다**
(§5 축자). 여기서 같은 판정을 다시 적으면 두 화면이 서로 다른 연구실을 보여주게 된다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...domains import d1_identity, d3_catalog, d6_project, d8_insight
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db
from .catalog import LINEAGE_STATES, PAGE_SIZE, _compose, _decode_cursor, _encode_cursor, _iso

router = APIRouter()

#: 데이터 맵 계보 축의 **줄 순서**. `확정` → `원천` → `확인 필요` → `기록 없음` 이다 —
#: 왼쪽 둘이 지표의 「계보 확정」을 이루고 오른쪽 둘이 「미확정」을 이루므로, 그 순서로
#: 놓아야 카드 안의 계산 한 줄(`확정 + 원천 = 지표의 계보 확정`)이 눈으로 읽힌다 (§5).
#: 값 자체는 카탈로그의 것을 그대로 쓴다 — `LINEAGE_STATES` 를 여기서 다시 적지 않는다.
MAP_STATE_ORDER = ("확정", "원천", "확인 필요", "기록 없음")
assert set(MAP_STATE_ORDER) == set(LINEAGE_STATES)

#: 지표의 「계보 확정」에 드는 상태 (§5 · §4 용어 정의 축자 —
#: 「원천은 가공 전 데이터가 없는 것이 정상이라 미확정으로 세지 않는다」).
SETTLED_STATES = ("확정", "원천")


@router.get("/dashboard/summary", name="getDashboardSummary")
def get_dashboard_summary(subject: Subject = Depends(current_subject),
                          db: Session = Depends(scoped_db)) -> dict:
    """요약 지표 넷 — 프로젝트 · 데이터셋 · 계보 확정 · Verified (§5).

    **다섯째 지표를 만들지 않는다.** `lineageUnsettledCount` 는 계보 확정 타일 아래에
    작게 붙는 값이지 독립된 타일이 아니다 (§8 「확정 개수를 크게, 아직 확인이 필요한
    건수를 아래 작게」) — 계약도 그래서 다섯 필드를 넷의 타일로 적었다.
    """
    rows = _compose(db)
    states = [row["lineageState"] for row in rows]
    return {
        "projectCount": len(d6_project.list_projects(db)),
        "datasetCount": len(rows),
        "lineageSettledCount": sum(1 for s in states if s in SETTLED_STATES),
        "lineageUnsettledCount": sum(1 for s in states if s not in SETTLED_STATES),
        "verifiedCount": sum(1 for row in rows if row["verified"]),
    }


@router.get("/dashboard/data-map", name="getDataMap")
def get_data_map(subject: Subject = Depends(current_subject),
                 db: Session = Depends(scoped_db)) -> dict:
    """데이터 맵 — 계보 상태별(위) · 주제별 (§5).

    **계보 네 값은 0이어도 줄을 지우지 않는다** (계약 산문 축자). 0건인 상태를 지우면
    화면은 「그런 상태는 없다」로 읽고, 채워야 할 칸이 있다는 사실 자체가 사라진다.

    ⚠ **주제가 없는 데이터셋은 주제 축에 줄을 만들지 않는다.** 계약이 `value` 를
    `minLength: 1` 로 적었고, 「미분류」 같은 이름을 서버가 지어내면 카탈로그 필터에
    없는 값이 화면에만 생긴다 — 묶는 기준이 카탈로그와 같아야 한다는 §5 를 깬다.
    그래서 두 축의 합이 서로 다를 수 있고, **분모는 언제나 `totalCount` 다.**
    """
    rows = _compose(db)
    by_state = {state: 0 for state in MAP_STATE_ORDER}
    by_topic: dict[str, int] = {}
    for row in rows:
        by_state[row["lineageState"]] += 1
        topic = row["topic"]
        if topic:
            by_topic[topic] = by_topic.get(topic, 0) + 1
    return {
        "totalCount": len(rows),
        "byLineageState": [{"value": s, "count": by_state[s]} for s in MAP_STATE_ORDER],
        # 큰 묶음이 먼저 — 같으면 이름순이라 회차마다 순서가 흔들리지 않는다.
        "byTopic": [{"value": v, "count": c}
                    for v, c in sorted(by_topic.items(), key=lambda kv: (-kv[1], kv[0]))],
    }


@router.get("/dashboard/activities", name="listActivities")
def list_activities(subject: Subject = Depends(current_subject),
                    db: Session = Depends(scoped_db),
                    cursor: str | None = Query(default=None)) -> dict:
    """최근 활동 — **바꾼 일만** (§5 · §10 · 계약 산문).

    **대상이 사라진 줄은 조용히 뺀다** (§9 축자 「이 데이터는 더 이상 없어요 · 목록에서
    항목을 조용히 뺀다」). 묘비가 된 데이터셋·지워진 프로젝트의 이름을 지어내지 않는다.

    화면 상한(최근 3건)은 화면이 정한다 — 서버는 봉투 그대로 준다 (`routes/access.py`
    의 `listPendingAccessRequests` 와 같은 규칙).
    """
    named: list[dict] = []
    for row in d8_insight.recent_activities(db):
        target = _target(db, row["target_kind"], row["target_id"])
        if target is None:
            continue
        named.append({
            "activityId": row["id"],
            "actor": _actor(db, row["actor_account_id"]),
            "action": row["action"],
            "target": target,
            "occurredAt": _iso(row["occurred_at"]),
        })
    offset = _decode_cursor(cursor)
    page = named[offset:offset + PAGE_SIZE]
    return {
        "items": page,
        "totalCount": len(named),
        "nextCursor": (_encode_cursor(offset + PAGE_SIZE)
                       if offset + PAGE_SIZE < len(named) else None),
    }


def _actor(db: Session, account_id: str) -> dict:
    """행위자 이름은 **D1 이 말한다.** 없으면 식별자를 그대로 든다 — 지어내지 않는다."""
    row = d1_identity.find_account(db, Ulid(account_id))
    return {"accountId": account_id, "name": (row or {}).get("name") or account_id}


def _target(db: Session, kind: str, target_id: str) -> dict | None:
    """대상 이름은 **그 대상을 가진 도메인이 말한다** (D3 · D6). 사라졌으면 `None` (§9)."""
    if kind == "데이터셋":
        core = d3_catalog.find_dataset_core(db, Ulid(target_id))
        return None if core is None else {"kind": kind, "id": target_id, "name": core.name}
    record = d6_project.find_project(db, Ulid(target_id))
    return None if record is None else {"kind": kind, "id": target_id, "name": record.name}
