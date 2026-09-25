"""Required dev account profile, protected preparation and resumable finalization."""
import argparse,re,hashlib,json,os,pathlib,shlex,stat,subprocess,sys,tempfile
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
DEFAULT_PROFILE=pathlib.Path(os.environ.get('COLAB_RESEED_ACCOUNTS_PROFILE',str(pathlib.Path.home()/'.config/colab-platform/dev-reseed-accounts-approved.json'))).expanduser()
IDENTITY=('email','name','admin','role','lab','account_id','lab_id','initial_password_strategy')
# ownerManaged = 소유자가 비밀번호를 관리하는 운영자(2026-09-25 사용자 결정). 없으면 false 다.
# 최종화·검증은 그 계정의 「초기 자격」 조건(비밀번호 = 이메일 · 변경 요구)만 건너뛰고 비밀번호를 바꾸지 않는다.
# 교수 계정에는 둘 수 없다 — 교수 최종화는 초기 비밀번호로 되돌리는 절차다.
def owner_managed(e):
 value=e.get('ownerManaged',False)
 if not isinstance(value,bool):raise ValueError('ownerManaged must be boolean')
 if value and not e.get('admin'):raise ValueError('ownerManaged is for operators only')
 return value
def validate(entries,expected,policy=True):
 if not isinstance(entries,list) or len(entries)!=5 or len({e.get('email') for e in entries})!=5:raise ValueError('exact five accounts required')
 want={e['email']:e for e in expected}
 if set(want)!={e['email'] for e in entries}:raise ValueError('approved account set required')
 for e in entries:
  if any(e.get(k)!=want[e['email']].get(k) for k in IDENTITY):raise ValueError('account identity or password policy mismatch')
  if policy and owner_managed(e)!=owner_managed(want[e['email']]):raise ValueError('ownerManaged differs from approved profile')
  if e.get('password_file') and private(e['password_file']).read_text().strip()!=e['email']:raise ValueError('initial password mismatch')
def private(path):
 p=pathlib.Path(path)
 if p.is_symlink() or not p.is_file() or stat.S_IMODE(p.stat().st_mode)!=0o600:raise ValueError('private regular file 0600 required')
 return p

