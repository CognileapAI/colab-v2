#!/usr/bin/env python3
"""Validate and execute a human-merged develop to product release."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
import urllib.parse
import io
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


class ReleaseRejected(ValueError): pass
class PreparationError(RuntimeError): pass

SHA_RE = re.compile(r"[0-9a-f]{40}")
SECRET_KEYS = {"password", "token", "secret", "private_key", "webhook"}
REQUIRED_CONFIG = {"repository", "allowed_actor_ids", "environment", "deploy_plan_path", "manifest_path", "manifest_sha256", "state_directory", "host_config_path", "github_token_env"}


def _pr(event):
    value = event.get("pull_request") if isinstance(event, dict) else None
    if not isinstance(value, dict): raise ReleaseRejected("pull_request closed 이벤트만 허용됩니다.")
    return value


def _sha(value, name):
    if not isinstance(value, str) or not SHA_RE.fullmatch(value): raise ReleaseRejected(f"{name} SHA가 필요합니다.")
    return value


def select_release(event: dict, repository: str, allowed_actor_ids: set[int]) -> dict:
    pr = _pr(event)
    try:
        base, head, actor = pr["base"], pr["head"], pr["merged_by"]
        same_repo = event["repository"]["full_name"] == repository == base["repo"]["full_name"] == head["repo"]["full_name"]
        eligible = event.get("action") == "closed" and pr.get("merged") is True and base.get("ref") == "product" and head.get("ref") == "develop"
        human = actor.get("type") == "User" and type(actor.get("id")) is int and actor["id"] in allowed_actor_ids
        number = pr["number"]
    except (KeyError, TypeError):
        raise ReleaseRejected("병합 이벤트 필드가 누락됐습니다.") from None
    if not same_repo or not eligible or not human or type(number) is not int or number < 1:
        raise ReleaseRejected("허용된 동일 저장소 develop → product 사람 병합이 아닙니다.")
    return {"sha": _sha(pr.get("merge_commit_sha"), "merge"), "pr_number": number, "actor_id": actor["id"],
            "head_sha": _sha(head.get("sha"), "head"), "base_sha": _sha(base.get("sha"), "base")}


def bind_release(event, api_event, repository, allowed_actor_ids, parents, manifest_path=None, manifest_sha256=None):
    original = select_release(event, repository, allowed_actor_ids)
    current = select_release(api_event, repository, allowed_actor_ids)
    if original != current: raise ReleaseRejected("GitHub API 재검증 결과가 이벤트와 다릅니다.")
    if list(parents) != [original["base_sha"], original["head_sha"]]: raise ReleaseRejected("merge commit 부모가 승인된 base/head와 다릅니다.")
    if manifest_path is not None:
        path = Path(manifest_path)
        if not path.is_file(): raise PreparationError("manifest 파일이 없습니다.")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != manifest_sha256: raise ReleaseRejected("manifest digest가 변경됐습니다.")
        original["manifest_sha256"] = actual
    return original


def load_operator_input(path):
    path = Path(path)
    if not path.is_file(): raise PreparationError("운영자 설정 파일이 없습니다.")
    try: value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc: raise ReleaseRejected("운영자 설정 JSON이 잘못됐습니다.") from exc
    if not isinstance(value, dict) or value.get("schema") != "colab-product-operator-input/1" or not REQUIRED_CONFIG <= value.keys():
        raise ReleaseRejected("운영자 설정 필드가 누락됐습니다.")
    if any(str(k).lower() in SECRET_KEYS for k in value): raise ReleaseRejected("비밀 값은 인라인으로 둘 수 없습니다.")
    if value["environment"] != "prod" or not re.fullmatch(r"[^/\s]+/[^/\s]+", str(value["repository"])):
        raise ReleaseRejected("운영 환경 또는 저장소가 잘못됐습니다.")
    actors = value["allowed_actor_ids"]
    if not isinstance(actors, list) or not actors or any(type(a) is not int or a < 1 for a in actors): raise ReleaseRejected("허용 사람 ID가 필요합니다.")
    if not re.fullmatch(r"[0-9a-f]{64}", str(value["manifest_sha256"])): raise ReleaseRejected("manifest sha256이 필요합니다.")
    for key in ("deploy_plan_path", "manifest_path", "state_directory", "host_config_path", "github_token_env"):
        if not isinstance(value[key], str) or not value[key].strip(): raise ReleaseRejected(f"{key} 참조가 필요합니다.")
    if "initial_reseed_plan_path" in value and (not isinstance(value["initial_reseed_plan_path"], str) or not value["initial_reseed_plan_path"].strip()):
        raise ReleaseRejected("initial_reseed_plan_path 참조가 비었습니다.")
    checks=value.get('required_checks')
    if not isinstance(checks,list) or not checks or any(not isinstance(x,dict) or set(x)!={'name','app_id'} or not isinstance(x['name'],str) or type(x['app_id']) is not int for x in checks):raise ReleaseRejected('required_checks 이름/app id가 필요합니다.')
    if type(value.get('promotion_workflow_id')) is not int or value['promotion_workflow_id'] < 1 or value.get('promotion_workflow_path') != '.github/workflows/product-promotion.yml':
        raise ReleaseRejected('promotion workflow id/path가 필요합니다.')
    return value


def classify_candidate(deployed_sha, candidate_sha, is_ancestor):
    if deployed_sha == candidate_sha: return "duplicate"
    if is_ancestor(deployed_sha, candidate_sha): return "deploy"
    if is_ancestor(candidate_sha, deployed_sha): raise ReleaseRejected("낡은 배포 후보입니다.")
    raise ReleaseRejected("현재 운영 계보와 관련 없는 배포 후보입니다.")

def select_promotion_run(runs, workflow_id, workflow_path, pr_number, head_sha):
    eligible=[run for run in runs if isinstance(run,dict) and run.get('workflow_id')==workflow_id and str(run.get('path','')).split('@')[0]==workflow_path and run.get('event')=='pull_request' and run.get('status')=='completed' and run.get('conclusion')=='success' and run.get('head_sha')==head_sha and any(x.get('number')==pr_number for x in run.get('pull_requests',[]) if isinstance(x,dict))]
    if not eligible:raise ReleaseRejected('promotion 성공 실행을 찾지 못했습니다.')
    return max(eligible,key=lambda run:run.get('id',-1))

def candidate_from_record(record):
    if not isinstance(record,dict) or record.get('schema','colab-product-release-state/1')!='colab-product-release-state/1' or record.get('status') not in ('ready','running','failed','verified'):raise PreparationError('release 상태가 없거나 잘못됐습니다.')
    value=record.get('latest_sha')
    if record.get('status')=='verified' and not isinstance(value,str):raise PreparationError('검증된 release의 latest_sha가 없습니다.')
    if value is not None and (not isinstance(value,str) or not SHA_RE.fullmatch(value)):raise PreparationError('release latest_sha가 잘못됐습니다.')
    return value

def artifact_redirect_url(url):
    parsed=urllib.parse.urlparse(url);host=(parsed.hostname or '').lower()
    trusted=(host.endswith('.blob.core.windows.net') and host.startswith('productionresults')) or host.endswith('.actions.githubusercontent.com')
    if parsed.scheme!='https' or not trusted or parsed.username or parsed.password:raise ReleaseRejected('신뢰할 수 없는 artifact redirect입니다.')
    return url

def initialization_mode(record,pr_number):
    if record.get('initial_reseed') == 'ready':
        if record.get('initial_reseed_pr_number') != pr_number:raise ReleaseRejected('최초 reseed는 등록한 PR에서만 실행할 수 있습니다.')
        return 'initial'
    if record.get('initial_reseed') == 'succeeded':return 'normal'
    raise ReleaseRejected('최초 reseed 상태를 확인할 수 없습니다.')

def verify_manifest_binding(root,head_sha,repo_path,digest):
    root=Path(root).resolve();relative=Path(repo_path)
    if relative.is_absolute() or '..' in relative.parts or str(relative) in ('','.'):raise ReleaseRejected('manifest 저장소 경로가 잘못됐습니다.')
    try:blob=subprocess.check_output(['git','-C',str(root),'show',f'{head_sha}:{relative.as_posix()}'])
    except subprocess.SubprocessError as exc:raise ReleaseRejected('manifest 경로가 head에 추적되지 않았습니다.') from exc
    path=root/relative
    if hashlib.sha256(blob).hexdigest()!=digest or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ReleaseRejected('manifest 결속이 head/merge 파일과 다릅니다.')
    return path


def verify_workflow_policy(root, binding, config):
    """PR-sourced workflow code must match the operator's reviewed policy on both parents."""
    expected = config.get('promotion_workflow_sha256')
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise PreparationError('검토한 promotion workflow의 SHA256이 필요합니다.')
    path = config['promotion_workflow_path']
    if path != '.github/workflows/product-promotion.yml':
        raise ReleaseRejected('승격 workflow 정책 경로가 다릅니다.')
    for sha in (binding['base_sha'], binding['head_sha']):
        try:
            blob = subprocess.check_output(['git', '-C', str(root), 'show', f'{sha}:{path}'], stderr=subprocess.DEVNULL)
        except subprocess.SubprocessError as exc:
            raise ReleaseRejected('승격 workflow가 승인된 두 부모에 없습니다.') from exc
        if hashlib.sha256(blob).hexdigest() != expected:
            raise ReleaseRejected('승격 workflow가 검토한 정책과 다릅니다.')

