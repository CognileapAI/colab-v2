"""Single-run doctor evidence emitter; bundled with ops, no harness checkout dependency."""
import argparse
import contextlib
import datetime
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse

MARKS = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮'


def sha256(raw): return hashlib.sha256(raw).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def canonical(value): return json.dumps(value, sort_keys=True, ensure_ascii=False).encode()


def redact(text):
    def url(match):
        value = urllib.parse.urlsplit(match[0])
        netloc = value.netloc.split('@')[-1]
        return urllib.parse.urlunsplit((value.scheme, netloc, value.path, '[REDACTED]' if value.query else '', ''))
    text = re.sub(r'''(?i)(["'](?:token|password|secret|aws_secret_access_key|aws_session_token)["']\s*:\s*)(["'])(.*?)\2''', r'\1"[REDACTED]"', text)
    text = re.sub(r'[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>\"\']+', url, text)
    text = re.sub(r'(?i)\b(authorization\s*:\s*bearer|bearer)\s+[^\s,;]+', r'\1 [REDACTED]', text)
    text = re.sub(r'(?i)\b(token|password|secret|aws_secret_access_key|aws_session_token|x-amz-signature)\s*[:=]\s*[^\s,;]+', r'\1=[REDACTED]', text)
    return re.sub(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b', '[REDACTED]', text)


def regular(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)): raise ValueError('symlink evidence/source path')
    if not path.is_file(): raise OSError('required evidence/source file missing')
    return path


def source_snapshot(source, full):
    manifest = regular(source/'OPS_SOURCE_MANIFEST').read_bytes()
    text = manifest.decode()
    if f'# source_full_sha={full}\n' not in text: raise ValueError('source full SHA differs')
    found = {}
    for line in text.splitlines():
        if line.startswith('#'): continue
        match = re.fullmatch(r'([0-9a-f]{64})  (?:\./)?(.+)', line)
        if not match: raise ValueError('malformed source manifest')
        rel = Path(match[2])
        if rel.is_absolute() or '..' in rel.parts or str(rel) in found: raise ValueError('invalid source manifest path')
        actual = sha256(regular(source/rel).read_bytes())
        if actual != match[1]: raise ValueError('source content differs')
        found[str(rel)] = actual
    for name in ('deploy_doctor.py','deploy_doctor_evidence.py','s3_doctor.py'):
        if 'services/core-api/ops/'+name not in found: raise OSError('doctor source missing from bundle')
    actual_files=set()
    for path in source.rglob('*'):
        if path.is_symlink(): raise ValueError('source symlink')
        if path.is_file() and path!=source/'OPS_SOURCE_MANIFEST': actual_files.add(str(path.relative_to(source)))
    if actual_files!=set(found): raise ValueError('source contains unlisted or missing files')
    return {'manifest_sha256': sha256(manifest), 'files': len(found)}


def state_snapshot(ctx, pre_path, source):
    raw = regular(pre_path).read_bytes(); pre = json.loads(raw)
    full = pre.get('sha')
    if not isinstance(full,str) or not re.fullmatch('[0-9a-f]{40}',full): raise ValueError('pre full SHA missing')
    if ctx.env not in ('dev','prod') or pre.get('environment') != ctx.env: raise ValueError('environment differs')
    for key in ('release_id','run_id','started_at'):
        if not isinstance(pre.get(key),str) or not pre[key]: raise ValueError('pre identity missing')
    state = Path(ctx.state_dir)
    values = {name:regular(state/name).read_text().strip() for name in ('CURRENT_SHA','CURRENT_FULL_SHA','MAIN_SHA')}
    if values['CURRENT_SHA'] != full[:12] or values['CURRENT_FULL_SHA'] != full: raise ValueError('running SHA differs from full target')
    match = re.fullmatch(r'main=([0-9a-f]{12,40}) candidate=([0-9a-f]{12,40}) ancestor=yes',values['MAIN_SHA'])
    if not match or match[2] != full[:12]: raise ValueError('MAIN_SHA candidate/ancestry differs')
    return pre, {'pre_file_sha256':sha256(raw),'state':values,'source':source_snapshot(source,full)}


def exclusive(path, raw):
    if any(parent.is_symlink() for parent in (path,*path.parents)): raise ValueError('artifact symlink')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


