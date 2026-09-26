"""Checkout/task/run-scoped runtime paths. No general outside-checkout exception."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import subprocess
import re

# Roles that run gates and therefore get a bound report path (`bind_paths` below).
# ⚠ This tuple is the single source — `scripts/harness/hooks/lifecycle_contract.py` reads
#   it from here rather than keeping a second copy. Two copies of a role list eventually
#   disagree, and the way they disagree is that a role can open a task but never close one.
GATE_ROLES = ('lane-worker', 'measurement-lane')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def identity(root):
    root = Path(git(root, 'rev-parse', '--show-toplevel')).resolve()
    private = Path(git(root, 'rev-parse', '--absolute-git-dir')).resolve()
    common = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
    key = hashlib.sha256((str(root) + '\0' + str(private)).encode()).hexdigest()[:32]
    return root, common, key


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{32}', value):
        raise ValueError('invalid task/run identity')
    return value


def confined(base, target):
    base, target = Path(base), Path(target)
    if not target.is_absolute() or '..' in target.parts or not target.is_relative_to(base):
        raise ValueError('path outside declared task runtime')
    current = base
    if current.is_symlink():
        raise ValueError('runtime symlink forbidden')
    for part in target.relative_to(base).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('runtime symlink forbidden')
    if target.resolve() != target:
        raise ValueError('runtime path is not canonical')
    return target


def directory(root, task_id):
    _, common, key = identity(root)
    return confined(common, common / 'colab-harness' / key / identifier(task_id))


def record_path(root, task_id):
    return confined(directory(root, task_id), directory(root, task_id) / 'task.json')


def marker_dir(root):
    """Index of open fix tasks: `<common>/colab-harness/red-locked/<task_id>` holds its record path.

    Shared by every checkout of one repository (the common dir), so a parent session and its lane
    worktrees see one index. The marker is only an index; task.json is the verdict.
    """
    _, common, _ = identity(root)
    return confined(common, common / 'colab-harness' / 'red-locked')


def run_directory(root, task):
    actual, _, key = identity(root)
    if task.get('schema') != 'colab-task/2' or task.get('checkout') != str(actual) or task.get('checkout_id') != key:
        raise ValueError('runtime task checkout differs')
    base = directory(root, task['task_id'])
    return confined(base, base / identifier(task['run_id']))


def relative_artifact(value):
    if not isinstance(value, str) or not value.startswith('runtime:artifacts/'):
        raise ValueError('new artifact must use runtime:artifacts/<name> (legacy needs --legacy)')
    rel = value.removeprefix('runtime:')
    if '..' in PurePosixPath(rel).parts or PurePosixPath(rel).as_posix() != rel or rel.endswith('/'):
        raise ValueError('invalid runtime artifact declaration')
    return rel


def bind_paths(root, task):
    base = run_directory(root, task)
    task['artifacts'] = [str(confined(base, base / relative_artifact(name))) for name in task['artifact_declarations']]
    # Every role that runs gates needs a bound report. Without this, the role's `report`
    # is None and `verify_task_report` fails on every single handoff — the role would be
    # able to open a task and never able to close one.
    task['report'] = str(base / 'gate-summary.json') if task['role'] in GATE_ROLES else None
    # A fix task's `fix-red:<spec>` rows follow the declared gates with continuing log numbers.
    task['logs'] = [str(base / 'logs' / f'{index}.log') for index, _ in enumerate([*task['gates'], *fix_rows(task)])]
    return task


def fix_rows(task):
    """Gate-summary row names a fix task adds after its declared gates (one per recorded RED)."""
    return ['fix-red:' + entry['spec'] for entry in (task.get('fix') or {}).get('red', [])]


def resolve(root, task, name, *, artifact_only=False):
    base = run_directory(root, task)
    if isinstance(name, str) and name.startswith('runtime:'):
        name = str(base / relative_artifact(name))
    allowed = list(task['artifacts'])
    if not artifact_only:
        allowed += [task.get('report'), *task.get('logs', [])]
    if not isinstance(name, str) or name not in allowed:
        raise ValueError('undeclared task runtime path or other run')
    return confined(base, Path(name))


def verify_outputs(root, task):
    base = run_directory(root, task)
    if not base.exists():
        return
    for path in base.rglob('*'):
        confined(base, path)
        if not path.is_dir():
            resolve(root, task, str(path))


def save(root, task):
    target = record_path(root, task['task_id'])
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = confined(target.parent, target.with_suffix('.tmp'))
    temporary.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)
