"""계보 레코드 생성 — 가공 방식은 관계에 부착한다 (DR-15 · DATAMODEL §4.2).

PoC 는 relation_type 이 항상 `derived`, description 이 항상 NULL 이었고
워커가 계보를 만들지 않았다. v2 워커는 파이프라인이 돌 때 관계 정보(가공 방식·
파라미터)를 담은 계보 레코드를 만든다. 커밋(쓰기)은 사람 확인 뒤 P2 경로다 —
여기는 레코드의 형태와 불변식만 책임진다.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def make_lineage_record(
    *, parent_dataset_id: str, child_dataset_id: str, relation_type: str,
    method: str, params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not parent_dataset_id or not child_dataset_id:
        raise ValueError("계보 레코드에 부모/자식 데이터셋 ID 는 필수다")
    if parent_dataset_id == child_dataset_id:
        raise ValueError("자기 자신으로의 계보는 만들 수 없다")
    if not method or not method.strip():
        raise ValueError("가공 방식(method)은 공란일 수 없다 — DR-15 의 요점이다")
    return {
        "parent_dataset_id": parent_dataset_id,
        "child_dataset_id": child_dataset_id,
        "relation_type": relation_type,
        "method": method,
        "params": dict(params or {}),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