def provision_release(directory, approval, initial_reseed_pr_number):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    path=directory/'release.json'
    if path.exists():
        try: previous=json.loads(path.read_text())
        except (OSError,json.JSONDecodeError) as exc:raise PreparationError('승격 기록을 읽을 수 없습니다.') from exc
        if previous.get('status') != 'verified':raise ReleaseRejected('미완료 승격 기록은 덮어쓸 수 없습니다.')
        value=dict(previous,status='ready',approval=approval,merge_sha=None)
    else:value={'schema':'colab-product-release-state/1','status':'ready','approval':approval,
                'initial_reseed_pr_number':initial_reseed_pr_number,'initial_reseed':'ready','latest_sha':None}
    _save(path,value)
    return 0

def authorize_release(directory, bound, approval, resume):
    directory=Path(directory);path=directory/'release.json'
    if not path.is_file():raise PreparationError('명시적으로 등록한 승격 기록이 없습니다.')
    try:record=json.loads(path.read_text())
    except (OSError,json.JSONDecodeError) as exc:raise PreparationError('승격 기록을 읽을 수 없습니다.') from exc
    if record.get('status') == 'verified' and not resume and record.get('latest_sha'):
        record=dict(record,status='ready',approval=approval,merge_sha=None)
    if record.get('approval') != approval:raise ReleaseRejected('병합 후 승격 검증이 사전 승인과 다릅니다.')
    for key in ('pr_number','base_sha','head_sha','manifest_sha256'):
        if bound.get(key) != approval.get(key):raise ReleaseRejected('병합 후 승격 입력이 사전 승인과 다릅니다.')
    if record.get('status') in ('failed','running') and not resume:raise ReleaseRejected('실패하거나 중단된 배포는 사람이 명시적으로 재개해야 합니다.')
    if record.get('status') not in ('ready','failed','running'):raise ReleaseRejected('승격 기록 상태가 실행을 허용하지 않습니다.')
    return record

