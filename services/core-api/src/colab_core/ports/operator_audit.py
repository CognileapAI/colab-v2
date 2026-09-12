from __future__ import annotations
from typing import Protocol
from sqlalchemy.orm import Session

class AuditExportPort(Protocol):
    def pending(self, session: Session, limit: int) -> list[dict]: ...
    def ack(self, session: Session, source_id: str, receipt_hash: str) -> None: ...
