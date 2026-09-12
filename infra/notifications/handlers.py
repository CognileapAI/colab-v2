"""AWS entry points. A queue acknowledgement always follows durable acceptance."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os

from .aws_events import normalize
from .aws_store import DynamoStore
from .delivery import process
from .events import make_event, validate


def runtime_config():
    config = {'table': os.environ['COLAB_OPERATOR_TABLE'],
              'manifest': json.loads(os.environ['COLAB_OPERATOR_MANIFEST_JSON']),
              'queue_urls': {c: os.environ[c.upper() + '_QUEUE_URL'] for c in ('development', 'activity')},
              'queue_arns': {c: os.environ[c.upper() + '_QUEUE_ARN'] for c in ('development', 'activity')},
              'secret_arns': {c: os.environ[c.upper() + '_WEBHOOK_SECRET_ARN'] for c in ('development', 'activity')}}
    for name in ('queue_urls', 'queue_arns', 'secret_arns'):
        if len(set(config[name].values())) != 2:
            raise ValueError('development and activity routes must be distinct')
    alarms = config['manifest']['aws']['alarms']
    for key in ('INSTANCE_STATUS_ALARM_NAME', 'SYSTEM_STATUS_ALARM_NAME'):
        if alarms.get(os.environ[key]) != config['manifest']['environment']:
            raise ValueError('managed EC2 alarms must be explicitly mapped in the manifest')
    return config


def _client(service, supplied):
    if supplied is not None:
        return supplied
    import boto3
    return boto3.client(service)


def _sender(config, secrets=None):
    from .http_sender import HttpSender
    secrets = _client('secretsmanager', secrets)
    urls = {}
    for channel, arn in config['secret_arns'].items():
        secret = secrets.get_secret_value(SecretId=arn)['SecretString']
        try:
            value = json.loads(secret)
        except ValueError:
            value = secret
        urls[channel] = value['webhook_url'] if isinstance(value, dict) else value
        if not isinstance(urls[channel], str) or not urls[channel].startswith('https://hooks.slack.com/services/'):
            raise ValueError('Slack incoming webhook secret required')
    return HttpSender(urls)


def publish(record, store, sqs, config):
    record = validate(record)
    store.put(record)
    # The small pointer may expire from SQS: the full event remains in DynamoDB.
    sqs.send_message(QueueUrl=config['queue_urls'][record['channel']],
                     MessageBody=json.dumps({'event_id': record['event_id']}, separators=(',', ':')))
    return {'event_id': record['event_id'], 'accepted': True}


def ingest(event, context, *, client=None, sqs=None, config=None):
    config = config or runtime_config()
    store = DynamoStore(_client('dynamodb', client), config['table'])
    if 'audit' in event:
        return store.accept_archive(event['audit'])
    records = [validate(event['record'])] if 'record' in event else normalize(event, config['manifest'])
    queue = _client('sqs', sqs)
    for record in records:
        publish(record, store, queue, config)
    return {'accepted': len(records)}


def consume(event, context, *, client=None, sender=None, config=None, now=None):
    config = config or runtime_config()
    store = DynamoStore(_client('dynamodb', client), config['table'])
    now = now or dt.datetime.now(dt.timezone.utc)
    channels = {arn: channel for channel, arn in config['queue_arns'].items()}
    if len(channels) != 2:
        raise ValueError('two distinct trusted queue ARNs required')
    failures = []
    for message in event.get('Records', []):
        try:
            channel = channels[message['eventSourceARN']]
            body = json.loads(message['body'])
            if 'event_id' in body:
                records = [store.get(body['event_id'])['record']]
            elif 'record' in body:
                records = [validate(body['record'])]
            else:
                if channel != 'development':
                    raise ValueError('AWS events cannot enter activity queue')
                records = normalize(body, config['manifest'])
            for record in records:
                if record['channel'] != channel:
                    raise ValueError('event and trusted queue channels differ')
                store.put(record)
                if sender is None:
                    sender = _sender(config)
                process(record['event_id'], store, sender, now)
        except Exception:
            diagnostic = hashlib.sha256(message['messageId'].encode()).hexdigest()
            try:
                old, version = store._read('poison#' + diagnostic)
                store._save('poison#' + diagnostic, {'reason': 'message_processing_failed',
                    'attempts': (old or {}).get('attempts', 0) + 1, 'last_at': now.isoformat()}, version)
            except Exception:
                pass  # The SQS message remains unacknowledged if durable diagnosis is unavailable.
            # Never log untrusted bodies, webhook values or exception representations.
            failures.append({'itemIdentifier': message['messageId']})
    return {'batchItemFailures': failures}


def _attention(store, now):
    for item in store.unresolved(now):
        record = item['record']
        if record['source'] == 'operator-delivery':
            continue
        identity = 'delivery-attention-' + hashlib.sha256(record['event_id'].encode()).hexdigest()
        warning = make_event(source='operator-delivery', environment=record['environment'],
            severity='error', channel='development', occurred_at=dt.datetime.fromisoformat(item['unresolved_since']),
            event_id=identity, payload={'kind': 'probe.unobservable', 'target': record['event_id'],
            'status': '전송 확인 필요', 'incident_id': identity})
        store.put(warning)


def retry(event, context, *, client=None, sqs=None, config=None, now=None):
    config = config or runtime_config()
    store = DynamoStore(_client('dynamodb', client), config['table'])
    queue = _client('sqs', sqs)
    now = now or dt.datetime.now(dt.timezone.utc)
    _heartbeats(store, config, now)
    _flows(store, config, now)
    _attention(store, now)
    count = 0
    for event_id in store.due(now):
        if context is not None and context.get_remaining_time_in_millis() < 3000:
            break
        record = store.get(event_id)['record']
        queue.send_message(QueueUrl=config['queue_urls'][record['channel']],
                           MessageBody=json.dumps({'event_id': event_id}, separators=(',', ':')))
        count += 1
    return {'republished': count, 'unresolved': len(store.unresolved(now)),
            'pending': sum(item['state'] != 'sent' for item,_ in store._all('event#').values())}


def record_heartbeat(store,environment,target,at):
    if environment not in {"dev","staging"} or target not in {"service-health","backup-freshness","deploy-verification"}:raise ValueError("heartbeat target")
    key="heartbeat#"+environment+":"+target
    old,version=store._read(key)
    if old and dt.datetime.fromisoformat(old["observed_at"])>at:return
    store._save(key,{"observed_at":at.isoformat()},version)


def _heartbeats(store,config,now):
    from .producers import heartbeat
    manifest=config["manifest"]
    for declared in manifest.get("probes",[]):
        target=declared["target"] if isinstance(declared,dict) else declared
        key=manifest["environment"]+":"+target
        observed,_=store._read("heartbeat#"+key)
        at=dt.datetime.fromisoformat(observed["observed_at"] if observed else manifest["coverage_started_at"])
        old,version=store._read("heartbeat-state#"+key)
        old=old or {}
        # Persist immutable notification records before publishing them.
        for record in old.get("pending",[]):store.put(record)
        state,events=heartbeat(old,at,now,manifest["environment"],target)
        state["pending"]=events
        store._save("heartbeat-state#"+key,state,version)
        for record in events:store.put(record)


def _flow_transition(store,target,bad,since,now):
    key='flow-state#'+target
    state,version=store._read(key);state=state or {'active':False,'incident':0}
    for record in state.get('pending',[]):store.put(record)
    state['pending']=[]
    if bad:
        state.setdefault('bad_since',since.isoformat())
        due=now-dt.datetime.fromisoformat(state['bad_since'])>=dt.timedelta(minutes=15)
        if due and not state['active']:
            state['active']=True;state['incident']+=1
            state['pending']=[make_event(source='operator-flow',environment='dev',severity='error',channel='development',occurred_at=now,
                event_id=f"operator-flow:{target}:{state['incident']}:failed",payload={'kind':'probe.unobservable','target':target,'status':'수집 또는 일일 보고가 15분 이상 정상 완료되지 않음'})]
    else:
        state.pop('bad_since',None)
        if state['active']:
            state['active']=False
            state['pending']=[make_event(source='operator-flow',environment='dev',severity='info',channel='development',occurred_at=now,
                event_id=f"operator-flow:{target}:{state['incident']}:recovered",payload={'kind':'probe.recovered','target':target,'status':'정상 완료 확인'})]
    store._save(key,state,version)
    for record in state['pending']:store.put(record)


def _flows(store,config,now):
    from zoneinfo import ZoneInfo
    manifest=config['manifest']
    if manifest.get('environment')!='dev' or manifest.get('usage')!='live':return
    coverage=dt.datetime.fromisoformat(manifest['coverage_started_at'])
    collection,_=store._read('collection#latest')
    at=dt.datetime.fromisoformat(collection['collected_at']) if collection else coverage
    stale=now-at>=dt.timedelta(minutes=15)
    failed=not collection or collection.get('status')!='complete'
    # Fresh partial snapshots do not reset a continuously failing collection.
    _flow_transition(store,'operator-export',failed or stale,at if stale or not collection else now,now)
    local=now.astimezone(ZoneInfo('Asia/Seoul'));day=local.date()-dt.timedelta(days=1)
    expected=day>=coverage.astimezone(ZoneInfo('Asia/Seoul')).date()
    deadline=dt.datetime.combine(local.date(),dt.time(8),tzinfo=local.tzinfo)
    if not expected or now<deadline:return
    report,_=store._read('report#'+day.isoformat())
    bad=not report or report.get('status')!='sent' or report.get('complete') is not True
    _flow_transition(store,'operator-daily',bad,deadline,now)
