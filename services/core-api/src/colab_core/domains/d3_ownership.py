"""D3 ownership facts, constrained by both lab and current account."""
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..kernel.ids import Ulid

_OWNED = text("""
    SELECT id FROM d3_dataset
    WHERE id = ANY(CAST(:ids AS char(26)[]))
      AND lab_id = current_lab_id()
      AND owner_account_id = current_account_id()
""")

class DatasetOwnershipAdapter:
    def __init__(self, session: Session) -> None:
        self._session = session

    def owned_dataset_ids(self, dataset_ids: list[Ulid]) -> set[str]:
        if not dataset_ids:
            return set()
        return {str(row[0]) for row in self._session.execute(
            _OWNED, {"ids": [str(value) for value in dataset_ids]})}
