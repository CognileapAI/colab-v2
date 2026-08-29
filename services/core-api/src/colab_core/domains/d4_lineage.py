"""D4 Lineage — 관계(부모 여럿) · 확인 기록. **사람이 확인한 것만 저장된다.**

D10 이 이 도메인에 쓰는 경로는 존재하지 않는다 (CLAUDE.md §3-2). 여기에도 만들지 않는다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.lineage import LV_CAP, LineageSummary

# 주입력 부모의 최대 Lv 를 재귀로 센다 — Lv 는 컬럼이 아니라 계산이다 (PLAN-SoT §9-⑳).
# 보조입력은 Lv 계산에서 빠진다 (common.json#/$defs/ParentRole).
#
# **재귀항에 둘이 걸려 있다 — 둘 다 정본에서 나온다 (`PLAN-SoT §9 〈133〉`).**
#
# ⑴ `UNION`(중복 제거). `UNION ALL` 이면 CTE 가 뽑는 것은 **노드가 아니라 경로**다.
#    다이아몬드 `A → {B, C} → D` 가 k 겹 쌓이면 행 수가 **2^k** 로 간다. 그리고
#    다이아몬드는 **합법이고 순환이 아니다** — `would_create_cycle` 이 막는 그래프가
#    아니다. 실측 = 마름모 18 겹에서 `listDatasets` 가 **9.4 초**였다.
#    `catalog.py` 의 목록·상세가 둘 다 `summaries()` 를 부르므로
#    **카탈로그를 여는 것만으로 터졌다.**
#
# ⑵ `LEAST(p.level + 1, LV_CAP)` (깊이 접기). `POL-020` 이 Lv 를 상한 2 로 자르므로
#    뿌리에서 2 홉을 넘어가면 **값이 바뀌지 않는다.** 절단이 아니라 **볼 이유가 없는
#    곳을 안 보는 것**이고, 근사가 아니라 정확한 의미다.
#
#    ⚠ **재귀를 멈추는 것(`WHERE p.level < LV_CAP`)이 아니라 값을 접는 것이다.**
#    멈추면 상한보다 깊은 노드는 `depth` 행이 아예 안 생겨 부모 Lv 가 NULL 이 되고
#    **Lv0 으로 떨어진다** — 원자료가 아닌 것을 원자료라고 말하게 된다. 실제로 그렇게
#    틀렸다. 접으면 값이 `LV_CAP` 에서 고정되고, `UNION` 이 (노드, 레벨) 쌍을 중복
#    제거하므로 **새 쌍이 안 나오는 순간 재귀가 끝난다.** 행 수 상한 = 노드 × (LV_CAP+1).
#
#    **오류를 내지 않는다** — `POL-020` 은 깊은 사슬을 자르기만 하고 금지하지
#    않으므로, 상한 초과를 오류로 만들면 정본이 허용한 데이터를 막게 된다.
_SUMMARY = text(f"""
    WITH RECURSIVE depth(dataset_id, level) AS (
        SELECT d.id, 0
          FROM d3_dataset d
         WHERE NOT EXISTS (
             SELECT 1 FROM d4_lineage_edge e
              WHERE e.child_dataset_id = d.id AND e.parent_role = '주입력'
         )
        UNION
        SELECT e.child_dataset_id, LEAST(p.level + 1, {LV_CAP})
          FROM d4_lineage_edge e
          JOIN depth p ON p.dataset_id = e.parent_dataset_id
         WHERE e.parent_role = '주입력'
    )
    SELECT t.dataset_id,
           (SELECT count(*) FROM d4_lineage_edge e WHERE e.child_dataset_id = t.dataset_id)
               AS parent_count,
           (SELECT max(d.level) FROM depth d
             JOIN d4_lineage_edge e ON e.parent_dataset_id = d.dataset_id
            WHERE e.child_dataset_id = t.dataset_id AND e.parent_role = '주입력')
               AS max_primary_parent_level,
           EXISTS (SELECT 1 FROM d4_lineage_unknown u WHERE u.dataset_id = t.dataset_id)
               AS marked_unknown
      FROM unnest(CAST(:ids AS char(26)[])) AS t(dataset_id)
