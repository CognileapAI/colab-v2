#!/usr/bin/env python3
"""Prepare and deliver one session-bound, verified Slack completion notice."""
import argparse, getpass, hashlib, http.client, importlib.util, json, os, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "colab-slack-completion/1"
DEFAULT_SECRET = Path.home()/".config/colab/slack-webhook"
class CompletionError(ValueError): pass

def git_dir(root):
    p=subprocess.run(["git","-C",str(root),"rev-parse","--absolute-git-dir"],text=True,capture_output=True)
    if p.returncode: raise CompletionError("not a Git checkout")
    return Path(p.stdout.strip())
def checkout(root):
    p=subprocess.run(["git","-C",str(root),"rev-parse","--show-toplevel"],text=True,capture_output=True)
    if p.returncode: raise CompletionError("not a Git checkout")
    return Path(p.stdout.strip()).resolve()
def safe_session(value):
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,160}",value): raise CompletionError("invalid session id")
    return value
def box(root): return git_dir(root)/"slack-completion"
def pending_path(root,s): return box(root)/f"{safe_session(s)}.pending.json"
def sending_path(root,s): return box(root)/f"{safe_session(s)}.sending.json"
def receipt_path(root,s,completion,state): return box(root)/f"{safe_session(s)}.{completion}.{state}.json"
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot(root):
    p=subprocess.run(["git","-C",str(root),"status","--porcelain=v1","-z","--untracked-files=all"],capture_output=True)
    if p.returncode: raise CompletionError("cannot inspect checkout")
    head=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],text=True,capture_output=True,check=True).stdout.strip()
    h=hashlib.sha256(head.encode()+b"\0"+p.stdout)
    for raw in p.stdout.split(b"\0"):
        if not raw: continue
        rel=raw[3:].decode("utf-8",errors="surrogateescape")
        path=Path(root)/rel
        if path.is_file(): h.update(rel.encode("utf-8",errors="surrogateescape")); h.update(path.read_bytes())
    return h.hexdigest()
def verify_evidence(root,task_id,path):
    source=Path(root)/".claude/hooks/lifecycle_contract.py"
    spec=importlib.util.spec_from_file_location("colab_lifecycle_contract",source)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    task=module.load_task(Path(root),task_id); module.verify_task_report(Path(root),task,str(path))
def prepare(root,session,report,evidence,whole_scope_complete,pending_work,verifier=verify_evidence):
    root=checkout(root); report=Path(report).resolve(); evidence=[(t,Path(p).resolve()) for t,p in evidence]
    if not whole_scope_complete or pending_work: raise CompletionError("whole scope is not complete")
    if not evidence or not report.is_file() or not report.read_text(encoding="utf-8").strip(): raise CompletionError("completion inputs missing")
    if any(root not in p.parents for p in [report,*[p for _,p in evidence]]): raise CompletionError("completion inputs must be in this checkout")
    [verifier(root,t,p) for t,p in evidence]
    session=safe_session(session)
    task_ids=[t for t,_ in evidence]
    if len(set(task_ids))!=len(task_ids): raise CompletionError("duplicate completion evidence task")
    material=json.dumps(sorted(task_ids),separators=(",",":")).encode()
    completion=hashlib.sha256(material).hexdigest()[:24]
    if pending_path(root,session).exists() or sending_path(root,session).exists(): raise CompletionError("a completion is already pending")
    if receipt_path(root,session,completion,"sent").exists() or receipt_path(root,session,completion,"uncertain").exists():
        raise CompletionError("completion already delivered or uncertain")
    data={"schema":SCHEMA,"session_id":session,"completion_id":completion,"root":str(root),"whole_scope_complete":True,"pending_work":[],
          "snapshot":snapshot(root),"report":{"path":str(report),"sha256":digest(report)},
          "evidence":[{"task_id":t,"path":str(p),"sha256":digest(p)} for t,p in evidence]}
    target=pending_path(root,session); target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    tmp=target.with_name(target.name+f".tmp-{os.getpid()}")
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as out: out.write(json.dumps(data,ensure_ascii=False))
        os.link(tmp,target); tmp.unlink()
    except Exception:
        tmp.unlink(missing_ok=True); raise
    return target
def validate_url(value):
    if not isinstance(value,str) or value!=value.strip() or any(ord(c)<33 or ord(c)==127 for c in value): raise CompletionError("invalid Slack webhook URL")
    u=urlsplit(value)
    if u.scheme!="https" or u.hostname!="hooks.slack.com" or u.port not in (None,443) or u.username or u.password or u.query or u.fragment:
        raise CompletionError("invalid Slack webhook URL")
    if not re.fullmatch(r"/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9_-]+",u.path): raise CompletionError("invalid Slack webhook URL")
    return value
