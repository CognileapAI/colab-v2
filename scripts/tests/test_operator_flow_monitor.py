import copy,datetime as dt,unittest
from scripts.tests.test_operator_aws_runtime import DynamoSDK,QueueSDK,CONFIG
from infra.notifications.aws_store import DynamoStore
from infra.notifications import handlers
UTC=dt.timezone.utc
class FlowMonitorTests(unittest.TestCase):
 def setUp(self):
  self.sdk=DynamoSDK();self.queue=QueueSDK();self.store=DynamoStore(self.sdk,'table');self.config=copy.deepcopy(CONFIG);self.config['table']='table';self.config['manifest'].update(environment='dev',usage='live',coverage_started_at='2026-09-10T00:00:00+09:00',probes=['service-health'])
 def tick(self,at):
  handlers.record_heartbeat(self.store,'dev','service-health',at)
  handlers.retry({},None,client=self.sdk,sqs=self.queue,config=self.config,now=at)
 def save(self,key,value):self.store._save(key,value,self.store._read(key)[1])
 def records(self):return [r['record'] for r,_ in self.store._all('event#').values() if r['record']['source']=='operator-flow']
 def test_daily_missing_after_grace_and_recovers_once(self):
  at=dt.datetime(2026,9,11,23,0,tzinfo=UTC)
  self.save('collection#latest',{'status':'complete','collected_at':at.isoformat()});self.tick(at);self.assertEqual(self.records(),[])
  at+=dt.timedelta(minutes=15);self.save('collection#latest',{'status':'complete','collected_at':at.isoformat()});self.tick(at)
  self.assertEqual([r['payload']['target'] for r in self.records()],['operator-daily'])
  self.tick(at+dt.timedelta(minutes=1));self.assertEqual(len(self.records()),1)
  self.save('report#2026-09-11',{'status':'sent','complete':True});self.tick(at+dt.timedelta(minutes=2));self.tick(at+dt.timedelta(minutes=3));self.assertEqual(len(self.records()),2);self.assertEqual(self.records()[-1]['payload']['kind'],'probe.recovered')
 def test_continuous_partial_export_warns_then_recovers_without_audit_payload(self):
  at=dt.datetime(2026,9,11,20,tzinfo=UTC)
  for minute in (0,14,15,16):
   now=at+dt.timedelta(minutes=minute);self.save('collection#latest',{'status':'partial','collected_at':now.isoformat(),'accounts':[{'name':'private-user'}]});self.tick(now)
  self.assertEqual(len(self.records()),1);self.assertEqual(self.records()[0]['payload']['target'],'operator-export');self.assertNotIn('private-user',str(self.records()))
  now=at+dt.timedelta(minutes=17);self.save('collection#latest',{'status':'complete','collected_at':now.isoformat()});self.tick(now);self.tick(now+dt.timedelta(minutes=1));self.assertEqual(len(self.records()),2)

 def test_stale_export_warns_and_pending_warning_replays_exact_body_after_failure(self):
  from unittest.mock import patch
  at=dt.datetime(2026,9,11,20,tzinfo=UTC)
  self.save('collection#latest',{'status':'complete','collected_at':at.isoformat()})
  now=at+dt.timedelta(minutes=15)
  original=DynamoStore.put
  def unavailable(store,record):
   if record['source']=='operator-flow':raise OSError('unavailable')
   return original(store,record)
  with patch.object(DynamoStore,'put',unavailable):
   with self.assertRaises(OSError):self.tick(now)
  state,_=self.store._read('flow-state#operator-export');pending=state['pending'];self.assertEqual(len(pending),1)
  self.tick(now+dt.timedelta(minutes=1));self.assertEqual(self.records(),pending)
 def test_rehearsal_never_emits_flow_alerts(self):
  self.config['manifest'].update(environment='staging',usage='rehearsal',probes=[])
  self.tick(dt.datetime(2026,9,12,0,tzinfo=UTC));self.assertEqual(self.records(),[])
