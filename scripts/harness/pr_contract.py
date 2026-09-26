"""Validate a local PR draft/completion contract; never publish or grant approval."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RATE_MODE_RE = re.compile(r'^eval/harness/(H\d\d-[^/]+)/mode$')


def configuration():
    manifest = json.loads((ROOT / '.agents/harness.yaml').read_text())
    cfg = dict(manifest['pr_contract'])
    cfg['required_sections'] = list(dict.fromkeys(manifest['evidence']['required_pr_sections'] + cfg['required_sections']))
    return cfg


def visible(text):
    spec = importlib.util.spec_from_file_location('pr_adr_text', Path(__file__).with_name('adr_gate.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.visible(text)


def field(body, name):
    values = re.findall(r'^' + re.escape(name) + r':[ \t]*(.+)$', body, re.M)
    return values[0].strip() if len(values) == 1 else ''


def head_rate_tasks(head, root=ROOT):
    """Sorted eval tasks whose `mode` file in the head tree says exactly `rate`; None if unreadable.

    15라운드 판정 H18-rate: a rate task leaves the eval regression set, so the PR body names it."""
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, check=True).stdout
    try:
        paths = git('ls-tree', '-r', '--name-only', head, '--', 'eval/harness').splitlines()
        return sorted(m[1] for m in map(RATE_MODE_RE.match, paths)
                      if m and git('show', f'{head}:{m[0]}').rstrip('\n') == 'rate')
    except (OSError, subprocess.CalledProcessError):
        return None


def validate(text, head, cfg, *, mode='draft', evidence=None, artifact_root=None, rate_tasks=None):
    body = visible(text)
    problems = []
    if not re.fullmatch('[0-9a-f]{40}', head) or field(body, 'Head-SHA') != head:
        problems.append('full Head-SHA must match the requested head')
    if rate_tasks is None:
        rate_tasks = head_rate_tasks(head)
    name = cfg['rate_tasks_field']
    if rate_tasks is None:
        problems.append(f'{name} cannot be checked: the head tree mode=rate tasks are unreadable')
    elif field(body, name) != (', '.join(rate_tasks) or cfg['rate_tasks_none']):
        problems.append(f'{name} must equal the head tree mode=rate tasks: '
                        + (', '.join(rate_tasks) or cfg['rate_tasks_none']))
    plan = field(body, 'Plan-Ref')
    if not plan or re.search(r'<[^>]+>|TODO|TBD', plan):
        problems.append('Plan-Ref is missing or a placeholder')
    headings = list(re.finditer(r'^## (.+)$', body, re.M))
    for section in cfg['required_sections']:
        positions = [index for index, match in enumerate(headings) if match[1] == section]
        if len(positions) != 1:
            problems.append('missing or duplicate PR section: ' + section)
            continue
        index = positions[0]
        content = body[headings[index].end():headings[index + 1].start() if index + 1 < len(headings) else len(body)].strip()
        if not content or re.search(r'<[^>]+>|\bTODO\b|\bTBD\b', content):
            problems.append('empty or placeholder PR section: ' + section)
    status = field(body, '검증 상태')
    if mode not in ('draft', 'complete'):
        problems.append('unknown PR validation mode')
    if status not in ('미검증', '부분 검증', '검증됨'):
        problems.append('검증 상태 must explicitly state verification status')
    if mode == 'complete' and status != '검증됨':
        problems.append('completion requires 검증됨')
    if evidence is None:
        if mode == 'complete' or status == '검증됨':
            problems.append('verified claim requires CI evidence')
        return problems
    if not isinstance(evidence, dict) or evidence.get('schema') != cfg['evidence_schema']:
        return problems + ['invalid CI evidence schema']
    shas = evidence.get('event_shas') or {}
    actual_head = shas.get('head_sha', shas.get('after_sha', evidence.get('commit')))
    if actual_head != head:
        problems.append('CI evidence belongs to another head')
    for name in ('Evidence-Ref', 'CI-Ref'):
        if not field(body, name) or re.search(r'<[^>]+>', field(body, name)):
            problems.append(name + ' is required with evidence')
    counts = evidence.get('counts', {})
    jobs = evidence.get('jobs', [])
    if not isinstance(counts, dict) or any(type(counts.get(key)) is not int or counts[key] < 0 for key in cfg['required_counts']):
        problems.append('CI evidence has invalid three-state counts')
    elif mode == 'complete' or status == '검증됨':
        if counts['green'] <= 0 or counts['red_judgment'] or counts['red_readiness']:
            problems.append('CI evidence is not green')
        if not isinstance(jobs, list) or not jobs or any(not isinstance(job, dict) for job in jobs):
            problems.append('CI evidence jobs are missing')
        else:
            names = [job.get('name') for job in jobs]
            if len(set(names)) != len(names) or any(not name for name in names):
                problems.append('CI evidence job names are invalid')
            for state in cfg['required_counts']:
                if sum(job.get('state') == state for job in jobs) != counts[state]:
                    problems.append('CI evidence counts disagree with jobs')
            if any(job.get('state') not in (*cfg['required_counts'], 'not_applicable') for job in jobs):
                problems.append('CI evidence contains an unknown state')
    if mode == 'complete' or status == '검증됨':
        if artifact_root is None:
            problems.append('verified claim requires the actual CI artifact bundle')
        else:
            spec = importlib.util.spec_from_file_location('pr_ci_evidence', Path(__file__).with_name('verify_evidence.py'))
            checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
            try:
                checker.verify_ci_bundle(evidence, Path(artifact_root))
            except (checker.EvidenceError, OSError, ValueError, TypeError, KeyError) as error:
                problems.append('CI bundle rejected: ' + str(error))
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('body', type=Path)
    parser.add_argument('--head', required=True)
    parser.add_argument('--mode', choices=('draft', 'complete'), default='draft')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--artifact-root', type=Path, help='downloaded producer artifact bundle; required for verified claims')
    args = parser.parse_args()
    try:
        cfg = configuration()
        body = args.body.read_text(encoding='utf-8')
        evidence = None
        if args.evidence:
            raw = args.evidence.read_bytes()
            if field(visible(body), 'Evidence-SHA256') != hashlib.sha256(raw).hexdigest():
                print('Evidence-SHA256 differs from the supplied evidence file', file=sys.stderr)
                return 1
            evidence = json.loads(raw)
        problems = validate(body, args.head, cfg, mode=args.mode, evidence=evidence, artifact_root=args.artifact_root)
        if problems:
            print('\n'.join(problems), file=sys.stderr)
            return 1
        print(f'PASS: local PR {args.mode}; publication still needs user approval')
        return 0
    except (OSError, ValueError, KeyError) as error:
        print('::gate-readiness-failure:: PR contract: ' + str(error), file=sys.stderr)
        return 78


if __name__ == '__main__': raise SystemExit(main())
