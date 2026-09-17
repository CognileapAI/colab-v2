"""Compose catalogue ownership and access policy without cross-domain table reads.

⭑ **⟨2026-09-18 develop 동기화⟩ 두 갈래가 이 한 자리에서 합쳐진다.**
  · `dataset_labs` — 관리자(교수·시스템)의 대상 연구실 (`0033_admin_body_access`)
  · `ownership`    — 비공개 자료 소유자 (`0032_private_owner_access`)
  조립을 두 벌로 두면 한쪽 호출 경로만 좁은 판정을 받는다. 이름은 하나다.
"""
from sqlalchemy.orm import Session

from ..domains import d2_access, d3_catalog
from ..domains.d3_ownership import DatasetOwnershipAdapter


def dataset_access(db: Session) -> d2_access.DatasetAccessAdapter:
    return d2_access.DatasetAccessAdapter(
        db, DatasetOwnershipAdapter(db), lambda ids: d3_catalog.dataset_labs(db, ids))