def save(path,value):
 path=pathlib.Path(path);path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=path.parent)
 try:
  with os.fdopen(fd,'w') as f:json.dump(value,f,sort_keys=True);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
  fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd)
  finally:os.close(fd)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def fingerprint(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def professor(entries):return next(e for e in entries if not e['admin'])
def prepare(entries,directory):
 directory=pathlib.Path(directory);directory.mkdir(mode=0o700,parents=True,exist_ok=True);out=[]
 for i,e in enumerate(entries):
  pw=directory/('initial-'+str(i)+'.txt')
  if pw.exists():
   if private(pw).read_text().strip()!=e['email']:raise ValueError('existing password input changed')
  else:
   fd=os.open(pw,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'w') as f:f.write(e['email']+'\n');f.flush();os.fsync(f.fileno())
  row={**e,'password_file':str(pw)};out.append(row)
  if e['admin']:save(directory/('operator-'+str(i)+'.json'),[{k:e[k] for k in ('email','name','role','lab','admin')}])
 save(directory/'accounts.json',out)
 return out

def finalize_store(store,entries,verify_password):
 rows={r.email:r for r in store.list_accounts()};wanted={e['email']:e for e in entries};p=professor(entries)
 if set(rows)!=set(wanted):raise ValueError('unexpected or missing accounts')
 for email,e in wanted.items():
  r=rows[email]
  if r.name!=e['name'] or (r.role or '')!=e['role'] or (r.lab_name or '')!=e['lab']:raise ValueError('role/name/affiliation drift')
  if e['admin'] and (not r.operator or r.lab_id is not None):raise ValueError('labless operator mismatch')
  if not e['admin'] and (r.account_id!=e['account_id'] or r.lab_id!=e['lab_id']):raise ValueError('professor identity mismatch')
  cred=store.find(email)
  if cred is None or cred.status!='active':raise ValueError('credential missing/inactive')
  if e['admin'] and not owner_managed(e) and (not cred.must_change_password or not verify_password(email,cred.password)):raise ValueError('operator initial credential changed')
 r=rows[p['email']];cred=store.find(p['email'])
 initial=cred.must_change_password and verify_password(p['email'],cred.password)
 if not initial:
  if not r.operator:raise ValueError('final professor credential drift; refusing another reset')
  if store.reset_password(r.account_id,p['email']) is None:raise ValueError('professor reset failed')
 if r.operator:
  actor=next(rows[e['email']] for e in entries if e['admin'])
  if store.set_operator(r.account_id,False,actor_account_id=actor.account_id) is not False:raise ValueError('operator removal failed')
 final={r.email:r for r in store.list_accounts()}
 for email,e in wanted.items():
  cred=store.find(email)
  if final[email].operator is not e['admin'] or cred is None or cred.status!='active':raise ValueError('final account policy mismatch')
  if not owner_managed(e) and (not cred.must_change_password or not verify_password(email,cred.password)):raise ValueError('final account policy mismatch')
 return {'accounts':5,'operators':4,'professors':1,'must_change_password':True,'password_changed_by_check':False,'owner_managed':sum(map(owner_managed,entries))}

def verify_logins(entries,base_url,opener=urlopen):
 def request(method,path,data=None,token=None,status=200):
  h={'Content-Type':'application/json'}
  if token:h['Authorization']='Bearer '+token
  req=Request(base_url.rstrip('/')+'/api/v1'+path,data=json.dumps(data).encode() if data is not None else None,headers=h,method=method)
  with opener(req,timeout=30) as res:
   if res.status!=status:raise ValueError('login verification response mismatch')
   return json.load(res) if status!=204 else None
 # 소유자 관리 운영자는 초기 비밀번호가 없다 — 로그인을 시도하지 않는다(신원·권한은 finalize_store 가 저장소에서 대조했다).
 for e in [e for e in entries if not owner_managed(e)]:
  token=request('POST','/sessions',{'accountName':e['email'],'password':private(e['password_file']).read_text().strip()},status=201)['token']
  try:
   me=request('GET','/me-v2',token=token)
   if not me.get('accountId') or me.get('labId')!=e.get('lab_id') or (e.get('account_id') and me['accountId']!=e['account_id']):raise ValueError('initial login account boundary mismatch')
   if any(me.get(k)!=v for k,v in {'email':e['email'],'name':e['name'],'mustChangePassword':True,'canManageServiceAccounts':e['admin']}.items()) or (me.get('role') or '')!=e['role'] or (me.get('labName') or '')!=e['lab']:raise ValueError('initial login identity/policy mismatch')
  finally:request('DELETE','/sessions/current',token=token,status=204)
 owners=sum(map(owner_managed,entries))
 return {'accounts':5,'operators':4,'professors':1,'must_change_password':True,'password_changed_by_check':False,'owner_managed':owners,'initial_logins':5-owners}

def clear_legacy(paths,backup):
 backup=pathlib.Path(backup);backup.mkdir(mode=0o700,parents=True,exist_ok=True)
 for value in paths:
  p=pathlib.Path(value);info=p.stat();raw=p.read_bytes();old=backup/p.name
  if p.is_symlink() or not isinstance(json.loads(raw),dict):raise ValueError('legacy file format')
  if old.exists():
   if json.loads(raw)!={}:raise ValueError('legacy changed after backup')
   continue
  fd=os.open(old,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  fd=os.open(backup,os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd)
  finally:os.close(fd)
  # Preserve inode: deployment may bind mount these exact files.
  with p.open('w') as f:f.write('{}\n');f.flush();os.fsync(f.fileno())
  os.chown(p,info.st_uid,info.st_gid);os.chmod(p,stat.S_IMODE(info.st_mode))

def remote(args,mode,payload,container=True):
 source=pathlib.Path(__file__).read_text()
 cmd=['sudo']+(['docker','exec','-i','colab_v2_dev_core_api'] if container else [])+['python3','-c',source,mode]
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-i',args.key,args.ssh,shlex.join(cmd)],input=json.dumps(payload),capture_output=True,text=True)
 if p.returncode:raise ValueError('remote account operation failed; retained state requires review')
 return json.loads(p.stdout)

class ReadOnlyStore:
 def __init__(self,store):self.store=store
 def list_accounts(self):return self.store.list_accounts()
 def find(self,email):return self.store.find(email)
 def reset_password(self,*a,**kw):raise ValueError('finalization incomplete')
 def set_operator(self,*a,**kw):raise ValueError('finalization incomplete')

def require_binding(value):
 if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('execution binding required')

def assert_dev_container():
 url=pathlib.Path(os.environ['COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE']).read_text().strip()
 if not re.fullmatch(r'colab-platform-dev(?:-db)?\.[a-z0-9.-]+',urlsplit(url).hostname or ''):raise ValueError('dev database required')
 if os.environ.get('COLAB_CORE_S3_BUCKET')!='colab-platform-data-dev':raise ValueError('dev container required')
 for key in ('COLAB_CORE_SUBJECTS_FILE','COLAB_CORE_CREDENTIALS_FILE'):
  if json.loads(pathlib.Path(os.environ[key]).read_text())!={}:raise ValueError('legacy credentials remain')

def assert_dev_stopped(paths):
 result=subprocess.run(['docker','inspect','colab_v2_dev_core_api'],capture_output=True,text=True,check=True)
 info=json.loads(result.stdout)[0]
 env=dict(v.split('=',1) for v in info['Config']['Env'] if '=' in v)
 if info['State']['Running'] or env.get('COLAB_CORE_S3_BUCKET')!='colab-platform-data-dev':raise ValueError('stopped dev container required')
 mounts={v['Destination']:v['Source'] for v in info['Mounts']}
 expected=[]
 for key in ('COLAB_CORE_SUBJECTS_FILE','COLAB_CORE_CREDENTIALS_FILE'):
  target=env[key]
  if target in mounts:expected.append(mounts[target]);continue
  parent=str(pathlib.PurePosixPath(target).parent)
  expected.append(str(pathlib.PurePosixPath(mounts[parent])/pathlib.PurePosixPath(target).name))
 if [str(pathlib.Path(p).resolve()) for p in paths]!=[str(pathlib.Path(p).resolve()) for p in expected]:raise ValueError('dev legacy mounts mismatch')

def remote_main(mode):
 payload=json.load(sys.stdin)
 if mode=='remote-clear':
  assert_dev_stopped(payload['paths'])
  clear_legacy(payload['paths'],payload['backup']);print(json.dumps({'legacy_empty':True}));return
 from sqlalchemy import create_engine
 from sqlalchemy.orm import sessionmaker
 from colab_core.kernel.db_credentials import DatabaseCredentialStore
 from colab_core.kernel.password import verify_password
 assert_dev_container()
 store=DatabaseCredentialStore(sessionmaker(create_engine(pathlib.Path(os.environ['COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE']).read_text().strip())))
 if mode=='remote-verify':
  # Never mutates on report/reverification; compare current final policy only.
  for e in payload['entries']:
   cred=store.find(e['email'])
   if owner_managed(e):continue
   if cred is None or not cred.must_change_password or not verify_password(e['email'],cred.password):raise ValueError('final credential changed')
  store=ReadOnlyStore(store)
 result=finalize_store(store,payload['entries'],verify_password);print(json.dumps(result))

def detail_binding(entries,seed,run,target):
 if not re.fullmatch('[0-9a-f]{12}(?:[0-9a-f]{28})?',target or ''):raise ValueError('target sha required')
 seed=pathlib.Path(seed);run=pathlib.Path(run)
 paths=[seed/'state.json',seed/'verify.json',run/'counts.json',run/'preview-judgment.tsv']
 return {'profile':fingerprint(entries),'target_sha':target,'run_dir':str(run.resolve()),'files':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}

def proof(entries,work,run,target,write=False):
 work=pathlib.Path(work);path=work/'details-verified.json'
 if write:
  value=detail_binding(entries,work.parent,run,target);save(path,value)
 else:
  value=json.loads(private(path).read_text())
  if detail_binding(entries,work.parent,value['run_dir'],target)!=value:raise ValueError('data verification evidence changed')
 return fingerprint(value)

def main():
 if len(sys.argv)>1 and sys.argv[1].startswith('remote-'):remote_main(sys.argv[1]);return
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['validate','prepare','professor','sql','clear-legacy','finalize','verify','record-details','check-details','check-created']);ap.add_argument('--profile',default=str(DEFAULT_PROFILE));ap.add_argument('--work');ap.add_argument('--sql');ap.add_argument('--base-url');ap.add_argument('--ssh');ap.add_argument('--key');ap.add_argument('--secrets-dir');ap.add_argument('--binding');ap.add_argument('--run-dir');ap.add_argument('--target-sha');a=ap.parse_args()
 expected=json.loads(private(DEFAULT_PROFILE).read_text());entries=json.loads(private(a.profile).read_text());validate(entries,expected)
 entries=sorted(entries,key=lambda e:[v['email'] for v in expected].index(e['email']))
 if a.action=='validate':return
 if a.action=='check-created':
  rows=json.loads((pathlib.Path(a.work).parent/'state.json').read_text()).get('accounts',{})
  if set(rows)!={e['email'] for e in entries if e['admin']} or any(r.get('status')!='created' for r in rows.values()):raise ValueError('four operators not created')
  return
 if a.action in ('record-details','check-details'):
  print(proof(entries,a.work,a.run_dir,a.target_sha,a.action=='record-details'));return
 if a.action=='professor':
  p=professor(entries);print('\t'.join(p[k] for k in ('account_id','email','name','role','lab_id')));return
 if a.action=='sql':
  p=professor(entries);text=pathlib.Path(a.sql).read_text();old="('%s', '%s', '%s', 'pi@hymets.invalid')"%(p['account_id'],p['lab_id'],p['name'])
  if text.count(old)!=1:raise ValueError('canonical professor SQL identity changed')
  print(text.replace(old,old.replace('pi@hymets.invalid',p['email'])),end='');return
 if a.action=='prepare':prepare(entries,a.work);return
 paths=[str(pathlib.PurePosixPath(a.secrets_dir)/n) for n in ('subjects.json','credentials.json')]
 if a.action=='clear-legacy':
  result=remote(a,'remote-clear',{'paths':paths,'backup':str(pathlib.PurePosixPath(a.secrets_dir)/('dev-reseed-legacy-backup-'+fingerprint(str(pathlib.Path(a.work).resolve()))[:16]))},False);save(pathlib.Path(a.work)/'legacy-cleared.json',result);return
 require_binding(a.binding)
 work=pathlib.Path(a.work);prepared=json.loads(private(work/'accounts.json').read_text());validate(prepared,entries,policy=False)
 # 준비 사본(accounts.json)은 ownerManaged 이전에 만들어졌을 수 있다 — 표시는 승인된 프로필 값을 따른다.
 prepared=[{**p,'ownerManaged':owner_managed(next(e for e in entries if e['email']==p['email']))} for p in prepared]
 journal=work/'finalization.json';identity={'profile':fingerprint(entries),'binding':a.binding}
 if not (work/'legacy-cleared.json').exists():raise ValueError('legacy cleanup evidence missing')
 if journal.exists():
  old=json.loads(private(journal).read_text())
  if any(old.get(k)!=v for k,v in identity.items()):raise ValueError('finalization identity changed')
 elif a.action=='verify':raise ValueError('finalization has not completed')
 else:old={}
 mode='remote-verify' if old.get('state')=='complete' or a.action=='verify' else 'remote-finalize'
 (work/'verification.json').unlink(missing_ok=True)
 save(journal,{**identity,'state':old.get('state','started')})
 remote(a,mode,{'entries':entries,'legacy_paths':paths})
 save(journal,{**identity,'state':'complete'})
 result=verify_logins(prepared,a.base_url);save(work/'verification.json',{**identity,**result})
 print('accounts verified: 5; operators: 4; professor: 1; owner-managed operators: %d; initial-password change required for the rest'%result['owner_managed'])
if __name__=='__main__':
 try:main()
 except Exception:raise SystemExit('account operation failed; inspect protected execution state, do not repeat reset')