def _save(path,value):
    path=Path(path);temporary=path.with_name('.'+path.name+'.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w') as stream:json.dump(value,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path);directory_fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory_fd)
        finally:os.close(directory_fd)
    finally:temporary.unlink(missing_ok=True)


def deployment_plan(source, bound):
    source = Path(source)
    try: plan = json.loads(source.read_text())
    except (OSError, json.JSONDecodeError) as exc: raise PreparationError("배포 계획을 읽을 수 없습니다.") from exc
    targets = plan.get("targets") if isinstance(plan, dict) else None
    if not isinstance(plan, dict) or plan.get("schema") != "colab-deploy/1" or not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict) or targets[0].get("name") != "pr":
        raise ReleaseRejected("운영 배포 계획은 pr 대상 하나여야 합니다.")
    plan["id"] = f"product-pr-{bound['pr_number']}-{bound['sha'][:12]}"
    plan["candidate_sha"] = bound["sha"]
    targets[0]["version"] = bound["sha"]
    return plan


def materialize_plan(source, target, bound):
    target = Path(target)
    plan = deployment_plan(source, bound)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    os.chmod(temporary, 0o600); os.replace(temporary, target)
    return plan


def materialize_reseed_plan(source, target, candidate_sha):
    source, target = Path(source), Path(target)
    try: plan = json.loads(source.read_text())
    except (OSError, json.JSONDecodeError) as exc: raise PreparationError("최초 reseed 계획을 읽을 수 없습니다.") from exc
    if not isinstance(plan, dict) or plan.get("schema") != "colab-product-reseed/1" or plan.get("environment") != "prod":
        raise ReleaseRejected("최초 reseed 계획 schema/environment가 잘못됐습니다.")
    if plan.get("candidate_sha", object()) is not None: raise ReleaseRejected("reseed 템플릿 candidate_sha는 null이어야 합니다.")
    plan["candidate_sha"] = _sha(candidate_sha, "candidate")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700);temporary=target.with_suffix(".tmp")
    temporary.write_text(json.dumps(plan, ensure_ascii=False, indent=2));os.chmod(temporary,0o600);os.replace(temporary,target)
    return plan


