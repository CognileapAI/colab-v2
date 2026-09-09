"""Shared, fail-closed task evidence for Claude H6/H7 and the Codex adapter.

This is a lifecycle evidence contract, not a sandbox or a signature authority.
Task records live in the checkout's private git directory, never in another lane.
"""
from __future__ import annotations
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
import stat
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

WATCH = ('dev-package/sessions/', 'dev-package/reports/', 'dev-package/intent/')
STATES = ('green', 'red_판정', 'red_준비')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode('utf-8').strip()


def checkout(cwd):
    return Path(git(Path(cwd), 'rev-parse', '--show-toplevel')).resolve()


def inside(root, name):
    if not isinstance(name, str) or not name or '\x00' in name:
        raise ValueError('missing path')
    path = (root / name).resolve()
    if not path.is_relative_to(root) or path == root or '.git' in path.relative_to(root).parts:
        raise ValueError('path outside task checkout')
    return path


def digest(path):
    if path.is_symlink():
        return 'link:' + hashlib.sha256(os.readlink(path).encode()).hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root, report=None):
    # Include dirty tracked files, staged content's working copy and untracked sources.
    # Ignored runtime dependencies are not code evidence; the explicit report directory
    # is output, not input. No blanket exclusion of tests, fixtures, or source files.
    excluded = inside(root, report).parent if report else None
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z', '--cached',
                                     '--others', '--exclude-standard']).decode().split('\0')
    def read(name):
        path = root / name
        if excluded and path.is_relative_to(excluded):
            return None
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            return name, None
        if stat.S_ISLNK(mode) or stat.S_ISREG(mode):
            return name, digest(path)
        raise ValueError('unsupported repository input: ' + name)
    # Bound only I/O concurrency, never the inspected file set. Avoid repeated
    # serial NTFS/WSL round trips; every content hash is recomputed on every check.
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pair for pair in pool.map(read, sorted(set(names) - {''})) if pair is not None)


