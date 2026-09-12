from __future__ import annotations
import json
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..kernel.scope import require_lab_scope
from ..kernel.ids import Ulid
_LAB=text("SELECT current_lab_id()")
_AUDIT=text("""INSERT INTO d3_operator_audit (id,source_id,lab_id,actor_id,target_id,action,before_snapshot,after_snapshot,occurred_at) VALUES (:id,:source_id,current_lab_id(),:actor,:target,:action,CAST(:before AS jsonb),CAST(:after AS jsonb),COALESCE(CAST(:at AS timestamptz),now()))""")
_EXPORT=text("""INSERT INTO d3_operator_export (id,source_id,lab_id,occurred_at,payload) VALUES (:id,:source_id,current_lab_id(),COALESCE(CAST(:at AS timestamptz),now()),CAST(:payload AS jsonb)) ON CONFLICT(source_id) DO NOTHING""")
def append_snapshot(session:Session,*,actor_id,target_id,action,before,after,occurred_at=None)->str:
    session.execute(_LAB).scalar_one(); source_id=str(Ulid.generate()); payload={"source_id":source_id,"actor_id":str(actor_id),"target_id":str(target_id),"action":action,"before":before,"after":after}; values={"id":str(Ulid.generate()),"source_id":source_id,"actor":str(actor_id),"target":str(target_id),"action":action,"before":json.dumps(before),"after":json.dumps(after),"at":occurred_at,"payload":json.dumps(payload)}
    session.execute(_AUDIT,values); session.execute(_EXPORT,{**values,"id":str(Ulid.generate())}); return source_id


def pending_exports(session: Session, limit: int = 500) -> list[dict]:
    require_lab_scope(session)
    rows=session.execute(text("SELECT source_id,lab_id,occurred_at,payload FROM d3_operator_export WHERE receipt_hash IS NULL ORDER BY occurred_at,source_id LIMIT :limit"), {"limit": limit}).mappings()
    return [{**dict(r["payload"]),"source_id":r["source_id"].strip(),"lab_id":r["lab_id"].strip(),"occurred_at":r["occurred_at"].isoformat(),"source_table":"d3_operator_export"} for r in rows]

def ack_export(session: Session, receipt: dict) -> int:
    require_lab_scope(session)
    import hashlib, hmac
    row=session.execute(text("SELECT source_id,lab_id,occurred_at,payload FROM d3_operator_export WHERE source_id=:source AND receipt_hash IS NULL"),{"source":receipt["source_id"]}).mappings().one_or_none()
    if row is None:return 0
    exported={**dict(row["payload"]),"source_id":row["source_id"].strip(),"lab_id":row["lab_id"].strip(),"occurred_at":row["occurred_at"].isoformat(),"source_table":"d3_operator_export"}
    actual=hashlib.sha256(json.dumps(exported,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    expected=hashlib.sha256((receipt["source_id"]+receipt["content_hash"]).encode()).hexdigest()
    if not hmac.compare_digest(actual,receipt["content_hash"]) or not hmac.compare_digest(expected,receipt["receipt_hash"]):raise ValueError("receipt proof mismatch")
    return session.execute(text("UPDATE d3_operator_export SET receipt_hash=:receipt,received_at=now() WHERE source_id=:source AND receipt_hash IS NULL"),{"receipt":receipt["receipt_hash"],"source":receipt["source_id"]}).rowcount


def append_deletion_snapshots(cursor, *, ids: list[str], actor_id: str) -> None:
    """Purge shares its existing transaction; no independent commit or target FK."""
    cursor.execute("SELECT current_lab_id()")
    if not cursor.fetchone()[0]:
        raise ValueError("operator lab scope is required")
    cursor.execute("SELECT d.id,dd.name,dd.summary FROM d3_dataset d LEFT JOIN d3_dataset_description dd ON dd.dataset_id=d.id WHERE d.id=any(%s) FOR UPDATE OF d", (ids,))
    rows = cursor.fetchall()
    if len(rows) != len(ids):
        raise ValueError("deletion snapshot target count mismatch")
    for target,name,summary in rows:
        source=str(Ulid.generate())
        before={"name":name,"summary":summary}
        payload={"source_id":source,"actor_id":actor_id,"target_id":target.strip(),"action":"dataset.deleted","before":before,"after":None}
        cursor.execute("""INSERT INTO d3_operator_audit
            (id,source_id,lab_id,actor_id,target_id,action,before_snapshot,after_snapshot,occurred_at)
            VALUES (%s,%s,current_lab_id(),%s,%s,'dataset.deleted',%s::jsonb,'null'::jsonb,now())""",
            (str(Ulid.generate()),source,actor_id,target,json.dumps(before)))
        cursor.execute("""INSERT INTO d3_operator_export(id,source_id,lab_id,occurred_at,payload)
            VALUES (%s,%s,current_lab_id(),now(),%s::jsonb)""",(str(Ulid.generate()),source,json.dumps(payload)))
