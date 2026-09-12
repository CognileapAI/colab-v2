import json
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..kernel.scope import require_lab_scope

def pending_exports(session: Session, limit: int = 500) -> list[dict]:
    require_lab_scope(session)
    rows=session.execute(text("SELECT source_id,lab_id,occurred_at,payload FROM d5_operator_export WHERE receipt_hash IS NULL ORDER BY occurred_at,source_id LIMIT :limit"), {"limit": limit}).mappings()
    return [{**dict(r["payload"]),"source_id":r["source_id"].strip(),"lab_id":r["lab_id"].strip(),"occurred_at":r["occurred_at"].isoformat(),"source_table":"d5_operator_export"} for r in rows]

def ack_export(session: Session, receipt: dict) -> int:
    require_lab_scope(session)
    import hashlib, hmac
    row=session.execute(text("SELECT source_id,lab_id,occurred_at,payload FROM d5_operator_export WHERE source_id=:source AND receipt_hash IS NULL"),{"source":receipt["source_id"]}).mappings().one_or_none()
    if row is None:return 0
    exported={**dict(row["payload"]),"source_id":row["source_id"].strip(),"lab_id":row["lab_id"].strip(),"occurred_at":row["occurred_at"].isoformat(),"source_table":"d5_operator_export"}
    actual=hashlib.sha256(json.dumps(exported,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    expected=hashlib.sha256((receipt["source_id"]+receipt["content_hash"]).encode()).hexdigest()
    if not hmac.compare_digest(actual,receipt["content_hash"]) or not hmac.compare_digest(expected,receipt["receipt_hash"]):raise ValueError("receipt proof mismatch")
    return session.execute(text("UPDATE d5_operator_export SET receipt_hash=:receipt,received_at=now() WHERE source_id=:source AND receipt_hash IS NULL"),{"receipt":receipt["receipt_hash"],"source":receipt["source_id"]}).rowcount