""")


# ── 쓰기 — **사람이 확인한 것만 들어온다** ──────────────────────────────────
#
# D10 이 이 함수들에 닿는 경로는 없다. AI 제안은 `listUploadLineageSuggestions` 로 **읽혀
# 나갈** 뿐이고, 저장은 사람이 `createDataset`·`addLineageParent` 를 눌렀을 때만 일어난다
# (`CLAUDE.md §3-2` · `ai-no-lineage-write` 게이트).

#: 계보 관계가 **되돌릴 수 없는 것**이라 세 가지를 관계 삽입 **전에** 막는다.
#:   ① 자기부모 `A→A`  ② 순환 `A→B→A`(길이 무관)  ③ 같은 쌍 두 번
#: ①③ 은 DB 제약이 이미 있고(`CHECK (child <> parent)` · `UNIQUE(child, parent)`),
#: ②는 **DB 가 못 막는다** — 그래서 여기 재귀 질의가 있다. `DR-15` 가 PoC 의 순환 감지를
#: 계승감으로 지목한 자리이고, 한번 들어가면 *어느 행이 오염됐는가* 를 가릴 정보가
#: 바로 그 기록으로 지워진다.
_REACHES = text("""
    WITH RECURSIVE up(dataset_id) AS (
        -- `ulid` 도메인으로 캐스트한다. `char(26)` 로 적으면 재귀항(`bpchar`)과 타입이
        -- 어긋나 PostgreSQL 이 질의를 거부한다 — 실제로 그렇게 터졌다.
        SELECT CAST(:from_id AS ulid)
        UNION
        SELECT e.parent_dataset_id
          FROM d4_lineage_edge e
          JOIN up ON up.dataset_id = e.child_dataset_id
    )
    SELECT 1 FROM up WHERE dataset_id = :to_id LIMIT 1
""")

_INSERT_EDGE = text("""
    INSERT INTO d4_lineage_edge
      (id, lab_id, child_dataset_id, parent_dataset_id, parent_role, method, origin,
       confirmed_by_account_id)
    VALUES (:id, current_lab_id(), :child, :parent, :role, :method, :origin, :confirmed_by)
    RETURNING id
""")

_DELETE_EDGE = text("""
    DELETE FROM d4_lineage_edge
     WHERE child_dataset_id = :child AND parent_dataset_id = :parent
     RETURNING id
""")

_MARK_UNKNOWN = text("""
    INSERT INTO d4_lineage_unknown (dataset_id, lab_id, marked_by_account_id)
    VALUES (:dataset_id, current_lab_id(), :actor)
    ON CONFLICT (dataset_id) DO NOTHING
""")

_CLEAR_UNKNOWN = text("DELETE FROM d4_lineage_unknown WHERE dataset_id = :dataset_id")

_EDGES_OF = text("""
    SELECT e.child_dataset_id, e.parent_dataset_id, e.parent_role, e.method, e.origin,
           e.confirmed_at, e.confirmed_by_account_id, a.name AS confirmed_by_name
      FROM d4_lineage_edge e
      JOIN d1_account a ON a.id = e.confirmed_by_account_id
     WHERE e.child_dataset_id = :dataset_id OR e.parent_dataset_id = :dataset_id
     ORDER BY e.confirmed_at, e.id
