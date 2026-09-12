"""Production adapters with only the AWS SDK boundary replaced."""
import copy, datetime as dt, json, threading, unittest
from infra.notifications.aws_store import DynamoStore
from infra.notifications.events import make_event
from infra.notifications import handlers

class ConditionalFailure(Exception):
    response={'Error':{'Code':'TransactionCanceledException'},'CancellationReasons':[{'Code':'ConditionalCheckFailed'}]}

class DynamoSDK:
    def __init__(self): self.items={}; self.lock=threading.Lock(); self.transactions=[]
    def get_item(self, **args):
        value=self.items.get(args['Key']['pk']['S'])
        return {'Item':copy.deepcopy(value)} if value else {}
    def scan(self, **args):
        start=args.get('ExclusiveStartKey',{}).get('pk',{}).get('S')
        keys=[k for k in sorted(self.items) if start is None or k>start]; page=keys[:2]
        result={'Items':[copy.deepcopy(self.items[k]) for k in page]}
        if len(keys)>2: result['LastEvaluatedKey']={'pk':{'S':page[-1]}}
        return result
    def _check(self,args):
        old=self.items.get(args['Item']['pk']['S'])
        if args['ConditionExpression']=='attribute_not_exists(pk)':
            if old is not None: raise ConditionalFailure()
        elif not old or old['version']!=args['ExpressionAttributeValues'][':v']: raise ConditionalFailure()
    def put_item(self, **args):
        with self.lock:
            self._check(args); self.items[args['Item']['pk']['S']]=copy.deepcopy(args['Item'])
        return {}
    def transact_write_items(self, **args):
        with self.lock:
            for action in args['TransactItems']: self._check(action['Put'])
            for action in args['TransactItems']:
                item=action['Put']['Item']; self.items[item['pk']['S']]=copy.deepcopy(item)
            self.transactions.append(copy.deepcopy(args))
        return {}

class QueueSDK:
    def __init__(self): self.messages=[]
    def send_message(self, **args):
        self.messages.append(args); return {'MessageId':str(len(self.messages))}

NOW=dt.datetime(2026,9,12,tzinfo=dt.timezone.utc)
CONFIG={'table':'test-table','queue_urls':{'development':'queue-dev','activity':'queue-activity'},
        'queue_arns':{'development':'arn:queue:dev','activity':'arn:queue:activity'},
        'manifest':{'environment':'dev','aws':{'account_id':'123456789012',
          'regions':['ap-northeast-2','us-east-1'],'services':['EC2','RDS'],
          'resources':{'i-core':'dev'},'alarms':{'core-status':'dev'}}}}
def event(event_id='runtime-event-one',severity='error'):
    return make_event(source='deploy',environment='dev',severity=severity,channel='development',occurred_at=NOW,
                      event_id=event_id,payload={'kind':'deploy.failed','release_id':'test-release'})

class AwsRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.sdk=DynamoSDK(); self.queue=QueueSDK(); self.store=DynamoStore(self.sdk,CONFIG['table'])
    def test_queue_consume_and_duplicate(self):
        record=event(); handlers.publish(record,self.store,self.queue,CONFIG)
        self.assertEqual(len(self.queue.messages),1)
        batch={'Records':[{'messageId':'m1','eventSourceARN':'arn:queue:dev','body':self.queue.messages[0]['MessageBody']}]}
        posts=[]
        def sender(channel,text): posts.append((channel,text)); return 200,'ok',None
        for _ in range(2):
            result=handlers.consume(batch,None,client=self.sdk,sender=sender,config=CONFIG,now=NOW)
            self.assertEqual(result,{'batchItemFailures':[]})
        self.assertEqual(len(posts),1); self.assertEqual(self.store.get(record['event_id'])['state'],'sent')
    def test_wrong_queue_has_no_post_or_success_ack(self):
        batch={'Records':[{'messageId':'bad','eventSourceARN':'arn:queue:activity','body':json.dumps({'record':event()})}]}
        posts=[]
        result=handlers.consume(batch,None,client=self.sdk,sender=lambda *x:posts.append(x),config=CONFIG,now=NOW)
        self.assertEqual(result['batchItemFailures'],[{'itemIdentifier':'bad'}]); self.assertEqual(posts,[])
    def test_archive_receipt_replay_and_dirty_are_atomic(self):
        audit={'source_id':'audit-runtime','lab_id':'lab','actor_id':'actor','target_id':'target',
               'action':'project.deleted','occurred_at':'2026-09-11T15:00:00+00:00'}
        receipt=self.store.accept_archive(audit)
        self.assertEqual(self.store.accept_archive(audit),receipt)
        self.assertEqual(len(self.sdk.transactions[0]['TransactItems']),2)
        self.assertTrue(self.store.archive_snapshot()['dirty']['2026-09-12'])
    def test_expired_important_and_general_claims_differ(self):
        self.store.put(event()); self.assertIsNotNone(self.store.claim('runtime-event-one',NOW))
        recovered=self.store.claim('runtime-event-one',NOW+dt.timedelta(seconds=31))
        self.assertTrue(recovered['duplicate_warning'])
        self.store.put(event('runtime-event-general','info')); later=NOW+dt.timedelta(minutes=2)
        self.assertIsNotNone(self.store.claim('runtime-event-general',later))
        self.assertIsNone(self.store.claim('runtime-event-general',later+dt.timedelta(seconds=31)))
        self.assertEqual(self.store.get('runtime-event-general')['state'],'uncertain')
    def test_due_scan_paginates_and_retry_republishes(self):
        for index in range(5): self.store.put(event('runtime-event-'+str(index)))
        result=handlers.retry({},None,client=self.sdk,sqs=self.queue,config=CONFIG,now=NOW)
        self.assertEqual(result['republished'],5); self.assertEqual(len(self.queue.messages),5)
    def test_stale_owner_cannot_finish_new_claim(self):
        self.store.put(event()); first=self.store.claim('runtime-event-one',NOW)
        second=self.store.claim('runtime-event-one',NOW+dt.timedelta(seconds=31))
        self.assertNotEqual(first['claim_token'],second['claim_token'])
        self.store.finish('runtime-event-one','sent',None,'accepted',claim_token=first['claim_token'])
        self.assertEqual(self.store.get('runtime-event-one')['state'],'sending')
if __name__=='__main__': unittest.main()
