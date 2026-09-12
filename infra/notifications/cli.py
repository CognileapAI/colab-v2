from __future__ import annotations
import argparse, datetime as dt, json, re
from pathlib import Path
from urllib.parse import urlparse
from .delivery import FileStore, process
from .events import validate
from .http_sender import HttpSender


def validate_manifest(m, profile):
    if m.get('schema')!='colab.operator-manifest/1': raise ValueError('manifest schema')
    if (m['environment'],m['usage']) not in {('dev','live'),('staging','rehearsal')}: raise ValueError('environment usage')
    def aware(value):
        parsed=dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None: raise ValueError('timezone required')
    aware(m['coverage_started_at']);ex=m['test_exclusions'];aware(ex['effective_at'])
    for key in ('lab_ids','account_ids'):
        if not isinstance(ex[key],list) or any(not isinstance(v,str) or not v.strip() for v in ex[key]): raise ValueError('exclusion ids')
    if not isinstance(m['sources'],list) or len(m['sources'])!=5 or set(m['sources'])!={'d2','d3','d5','d6','d8'}: raise ValueError('all five audit sources required')
    if not isinstance(m['probes'],list) or not m['probes']:raise ValueError('explicit probes required')
    targets=[]
    for probe in m['probes']:
        if not isinstance(probe,dict) or probe.get('target') not in {'service-health','backup-freshness','deploy-verification'}:raise ValueError('probe target')
        command=probe.get('command')
        if not isinstance(command,list) or not command or any(not isinstance(v,str) or not v or '\x00' in v for v in command):raise ValueError('probe argv required')
        if not isinstance(probe.get('timeout'),(int,float)) or not 0<probe['timeout']<=300:raise ValueError('probe timeout')
        targets.append(probe['target'])
    if len(set(targets))!=len(targets):raise ValueError('duplicate probe target')
    channels=m['channels']
    if set(channels)!={'development','activity'} or len(set(channels.values()))!=2 or any(not isinstance(v,str) or not v.strip() for v in channels.values()): raise ValueError('two channels required')
    if profile=='local':
        endpoints=m['local_channels']
        if set(endpoints)!=set(channels) or len(set(endpoints.values()))!=2: raise ValueError('two local endpoints required')
        for endpoint in endpoints.values():
            u=urlparse(endpoint)
            if u.scheme not in {'http','https'} or u.hostname not in {'localhost','127.0.0.1','::1'} or u.username or u.password or u.query or u.fragment: raise ValueError('loopback endpoint required')
    else:
        if any(not re.fullmatch(r'arn:aws:secretsmanager:[a-z0-9-]+:[0-9]{12}:secret:.+',v) for v in channels.values()): raise ValueError('secret ARN required')
        a=m['aws']
        if not re.fullmatch(r'[0-9]{12}',a['account_id']): raise ValueError('AWS account')
        if not isinstance(a['regions'],list) or 'us-east-1' not in a['regions'] or not a['services']: raise ValueError('AWS scope')
        for key in ('resources','alarms'):
            if not isinstance(a[key],dict) or not a[key] or any(v not in {'dev','staging'} for v in a[key].values()): raise ValueError('AWS mappings')
    return m


def _store(args):
    if args.profile=='connected':
        from .aws_store import DynamoStore
        from .handlers import _client,runtime_config
        config=runtime_config()
        return DynamoStore(_client('dynamodb',None),config['table'])
    if not args.store: raise ValueError('local store required')
    return FileStore(Path(args.store))


def main(argv=None):
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate');v.add_argument('--manifest',required=True);v.add_argument('--profile',choices=('local','connected'),required=True)
    for command in ('ingest','status','resolve','publish-pending','daily','drain-spool','heartbeat','probe'):
        p=sub.add_parser(command);p.add_argument('--store');p.add_argument('--profile',choices=('local','connected'),default='local')
        if command in {'daily','publish-pending','probe'}:p.add_argument('--manifest',required=True)
        if command=='probe':p.add_argument('--target',required=True);p.add_argument('--state',required=True);p.add_argument('--spool',required=True)
        if command=='daily':p.add_argument('--archive')
        if command=='ingest':p.add_argument('--event',required=True)
        if command=='drain-spool':p.add_argument('--spool',required=True)
        if command=='heartbeat':p.add_argument('--environment',choices=('dev','staging'),required=True);p.add_argument('--target',required=True)
        if command in {'status','resolve'}:p.add_argument('event_id')
        if command=='resolve':p.add_argument('action',choices=('confirmed-sent','retry'));p.add_argument('--actor',required=True)
    args=parser.parse_args(argv)
    try:
        manifest=validate_manifest(json.loads(Path(args.manifest).read_text()),args.profile) if hasattr(args,'manifest') else None
        if args.command=='validate':return 0
        if args.command=='probe':
            import fcntl
            from infra.ops.alarm_runner import main as alarm
            probe=next((p for p in manifest['probes'] if p['target']==args.target),None)
            if not probe:raise ValueError('undeclared probe')
            state=Path(args.state);state.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            with state.with_suffix('.lock').open('a') as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:return 75
                code=alarm(['--state',args.state,'--target',args.target,'--threshold','2','--operator-spool',args.spool,'--environment',manifest['environment'],'--timeout',str(probe['timeout']),'--',*probe['command']])
                if args.profile=='connected':
                    from .handlers import record_heartbeat
                    record_heartbeat(_store(args),manifest['environment'],args.target,dt.datetime.now(dt.timezone.utc))
                return code
        store=_store(args);now=dt.datetime.now(dt.timezone.utc)
        if args.command=='daily':
            from . import jobs
            if args.profile=='connected':
                from .aws_store import DynamoArchive
                archive=DynamoArchive(store)
            else:
                from .archive import Archive
                if not args.archive:raise ValueError('archive required')
                archive=Archive(Path(args.archive))
            jobs.reconcile(archive,store);parts=jobs.run(now,manifest,archive);jobs.publish(parts,manifest,archive,store);return 0
        if args.command=='drain-spool':
            from .spool import drain
            print(json.dumps({'accepted':drain(Path(args.spool),store)}));return 0
        if args.command=='heartbeat':
            if args.profile!='connected':raise ValueError('remote heartbeat required')
            from .handlers import record_heartbeat
            record_heartbeat(store,args.environment,args.target,now);return 0
        if args.command=='ingest':store.put(validate(json.loads(Path(args.event).read_text())));return 0
        if args.command=='status':print(json.dumps(store.get(args.event_id),ensure_ascii=False));return 0
        if args.command=='resolve':
            if not args.actor.strip():raise ValueError('actor required')
            store.resolve(args.event_id,args.action,args.actor,now);return 0
        if args.profile=='connected':
            from .handlers import retry
            result=retry({},None)
            print(json.dumps(result));return 20 if result['pending'] or result['unresolved'] else 0
        sender=HttpSender(manifest['local_channels'],local_only=True)
        attempted=store.due(now)
        for event_id in attempted:process(event_id,store,sender,dt.datetime.now(dt.timezone.utc))
        with store._locked() as data:
            remaining=sum(v['state']!='sent' for v in data['events'].values())
        return 20 if remaining else 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):return 78

if __name__=='__main__':raise SystemExit(main())