def snapshot_hash(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def task_path(root, task_id):
    if not isinstance(task_id, str) or not re.fullmatch(r'[a-f0-9]{32}', task_id):
        raise ValueError('invalid or missing task_id')
    gitdir = Path(git(root, 'rev-parse', '--absolute-git-dir'))
    return gitdir / 'colab-lifecycle' / (task_id + '.json')


def load_task(root, task_id):
    task = json.loads(task_path(root, task_id).read_text(encoding='utf-8'))
    if task.get('schema') != 'colab-task/1' or task.get('task_id') != task_id or task.get('checkout') != str(root):
        raise ValueError('task identity or assigned checkout differs')
    return task


def begin(root, role, artifacts=None, gates=None, report=None, agent_id=None):
    root = checkout(root)
    artifacts, gates = artifacts or [], gates or []
    if role not in ('researcher', 'lane-worker'):
        raise ValueError('unsupported task role')
    if len(set(artifacts)) != len(artifacts) or len(set(gates)) != len(gates):
        raise ValueError('duplicate task declaration')
    for name in artifacts:
        if inside(root, name).relative_to(root).as_posix() != name or not name.startswith(WATCH):
            raise ValueError('artifact must be a repository-relative research output')
    if role == 'lane-worker':
        if not gates or any(not isinstance(g, str) or not g for g in gates) or not report:
            raise ValueError('lane requires explicit gates and report')
        rel = inside(root, report).relative_to(root).as_posix()
        if rel != report or not re.fullmatch(r'dev-package/reports/[^/]+(?:/[^/]+)*/gate-summary\.json', rel):
            raise ValueError('report must use a dedicated directory under dev-package/reports')
        if inside(root, report).parent.exists() and any(inside(root, report).parent.iterdir()):
            raise ValueError('new task requires an empty report directory')
    elif gates or report:
        raise ValueError('research task must not declare implementation gates')
    task_id = uuid.uuid4().hex
    task = dict(schema='colab-task/1', task_id=task_id, checkout=str(root), role=role,
                agent_id=agent_id, artifacts=artifacts, gates=gates, report=report,
                baseline=snapshot(root, report))
    path = task_path(root, task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
    return task


def validate_report(data, required, head_tree=None):
    if not isinstance(data, dict) or data.get('schema') != 'colab-gate-summary/1':
        raise ValueError('invalid report schema')
    if head_tree is not None and (not head_tree or data.get('tree') != head_tree):
        raise ValueError('report tree differs from current HEAD')
    counts = data.get('counts')
    if not isinstance(counts, dict) or any(type(counts.get(s)) is not int or counts[s] < 0 for s in STATES):
        raise ValueError('missing or invalid counts')
    rows = data.get('gates')
    if not isinstance(rows, list) or not rows:
        raise ValueError('no gate evidence')
    names, actual = set(), collections.Counter()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row['name']:
            raise ValueError('invalid gate row')
        if row['name'] in names or row.get('status') not in STATES:
            raise ValueError('duplicate gate or invalid state')
        names.add(row['name'])
        if row.get('state', row['status']) != row['status']:
            raise ValueError('inconsistent gate states')
        actual[row['status']] += 1
        if type(row.get('exit')) is not int or (row['status'] == 'green' and row['exit'] != 0):
            raise ValueError('invalid gate exit code')
    if any(actual[s] != counts[s] for s in STATES):
        raise ValueError('counts disagree with gate rows')
    if not required or not set(required).issubset(names):
        raise ValueError('required gates are missing')
    if counts['red_판정'] or counts['red_준비']:
        raise ValueError('gate failures remain')


def gate_evidence(root, task_id):
    task = load_task(root, task_id)
    if task['role'] != 'lane-worker':
        raise ValueError('gate evidence requires lane-worker task')
    return dict(task_id=task_id, run_id=task.get('run_id'), checkout=str(root), files=snapshot_hash(snapshot(root, task['report'])))


def verify_task_report(root, task, report=None):
    path = inside(root, report or task['report'])
    if path != inside(root, task['report']):
        raise ValueError('report path differs from declared task report')
    if not task.get('run_id'):
        raise ValueError('gate execution has not started for this task')
    data = json.loads(path.read_text(encoding='utf-8'))
    validate_report(data, task['gates'])
    expected = gate_evidence(root, task['task_id'])
    evidence = data.get('task_evidence')
    if not isinstance(evidence, dict) or evidence.get('before') != expected or evidence.get('after') != expected:
        raise ValueError('missing, stale, changed-during-run or other-task evidence')
    return data


def stop(data, expected_role):
    if not isinstance(data, dict):
        raise ValueError('invalid lifecycle payload')
    if data.get('agent_type') != expected_role:
        raise ValueError('hook role differs from event role')
    root = checkout(data['cwd'])
    message = data.get('last_assistant_message')
    if not isinstance(message, str):
        raise ValueError('missing final handoff')
    markers = re.findall(r'^COLAB_HANDOFF (\{[^\n]+\})\s*$', message, re.MULTILINE)
    if len(markers) != 1:
        raise ValueError('one final COLAB_HANDOFF JSON is required')
    handoff = json.loads(markers[0])
    task = load_task(root, handoff.get('task_id'))
    if task['role'] != expected_role or (task.get('agent_id') and task['agent_id'] != data.get('agent_id')):
        raise ValueError('task role or agent identity differs')
    if not isinstance(handoff.get('summary'), str) or not handoff['summary'].strip():
        raise ValueError('handoff requires actual findings or result')
    mode = handoff.get('mode')
    if expected_role == 'researcher':
        now = snapshot(root, task['report'])
        changed = {p for p in set(now) | set(task['baseline']) if now.get(p) != task['baseline'].get(p)}
        if mode in ('read-only', 'draft-return'):
            if changed or task['artifacts'] or handoff.get('artifacts') != {}:
                raise ValueError('read-only/draft-return requires unchanged files and no file artifacts')
        elif mode == 'artifacts':
            if not task['artifacts'] or any(not p.startswith(WATCH) for p in changed):
                raise ValueError('researcher changed files outside output scope or omitted artifacts')
            if not changed.issubset(set(task['artifacts'])):
                raise ValueError('this task has unhanded output: ' + ', '.join(sorted(changed - set(task['artifacts']))))
            expected = {p: digest(inside(root, p)) for p in task['artifacts']}
            if handoff.get('artifacts') != expected:
                raise ValueError('missing or changed task artifact handoff')
        else:
            raise ValueError('invalid researcher completion mode')
    else:
        if mode != 'complete':
            raise ValueError('lane completion requires current gate evidence')
        verify_task_report(root, task)
    return 'H6' if expected_role == 'researcher' else 'H7'


def gate_start(root, task_id):
    task = load_task(root, task_id)
    if task['role'] != 'lane-worker':
        raise ValueError('gate execution requires lane-worker task')
    path = task_path(root, task_id)
    report = inside(root, task['report'])
    previous = task.get('run_id') or 'unbound'
    if report.exists():
        archive = path.parent / 'history' / task_id / (previous + '.json')
        archive.parent.mkdir(parents=True, exist_ok=True)
        os.replace(report, archive)
    task['run_id'] = uuid.uuid4().hex
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
    return gate_evidence(root, task_id)


def run_gates(root, task_id):
    """One invocation of exactly the declared gate set, with one execution identity."""
    before = gate_start(root, task_id)
    task = load_task(root, task_id)
    rows = []
    logs = task_path(root, task_id).parent / 'runs' / task_id / task['run_id']
    logs.mkdir(parents=True, exist_ok=True)
    for index, gate in enumerate(task['gates']):
        if gate in ('all', 'task'):
            raise ValueError('declare concrete gates, not nested group selectors')
        # Child execution does not start another report wrapper or run identity.
        # The parent captures each actual exit once and emits one group summary.
        env = dict(os.environ, COLAB_TASK_ID=task_id, COLAB_GATE_SUMMARY_CHILD='1')
        result = subprocess.run(['bash', str(root/'gates/run.sh'), gate], cwd=root,
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (logs / (str(index) + '.log')).write_text(result.stdout, encoding='utf-8')
        print(result.stdout, end='', flush=True)
        readiness = next((line for line in result.stdout.splitlines() if line.startswith('::gate-readiness-failure::')), '')
        state = 'green' if result.returncode == 0 else ('red_준비' if result.returncode == 78 or readiness else 'red_판정')
        rows.append(dict(name=gate, status=state, state=state, exit=result.returncode, readiness=readiness or None))
    after = gate_evidence(root, task_id)
    counts = {state: sum(row['status'] == state for row in rows) for state in STATES}
    doc = dict(schema='colab-gate-summary/1', gates=rows, counts=counts,
               targets=dict(requested='task', selected=task['gates']),
               task_evidence=dict(before=before, after=after))
    report = inside(root, task['report'])
    report.parent.mkdir(parents=True, exist_ok=True)
    temporary = report.with_suffix('.tmp')
    temporary.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, report)
    print('── 계 : green {green} / red(판정) {red_판정} / red(준비) {red_준비}'.format(**counts))
    if before != after:
        print('::gate-readiness-failure:: working files changed during task gates', file=sys.stderr)
        return 78
    return 78 if counts['red_준비'] else (1 if counts['red_판정'] else 0)


def validate_input(data, field):
    if not isinstance(data, dict) or not isinstance(data.get('tool_name'), str) or not data['tool_name']:
        raise ValueError('malformed tool envelope')
    applicable = ('Bash',) if field == 'command' else ('Edit', 'Write')
    if data['tool_name'] not in applicable:
        return data
    if not isinstance(data.get('cwd'), str) or not Path(data['cwd']).is_dir():
        raise ValueError('missing or invalid tool cwd')
    ti = data.get('tool_input')
    if not isinstance(ti, dict) or not isinstance(ti.get(field), str) or not ti[field].strip() or '\x00' in ti[field]:
        raise ValueError('missing or invalid tool_input.' + field)
    data['cwd'] = str(Path(data['cwd']).resolve())
    if field == 'file_path':
        root = checkout(data['cwd'])
        target = inside(root, str(Path(data['cwd']) / ti[field]))
        ti['file_path'] = str(target)
        if target.relative_to(root).as_posix() == 'dev-package/PLAN-SoT.md':
            content = 'new_string' if data['tool_name'] == 'Edit' else 'content'
            if not isinstance(ti.get(content), str):
                raise ValueError('decision guard requires tool_input.' + content)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('begin')
    start.add_argument('--role', required=True, choices=('researcher','lane-worker'))
    start.add_argument('--artifact', action='append', default=[])
    start.add_argument('--gate', action='append', default=[])
    start.add_argument('--report')
    start.add_argument('--agent-id')
    for name in ('gate-snapshot', 'gate-start', 'run-gates'):
        snap = commands.add_parser(name)
        snap.add_argument('--task', required=True)
    envelope = commands.add_parser('validate-input')
    envelope.add_argument('--field', required=True, choices=('command', 'file_path'))
    finish = commands.add_parser('handoff')
    finish.add_argument('--task', required=True)
    finish.add_argument('--mode', required=True, choices=('read-only','draft-return','artifacts','complete'))
    finish.add_argument('--summary', required=True)
    hook = commands.add_parser('stop')
    hook.add_argument('--role', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'validate-input':
            print(json.dumps(validate_input(json.load(sys.stdin), args.field)))
        elif args.command == 'stop':
            label = stop(json.load(sys.stdin), args.role)
            print(label + ' — current task evidence and handoff verified; no automatic commit')
        else:
            root = checkout(Path.cwd())
            if args.command == 'begin':
                task = begin(root, args.role, args.artifact, args.gate, args.report, args.agent_id)
                print(json.dumps({k: v for k, v in task.items() if k != 'baseline'}, ensure_ascii=False))
            elif args.command == 'gate-snapshot':
                print(json.dumps(gate_evidence(root, args.task)))
            elif args.command == 'gate-start':
                print(json.dumps(gate_start(root, args.task)))
            elif args.command == 'run-gates':
                return run_gates(root, args.task)
            else:
                task = load_task(root, args.task)
                handoff = dict(task_id=args.task, mode=args.mode, summary=args.summary,
                               artifacts={p: digest(inside(root, p)) for p in task['artifacts']})
                marker = 'COLAB_HANDOFF ' + json.dumps(handoff, ensure_ascii=False)
                stop(dict(cwd=str(root), agent_type=task['role'], agent_id=task.get('agent_id'),
                          last_assistant_message=marker), task['role'])
                print(marker)
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print('lifecycle evidence blocked: ' + str(exc), file=sys.stderr)
        return 2 if args.command in ('stop', 'validate-input') else 78

if __name__ == '__main__':
    sys.exit(main())