def fetch_pr(repository, number, token):
    request = urllib.request.Request(f"https://api.github.com/repos/{repository}/pulls/{number}", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(request, timeout=30) as response: pr = json.load(response)
    return {"action": "closed", "repository": {"full_name": repository}, "pull_request": pr}

def fetch_checks(repository, sha, token):
    request=urllib.request.Request(f"https://api.github.com/repos/{repository}/commits/{sha}/check-runs?per_page=100",headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
    with urllib.request.urlopen(request,timeout=30) as response:value=json.load(response)
    return value.get('check_runs',[])

def _api_json(url,token):
    request=urllib.request.Request(url,headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)

def fetch_commit_parents(repository,sha,token):
    value=_api_json(f'https://api.github.com/repos/{repository}/commits/{sha}',token)
    parents=value.get('parents') if isinstance(value,dict) else None
    if not isinstance(parents,list):raise ReleaseRejected('check SHA 부모를 확인할 수 없습니다.')
    return [x.get('sha') for x in parents if isinstance(x,dict)]

def verify_check_binding(approval,parents):
    if list(parents)!=[approval.get('base_sha'),approval.get('head_sha')]:raise ReleaseRejected('check SHA 부모가 승인 base/head와 다릅니다.')
    return True

def fetch_promotion_approval(repository,workflow_id,workflow_path,pr_number,head_sha,token):
    query=urllib.parse.urlencode({'event':'pull_request','head_sha':head_sha,'status':'completed','per_page':100})
    data=_api_json(f'https://api.github.com/repos/{repository}/actions/workflows/{workflow_id}/runs?{query}',token)
    run=select_promotion_run(data.get('workflow_runs',[]),workflow_id,workflow_path,pr_number,head_sha)
    artifacts=_api_json(f'https://api.github.com/repos/{repository}/actions/runs/{run["id"]}/artifacts?per_page=100',token).get('artifacts',[])
    name=f'product-promotion-{head_sha}';matches=[x for x in artifacts if x.get('name')==name and not x.get('expired')]
    if len(matches)!=1 or matches[0].get('workflow_run',{}).get('head_sha')!=head_sha:raise ReleaseRejected('promotion artifact를 정확히 하나 찾지 못했습니다.')
    request=urllib.request.Request(matches[0]['archive_download_url'],headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    try:urllib.request.build_opener(NoRedirect).open(request,timeout=30)
    except urllib.error.HTTPError as response:
        if response.code not in (301,302,303,307,308):raise
        location=artifact_redirect_url(response.headers.get('Location'))
    else:raise ReleaseRejected('artifact API redirect가 필요합니다.')
    with urllib.request.urlopen(urllib.request.Request(location),timeout=30) as response:archive=response.read()
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:value=json.loads(bundle.read('approval.json'))
    except (zipfile.BadZipFile,KeyError,json.JSONDecodeError) as exc:raise ReleaseRejected('promotion artifact 내용이 잘못됐습니다.') from exc
    return value


def _resolve(base, value):
    path = Path(value); return path if path.is_absolute() else base / path


def _parents(root, sha):
    fields = subprocess.check_output(["git", "-C", str(root), "show", "-s", "--format=%P", sha], text=True).split()
    if len(fields) != 2: raise ReleaseRejected("승격은 두 부모를 가진 merge commit이어야 합니다.")
    return fields


@contextlib.contextmanager
def _lock(directory, provision=False):
    if provision: directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not directory.is_dir(): raise PreparationError('명시적으로 등록한 승격 상태가 없습니다.')
    fd = os.open(directory / "product-release.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield fd
    finally: os.close(fd)


def cli(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--event",required=True);parser.add_argument("--config",required=True);mode=parser.add_mutually_exclusive_group();mode.add_argument("--check",action="store_true");mode.add_argument("--provision",action="store_true");mode.add_argument("--resume",action="store_true");args=parser.parse_args(argv)
    try:
        root=Path(subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip())
        event=json.loads(Path(args.event).read_text());config_path=Path(args.config);config=load_operator_input(config_path);base=config_path.resolve().parent
        token=os.environ.get(config["github_token_env"])
        if not token: raise PreparationError("GitHub API 토큰이 없습니다.")
        manifest_ref=config.get('manifest_repo_path',config['manifest_path'])
        if args.provision:
            from scripts.product_promotion import build_approval,validate as validate_promotion
            source=validate_promotion(event,config['repository']);number=event.get('pull_request',{}).get('number')
            current=fetch_pr(config['repository'],number,token)
            if validate_promotion(current,config['repository']) != source:raise ReleaseRejected('GitHub API의 PR head/base가 이벤트와 다릅니다.')
            artifact=fetch_promotion_approval(config['repository'],config['promotion_workflow_id'],config['promotion_workflow_path'],number,source['head_sha'],token)
            verify_workflow_policy(root,source,config)
            manifest=verify_manifest_binding(root,source['head_sha'],manifest_ref,artifact['manifest_sha256'])
            verify_check_binding(artifact,fetch_commit_parents(config['repository'],artifact.get('check_sha'),token))
            promotion=build_approval(current,config['repository'],manifest,artifact['required_checks'],fetch_checks(config['repository'],artifact['check_sha'],token))
            if artifact.get('required_checks') != config['required_checks']:raise ReleaseRejected('promotion artifact 필수 검사가 운영 설정과 다릅니다.')
            if promotion != artifact:raise ReleaseRejected('promotion artifact와 API 재검증 결과가 다릅니다.')
            if promotion['manifest_sha256'] != config['manifest_sha256']:raise ReleaseRejected('운영 manifest digest가 설정과 다릅니다.')
            state=Path(config['state_directory'])
            with _lock(state,provision=True):provision_release(state,promotion,config.get('initial_reseed_pr_number'))
            return 0
        selected=select_release(event,config["repository"],set(config["allowed_actor_ids"]))
        checkout_sha=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
        if checkout_sha != selected["sha"]: raise ReleaseRejected("작업 사본이 고정된 병합 SHA가 아닙니다.")
        current=fetch_pr(config["repository"],selected["pr_number"],token)
        artifact=fetch_promotion_approval(config['repository'],config['promotion_workflow_id'],config['promotion_workflow_path'],selected['pr_number'],selected['head_sha'],token)
        verify_workflow_policy(root,selected,config)
        manifest=verify_manifest_binding(root,selected['head_sha'],manifest_ref,artifact['manifest_sha256'])
        verify_check_binding(artifact,fetch_commit_parents(config['repository'],artifact.get('check_sha'),token))
        bound=bind_release(event,current,config["repository"],set(config["allowed_actor_ids"]),_parents(root,selected["sha"]),manifest,artifact['manifest_sha256'])
        from scripts.product_promotion import build_approval
        # GitHub replaces merge_commit_sha with the real human merge after closing.
        # The earlier synthetic check commit has already been bound to these same parents.
        checked_event=dict(current,pull_request=dict(current['pull_request'],merge_commit_sha=artifact['check_sha']))
        promotion=build_approval(checked_event,config['repository'],manifest,artifact['required_checks'],fetch_checks(config['repository'],artifact['check_sha'],token))
        if artifact.get('required_checks') != config['required_checks']:raise ReleaseRejected('promotion artifact 필수 검사가 운영 설정과 다릅니다.')
        if promotion != artifact:raise ReleaseRejected('promotion artifact와 병합 후 API 재검증 결과가 다릅니다.')
        plan=_resolve(base,config["deploy_plan_path"]);host=_resolve(base,config["host_config_path"])
        if not plan.is_file() or not host.is_file(): raise PreparationError("배포 계획 또는 운영 호스트 설정이 없습니다.")
        candidate_plan=deployment_plan(plan,bound)
        try:
            from scripts import deploy_release as executor
        except ModuleNotFoundError:
            import deploy_release as executor
        executor.validate(candidate_plan,root)
        if args.check:
            print(json.dumps(bound,sort_keys=True));return 0
        state=Path(config["state_directory"])
        with _lock(state) as parent_lock_fd:
            release_record=authorize_release(state,bound,promotion,args.resume)
            initial=initialization_mode(release_record,bound['pr_number'])=='initial'
            if initial:
                if not config.get('initial_deploy_plan_path') or not config.get('initial_reseed_plan_path'):raise PreparationError('최초 배포/reseed 계획 참조가 없습니다.')
                plan=_resolve(base,config['initial_deploy_plan_path'])
            deployed=candidate_from_record(release_record)
            if deployed:
                def ancestor(older,newer):return subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",older,newer]).returncode==0
                if classify_candidate(deployed,bound["sha"],ancestor)=="duplicate":print("이미 배포된 merge SHA — 실행·알림 없음");return 0
            if initial:
                reseed_runtime=state/"initial-reseed-plan.json"
                materialize_reseed_plan(_resolve(base,config["initial_reseed_plan_path"]),reseed_runtime,bound["sha"])
                template=json.loads(plan.read_text());arguments=[arg for target in template.get("targets",[]) for phase in ("deploy","verify") for command in target.get(phase,[]) for arg in command]
                if str(reseed_runtime) not in arguments: raise ReleaseRejected("배포 계획이 고정된 최초 reseed 런타임 계획을 참조하지 않습니다.")
            bound_plan=state/f"plan-{bound['sha']}.json";materialize_plan(plan,bound_plan,bound)
            release_record.update(status='running',merge_sha=bound['sha']);_save(state/'release.json',release_record)
            command=[sys.executable,str(root/"scripts/deploy_release.py"),"run","--plan",str(bound_plan),"--state-dir",str(state/"deploy"),"--notification-off"]
            if args.resume:command.append('--resume-failed')
            env=dict(os.environ,COLAB_PRODUCT_RELEASE_LOCK_FD=str(parent_lock_fd))
            code=subprocess.run(command,pass_fds=(parent_lock_fd,),env=env).returncode
            if code != 0:
                release_record['status']='failed';_save(state/'release.json',release_record);return code
            release_record.update(status='verified',latest_sha=bound['sha'])
            if initial:release_record['initial_reseed']='succeeded'
            _save(state/'release.json',release_record)
        return 0
    except PreparationError as error: print(str(error),file=sys.stderr);return 78
    except (ReleaseRejected,OSError,ValueError,subprocess.SubprocessError) as error: print(str(error),file=sys.stderr);return 1

if __name__ == "__main__": raise SystemExit(cli())
