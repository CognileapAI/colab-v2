import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from infra.notifications import cli, spool, producers
from infra.notifications.delivery import FileStore
from infra.notifications.install_jobs import render

NOW=dt.datetime(2026,9,12,tzinfo=dt.timezone.utc)
def manifest():
 return {'schema':'colab.operator-manifest/1','environment':'dev','usage':'live','channels':{'development':'dev','activity':'act'},'local_channels':{'development':'http://127.0.0.1:1/dev','activity':'http://127.0.0.1:1/act'},'coverage_started_at':NOW.isoformat(),'test_exclusions':{'lab_ids':[],'account_ids':[],'effective_at':NOW.isoformat()},'sources':['d2','d3','d5','d6','d8'],'probes':[{'target':t,'command':['/bin/true'],'timeout':2} for t in ['service-health','backup-freshness','deploy-verification']]}
class RuntimeWiringTests(unittest.TestCase):
 def test_manifest_rejects_missing_audit_source(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'manifest.json';m=manifest();m['sources'].remove('d8');p.write_text(json.dumps(m))
   self.assertEqual(cli.main(['validate','--manifest',str(p),'--profile','local']),78)
 def test_spool_drain_retains_rejected_and_accepts_durably(self):
  with tempfile.TemporaryDirectory() as d:
   directory=Path(d)/'spool';store=FileStore(Path(d)/'store.json');event=producers.release_result('release','dev','verify',0,'v1',NOW);spool.append(directory,event)
   self.assertTrue(hasattr(spool,'drain'),'spool requires durable drain consumer')
   with patch.object(store,'put',side_effect=OSError('unavailable')):
    with self.assertRaises(OSError):spool.drain(directory,store)
   self.assertEqual(len(list(directory.glob('*.json'))),1)
   self.assertEqual(spool.drain(directory,store),1)
   self.assertEqual(store.get(event['event_id'])['state'],'pending');self.assertEqual(spool.drain(directory,store),0)
 def test_publish_pending_nonzero_when_not_delivered(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'manifest.json';p.write_text(json.dumps(manifest()));s=Path(d)/'store.json';store=FileStore(s);store.put(producers.release_result('r','dev','verify',0,'v',NOW))
   with patch('infra.notifications.cli.HttpSender',return_value=lambda *a:(403,'invalid',0)):
    self.assertEqual(cli.main(['publish-pending','--store',str(s),'--manifest',str(p),'--profile','local']),20)
 def test_schedule_uses_existing_entrypoints(self):
  jobs=render(manifest())
  self.assertIn('infra.notifications.cli',jobs['retry']['command']);self.assertIn('operator_audit_export.py',jobs['export']['command']);self.assertIn(' daily ',jobs['daily']['command'])
 def test_heartbeat_stale_and_recovery_transition(self):
  self.assertTrue(hasattr(producers,'heartbeat'),'missing heartbeat state machine')
  state,events=producers.heartbeat({},NOW,NOW+dt.timedelta(minutes=16),'dev','service-health')
  self.assertEqual(events[0]['payload']['kind'],'probe.unobservable')
  state,repeats=producers.heartbeat(state,NOW,NOW+dt.timedelta(minutes=20),'dev','service-health');self.assertEqual(repeats,[])
  state,events=producers.heartbeat(state,NOW+dt.timedelta(minutes=21),NOW+dt.timedelta(minutes=21),'dev','service-health');self.assertEqual(events[0]['payload']['kind'],'probe.recovered')

class AlarmWiringTests(unittest.TestCase):
 def test_alarm_runner_emits_durable_failure_and_recovery(self):
  from infra.ops import alarm_runner
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);base=['--state',str(root/'state.json'),'--target','service-health','--threshold','2','--operator-spool',str(root/'spool'),'--environment','dev','--']
   try:
    alarm_runner.main(base+['false']);alarm_runner.main(base+['false']);alarm_runner.main(base+['true'])
   except SystemExit:self.fail('runner lacks durable producer arguments')
   records=[json.loads(p.read_text()) for p in (root/'spool').glob('*.json')]
   self.assertEqual({r['payload']['kind'] for r in records},{'probe.failed','probe.recovered'})

class ReleaseRuntimeTests(unittest.TestCase):
 def test_staging_plan_enables_durable_operator_route(self):
  from scripts import deploy_release
  with patch.object(deploy_release.subprocess,'check_output',return_value='a'*40),patch.object(deploy_release.slack,'snapshot',return_value='b'*64):
   plan=deploy_release.staging_plan(Path.cwd(),['--target','staging'])
  self.assertIn('operator_notifications',plan)
 def test_notification_retry_does_not_run_verification_again(self):
  from scripts.tests.test_deploy_release import ReleaseTests
  case=ReleaseTests();case.setUp()
  try:
   case.secret.unlink();self.assertEqual(case.run_plan(),20);case.calls.clear();case.secret.write_text('https://hooks.slack.com/services/T/B/test')
   self.assertEqual(case.run_plan(retry_notification=True),0);self.assertEqual(case.calls,[])
  finally:case.doCleanups()

class RemoteHeartbeatTests(unittest.TestCase):
 def test_remote_retry_detects_absence_without_producer_running(self):
  from scripts.tests.test_operator_aws_runtime import DynamoSDK,QueueSDK,CONFIG
  from infra.notifications.aws_store import DynamoStore
  from infra.notifications import handlers
  import copy
  sdk=DynamoSDK();queue=QueueSDK();config=copy.deepcopy(CONFIG);config['manifest'].update(environment='dev',probes=['service-health'],coverage_started_at=NOW.isoformat());store=DynamoStore(sdk,config['table'])
  handlers.retry({},None,client=sdk,sqs=queue,config=config,now=NOW+dt.timedelta(minutes=16))
  records=[v['record'] for v,_ in store._all('event#').values()]
  self.assertEqual(len(records),1);self.assertEqual(records[0]['payload']['kind'],'probe.unobservable')
  handlers.record_heartbeat(store,'dev','service-health',NOW+dt.timedelta(minutes=17))
  handlers.retry({},None,client=sdk,sqs=queue,config=config,now=NOW+dt.timedelta(minutes=17))
  records=[v['record'] for v,_ in store._all('event#').values()]
  self.assertEqual({r['payload']['kind'] for r in records},{'probe.unobservable','probe.recovered'})

class StagingProbeTests(unittest.TestCase):
 def test_staging_explicit_probe_runs_and_spools_without_dev_fallback(self):
  import sys
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);m=manifest();m.update(environment='staging',usage='rehearsal',probes=[{'target':'service-health','command':[sys.executable,'-c','raise SystemExit(1)'],'timeout':2}]);p=root/'manifest.json';p.write_text(json.dumps(m))
   args=['probe','--manifest',str(p),'--profile','local','--target','service-health','--state',str(root/'state.json'),'--spool',str(root/'spool')]
   try:codes=[cli.main(args),cli.main(args)]
   except SystemExit:self.fail('missing declared staging probe entrypoint')
   self.assertEqual(codes,[1,1]);records=[json.loads(p.read_text()) for p in (root/'spool').glob('*.json')];self.assertEqual(len(records),1);self.assertEqual(records[0]['environment'],'staging')
