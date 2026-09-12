from __future__ import annotations
import contextlib, datetime as dt, fcntl, hashlib, json, os, uuid
from pathlib import Path

class Archive:
    def __init__(self,directory:Path):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(self.directory,0o700)
        self.path=self.directory/"archive.json";self.lock_path=self.directory/"archive.lock"
    @contextlib.contextmanager
    def transaction(self):
        fd=os.open(self.lock_path,os.O_CREAT|os.O_RDWR,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX)
            data=json.loads(self.path.read_text()) if self.path.exists() else {"schema":"colab.operator-archive/1","events":{},"dirty":{},"reports":{}}
            yield data
            temp=self.path.with_name(self.path.name+"."+uuid.uuid4().hex+".tmp");out=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(out,"w") as stream:json.dump(data,stream,ensure_ascii=False,sort_keys=True);stream.flush();os.fsync(stream.fileno())
            os.replace(temp,self.path);p=os.open(self.directory,os.O_RDONLY|os.O_DIRECTORY);os.fsync(p);os.close(p)
        finally:os.close(fd)
    def accept(self,record:dict)->dict:
        required={"source_id","lab_id","actor_id","target_id","action","occurred_at"}
        if required-record.keys():raise ValueError("audit source fields missing")
        raw=json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode();digest=hashlib.sha256(raw).hexdigest()
        if dt.datetime.fromisoformat(record["occurred_at"]).tzinfo is None:raise ValueError("aware audit timestamp required")
        day=dt.datetime.fromisoformat(record["occurred_at"]).astimezone(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
        with self.transaction() as data:
            old=data["events"].get(record["source_id"])
            if old and old["hash"]!=digest:raise ValueError("source id collision")
            if not old:
                data["events"][record["source_id"]]={"hash":digest,"record":record}
                data["dirty"][day]=True
        return {"source_id":record["source_id"],"content_hash":digest,"receipt_hash":hashlib.sha256((record["source_id"]+digest).encode()).hexdigest()}
    def record_collection(self, collection:dict):
        if collection.get("status") not in {"complete","partial","failed"}:
            raise ValueError("explicit collection status required")
        observed=dt.datetime.fromisoformat(collection["collected_at"])
        if observed.tzinfo is None:raise ValueError("aware collection timestamp required")
        with self.transaction() as data:
            previous=data.get("collection")
            if previous and dt.datetime.fromisoformat(previous["collected_at"])>observed:
                raise ValueError("older collection snapshot cannot replace newer facts")
            data["collection"]=json.loads(json.dumps(collection))
    def snapshot(self):
        with self.transaction() as data:return json.loads(json.dumps(data))