def verify_emitted(pre, post, artifact_dir):
    if post.get('schema') != 'colab-doctor-evidence/1' or post.get('producer') != 'deploy_doctor.run/1': raise ValueError('emitted doctor evidence required')
    for key in ('sha','environment','release_id','run_id','started_at'):
        if post.get(key) != pre.get(key): raise ValueError('doctor release identity differs')
    if post.get('pre_sha256') != sha256(canonical(pre)): raise ValueError('doctor pre content differs')
    before, after = post.get('before'),post.get('after')
    if not isinstance(before,dict) or before != after: raise ValueError('running state/source changed')
    if before.get('state',{}).get('CURRENT_FULL_SHA') != pre['sha'] or before.get('state',{}).get('CURRENT_SHA') != pre['sha'][:12]: raise ValueError('doctor running SHA differs')
    match=re.fullmatch(r'main=([0-9a-f]{12,40}) candidate=([0-9a-f]{12,40}) ancestor=yes',before['state'].get('MAIN_SHA',''))
    if not match or match[2]!=pre['sha'][:12]: raise ValueError('doctor ancestry differs')
    source=before.get('source',{})
    if not re.fullmatch('[0-9a-f]{64}',source.get('manifest_sha256','')) or type(source.get('files')) is not int or source['files']<3: raise ValueError('doctor source evidence missing')
    if post.get('allow_skip') is not False or type(post.get('doctor_exit')) is not int or post['doctor_exit'] != 0 or post.get('exit') != 0: raise ValueError('doctor not fully successful')
    rows=post.get('rows')
    if not isinstance(rows,list) or len(rows)!=15 or any(not isinstance(row,dict) for row in rows): raise ValueError('doctor requires exactly 15 items')
    if [row.get('mark') for row in rows] != list(MARKS) or any(row.get('status')!='✓' for row in rows): raise ValueError('doctor missing/duplicate/skipped/failed item')
    start=datetime.datetime.fromisoformat(post['doctor_started_at']);finish=datetime.datetime.fromisoformat(post['finished_at'])
    if start.tzinfo is None or finish.tzinfo is None or finish<=start or start<datetime.datetime.fromisoformat(pre['started_at']): raise ValueError('doctor execution time differs')
    log=post.get('log')
    if not isinstance(log,dict) or log.get('file')!='doctor.log': raise ValueError('doctor log missing')
    raw=regular(Path(artifact_dir)/'doctor.log').read_bytes()
    if log.get('sha256') != sha256(raw) or log.get('bytes') != len(raw) or not raw: raise ValueError('doctor log changed or missing')


def emit(ctx, pre_path, output, source, *, doctor=None, test_injection=False):
    output,pre_path,source=Path(output),Path(pre_path),Path(source)
    log=output.parent/'doctor.log'
    try:
        if output.exists() or log.exists(): raise OSError('prior post/log exists; use a fresh run directory')
        if not output.parent.is_dir(): raise OSError('dedicated artifact directory missing')
        pre,before=state_snapshot(ctx,pre_path,source)
    except (OSError,ValueError,KeyError):
        print('doctor evidence readiness failure: state/source/output prerequisite',file=sys.stderr);return 78
    captured=io.StringIO();started=now();after=None;code=1;doctor_code=1;rep=None
    with contextlib.redirect_stdout(captured),contextlib.redirect_stderr(captured):
        try:
            if doctor is None: doctor=importlib.import_module('deploy_doctor')
            if not test_injection:
                for actual,name in ((Path(__file__),'deploy_doctor_evidence.py'),(Path(doctor.__file__),'deploy_doctor.py')):
                    expected=source/'services/core-api/ops'/name
                    if regular(actual).resolve()!=regular(expected).resolve() or actual.read_bytes()!=expected.read_bytes(): raise ValueError('executing source differs from manifest source')
            rep=doctor.DeployReport()
            doctor_code=doctor.run(ctx,report=rep)
            _,after=state_snapshot(ctx,pre_path,source)
            code=doctor_code if before==after else 1
        except Exception as exc:
            print('doctor execution exception: '+type(exc).__name__);code=1
    raw=redact(captured.getvalue()).encode()
    post={key:pre[key] for key in ('sha','environment','release_id','run_id','started_at')}
    post.update(schema='colab-doctor-evidence/1',producer='deploy_doctor.run/1',phase='post',pre_sha256=sha256(canonical(pre)),
        doctor_started_at=started,finished_at=now(),doctor_exit=doctor_code,exit=code,allow_skip=ctx.allow_skip,
        before=before,after=after,rows=[{'mark':m,'status':s} for m,_t,s in rep.items] if rep else [],
        log={'file':'doctor.log','sha256':sha256(raw),'bytes':len(raw)})
    try:
        exclusive(log,raw)
        try: verify_emitted(pre,post,output.parent)
        except (ValueError,KeyError,TypeError): post['exit']=code=1
        exclusive(output,json.dumps(post,ensure_ascii=False,indent=2).encode())
    except (OSError,ValueError): return 78
    print(raw.decode(),end='');print('doctor evidence exit='+str(code))
    return code


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pre',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('doctor_args',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    try:
        doctor=importlib.import_module('deploy_doctor')
        ctx=doctor.parse_args(args.doctor_args[1:] if args.doctor_args[:1]==['--'] else args.doctor_args)
    except (ImportError,OSError):
        print('doctor evidence readiness failure: source dependency',file=sys.stderr);return 78
    return emit(ctx,args.pre,args.output,args.source,doctor=doctor)


if __name__=='__main__':raise SystemExit(main())
