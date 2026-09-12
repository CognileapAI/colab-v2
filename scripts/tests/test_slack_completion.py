import importlib.util, json, subprocess, tempfile, threading, unittest
from pathlib import Path
from unittest import mock

P = Path(__file__).parents[1] / "slack_completion.py"
S = importlib.util.spec_from_file_location("slack_completion", P)
slack = importlib.util.module_from_spec(S); S.loader.exec_module(slack)

class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.r=Path(self.t.name)
  subprocess.run(["git","init","-q",str(self.r)],check=True)
  subprocess.run(["git","-C",str(self.r),"config","user.email","t@e"],check=True)
  subprocess.run(["git","-C",str(self.r),"config","user.name","T"],check=True)
  (self.r/"a").write_text("a"); subprocess.run(["git","-C",str(self.r),"add","a"],check=True)
  subprocess.run(["git","-C",str(self.r),"commit","-qm","a"],check=True)
  self.e=self.r/"gate.json"; self.e.write_text(json.dumps({"schema":"colab-gate-summary/1","counts":{"green":1,"red_판정":0,"red_준비":0},"gates":[{"name":"g","state":"green","exit":0}]}))
  self.m=self.r/"report.md"; self.m.write_text("무엇을 바꿨나요?\n완료\n\n어떻게 확인했나요?\n통과\n")
 def tearDown(self): self.t.cleanup()
 def verify(self,root,task,path):
  d=json.loads(path.read_text()); c=d["counts"]
  if c["red_판정"] or c["red_준비"]: raise slack.CompletionError("red")
 def prep(self): slack.prepare(self.r,"s1",self.m,[("task",self.e)],True,[],verifier=self.verify)
 def event(self,s="s1"): return {"hook_event_name":"Stop","session_id":s,"cwd":str(self.r)}
 def test_ordinary_stop_no_send(self):
  f=mock.Mock(); self.assertEqual(slack.handle_stop(self.event("none"),sender=f),{}); f.assert_not_called()
 def test_bad_evidence_and_incomplete_scope_rejected(self):
  d=json.loads(self.e.read_text()); d["counts"]["red_준비"]=1; self.e.write_text(json.dumps(d))
  with self.assertRaises(slack.CompletionError): self.prep()
  with self.assertRaises(slack.CompletionError): slack.prepare(self.r,"s1",self.m,[],False,["review"],verifier=self.verify)
 def test_changed_report_rejected(self):
  self.prep(); self.m.write_text("changed"); f=mock.Mock(); result=slack.handle_stop(self.event(),sender=f,verifier=self.verify); f.assert_not_called(); self.assertIn("systemMessage",result)
 def test_missing_or_invalid_secret_keeps_pending(self):
  self.prep()
  for value in ("","https://example.com/services/a/b/c"):
   p=slack.box(self.r)/"secret"; p.write_text(value); f=mock.Mock(); result=slack.handle_stop(self.event(),sender=f,secret_path=p,verifier=self.verify)
   f.assert_not_called(); self.assertTrue(slack.pending_path(self.r,"s1").exists())
   self.assertIn("systemMessage",result)
 def test_concurrent_stop_sends_once(self):
  self.prep(); p=slack.box(self.r)/"secret"; p.write_text("https://hooks.slack.com/services/T1/B2/abc")
  calls=[]; b=threading.Barrier(2)
  def send(u,t): calls.append((u,t))
  def run(): b.wait(); slack.handle_stop(self.event(),sender=send,secret_path=p,verifier=self.verify)
  ts=[threading.Thread(target=run) for _ in range(2)]; [x.start() for x in ts]; [x.join() for x in ts]
  self.assertEqual(len(calls),1)
 def test_ambiguous_failure_not_retried(self):
  self.prep(); p=slack.box(self.r)/"secret"; p.write_text("https://hooks.slack.com/services/T1/B2/abc"); calls=[]
  def fail(u,t): calls.append(1); raise TimeoutError("secret")
  for _ in range(2): slack.handle_stop(self.event(),sender=fail,secret_path=p,verifier=self.verify)
  self.assertEqual(len(calls),1); self.assertTrue(list(slack.box(self.r).glob("s1.*.uncertain.json")))
  with self.assertRaises(slack.CompletionError): self.prep()
 def test_setup_preserves_old_value_on_invalid_input(self):
  p=self.r/"secret"; p.write_text("old")
  with self.assertRaises(slack.CompletionError): slack.install_secret(p,"https://hooks.slack.com/services/T/B/x\n")
  self.assertEqual(p.read_text(),"old"); slack.install_secret(p,"https://hooks.slack.com/services/T/B/abc")
  self.assertEqual(p.stat().st_mode & 0o777,0o600)
 def test_clean_head_change_is_rejected(self):
  self.prep(); (self.r/"a").write_text("b"); subprocess.run(["git","-C",str(self.r),"commit","-am","b","-q"],check=True)
  p=slack.box(self.r)/"secret"; p.write_text("https://hooks.slack.com/services/T/B/abc"); f=mock.Mock()
  slack.handle_stop(self.event(),sender=f,secret_path=p,verifier=self.verify); f.assert_not_called()
 def test_success_receipt_prevents_reprepare(self):
  self.prep(); p=slack.box(self.r)/"secret"; p.write_text("https://hooks.slack.com/services/T/B/abc")
  slack.handle_stop(self.event(),sender=lambda u,t:None,secret_path=p,verifier=self.verify)
  self.assertTrue(list(slack.box(self.r).glob("s1.*.sent.json")))
  with self.assertRaises(slack.CompletionError): self.prep()
  self.m.write_text("무엇을 바꿨나요?\n두 번째 작업\n")
  with self.assertRaises(slack.CompletionError): self.prep()
  slack.prepare(self.r,"s1",self.m,[("task-2",self.e)],True,[],verifier=self.verify)
  self.assertTrue(slack.pending_path(self.r,"s1").exists())
 def test_lifecycle_verifier_runs_at_prepare_and_stop(self):
  calls=[]
  def verify(root,task,path): calls.append((task,path))
  slack.prepare(self.r,"s1",self.m,[("task",self.e)],True,[],verifier=verify)
  p=slack.box(self.r)/"secret"; p.write_text("https://hooks.slack.com/services/T/B/abc")
  slack.handle_stop(self.event(),sender=lambda u,t:None,secret_path=p,verifier=verify)
  self.assertEqual([x[0] for x in calls],["task","task"])
 def test_sender_cannot_rearm_same_session_while_in_flight(self):
  self.prep(); p=slack.box(self.r)/"secret"; p.write_text("https://hooks.slack.com/services/T/B/abc"); calls=[]
  def send(u,t):
   calls.append(1)
   with self.assertRaises(slack.CompletionError): self.prep()
   slack.handle_stop(self.event(),sender=lambda u,t:calls.append(2),secret_path=p,verifier=self.verify)
  slack.handle_stop(self.event(),sender=send,secret_path=p,verifier=self.verify)
  slack.handle_stop(self.event(),sender=lambda u,t:calls.append(3),secret_path=p,verifier=self.verify)
  self.assertEqual(calls,[1])
 def test_subdirectory_prepare_and_stop_use_checkout_root(self):
  sub=self.r/"nested"; sub.mkdir()
  slack.prepare(sub,"s1",self.m,[("task",self.e)],True,[],verifier=self.verify)
  p=slack.box(self.r)/"secret"; p.write_text("https://hooks.slack.com/services/T/B/abc"); calls=[]
  slack.handle_stop({"hook_event_name":"Stop","session_id":"s1","cwd":str(sub)},sender=lambda u,t:calls.append(1),secret_path=p,verifier=self.verify)
  self.assertEqual(calls,[1])
 def test_hook_cli_emits_declared_delivery_failure(self):
  self.prep()
  event=json.dumps(self.event())
  with mock.patch.object(slack,"handle_stop",return_value={"systemMessage":"safe failure"}):
   with mock.patch("builtins.print") as output:
    self.assertEqual(slack.cli(["hook"],stdin=event),0)
  self.assertIn("systemMessage",output.call_args.args[0])

if __name__=="__main__": unittest.main()
