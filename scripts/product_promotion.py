#!/usr/bin/env python3
"""Read-only PR source check, executed from the protected base checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import os
import urllib.request
import time

def fetch_checks(repository,sha,token):
    request=urllib.request.Request(f'https://api.github.com/repos/{repository}/commits/{sha}/check-runs?per_page=100',headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response).get('check_runs',[])

def _successful_checks(check_runs, check_sha, required_checks):
    successful={(x.get('name'),x.get('app',{}).get('id')) for x in check_runs if isinstance(x,dict) and x.get('head_sha')==check_sha and x.get('status')=='completed' and x.get('conclusion')=='success'}
    return all((item['name'],item['app_id']) in successful for item in required_checks)

def wait_for_checks(repository, sha, token, required_checks, *, fetch=fetch_checks, attempts=60, interval=10, sleeper=time.sleep):
    for attempt in range(attempts):
        runs=fetch(repository,sha,token)
        if _successful_checks(runs,sha,required_checks): return runs
        failed={(x.get('name'),x.get('app',{}).get('id')) for x in runs if isinstance(x,dict) and x.get('head_sha')==sha and x.get('status')=='completed' and x.get('conclusion') not in (None,'success')}
        if any((x['name'],x['app_id']) in failed for x in required_checks): raise ValueError('필수 검사가 실패했습니다.')
        if attempt+1<attempts:sleeper(interval)
    raise ValueError('필수 검사가 제한 시간 안에 완료되지 않았습니다.')

def build_approval(event, repository, manifest_path, required_checks, check_runs):
    source = validate(event, repository)
    try: number = event['pull_request']['number']
    except (KeyError, TypeError): raise ValueError('PR 번호가 필요합니다.') from None
    path = Path(manifest_path)
    if type(number) is not int or number < 1 or not path.is_file(): raise ValueError('PR 번호와 manifest가 필요합니다.')
    if not isinstance(required_checks,list) or not required_checks or any(not isinstance(x,dict) or set(x)!={'name','app_id'} or not isinstance(x['name'],str) or not x['name'] or type(x['app_id']) is not int or x['app_id']<1 for x in required_checks):raise ValueError('필수 검사 이름/app id 목록이 필요합니다.')
    check_sha=event['pull_request'].get('merge_commit_sha')
    if not isinstance(check_sha,str) or not re.fullmatch('[0-9a-f]{40}',check_sha):raise ValueError('PR check-suite SHA가 필요합니다.')
    if not _successful_checks(check_runs,check_sha,required_checks):raise ValueError('필수 검사가 신뢰한 app에서 같은 check SHA로 성공해야 합니다.')
    return {'schema':'colab-product-promotion/1','pr_number':number,**source,
            'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'required_checks':required_checks,'check_sha':check_sha}


def validate(event, repository):
    try:
        base = event['pull_request']['base']
        head = event['pull_request']['head']
        if not (event['repository']['full_name'] == base['repo']['full_name']
                == head['repo']['full_name'] == repository
                and base['ref'] == 'product' and head['ref'] == 'develop'):
            raise ValueError()
        for sha in (base['sha'], head['sha']):
            if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{40}', sha):
                raise ValueError()
        return {'base_sha': base['sha'], 'head_sha': head['sha']}
    except (KeyError, TypeError, ValueError):
        raise ValueError('동일 저장소 develop → product PR만 허용합니다.') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event', required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--manifest')
    parser.add_argument('--required-check-json', default='[]')
    parser.add_argument('--output')
    parser.add_argument('--github-token-env')
    args = parser.parse_args()
    try:
        event = json.loads(Path(args.event).read_text())
        if args.manifest:
            if not args.github_token_env or not os.environ.get(args.github_token_env):raise OSError('GitHub API token missing')
            source=validate(event,args.repository)
            required=json.loads(args.required_check_json);check_sha=event['pull_request'].get('merge_commit_sha')
            checks=wait_for_checks(args.repository,check_sha,os.environ[args.github_token_env],required)
            value=build_approval(event,args.repository,args.manifest,required,checks)
            text=json.dumps(value,sort_keys=True)
            if not args.output:raise ValueError('승격 artifact 출력 경로가 필요합니다.')
            Path(args.output).write_text(text)
        else:text=json.dumps(validate(event, args.repository), sort_keys=True)
        print(text)
        return 0
    except OSError:
        print('PR 이벤트 파일이 없습니다.', file=sys.stderr)
        return 78
    except ValueError:
        print('동일 저장소 develop → product PR과 유효한 SHA가 필요합니다.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