""")

# 확인 기록(`lineage_confirmed_at`)은 **`d3_dataset` 의 열**이라 여기서 쓰지 않는다 —
# D4 가 D3 테이블을 직접 만지면 불변규칙 1 위반이다. 그 쓰기는 `d3_catalog.confirm_lineage`.


class LineageCycle(Exception):
    """순환·자기부모. 호출자가 409 로 바꾼다."""


#: 계보 쓰기를 연구실 단위로 줄 세우는 락 (`PLAN-SoT §9 〈141〉` · 부차 결함 `D-B`).
#:
#: **`xact` 다 — 세션 락이 아니다.** 세션 단위로 잡으면 커넥션이 풀로 돌아가도 락이
#: 남아 다음 요청이 남의 락에 걸린다. 수명이 「요청 하나 = 트랜잭션 하나」와 같아야 한다.
#:
#: **열쇠는 `current_lab_id()` 에서 나온다** — 전역 락이면 한 연구실의 계보 쓰기가
#: 남의 연구실을 멈춘다. 경계가 이미 스코프 커널로 주입돼 있으므로 그 값을 그대로 쓴다.
_LOCK_LAB = text("SELECT pg_advisory_xact_lock(hashtext(current_lab_id()::text))")


def lock_lab_for_lineage_write(session: Session) -> None:
    """**검사와 삽입 사이를 닫는다.**

    `would_create_cycle` 의 SELECT 와 `_INSERT_EDGE` 사이에는 락이 하나도 없었고
    트랜잭션은 READ COMMITTED 다(`app/deps.py`). 그래서 `A → B` 와 `B → A` 를 두
    커넥션이 동시에 붙이면 **둘 다 검사를 통과하고 둘 다 삽입해 순환이 생긴다** —
    어느 쪽도 혼자서는 순환이 아니고, 상대가 커밋 전이라 서로를 못 본다.

    **그냥 두면 안 되는 이유** — 순환이 한 번 들어가면 `_SUMMARY` 의 재귀가 그 위를
    돌고, `deleteDataset` 이 501 이라 **지울 수단이 없다.** `〈133〉` 이 깊이를 접어
    무한 재귀는 막았지만 **순환 자체를 막는 것은 이 락뿐이다.**

    ⚠ **반드시 검사보다 먼저 부른다.** 검사 뒤에 잡으면 창이 그대로 남는다 —
    두 요청이 나란히 검사를 통과한 다음 차례로 락을 잡고 차례로 삽입한다.
    """
    session.execute(_LOCK_LAB)


def would_create_cycle(session: Session, *, child_id: Ulid, parent_id: Ulid) -> bool:
    """`parent → … → child` 가 이미 있으면, `child ← parent` 를 붙이는 순간 순환이다.

    **자기부모(`child == parent`)도 여기서 참이다** — 재귀 시작점이 자기 자신이라
    첫 행에서 걸린다. 규칙 하나로 둘을 다 막는다.
    """
    return session.execute(_REACHES, {
        "from_id": str(parent_id), "to_id": str(child_id)}).first() is not None


def add_parent(session: Session, *, child_id: Ulid, parent_id: Ulid, parent_role: str,
               method: str | None, origin: str, confirmed_by: Ulid) -> str:
    """관계 한 쌍. **확인 기록이 NOT NULL 이라 「누가 확인했는지」 없이 들어갈 수 없다.**"""
    if parent_role not in ("주입력", "보조입력"):
        raise ValueError(f"부모 역할이 2값 밖이다: {parent_role!r}")
    # 값 셋 = `ai`(AI 제안 → **사람이 확인**) · `manual`(사람이 손으로 이음) ·
    # `processed`(가공으로 자동 생성 — 생산 경로는 아직 없다, `PLAN-SoT §9 〈205〉`).
    # ⚠ `ai` 는 「AI 가 만들었다」가 아니다 — AI 는 계보를 쓰지 않는다 (`CLAUDE.md §3-2`).
    if origin not in ("ai", "manual", "processed"):
        raise ValueError(f"만들어진 경로가 3값 밖이다: {origin!r}")
    # **락이 검사보다 먼저다** (`〈141〉`). 순서가 곧 이 수정의 전부다 —
    # 검사 뒤에 잡으면 두 요청이 나란히 검사를 통과한 뒤 차례로 삽입해 순환이 남는다.
    # 값 검사(위 두 줄)는 DB 를 안 보므로 락 밖에 둔다 — 잘못된 요청이 남의 쓰기를
    # 기다리게 할 이유가 없다.
    lock_lab_for_lineage_write(session)
    if would_create_cycle(session, child_id=child_id, parent_id=parent_id):
        raise LineageCycle(f"{parent_id} → {child_id} 를 붙이면 계보에 순환이 생긴다.")
    edge_id = session.execute(_INSERT_EDGE, {
        "id": str(Ulid.generate()), "child": str(child_id), "parent": str(parent_id),
        "role": parent_role, "method": method, "origin": origin,
        "confirmed_by": str(confirmed_by),
    }).scalar_one()
    # 관계가 붙으면 `기록 없음` 표시는 사라진다 (DataModel §4.2).
    session.execute(_CLEAR_UNKNOWN, {"dataset_id": str(child_id)})
    return edge_id


def remove_parent(session: Session, *, child_id: Ulid, parent_id: Ulid) -> bool:
    """관계 한 쌍만 지운다 — **데이터셋은 지워지지 않는다.**"""
    return session.execute(_DELETE_EDGE, {
        "child": str(child_id), "parent": str(parent_id)}).first() is not None


def mark_unknown(session: Session, *, dataset_id: Ulid, actor_id: Ulid) -> None:
    """부모를 모르는 채 등록했다는 표시. **근거 없는 추측을 사실처럼 기록하지 않기 위한 자리.**"""
    session.execute(_MARK_UNKNOWN, {"dataset_id": str(dataset_id), "actor": str(actor_id)})


def is_unknown(session: Session, dataset_id: Ulid) -> bool:
    return session.execute(
        text("SELECT 1 FROM d4_lineage_unknown WHERE dataset_id = :id"),
        {"id": str(dataset_id)}).first() is not None


def edges_of(session: Session, dataset_id: Ulid) -> list[dict]:
    """이 데이터셋이 자식이거나 부모인 관계 전부. 그래프 조립은 app 이 한다."""
    return [dict(r) for r in
            session.execute(_EDGES_OF, {"dataset_id": str(dataset_id)}).mappings()]


class LineageSummaryAdapter:
    """`ports.LineageSummaryPort` 의 D4 쪽 구현 — **읽기 전용**이다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def summaries(self, dataset_ids: list[Ulid]) -> dict[str, LineageSummary]:
        if not dataset_ids:
            return {}
        rows = self._session.execute(_SUMMARY, {"ids": [str(i) for i in dataset_ids]}).mappings()
        return {
            r["dataset_id"]: LineageSummary(
                parent_count=int(r["parent_count"]),
                max_primary_parent_level=(
                    None if r["max_primary_parent_level"] is None
                    else int(r["max_primary_parent_level"])
                ),
                marked_unknown=bool(r["marked_unknown"]),
            )
            for r in rows
        }
