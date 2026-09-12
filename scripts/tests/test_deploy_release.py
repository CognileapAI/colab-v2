import importlib.util, json, os, subprocess, tempfile, unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('deploy_release',Path(__file__).parents[1]/'deploy_release.py')
d=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(d)
class ReleaseTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.state=self.root/'state';self.secret=self.root/'secret';self.secret.write_text('https://hooks.slack.com/services/T/B/test');self.calls=[];self.sent=[]
  self.plan={'schema':'colab-deploy/1','id':'release-1','summary':'디자인 배포','targets':[{'name':n,'version':'sha-'+n,'deploy':[['deploy',n]],'verify':[['verify',n]]} for n in ['dv','st']]}
 def execute(self,argv,cwd,env,log):self.calls.append(argv);return 0
 def run_plan(self,**kw):return d.run_plan(self.root,self.plan,state_dir=self.state,secret_path=self.secret,execute=kw.pop('execute',self.execute),sender=kw.pop('sender',lambda u,t:self.sent.append(t)),**kw)
 def status(self):return json.loads((self.state/'release-1'/'state.json').read_text())
 def test_two_targets_send_once_after_all_checks(self):
  self.assertEqual(self.run_plan(),0);self.assertEqual(self.calls,[['deploy','dv'],['deploy','st'],['verify','dv'],['verify','st']]);self.assertEqual(len(self.sent),1);self.assertIn('DV',self.sent[0]);self.assertIn('ST',self.sent[0]);self.assertEqual(self.status()['notification'],'sent')
 def test_repeat_does_not_redeploy_or_send(self):
  self.run_plan();self.calls.clear();self.assertEqual(self.run_plan(),0);self.assertEqual(self.calls,[]);self.assertEqual(len(self.sent),1)
 def test_failed_verification_never_announces_success(self):
  def execute(a,*rest):self.calls.append(a);return 1 if a==['verify','st'] else 0
  self.assertEqual(self.run_plan(execute=execute),1);self.assertEqual(self.sent,[]);self.assertEqual(self.status()['deployment'],'verification_failed')
 def test_operator_spool_records_failure_without_legacy_sender(self):
  self.plan['operator_notifications']={'spool_directory':str(self.root/'operator-spool')}
  def execute(a,*rest):self.calls.append(a);return 1 if a==['verify','st'] else 0
  self.assertEqual(self.run_plan(execute=execute),1);self.assertEqual(self.sent,[])
  events=list((self.root/'operator-spool').glob('*.json'));self.assertEqual(len(events),1)
  event=json.loads(events[0].read_text());self.assertEqual(event['channel'],'development');self.assertEqual(event['payload']['kind'],'deploy.verification_failed')
 def test_deploy_failure_never_verifies_or_sends(self):
  self.assertEqual(self.run_plan(execute=lambda *a:1),1);self.assertEqual(self.sent,[]);self.assertEqual(self.status()['deployment'],'failed')
 def test_missing_secret_retry_only_sends_saved_notification(self):
  self.secret.unlink();self.assertEqual(self.run_plan(),20);self.assertEqual(self.status()['deployment'],'verified');self.assertEqual(self.status()['notification'],'failed');self.calls.clear();self.secret.write_text('https://hooks.slack.com/services/T/B/test');self.assertEqual(self.run_plan(retry_notification=True),0);self.assertEqual(self.calls,[]);self.assertEqual(len(self.sent),1)
 def test_timeout_is_uncertain_and_never_retried(self):
  def send(*a):raise TimeoutError('private URL must not leak')
  self.assertEqual(self.run_plan(sender=send),20);self.assertEqual(self.status()['notification'],'uncertain');self.assertNotIn('private URL',(self.state/'release-1'/'state.json').read_text());self.assertEqual(self.run_plan(retry_notification=True),20);self.assertEqual(self.sent,[])
 def test_explicit_rejection_can_retry_without_redeployment(self):
  def send(*a):raise d.slack.CompletionError('rejected')
  self.assertEqual(self.run_plan(sender=send),20);self.calls.clear();self.assertEqual(self.run_plan(retry_notification=True),0);self.assertTrue(all(c[0]=='verify' for c in self.calls))
 def test_changed_identity_rejected_before_side_effects(self):
  self.run_plan();self.plan['targets'][0]['version']='different';self.calls.clear()
  with self.assertRaises(d.ReleaseError):self.run_plan()
  self.assertEqual(self.calls,[])
 def test_missing_verify_and_duplicate_targets_rejected(self):
  self.plan['targets'][0]['verify']=[]
  with self.assertRaises(d.ReleaseError):self.run_plan()
  self.plan['targets'][0]['verify']=[['verify']];self.plan['targets'][1]['name']='dv'
  with self.assertRaises(d.ReleaseError):self.run_plan()
  self.assertEqual(self.calls,[])
 def test_artifact_changed_refuses_before_deploy(self):
  self.plan['inputs']=[{'path':'bundle','sha256':'0'*64}];(self.root/'bundle').write_text('actual')
  with self.assertRaises(d.ReleaseError):self.run_plan()
  self.assertEqual(self.calls,[])
 def test_concurrent_release_lock_refuses_nested_sender(self):
  def send(*a):
   with self.assertRaises(d.ReleaseBusy):self.run_plan()
  self.assertEqual(self.run_plan(sender=send),0)
 def test_crash_during_send_is_not_retried(self):
  def send(*a):raise KeyboardInterrupt()
  with self.assertRaises(KeyboardInterrupt):self.run_plan(sender=send)
  self.assertEqual(self.status()['notification'],'sending');self.assertEqual(self.run_plan(retry_notification=True),20);self.assertEqual(self.sent,[])
 def test_crash_during_deploy_requires_manual_resolution(self):
  def execute(*a):raise KeyboardInterrupt()
  with self.assertRaises(KeyboardInterrupt):self.run_plan(execute=execute)
  self.calls.clear()
  with self.assertRaises(d.ReleaseError):self.run_plan()
  self.assertEqual(self.calls,[])
 def test_retry_never_invokes_failing_verification(self):
  self.secret.unlink();self.run_plan();self.secret.write_text('https://hooks.slack.com/services/T/B/test');self.assertEqual(self.run_plan(retry_notification=True,execute=lambda *a:1),0);self.assertEqual(len(self.sent),1)
 def test_release_ids_cannot_overwrite_another_release_state(self):
  self.plan['id']='foo.plan';self.run_plan()
  first=next(p for p in self.state.rglob('*.json') if json.loads(p.read_text()).get('schema')=='colab-release-state/1' and json.loads(p.read_text()).get('id')=='foo.plan');before=first.read_bytes()
  self.plan['id']='foo';self.run_plan();self.assertEqual(first.read_bytes(),before)
 def test_lock_lives_until_deployment_child_exits_after_parent_kill(self):
  import time
  child_code="from pathlib import Path;import os,time;p=Path("+repr(str(self.root))+");(p/'ready').write_text(str(os.getpid()));deadline=time.monotonic()+8\nwhile not (p/'finish').exists() and time.monotonic()<deadline:time.sleep(.02)"
  self.plan['targets']=[{'name':'st','version':'test','deploy':[[os.sys.executable,'-c',child_code]],'verify':[[os.sys.executable,'-c','pass']]}]
  code="import sys;sys.path.insert(0,"+repr(str(Path(__file__).parents[2]))+");from scripts import deploy_release as d;d.run_plan("+repr(str(self.root))+","+repr(self.plan)+",state_dir="+repr(str(self.state))+")"
  proc=subprocess.Popen([os.sys.executable,'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
   deadline=time.monotonic()+5
   while not (self.root/'ready').exists() and time.monotonic()<deadline:time.sleep(.02)
   self.assertTrue((self.root/'ready').exists());proc.kill();proc.wait(timeout=3)
   with self.assertRaises(d.ReleaseBusy):
    with d.release_lock(self.state):pass
  finally:
   (self.root/'finish').touch()
   if proc.poll() is None:proc.kill();proc.wait(timeout=3)
   time.sleep(.1)
class WiringTests(unittest.TestCase):
 def test_existing_staging_entry_and_callers_handle_notification_failure(self):
  root=Path(__file__).parents[2]
  self.assertIn('deploy_release.py', (root/'infra/staging/deploy.sh').read_text())
  self.assertIn('20', (root/'infra/staging/pipeline/run-pipeline.sh').read_text())
  self.assertIn('20)', (root/'infra/staging/pipeline/watch.sh').read_text())
 def test_unmanaged_dv_upload_is_rejected_before_credentials_or_network(self):
  root=Path(__file__).parents[2]
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'index.html').write_text('<html></html>')
   env=dict(os.environ);env.pop('COLAB_DEPLOY_MANAGED',None)
   r=subprocess.run([os.sys.executable,str(root/'services/core-api/ops/deploy_web.py'),'--dist',tmp,'--bucket','not-used'],env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,78);self.assertIn('deploy_release.py',r.stderr)

class EntryPointTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.repo=Path(__file__).parents[2]
  subprocess.run(['git','init','-q',str(self.root)],check=True)
  subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-qm','fixture'],check=True)
  import shutil
  shutil.copytree(self.repo/'infra/notifications',self.root/'infra/notifications')
  self.spool=self.root/'spool'
  (self.root/'scripts').mkdir();(self.root/'scripts/deploy_release.py').write_text((self.repo/'scripts/deploy_release.py').read_text())
  (self.root/'scripts/slack_completion.py').write_text("from pathlib import Path\nDEFAULT_SECRET=Path(__file__).parents[1]/'webhook'\nclass CompletionError(ValueError):pass\ndef validate_url(v):return v\ndef snapshot(root):return 'f'*64\ndef send_webhook(url,text):\n with (DEFAULT_SECRET.parent/'events').open('a') as f:f.write('notify\\n')\n")
  (self.root/'webhook').write_text('fixture-no-network')
 def call(self,*args):
  env=dict(os.environ,COLAB_OPERATOR_SPOOL_DIRECTORY=str(self.spool));env.pop('COLAB_DEPLOY_MANAGED',None);env.pop('PYTHONPATH',None)
  return subprocess.run([os.sys.executable,str(self.root/'scripts/deploy_release.py'),*args],cwd=self.root,env=env,capture_output=True,text=True)
 def test_real_cli_groups_targets_and_deduplicates_without_stop(self):
  def cmd(value):return [os.sys.executable,'-c',"from pathlib import Path; p=Path('events'); p.open('a').write("+repr(value+'\n')+")"]
  plan={'schema':'colab-deploy/1','id':'cli-release','targets':[{'name':n,'version':'abc123','deploy':[cmd('deploy-'+n)],'verify':[cmd('verify-'+n)]} for n in ['dv','st']]}
  (self.root/'release.json').write_text(json.dumps(plan))
  r=self.call('run','--plan','release.json');self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertEqual((self.root/'events').read_text().splitlines(),['deploy-dv','deploy-st','verify-dv','verify-st'])
  self.assertEqual(self.call('run','--plan','release.json').returncode,0);self.assertEqual(len(list(self.spool.glob('*.json'))),2)
 def test_staging_direct_entry_wraps_and_queues_operator_event(self):
  folder=self.root/'infra/staging';(folder/'verify').mkdir(parents=True,exist_ok=True)
  original=(self.repo/'infra/staging/deploy.sh').read_text();prefix=original.split('. "$HERE/pipeline/lib.sh"')[0]
  (folder/'deploy.sh').write_text(prefix+"printf 'deploy\\n' >> events\n")
  for name in ['verify-deploy.sh','verify-chains.sh']:(folder/'verify'/name).write_text("printf 'verify\\n' >> events\n")
  env=dict(os.environ,COLAB_OPERATOR_SPOOL_DIRECTORY=str(self.spool));env.pop('COLAB_DEPLOY_MANAGED',None);env.pop('PYTHONPATH',None)
  r=subprocess.run(['bash',str(folder/'deploy.sh'),'--target','staging'],cwd=self.root,env=env,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual((self.root/'events').read_text().splitlines(),['deploy','verify','verify'])
 def test_watch_keeps_deployment_success_on_notification_failure(self):
  import shutil
  folder=self.root/'watch';folder.mkdir();state=self.root/'pipeline-state';state.mkdir()
  for name in ['watch.sh','lib.sh']:shutil.copy2(self.repo/'infra/staging/pipeline'/name,folder/name)
  (folder/'run-pipeline.sh').write_text('#!/bin/sh\nexit 20\n');(folder/'run-pipeline.sh').chmod(0o755)
  (state/'LAST-SUCCESS.txt').write_text('deployment-ok')
  r=subprocess.run(['bash',str(folder/'watch.sh')],env=dict(os.environ,COLAB_PIPELINE_STATE_DIR=str(state)),capture_output=True,text=True)
  self.assertEqual(r.returncode,20);self.assertEqual((state/'LAST-SUCCESS.txt').read_text(),'deployment-ok');self.assertFalse((state/'DEPLOY-FAILED.txt').exists());self.assertTrue((state/'NOTIFICATION-FAILED.txt').exists())
 def test_pipeline_does_not_relabel_notification_failure_as_deploy_red(self):
  import shutil
  folder=self.root/'infra/staging/pipeline';(folder/'approval').mkdir(parents=True);fakebin=self.root/'bin';fakebin.mkdir()
  for name in ['run-pipeline.sh','lib.sh']:shutil.copy2(self.repo/'infra/staging/pipeline'/name,folder/name)
  (folder/'approval/target.sh').write_text('#!/bin/sh\nexit 0\n');(folder/'approval/target.sh').chmod(0o755)
  (folder.parent/'deploy.sh').write_text('#!/bin/sh\nexit 20\n');(folder.parent/'deploy.sh').chmod(0o755)
  (fakebin/'git').write_text('#!/bin/sh\ncase "$*" in *fetch*) exit 0;; *) echo abc123;; esac\n');(fakebin/'git').chmod(0o755)
  r=subprocess.run(['bash',str(folder/'run-pipeline.sh'),'--target','staging','--force'],env=dict(os.environ,PATH=str(fakebin)+os.pathsep+os.environ['PATH'],COLAB_PIPELINE_STATE_DIR=str(self.root/'state')),capture_output=True,text=True)
  self.assertEqual(r.returncode,20,r.stdout+r.stderr);self.assertNotIn('파이프라인 RED',r.stdout+r.stderr);self.assertIn('배포·검증 성공',r.stdout+r.stderr)
 def test_two_worktrees_share_one_deployment_lock(self):
  other=self.root/'other';subprocess.run(['git','-C',str(self.root),'worktree','add','--detach',str(other),'HEAD'],check=True,capture_output=True)
  self.assertEqual(d.state_directory(self.root),d.state_directory(other))
  with d.release_lock(d.state_directory(self.root)):
   with self.assertRaises(d.ReleaseBusy):
    with d.release_lock(d.state_directory(other)):pass

class OperatorOutboxRecoveryTests(unittest.TestCase):
 setUp=ReleaseTests.setUp
 execute=ReleaseTests.execute
 run_plan=ReleaseTests.run_plan
 status=ReleaseTests.status
 def test_failure_is_terminal_before_spool_failure_and_retry_keeps_failure(self):
  from unittest.mock import patch
  self.plan['operator_notifications']={'spool_directory':str(self.root/'operator-spool')}
  def fail(a,*rest):self.calls.append(a);return 1
  with patch('infra.notifications.spool.append',side_effect=OSError('disk unavailable')):
   with self.assertRaises(OSError):self.run_plan(execute=fail)
  state=self.status();self.assertEqual(state['deployment'],'failed');self.assertTrue(state.get('operator_outbox'))
  records=state['operator_outbox'];calls=list(self.calls)
  self.assertEqual(self.run_plan(retry_notification=True),1);self.assertEqual(self.calls,calls)
  self.assertEqual([json.loads(p.read_text()) for p in (self.root/'operator-spool').glob('*.json')],records)
  self.assertEqual(self.run_plan(),1);self.assertEqual(self.calls,calls)
 def test_partial_success_spool_restart_replays_identical_events_without_commands(self):
  from unittest.mock import patch
  from infra.notifications.spool import append
  self.plan['operator_notifications']={'spool_directory':str(self.root/'operator-spool')}
  appended=[]
  def flaky(directory,event):
   if appended:raise OSError('disk unavailable')
   appended.append(event);return append(directory,event)
  with patch('infra.notifications.spool.append',side_effect=flaky):
   with self.assertRaises(OSError):self.run_plan()
  state=self.status();self.assertEqual(state['deployment'],'verified');self.assertEqual(len(state.get('operator_outbox',[])),2)
  records=state['operator_outbox'];calls=list(self.calls)
  self.assertEqual(self.run_plan(retry_notification=True),0);self.assertEqual(self.calls,calls)
  actual=sorted([json.loads(p.read_text()) for p in (self.root/'operator-spool').glob('*.json')],key=lambda r:r['event_id'])
  self.assertEqual(actual,sorted(records,key=lambda r:r['event_id']));self.assertEqual(appended[0],records[0])
