"""Local Issue/PR/task evidence contract. No publication or migration claims by default."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[2]


class StateError(ValueError): pass
class ReadinessError(StateError): pass


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / relative)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_record(reference, root, schema):
    if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}:
        raise ReadinessError('record path/hash required')
    path = Path(root)/reference['path']
    raw = path.read_bytes()
    if digest(raw) != reference['sha256']: raise StateError('record hash differs')
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get('schema') != schema: raise StateError('record schema differs')
    return value


def verify_pr_record(reference, root):
    value = read_record(reference, root, 'colab-github-pr-record/1')
    source, record = value.get('source'), value.get('record')
    if not isinstance(source, dict) or not isinstance(record, dict): raise ReadinessError('PR source/record missing')
    project = json.loads((ROOT/'.agents/harness.yaml').read_text())['project']
    number = record.get('number')
    if type(number) is not int or number < 1: raise StateError('PR number missing')
    repo = project['repository']
    if source.get('repository') != repo or source.get('number') != number or source.get('endpoint') != f'repos/{repo}/pulls/{number}' or source.get('transport') != 'gh-api':
        raise StateError('PR capture source differs')
    try:
        fetched = datetime.datetime.fromisoformat(source['fetched_at'])
        merged = datetime.datetime.fromisoformat(record['merged_at'])
        if fetched.tzinfo is None or merged.tzinfo is None or fetched < merged: raise ValueError()
    except (KeyError, ValueError, TypeError): raise StateError('PR capture/merge timestamp invalid')
    if record.get('merged') is not True or record.get('state') != 'closed': raise StateError('PR not actually recorded merged')
    if any(not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{40}', sha) for sha in
           (record.get('head', {}).get('sha'), record.get('merge_commit_sha'))):
        raise StateError('PR record full head/merge SHA missing')
    if record.get('base', {}).get('repo', {}).get('full_name') != repo or record.get('base', {}).get('ref') != project['default_branch']:
        raise StateError('PR base/repository differs')
    return record


def verify_pr(pr, root):
    if not isinstance(pr, dict): raise ReadinessError('PR evidence missing')
    ci = module('state_ci', 'verify_evidence.py')
    try:
        for key in ('head_sha', 'merge_sha'):
            ci.sha(pr.get(key), key)
        if pr.get('merged') is not True: raise StateError('PR not merged')
        recorded = verify_pr_record(pr.get('record'), root)
        if pr.get('number') != recorded['number'] or pr.get('repository') != recorded['base']['repo']['full_name'] or pr.get('base_ref') != recorded['base']['ref'] or pr['head_sha'] != recorded.get('head', {}).get('sha') or pr['merge_sha'] != recorded.get('merge_commit_sha'):
            raise StateError('PR identity differs from captured record')
        if not isinstance(pr.get('ci'), dict) or not pr.get('artifact_root'):
            raise ReadinessError('actual CI bundle required')
        ci.verify_ci_bundle(pr['ci'], root / pr['artifact_root'])
        shas = pr['ci']['event_shas']
        if shas.get('head_sha'):
            if shas['head_sha'] != pr['head_sha'] or pr['ci']['commit'] != pr['merge_sha']:
                raise StateError('PR head/merge differ from CI')
        elif pr['ci']['commit'] != pr['merge_sha']:
            raise StateError('merged SHA differs from push CI')
    except ci.EvidenceReadinessError as exc: raise ReadinessError(str(exc)) from exc
    except ci.EvidenceError as exc: raise StateError(str(exc)) from exc


def verify_task(reference, root, issue=None):
    if not isinstance(reference, dict): raise ReadinessError('task evidence missing')
    lifecycle = module('state_lifecycle', 'hooks/lifecycle_contract.py')
    try:
        task = lifecycle.load_task(root, reference.get('task_id'))
        if task.get('schema') != 'colab-task/2': raise StateError('new state needs current runtime task')
        for key in ('run_id', 'checkout_id'):
            if reference.get(key) != task.get(key): raise StateError('task identity differs: ' + key)
        report = lifecycle.resolve_task_path(root, task, task['report'])
        if reference.get('report_sha256') != digest(report.read_bytes()):
            raise StateError('task report hash differs')
        result = lifecycle.verify_task_report(root, task)
        if issue is None: raise ReadinessError('work-item binding required')
        binding_path = lifecycle.resolve_task_path(root, task, reference.get('binding'), artifact_only=True)
        binding = json.loads(binding_path.read_text())
        if binding.get('schema') != 'colab-work-binding/1' or binding.get('item_id') != issue['id']:
            raise StateError('task belongs to another work item')
        completion = binding.get('completion_def')
        if not isinstance(completion, dict) or completion.get('path') != issue['product']['completion_def_ref']:
            raise StateError('task completion definition differs')
        definition = lifecycle.inside(root, completion['path'])
        if digest(definition.read_bytes()) != completion.get('sha256'):
            raise StateError('completion definition hash differs')
        gates = issue['product']['required_gates']
        if not gates or binding.get('required_gates') != gates or set(task['gates']) != set(gates) or {row['name'] for row in result['gates']} != set(gates):
            raise StateError('work-item required gates differ')
        return result
    except OSError as exc: raise ReadinessError('task report/record missing') from exc
    except (ValueError, TypeError, KeyError) as exc: raise StateError(str(exc)) from exc


def validate(value, root):
    """Return normalized id->issue only after all declared evidence is valid."""
    root = Path(root).resolve()
    if not isinstance(value, dict) or value.get('schema') != 'colab-work-state/1':
        raise ReadinessError('colab-work-state/1 evidence required')
    if set(value) != {'schema', 'issues'}: raise StateError('unsupported work-state fields')
    issues = value.get('issues')
    if not isinstance(issues, list) or not issues: raise ReadinessError('no work items declared')
    by_id, numbers = {}, set()
    for issue in issues:
        if not isinstance(issue, dict): raise StateError('invalid Issue entry')
        if set(issue) - {'id', 'number', 'state', 'dependencies', 'product', 'pr', 'task'}:
            raise StateError('unsupported Issue fields')
        iid = issue.get('id')
        if not isinstance(iid, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', iid) or iid in by_id:
            raise StateError('invalid or duplicate local ID')
        number = issue.get('number')
        if number is not None:
            if type(number) is not int or number < 1 or number in numbers: raise StateError('invalid or duplicate Issue number')
            numbers.add(number)
        if issue.get('state') not in ('open', 'closed'): raise StateError('invalid Issue state')
        deps = issue.get('dependencies')
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps) or len(deps) != len(set(deps)):
            raise StateError('invalid dependencies')
        by_id[iid] = issue
    # Reuse the existing product judgments without opening any legacy document.
    legacy = module('state_product_rules', '../../gates/tools/work_item_consistency.py')
    product_rows = []
    required = {'title', 'owner', 'status', 'stage', 'entry_conditions', 'completion_def_ref', 'evidence_ref', 'deadline', 'required_gates'}
    for iid, issue in by_id.items():
        product = issue.get('product')
        if not isinstance(product, dict) or set(product) != required:
            raise StateError('product metadata missing or unsupported')
        for key in ('title', 'owner', 'completion_def_ref'):
            if not isinstance(product[key], str) or not product[key].strip():
                raise StateError('product completion/title/owner declaration missing')
        gates = product['required_gates']
        if not isinstance(gates, list) or any(not isinstance(g, str) or not g for g in gates) or len(gates) != len(set(gates)):
            raise StateError('invalid required gate declaration')
        if (product['status'] == 'done') != (issue['state'] == 'closed'):
            raise StateError('Issue closed and product done disagree')
        deadline = product['deadline']
        if isinstance(deadline, dict) and deadline.get('fired') in (None, 'unknown'):
            raise ReadinessError('deadline requires a measured judgment')
        product_rows.append({'id': iid, 'name': product['title'], 'owner': product['owner'],
                             'status': product['status'], 'stage': product['stage'],
                             'entry_conditions': product['entry_conditions'], 'depends_on': issue['dependencies'],
                             'completion_def': product['completion_def_ref'], 'evidence': product['evidence_ref'],
                             'deadline': deadline})
    product_index = legacy.check_schema(product_rows)
    legacy.check_deadlines(product_index); legacy.check_conflicts(product_index)
    if legacy.problems: raise StateError('product schema/status/stage/deadline/conflict validation failed')
    visiting, visited = set(), set()
    def visit(iid):
        if iid in visiting: raise StateError('dependency cycle')
        if iid in visited: return
        visiting.add(iid)
        for dep in by_id[iid]['dependencies']:
            if dep not in by_id: raise StateError('missing dependency')
            visit(dep)
        visiting.remove(iid); visited.add(iid)
    for iid, issue in by_id.items():
        visit(iid)
        if issue['state'] == 'closed' or 'pr' in issue:
            verify_pr(issue.get('pr'), root)
        if issue['state'] == 'closed' or 'task' in issue:
            report = verify_task(issue.get('task'), root, issue)
            if 'pr' in issue and report.get('commit') != issue['pr']['head_sha']:
                raise StateError('task checked a different PR head')
        if issue['state'] == 'closed' and any(by_id[dep]['state'] != 'closed' for dep in issue['dependencies']):
            raise StateError('closed item has unfinished dependency')
    return by_id


def safe_export(items, source_ref):
    """Whitelist-only LOCAL draft. Never include note/evidence/completion prose."""
    rows = []
    for item in items:
        rows.append({'id': item['id'], 'title': item['name'], 'status': item['status'],
                     'stage': item['stage'], 'depends_on': item['depends_on'],
                     'completion_def_present': bool(item.get('completion_def')),
                     'source_ref': source_ref,
                     'source_sha256': digest(json.dumps(item, sort_keys=True, ensure_ascii=False).encode())})
    return {'schema': 'colab-work-export/1', 'publication': 'local-review-draft', 'items': rows}


def decision_index(raw, source_ref):
    rows, numbers = [], set()
    for line in raw.splitlines(keepends=True):
        match = re.match(rb'^\|\s*' + '〈'.encode() + rb'\s*(\d+)\s*' + '〉'.encode() + rb'\s*\|', line)
        if match:
            number = int(match[1])
            if number in numbers: raise StateError('duplicate historical decision number')
            numbers.add(number)
            rows.append({'number': number, 'source_ref': source_ref, 'sha256': digest(line)})
    if not rows: raise ReadinessError('no historical decisions indexed')
    return {'schema': 'colab-decision-index/1', 'source_sha256': digest(raw), 'decisions': rows}


def handoff_row_hashes(raw):
    """Hash every numbered row in the exact blocker section; no semantic count guess."""
    text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    active, header, rows = False, False, []
    for line in text.splitlines(keepends=True):
        if line.rstrip('\n') == '## 4. 블로커 (사람이 풀어야 할 것)':
            active = True; continue
        if active and line.startswith('## '): break
        if not active: continue
        if line.rstrip('\n') == '| # | 블로커 | 막는 것 |': header = True; continue
        if line.lstrip().startswith('|') and re.sub(r'[`*~ #\s]', '', line.lstrip().split('|')[1]).isdigit():
            rows.append(digest(line.encode()))
    if not header or not rows or len(rows) != len(set(rows)):
        raise ReadinessError('HANDOFF blocker rows absent or ambiguous')
    return set(rows)


def verify_handoff_classification(handoff, raw, issues):
    if handoff.get('source_sha256') != digest(raw): raise StateError('HANDOFF classification source changed')
    rows = handoff.get('classifications')
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows): raise ReadinessError('HANDOFF row classifications missing')
    hashes = [row.get('row_sha256') for row in rows]
    if len(set(hashes)) != len(hashes) or set(hashes) != handoff_row_hashes(raw):
        raise StateError('HANDOFF classification row set incomplete or changed')
    for row in rows:
        kind = row.get('kind')
        if kind not in ('issue', 'security-excluded', 'historical-resolved', 'unclassified'):
            raise StateError('unknown HANDOFF classification')
        if kind == 'unclassified': raise StateError('HANDOFF unclassified row remains')
        if kind == 'issue' and (type(row.get('issue_number')) is not int or not any(issue.get('number') == row['issue_number'] for issue in issues.values())):
            raise StateError('HANDOFF Issue mapping missing')


def verify_transition_complete(value, root, cfg):
    """Fail closed until compatibility is retired and all source items are mapped."""
    if cfg.get('mode') != 'retired': raise StateError('legacy compatibility still active')
    import yaml
    paths = cfg.get('consumer_paths')
    ledger = cfg.get('ledger')
    if not isinstance(paths, list) or not paths or not ledger:
        raise ReadinessError('transition measurement inventory missing')
    source = Path(root)/ledger
    items = yaml.safe_load(source.read_text())['items']
    closure = cfg.get('closure_evidence')
    if not isinstance(closure, dict): raise ReadinessError('transition closure records missing')
    mapping = read_record(closure.get('mapping'), root, 'colab-work-mapping/1')
    if mapping.get('ledger_sha256') != digest(source.read_bytes()): raise StateError('migration source ledger changed')
    rows = mapping.get('mappings')
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows): raise ReadinessError('mapping rows missing')
    indexed = {row.get('id'): row for row in rows}
    if len(indexed) != len(rows) or set(indexed) != {item['id'] for item in items}: raise StateError('unmigrated or duplicate legacy mappings')
    issues = {issue['id']: issue for issue in value['issues']}
    for item in items:
        row = indexed[item['id']]
        if row.get('source_sha256') != digest(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()): raise StateError('mapped item source changed')
        if row.get('kind') == 'historical-done' and item['status'] == 'done':
            continue  # Preserve old completion history; never fabricate a new PR for it.
        issue = issues.get(item['id'])
        if row.get('kind') != 'issue' or not issue or type(issue.get('number')) is not int or row.get('issue_number') != issue['number']:
            raise StateError('active item Issue mapping missing')
    handoff = read_record(closure.get('handoff'), root, 'colab-handoff-classification/1')
    verify_handoff_classification(handoff, (Path(root)/'dev-package/03-HANDOFF.md').read_bytes(), issues)
    external = closure.get('external_pr_records')
    if not isinstance(external, list) or len(external) != 2: raise ReadinessError('external PR resolution records missing')
    if {verify_pr_record(reference, root)['number'] for reference in external} != {35, 38}:
        raise StateError('external PR resolution set differs')
    # Do not trust a shortened user-supplied file inventory to prove zero consumers.
    measured = set(Path(root)/relative for relative in paths)
    for scope in ('scripts', 'gates', '.agents/skills'):
        folder = Path(root)/scope
        if not folder.is_dir(): raise ReadinessError('consumer scan scope missing: ' + scope)
        measured.update(path for path in folder.rglob('*') if path.is_file() and path.suffix in ('.py', '.sh', '.md')
                        and 'tests' not in path.parts and path.name != 'work_state.py')
    if not measured: raise ReadinessError('no consumer files measured')
    for path in measured:
        content = path.read_text()
        if any(token in content for token in ('dev-package/work-items.yaml', 'dev-package/03-HANDOFF.md', 'dev-package/PLAN-SoT.md')):
            raise StateError('legacy consumer remains: ' + str(path.relative_to(root)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--export-ledger', action='store_true')
    parser.add_argument('--decision-index', action='store_true')
    parser.add_argument('--transition-complete', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.export_ledger or args.decision_index:
            import yaml
            relative = 'dev-package/work-items.yaml' if args.export_ledger else 'dev-package/PLAN-SoT.md'
            raw = (args.root/relative).read_bytes()
            result = safe_export(yaml.safe_load(raw)['items'], relative) if args.export_ledger else decision_index(raw, relative)
            print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
        if args.input is None: raise ReadinessError('explicit --input work-state JSON required')
        value = json.loads(args.input.read_text())
        by_id = validate(value, args.root)
        if args.transition_complete:
            cfg = json.loads((args.root/'.agents/harness.yaml').read_text())['transition']
            verify_transition_complete(value, args.root, cfg)
        print(f'work-state: green {len(by_id)} local items; publication/transition completion not implied')
        return 0
    except (ReadinessError, OSError) as exc:
        print('::gate-readiness-failure:: ' + str(exc), file=sys.stderr); return 78
    except (StateError, ValueError, TypeError, KeyError) as exc:
        print('work-state: ' + str(exc), file=sys.stderr); return 1


if __name__ == '__main__': raise SystemExit(main())
