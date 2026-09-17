import importlib.util,json,pathlib,types,os
import pytest
P=pathlib.Path(__file__).parents[1]
def mod():
 s=importlib.util.spec_from_file_location('reseed_accounts',P/'accounts.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def profile():return json.loads((P/'accounts-profile.example.json').read_text())

@pytest.fixture(autouse=True)
def approved_profile(tmp_path,monkeypatch):
 p=tmp_path/'test-approved-profile.json';p.write_text(json.dumps(profile()));p.chmod(0o600)
 monkeypatch.setenv('COLAB_RESEED_ACCOUNTS_PROFILE',str(p))

def test_profile_requires_exact_five():
 m=mod();p=profile();m.validate(p,p)
 with pytest.raises(ValueError):m.validate(p[:-1],p)
def test_role_and_lab_cannot_be_added_to_operator():
 m=mod();p=profile();bad=json.loads(json.dumps(p));bad[0]['lab']='other';bad[0]['role']='교수'
 with pytest.raises(ValueError):m.validate(bad,p)
def test_prepare_creates_distinct_private_passwords(tmp_path):
 m=mod();p=profile();m.prepare(p,tmp_path)
 generated=json.loads((tmp_path/'accounts.json').read_text())
 assert len(generated)==5
 for e in generated:
  f=pathlib.Path(e['password_file']);assert f.stat().st_mode&0o777==0o600;assert f.read_text().strip()==e['email']
 assert len(list(tmp_path.glob('operator-*.json')))==4
def test_finalize_resume_never_resets_twice():
 m=mod();p=profile();rows=[];creds={};calls=[]
 for i,e in enumerate(p):
  rows.append(types.SimpleNamespace(email=e['email'],name=e['name'],role=e.get('role') or None,lab_name=e.get('lab') or None,lab_id=e.get('lab_id'),account_id=e.get('account_id') or str(i),operator=True))
  creds[e['email']]=types.SimpleNamespace(password=e['email'] if e['admin'] else 'temporary',must_change_password=e['admin'],status='active')
 class Store:
  def list_accounts(self):return rows
  def find(self,e):return creds[e]
  def reset_password(self,aid,pw):
   calls.append('reset');x=next(r for r in rows if r.account_id==aid);creds[x.email].password=pw;creds[x.email].must_change_password=True;return 2
  def set_operator(self,aid,v,actor_account_id):
   calls.append('operator');next(r for r in rows if r.account_id==aid).operator=v;return v
 st=Store();m.finalize_store(st,p,lambda pw,hash:pw==hash);m.finalize_store(st,p,lambda pw,hash:pw==hash)
 assert calls==['reset','operator']
def test_legacy_backup_retains_original_and_refuses_drift(tmp_path):
 m=mod();f=tmp_path/'subjects.json';f.write_text('{"old":{}}');f.chmod(0o600);m.clear_legacy([f],tmp_path/'backup');assert json.loads(f.read_text())=={}
 assert (tmp_path/'backup'/'subjects.json').read_text()=='{"old":{}}'
 f.write_text('{"new":{}}')
 with pytest.raises(ValueError):m.clear_legacy([f],tmp_path/'backup')

def test_read_only_wrapper_delegates_without_recursion():
 m=mod();store=types.SimpleNamespace(list_accounts=lambda:['row'],find=lambda email:email)
 ro=m.ReadOnlyStore(store)
 assert ro.list_accounts()==['row'] and ro.find('account')=='account'
 with pytest.raises(ValueError):ro.reset_password('id','password')

def test_container_dev_check_uses_mounted_paths(tmp_path,monkeypatch):
 m=mod()
 for key,name in [('COLAB_CORE_SUBJECTS_FILE','subjects.json'),('COLAB_CORE_CREDENTIALS_FILE','credentials.json')]:
  path=tmp_path/name;path.write_text('{}');monkeypatch.setenv(key,str(path))
 db=tmp_path/'db.url';db.write_text('postgresql://user:pw@colab-platform-dev.example/db');monkeypatch.setenv('COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE',str(db))
 monkeypatch.setenv('COLAB_CORE_S3_BUCKET','colab-platform-data-dev')
 m.assert_dev_container()
 monkeypatch.setenv('COLAB_CORE_S3_BUCKET','colab-platform-data-prod')
 with pytest.raises(ValueError):m.assert_dev_container()

def test_binding_must_be_nonempty_sha():
 m=mod()
 for value in [None,'','run','0'*63]:
  with pytest.raises(ValueError):m.require_binding(value)
 m.require_binding('a'*64)

def test_detail_proof_refuses_changed_seed(tmp_path):
 m=mod();seed=tmp_path/'seed';seed.mkdir();run=tmp_path/'run';run.mkdir();work=seed/'accounts';work.mkdir()
 for p in [seed/'state.json',seed/'verify.json',run/'counts.json',run/'preview-judgment.tsv']:p.write_text('{}')
 binding=m.proof(profile(),work,run,'a'*40,True)
 assert m.proof(profile(),work,None,'a'*40)==binding
 (seed/'state.json').write_text('{"changed":true}')
 with pytest.raises(ValueError):m.proof(profile(),work,None,'a'*40)

def test_report_rejects_missing_account_evidence(tmp_path):
 s=importlib.util.spec_from_file_location('reseed_report',P/'report.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
 with pytest.raises(ValueError):r.check_accounts(tmp_path,P/'accounts-profile.example.json','a'*40)

def test_remote_source_runs_with_python_c_without_file(tmp_path):
 import subprocess,sys
 source=(P/'accounts.py').read_text()
 # Input fails target check, rather than failing before remote_main (__file__).
 result=subprocess.run([sys.executable,'-c',source,'remote-clear'],input='{}',text=True,capture_output=True)
 assert '__file__' not in result.stderr and 'Traceback' not in result.stderr

def test_login_verifies_five_without_rotating_and_logs_out(tmp_path):
 import io
 m=mod();entries=m.prepare(profile(),tmp_path);calls=[];active={}
 class Response(io.StringIO):
  def __init__(self,value,status):super().__init__(json.dumps(value));self.status=status
 def opener(req,timeout):
  calls.append((req.method,req.full_url))
  if req.method=='POST':
   data=json.loads(req.data);assert data['accountName']==data['password'];active['entry']=next(e for e in entries if e['email']==data['accountName']);return Response({'token':'fixture'},201)
  if req.method=='DELETE':return Response(None,204)
  e=active['entry'];return Response(dict(email=e['email'],name=e['name'],role=e['role'] or None,labName=e['lab'] or None,labId=e.get('lab_id'),accountId=e.get('account_id','fixture'),mustChangePassword=True,canManageServiceAccounts=e['admin']),200)
 assert m.verify_logins(entries,'https://fixture.invalid',opener)['accounts']==5
 assert len(calls)==15 and sum(method=='DELETE' for method,url in calls)==5
 assert all('/api/v1/' in url for method,url in calls)
 assert not any('password' in url for method,url in calls)

def test_report_accepts_bound_five_account_evidence(tmp_path):
 m=mod();seed=tmp_path/'seed';seed.mkdir();run=tmp_path/'run';run.mkdir();work=seed/'accounts';work.mkdir()
 for p in [seed/'state.json',seed/'verify.json',run/'counts.json',run/'preview-judgment.tsv']:p.write_text('{}')
 binding=m.proof(profile(),work,run,'a'*12,True);identity={'profile':m.fingerprint(profile()),'binding':binding}
 m.save(work/'finalization.json',{**identity,'state':'complete'})
 m.save(work/'verification.json',{**identity,'accounts':5,'operators':4,'professors':1,'must_change_password':True,'password_changed_by_check':False})
 s=importlib.util.spec_from_file_location('reseed_report',P/'report.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
 r.check_accounts(work,pathlib.Path(os.environ['COLAB_RESEED_ACCOUNTS_PROFILE']),'a'*12)
 value=json.loads((work/'verification.json').read_text());value['accounts']=4;m.save(work/'verification.json',value)
 with pytest.raises(ValueError):r.check_accounts(work,pathlib.Path(os.environ['COLAB_RESEED_ACCOUNTS_PROFILE']),'a'*12)

def test_real_remote_verify_python_c_with_store_stub(tmp_path):
 import subprocess,sys,os
 m=mod();p=profile();env=dict(os.environ,COLAB_CORE_S3_BUCKET='colab-platform-data-dev')
 for key,name,data in [('COLAB_CORE_SUBJECTS_FILE','subjects','{}'),('COLAB_CORE_CREDENTIALS_FILE','credentials','{}'),('COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE','db','postgresql://x:y@colab-platform-dev-db.example/db')]:
  path=tmp_path/name;path.write_text(data);env[key]=str(path)
 prefix='''import sys,types,json
entries=json.loads(sys.argv.pop(2))
class Store:
 def __init__(self,*a):pass
 def list_accounts(self):return [types.SimpleNamespace(email=e['email'],name=e['name'],role=e['role'],lab_name=e['lab'],lab_id=e.get('lab_id'),account_id=e.get('account_id',str(i)),operator=e['admin']) for i,e in enumerate(entries)]
 def find(self,email):return types.SimpleNamespace(password=email,must_change_password=True,status='active')
 def reset_password(self,*a,**kw):raise AssertionError('unexpected reset')
 def set_operator(self,*a,**kw):raise AssertionError('unexpected operator mutation')
for name,values in {'sqlalchemy':{'create_engine':lambda x:None},'sqlalchemy.orm':{'sessionmaker':lambda x:None},'colab_core.kernel.db_credentials':{'DatabaseCredentialStore':Store},'colab_core.kernel.password':{'verify_password':lambda p,h:p==h}}.items():
 mod=types.ModuleType(name);mod.__dict__.update(values);sys.modules[name]=mod
'''
 result=subprocess.run([sys.executable,'-c',prefix+(P/'accounts.py').read_text(),'remote-verify',json.dumps(p)],env=env,input=json.dumps({'entries':p}),text=True,capture_output=True)
 assert result.returncode==0,result.stderr
 assert json.loads(result.stdout)['accounts']==5

def test_reset_rejects_existing_initial_password_file(tmp_path):
 import subprocess,os
 work=tmp_path/'seed';work.mkdir();old=work/'initial-password.txt';old.write_text('stale-initial');old.chmod(0o600)
 env=dict(os.environ,RESEED_DIR=str(P),ACCOUNTS_FILE=str(P/'accounts-profile.example.json'),PROVISION_LAB_SQL=str(P.parents[2]/'infra/staging/provision-lab.sql'),RESEED_ACCOUNT_EMAIL=profile()[-1]['email'],SEED_WORK_DIR=str(work))
 result=subprocess.run(['bash','-c','. "$RESEED_DIR/preflight.sh"; validate_seed_inputs 1'],env=env,capture_output=True,text=True)
 assert result.returncode!=0
 assert old.read_text()=='stale-initial'

def test_default_profile_is_private_external_config(tmp_path,monkeypatch):
 monkeypatch.setenv('COLAB_RESEED_ACCOUNTS_PROFILE',str(tmp_path/'approved.json'))
 m=mod()
 assert m.DEFAULT_PROFILE==tmp_path/'approved.json'
 # Public examples must never become the execution profile on missing config.
 monkeypatch.setattr('sys.argv',['accounts.py','validate'])
 with pytest.raises((ValueError,FileNotFoundError)):m.main()
 approved=tmp_path/'approved.json';approved.write_text(json.dumps(profile()));approved.chmod(0o600)
 m.main()
 approved.chmod(0o644)
 with pytest.raises(ValueError):m.main()