def install_secret(path,value):
    value=validate_url(value); path=Path(path); path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".tmp-{os.getpid()}")
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as out: out.write(value)
        os.replace(tmp,path)
    except Exception:
        tmp.unlink(missing_ok=True); raise
def send_webhook(url,text):
    u=urlsplit(validate_url(url)); body=json.dumps({"text":text},ensure_ascii=False).encode()
    conn=http.client.HTTPSConnection("hooks.slack.com",443,timeout=10)
    try:
        conn.request("POST",u.path,body,headers={"Content-Type":"application/json; charset=utf-8"})
        response=conn.getresponse(); response.read(4096)
        if response.status<200 or response.status>=300: raise CompletionError("Slack rejected completion notice")
    finally: conn.close()
def _load_notice(path,root,session,verifier):
    d=json.loads(path.read_text(encoding="utf-8"))
    if d.get("schema")!=SCHEMA or d.get("session_id")!=session or d.get("root")!=str(root) or not d.get("whole_scope_complete") or d.get("pending_work")!=[]: raise CompletionError("invalid completion notice")
    report=Path(d["report"]["path"]); evidence=d["evidence"]
    material=json.dumps(sorted(x["task_id"] for x in evidence),separators=(",",":")).encode()
    if d.get("completion_id")!=hashlib.sha256(material).hexdigest()[:24]: raise CompletionError("invalid completion identity")
    if digest(report)!=d["report"]["sha256"] or snapshot(root)!=d["snapshot"]: raise CompletionError("stale completion notice")
    for item in evidence:
        p=Path(item["path"])
        if digest(p)!=item["sha256"]: raise CompletionError("stale completion evidence")
        verifier(root,item["task_id"],p)
    return report.read_text(encoding="utf-8"),d
def handle_stop(event,sender=send_webhook,secret_path=DEFAULT_SECRET,verifier=verify_evidence):
    if not isinstance(event,dict) or event.get("hook_event_name")!="Stop": return {}
    try: root=checkout(event["cwd"]); session=safe_session(event["session_id"]); pending=pending_path(root,session)
    except Exception: return {}
    if not pending.exists(): return {}
    try:
        secret=validate_url(Path(secret_path).read_text(encoding="utf-8"))
        text,notice=_load_notice(pending,root,session,verifier)
    except Exception: return {"systemMessage":"Slack 완료 알림을 보내지 못했습니다. 웹훅 설정과 완료 증거를 확인하세요."}
    sending=sending_path(root,session)
    try:
        os.link(pending,sending)
        pending.unlink()
    except (FileExistsError,FileNotFoundError): return {}
    completion=notice["completion_id"]
    if receipt_path(root,session,completion,"sent").exists() or receipt_path(root,session,completion,"uncertain").exists():
        sending.unlink(missing_ok=True); return {}
    try:
        sender(secret,text)
    except Exception:
        os.replace(sending,receipt_path(root,session,completion,"uncertain")); return {"systemMessage":"Slack 전송 결과를 확인할 수 없습니다. 중복 방지를 위해 자동 재전송하지 않았습니다."}
    os.replace(sending,receipt_path(root,session,completion,"sent")); return {}
def cli(argv=None,stdin=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("setup")
    q=sub.add_parser("prepare"); q.add_argument("--session-id",default=os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")); q.add_argument("--report",required=True); q.add_argument("--evidence",action="append",required=True,metavar="TASK_ID:REPORT"); q.add_argument("--whole-scope-complete",action="store_true"); q.add_argument("--pending",action="append",default=[])
    sub.add_parser("hook"); a=p.parse_args(argv)
    result=None
    try:
        if a.cmd=="setup":
            if not sys.stdin.isatty(): raise CompletionError("setup requires an interactive terminal")
            install_secret(DEFAULT_SECRET,getpass.getpass("Slack Webhook URL: "))
        elif a.cmd=="prepare":
            items=[x.split(":",1) for x in a.evidence]
            if any(len(x)!=2 or not x[0] or not x[1] for x in items): raise CompletionError("evidence requires TASK_ID:REPORT")
            prepare(Path.cwd(),a.session_id,Path(a.report),items,a.whole_scope_complete,a.pending)
        else: result=handle_stop(json.loads(stdin if stdin is not None else sys.stdin.read()))
        print(json.dumps(result,ensure_ascii=False) if a.cmd=="hook" else "완료")
        return 0
    except Exception:
        print("Slack 완료 알림을 준비하지 못했습니다.",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(cli())
