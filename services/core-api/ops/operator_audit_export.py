#!/usr/bin/env python3
"""Export committed operator audit outboxes and acknowledge durable receipts."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os
from pathlib import Path
from sqlalchemy import create_engine, text
from colab_core.kernel.scope import require_operator_role
from sqlalchemy.orm import Session
from colab_core.domains import d1_identity, d2_audit, d3_audit, d5_audit, d6_audit, d8_audit

ADAPTERS={"d2_operator_export":d2_audit,"d3_operator_export":d3_audit,"d5_operator_export":d5_audit,"d6_operator_export":d6_audit,"d8_operator_export":d8_audit}
TABLES=tuple(ADAPTERS)

def _write_jsonl(path:Path,rows:list[dict])->str:
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(path.parent,0o700)
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    digest=hashlib.sha256()
    with os.fdopen(fd,"wb") as stream:
        for row in rows:
            line=json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()+b"\n"
            stream.write(line);digest.update(line)
        stream.flush();os.fsync(stream.fileno())
    return digest.hexdigest()

def pending(engine)->list[dict]:
    rows=[]
    with Session(engine) as session:
        labs=[str(r["id"]).strip() for r in d1_identity.list_operator_labs(session)]
        session.commit()
    for lab in labs:
        with Session(engine) as session, session.begin():
            session.execute(__import__("sqlalchemy").text("SELECT set_config('app.current_lab',:lab,true)"),{"lab":lab})
            for adapter in ADAPTERS.values():rows.extend(adapter.pending_exports(session, limit=2147483647))
    return rows

def export(manifest:dict,output:Path,engine)->int:
    rows=pending(engine);_write_jsonl(output,rows);return len(rows)

def ack(receipts:Path,engine)->int:
    records=[json.loads(line) for line in receipts.read_text().splitlines() if line.strip()]
    count=0
    for record in records:
        table=record.get("source_table");required={"source_id","lab_id","source_table","content_hash","receipt_hash"}
        if table not in ADAPTERS or required-record.keys() or any(not isinstance(record[k],str) for k in required):raise ValueError("invalid receipt")
        with Session(engine) as session, session.begin():
            session.execute(__import__("sqlalchemy").text("SELECT set_config('app.current_lab',:lab,true)"),{"lab":record["lab_id"]})
            count+=ADAPTERS[table].ack_export(session,record)
    return count

def sync(engine,remote_store)->int:
    """Acknowledge only observable remote receipts and publish actual collection facts."""
    count = 0
    collection = {"status":"failed","labs":[],"accounts":[],"sources":[],
                  "collected_at":dt.datetime.now(dt.timezone.utc).isoformat()}
    with Session(engine) as session:
        require_operator_role(session)
    try:
        with Session(engine) as session:
            collection["labs"] = [{"id":str(r["id"]).strip(),"name":r["name"]}
                for r in d1_identity.list_operator_labs(session)]
        for lab in collection["labs"]:
            with Session(engine) as session,session.begin():
                session.execute(text("SELECT set_config('app.current_lab',:lab,true)"),{"lab":lab["id"]})
                collection["accounts"].extend([{**r,"id":str(r["id"]).strip(),"lab_id":str(r["lab_id"]).strip()}
                    for r in d1_identity.list_operator_accounts(session)])
            for table,adapter in ADAPTERS.items():
                fact={"lab_id":lab["id"],"source":table.split('_')[0],"status":"failed","pending":None}
                collection["sources"].append(fact)
                try:
                    while True:
                        with Session(engine) as session,session.begin():
                            session.execute(text("SELECT set_config('app.current_lab',:lab,true)"),{"lab":lab["id"]})
                            rows=adapter.pending_exports(session)
                        if not rows:
                            fact.update(status="complete",pending=0)
                            break
                        for row in rows:
                            receipt=remote_store.accept_archive(row)
                            confirmed=remote_store._read("audit#"+row["source_id"])[0]
                            if not confirmed or confirmed.get("hash")!=receipt.get("content_hash"):
                                raise RuntimeError("remote durable receipt not observable")
                            proof={**receipt,"source_table":table,"lab_id":lab["id"]}
                            with Session(engine) as session,session.begin():
                                session.execute(text("SELECT set_config('app.current_lab',:lab,true)"),{"lab":lab["id"]})
                                count+=adapter.ack_export(session,proof)
                except Exception:
                    # Other domains can still be exported. No exception content enters Slack.
                    fact["status"]="failed"
        collection["status"] = "complete" if all(r["status"]=="complete" for r in collection["sources"]) else "partial"
    finally:
        # The scan start is a conservative completeness watermark, not the final ACK time.
        remote_store.record_collection(collection)
    if collection["status"] != "complete":
        raise RuntimeError("operator collection incomplete; committed sources retained")
    return count

def main(argv=None):
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="command",required=True)
    e=sub.add_parser("export");e.add_argument("--manifest",required=True);e.add_argument("--output",required=True)
    a=sub.add_parser("ack");a.add_argument("--manifest",required=True);a.add_argument("--receipt-file",required=True)
    s=sub.add_parser("sync");s.add_argument("--manifest",required=True)
    args=p.parse_args(argv)
    try:
        manifest=json.loads(Path(args.manifest).read_text());env=manifest.get("database_url_env","COLAB_OPERATOR_DATABASE_URL")
        url=os.environ.get(env)
        if not url:return 78
        engine=create_engine(url)
        if args.command=="export":export(manifest,Path(args.output),engine)
        elif args.command=="ack":return 78 # 파일만으로는 원격 영속 접수를 증명할 수 없다.
        else:
            import boto3
            from infra.notifications.aws_store import DynamoStore
            sync(engine,DynamoStore(boto3.client("dynamodb"),os.environ["COLAB_OPERATOR_TABLE"]))
        return 0
    except (OSError,ValueError,KeyError):return 78
if __name__=="__main__":raise SystemExit(main())
