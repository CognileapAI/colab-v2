"""Offline release evidence validation. Does not deploy, fetch, tag, or authorize."""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


class ReleaseEvidenceError(ValueError): pass
class ReadinessError(ReleaseEvidenceError): pass


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True).returncode


def identity(value):
    for key in ('sha', 'environment', 'release_id', 'run_id', 'started_at'):
        if not isinstance(value.get(key), str) or not value[key]:
            raise ReadinessError('missing release identity: ' + key)
    if not re.fullmatch('[0-9a-f]{40}', value['sha']):
        raise ReleaseEvidenceError('release requires full SHA')
    if value['environment'] not in ('dev', 'prod', 'staging'):
        raise ReleaseEvidenceError('unsupported release environment')


def verify_pre(value, root):
    identity(value)
    if value.get('schema') != 'colab-release-evidence/1':
        raise ReleaseEvidenceError('invalid release schema')
    branch = 'product' if value['environment'] == 'prod' else 'develop'
    ref = 'refs/remotes/origin/' + branch
    if git(root, 'rev-parse', '--verify', ref):
        raise ReadinessError(ref + ' unavailable; refresh separately')
    if git(root, 'merge-base', '--is-ancestor', value['sha'], ref):
        raise ReleaseEvidenceError('release SHA is not on ' + branch)
    pr = value.get('pr')
    if not isinstance(pr, dict): raise ReadinessError('merged PR evidence missing')
    if pr.get('merged') is not True or pr.get('base') != branch or pr.get('merge_commit_sha') != value['sha'] or type(pr.get('number')) is not int or pr['number'] < 1:
        raise ReleaseEvidenceError('merged PR does not identify this ' + branch + ' SHA')
    spec = importlib.util.spec_from_file_location('release_ci', Path(__file__).with_name('verify_evidence.py'))
    ci = importlib.util.module_from_spec(spec); spec.loader.exec_module(ci)
    evidence = value.get('ci')
    if not isinstance(evidence, dict): raise ReadinessError('CI evidence missing')
    if evidence.get('commit') != value['sha']:
        raise ReleaseEvidenceError('required-gates checked another SHA')
    bundle = value.get('artifact_root')
    if not isinstance(bundle, str) or not bundle: raise ReadinessError('CI bundle missing')
    try: ci.verify_ci_bundle(evidence, Path(bundle))
    except ci.EvidenceReadinessError as exc: raise ReadinessError(str(exc)) from exc
    except ci.EvidenceError as exc: raise ReleaseEvidenceError(str(exc)) from exc


def verify_post(pre, post, artifact_dir=None):
    identity(pre); identity(post)
    if pre['environment'] in ('dev','prod'):
        if artifact_dir is None: raise ReadinessError('actual doctor artifact directory required')
        source = Path(__file__).resolve().parents[2]/'services/core-api/ops/deploy_doctor_evidence.py'
        spec = importlib.util.spec_from_file_location('release_doctor_evidence', source)
        emitter = importlib.util.module_from_spec(spec); spec.loader.exec_module(emitter)
        try: emitter.verify_emitted(pre,post,Path(artifact_dir))
        except OSError as exc: raise ReadinessError('doctor log missing') from exc
        except (ValueError,KeyError,TypeError) as exc: raise ReleaseEvidenceError(str(exc)) from exc
        return
    for key in ('sha', 'environment', 'release_id', 'run_id', 'started_at'):
        if pre[key] != post[key]: raise ReleaseEvidenceError('post identity differs: ' + key)
    if post.get('phase') != 'post': raise ReleaseEvidenceError('post-deploy evidence required')
    try:
        start = datetime.datetime.fromisoformat(pre['started_at'])
        finish = datetime.datetime.fromisoformat(post['finished_at'])
        if start.tzinfo is None or finish.tzinfo is None or finish <= start: raise ValueError()
    except (KeyError, ValueError, TypeError): raise ReleaseEvidenceError('post evidence must follow deployment start')
    rows = post.get('checks')
    if not isinstance(rows, list): raise ReadinessError('post checks missing')
    wanted = {str(i) for i in range(1, 16)} if pre['environment'] == 'dev' else {'verify-deploy', 'verify-chains'}
    if len(rows) != len(wanted) or any(not isinstance(row, dict) for row in rows):
        raise ReleaseEvidenceError('incomplete post check set')
    if {row.get('name') for row in rows} != wanted or any(type(row.get('exit')) is not int or row['exit'] != 0 or row.get('exempt', False) for row in rows):
        raise ReleaseEvidenceError('post checks are not all green without exemptions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('pre', 'post'))
    parser.add_argument('--pre', required=True, type=Path)
    parser.add_argument('--post', type=Path)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--environment', choices=('dev','prod','staging'))
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        pre = json.loads(args.pre.read_text())
        if pre.get('sha') != args.sha: raise ReleaseEvidenceError('artifact SHA differs')
        if args.environment and pre.get('environment') != args.environment: raise ReleaseEvidenceError('release environment differs')
        verify_pre(pre, args.root)
        if args.phase == 'post':
            if args.post is None: raise ReadinessError('post evidence file required')
            verify_post(pre, json.loads(args.post.read_text()), args.post.parent)
        print('release evidence valid (local content only; no deployment authorization)')
        return 0
    except (ReadinessError, OSError) as exc:
        print(str(exc), file=sys.stderr); return 78
    except (ReleaseEvidenceError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr); return 1


if __name__ == '__main__': raise SystemExit(main())
