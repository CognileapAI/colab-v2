"""Read-only recapture of the dev reference corpus as snapshot v2 (corpus-expansion WU3).

Reads dev through the BYPASSRLS backup URL with a throwaway postgres:16-alpine client on the
dev host, inside `begin read only; ... rollback;`. This tool holds no write SQL.
Datasets are matched to `plan-manifest.yaml` by NAME only; a plan name with zero or several
dev matches is a preparation failure (no arbitrary pick).

Exit 0: every validation check passes. Exit 1: a check fails (outputs still written; they are
facts). Exit 78: preparation failure (env missing, output exists, read-only not on, name match).
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / 'dev-package/tools/dev-seed/plan-manifest.yaml'
CANONICAL_PATH = ROOT / 'dev-package/tools/dev-seed/canonical-metadata.json'
GRID_KIND = '기준 격자 파일'
KIND_ORDER = {GRID_KIND: 0, '본체': 1}
ROLE_ORDER = {'주입력': 0, '보조입력': 1}
# Same constant as services/core-api ports/lineage.py LV_CAP; used by the derived-level CTE.
LV_CAP = 3


class PreparationFailure(Exception):
    pass


def capture_sql():
    # max_primary_parent_level = d4_lineage._SUMMARY verbatim; the +1/cap step is derived_level()
    # (SQL LEAST ignores NULL, so the rule must not be folded into the query).
    return f"""begin read only;
set local timezone = 'UTC';
with recursive depth(dataset_id, level) as (
    select d.id, 0 from d3_dataset d
     where not exists (select 1 from d4_lineage_edge e
                        where e.child_dataset_id = d.id and e.parent_role = '주입력')
    union
    select e.child_dataset_id, least(p.level + 1, {LV_CAP})
      from d4_lineage_edge e join depth p on p.dataset_id = e.parent_dataset_id
     where e.parent_role = '주입력'
)
select json_build_object(
  'read_only', current_setting('transaction_read_only'),
  'captured_at', now(),
  'labs', (select coalesce(json_agg(id order by id), '[]') from d1_lab),
  'datasets', (select coalesce(json_agg(json_build_object(
        'id', d.id, 'lab_id', d.lab_id, 'owner_account_id', d.owner_account_id,
        'source_label', d.source_label, 'processing_level_user_set', d.processing_level_user_set,
        'max_primary_parent_level', (
            select max(p.level) from depth p
              join d4_lineage_edge e on e.parent_dataset_id = p.dataset_id
             where e.child_dataset_id = d.id and e.parent_role = '주입력'),
        'name', dd.name, 'topic', dd.topic, 'summary', dd.summary, 'category', dd.category,
        'data_type', dd.data_type, 'observation_interval_value', dd.observation_interval_value,
        'observation_interval_unit', dd.observation_interval_unit) order by d.id), '[]')
      from d3_dataset d join d3_dataset_description dd on dd.dataset_id = d.id
     where d.deleted_at is null),
  'autometa', (select coalesce(json_agg(json_build_object(
        'dataset_id', a.dataset_id, 'format', a.format, 'variables', a.variables,
        'period_start', a.period_start, 'period_end', a.period_end,
        'period_granularity', a.period_granularity, 'file_extension', a.file_extension,
        'crs', a.crs, 'grid', a.grid, 'bundle_file_name', a.bundle_file_name) order by a.dataset_id), '[]')
      from d3_dataset_autometa a),
  'variables', (select coalesce(json_agg(json_build_object(
        'dataset_id', v.dataset_id, 'ordinal', v.ordinal, 'name', v.name, 'unit', v.unit,
        'value_range', v.value_range, 'missing_rate', v.missing_rate,
        'is_representative', v.is_representative) order by v.dataset_id, v.ordinal), '[]')
      from d3_dataset_variable v),
  'files', (select coalesce(json_agg(json_build_object(
        'dataset_id', f.dataset_id, 'id', f.id, 'file_name', f.file_name, 'kind', f.kind,
        'size_bytes', f.size_bytes, 'relative_path', f.relative_path,
        'carries_lat', f.carries_lat, 'carries_lon', f.carries_lon) order by f.dataset_id, f.id), '[]')
      from d3_file f),
  'edges', (select coalesce(json_agg(json_build_object(
        'child_dataset_id', e.child_dataset_id, 'parent_dataset_id', e.parent_dataset_id,
        'parent_role', e.parent_role, 'method', e.method, 'origin', e.origin) order by e.id), '[]')
      from d4_lineage_edge e),
  'projects', (select coalesce(json_agg(json_build_object('id', p.id, 'name', p.name) order by p.id), '[]')
      from d6_project p),
  'project_links', (select coalesce(json_agg(json_build_object(
        'project_id', l.project_id, 'dataset_id', l.dataset_id) order by l.id), '[]')
      from d6_project_dataset l)
);
rollback;
"""


def derived_level(max_primary_parent_level):
    """d3_catalog.processing_level: Lv0 without a primary parent, else max + 1 capped at LV_CAP."""
    if max_primary_parent_level is None:
        return 0
    return min(max_primary_parent_level + 1, LV_CAP)


def _dev_env():
    try:
        return os.environ['COLAB_DEV_SSH'], os.path.expanduser(os.path.expandvars(os.environ['COLAB_DEV_KEY_FILE']))
    except KeyError as missing:
        raise PreparationFailure(f'dev environment missing: {missing}') from None


def _ssh(host, key, command, stdin=''):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'ConnectTimeout=15',
                        '-i', key, host, command], input=stdin, text=True, capture_output=True, timeout=300)
    if r.returncode != 0:
        raise PreparationFailure(f'remote command failed (exit {r.returncode}): {r.stderr.strip()[-400:]}')
    return r.stdout


def fetch_raw(host, key):
    psql = ('psql -X -q -v ON_ERROR_STOP=1 -tA '
            '"$(sed -E "s#^postgresql\\+psycopg://#postgresql://#" /s/b.url)" -f -')
    command = ('sudo docker run --rm -i --network host --user 0 '
               '-v /etc/colab/backup-platform-db.url:/s/b.url:ro postgres:16-alpine sh -c ' + shlex.quote(psql))
    lines = [x for x in _ssh(host, key, command, capture_sql()).splitlines() if x.startswith('{')]
    if len(lines) != 1:
        raise PreparationFailure('expected exactly one JSON line from the capture query')
    return json.loads(lines[0])


def fetch_deployed_revision(host, key):
    images = _ssh(host, key, "sudo docker ps --format '{{.Image}}'").split()
    tags = sorted({m.group(1) for i in images if (m := re.search(r':dev-([0-9a-f]{7,40})$', i))})
    return tags[0] if len(tags) == 1 else (tags or None)


def _match_names(raw, plan):
    by_name = {}
    for d in raw['datasets']:
        by_name.setdefault(d['name'], []).append(d)
    matched = {}
    for p in plan['datasets']:
        hits = by_name.get(p['name'], [])
        if len(hits) != 1:
            raise PreparationFailure(f"plan name matched {len(hits)} dev datasets (need exactly 1): {p['name']}")
        matched[p['name']] = hits[0]
    return matched


def _check(name, expected, actual):
    return {'check': name, 'expected': expected, 'actual': actual, 'ok': expected == actual}


def build(raw, plan, aux, deployed_revision=None):
    """Return (snapshot, name->id map, checks). Raises PreparationFailure on unusable input."""
    if raw.get('read_only') != 'on':
        raise PreparationFailure('transaction_read_only is not on')
    matched = _match_names(raw, plan)
    plan_by_name = {p['name']: p for p in plan['datasets']}
    id_to_name = {d['id']: d['name'] for d in matched.values()}
    ids = set(id_to_name)
    autometa = {a['dataset_id']: a for a in raw['autometa']}
    projects = {p['id']: p for p in raw['projects']}
    links = {}
    for link in raw['project_links']:
        links.setdefault(link['dataset_id'], []).append(projects[link['project_id']])
    files, variables, parents = {}, {}, {}
    for f in raw['files']:
        files.setdefault(f['dataset_id'], []).append(f)
    for v in raw['variables']:
        variables.setdefault(v['dataset_id'], []).append(v)
    for e in raw['edges']:
        parents.setdefault(e['child_dataset_id'], []).append(e)

    am_keys = ('format', 'variables', 'period_start', 'period_end', 'period_granularity', 'file_extension',
               'crs', 'grid', 'bundle_file_name')
    datasets = []
    for d in sorted(matched.values(), key=lambda x: x['id']):
        am = autometa.get(d['id'])
        datasets.append({
            'id': d['id'], 'name': d['name'], 'topic': d['topic'], 'summary': d['summary'],
            'source_label': d['source_label'], 'category': d['category'], 'data_type': d['data_type'],
            'observation_interval_value': d['observation_interval_value'],
            'observation_interval_unit': d['observation_interval_unit'],
            'manifest_key': None,
            'plan_seq': plan_by_name[d['name']]['seq'],
            'lab_id': d['lab_id'],
            'processing_level': d['processing_level_user_set'],
            'processing_level_derived': derived_level(d['max_primary_parent_level']),
            'projects': sorted(({'id': p['id'], 'name': p['name']} for p in links.get(d['id'], [])),
                               key=lambda p: p['id']),
            'files': [{k: f[k] for k in ('id', 'file_name', 'kind', 'size_bytes', 'relative_path',
                                         'carries_lat', 'carries_lon')}
                      for f in sorted(files.get(d['id'], []),
                                      key=lambda f: (KIND_ORDER.get(f['kind'], 9), f['file_name'], f['id']))],
            'autometa': None if am is None else {k: am[k] for k in am_keys},
            'variable_rows': [{k: v[k] for k in ('ordinal', 'name', 'unit', 'value_range', 'missing_rate',
                                                 'is_representative')}
                              for v in sorted(variables.get(d['id'], []), key=lambda v: v['ordinal'])],
            'parents': [{'parent_dataset_id': e['parent_dataset_id'], 'parent_role': e['parent_role'],
                         'method': e['method']}
                        for e in sorted(parents.get(d['id'], []),
                                        key=lambda e: (ROLE_ORDER.get(e['parent_role'], 9), e['parent_dataset_id']))],
        })

    ams = [x['autometa'] for x in datasets if x['autometa'] is not None]
    edges = [e for e in raw['edges'] if e['child_dataset_id'] in ids]
    all_files = [f for x in datasets for f in x['files']]
    counts = {
        'datasets': len(datasets), 'projects': len(raw['projects']), 'project_links': len(raw['project_links']),
        'lineage_edges': len(edges),
        'edges_by_role': dict(sorted(Counter(e['parent_role'] for e in edges).items())),
        'edges_with_method': sum(1 for e in edges if e['method']),
        'files_by_kind': dict(sorted(Counter(f['kind'] for f in all_files).items())),
        'variable_rows': sum(len(x['variable_rows']) for x in datasets),
        'processing_level': dict(sorted(Counter(x['processing_level'] for x in datasets).items())),
        'autometa_fill': {
            'rows': len(ams),
            **{k: sum(1 for a in ams if a[k] is not None) for k in ('format', 'crs', 'grid', 'period_start',
                                                                   'period_end')},
            'variables': sum(1 for a in ams if a['variables']),
            'variable_rows_datasets': sum(1 for x in datasets if x['variable_rows']),
        },
    }
    owners = sorted({d['owner_account_id'] for d in matched.values()})
    labs = sorted({d['lab_id'] for d in matched.values()})
    snapshot = {
        'format_version': 2,
        'environment': 'dev',
        'captured_at': raw['captured_at'],
        'deployed_revision': deployed_revision,
        'source': 'read-only SQL (begin read only / rollback) via BYPASSRLS backup URL; names matched to '
                  'dev-package/tools/dev-seed/plan-manifest.yaml',
        'subject': {'accountId': owners[0] if len(owners) == 1 else None,
                    'labId': labs[0] if len(labs) == 1 else None},
        'read_only': raw['read_only'],
        'visible_datasets': len(raw['datasets']),
        'counts': counts,
        'projects': sorted(({'id': p['id'], 'name': p['name'],
                             'datasets': sum(1 for x in datasets if p['id'] in {q['id'] for q in x['projects']})}
                            for p in raw['projects']), key=lambda p: p['id']),
        'datasets': datasets,
    }
    idmap = {x['name']: x['id'] for x in sorted(datasets, key=lambda x: x['name'])}

    aux_set = {(a['child'], a['parent']) for a in aux}
    plan_edges = {(p['name'], parent): ('보조입력' if (p['name'], parent) in aux_set else '주입력')
                  for p in plan['datasets'] for parent in p['parents']}
    dev_edges = {(id_to_name.get(e['child_dataset_id']), id_to_name.get(e['parent_dataset_id'])): e['parent_role']
                 for e in raw['edges']}
    by_id = {x['id']: x for x in datasets}
    checks = [
        _check('datasets_total', plan['expected']['datasets'], len(raw['datasets'])),
        _check('projects_total', sorted(p['name'] for p in plan['projects']),
               sorted(p['name'] for p in raw['projects'])),
        _check('edges_total', plan['expected']['edges'], len(raw['edges'])),
        _check('edge_pairs_vs_plan', sorted(map(list, plan_edges)), sorted(map(list, dev_edges))),
        _check('edge_roles_vs_plan', sorted([*k, v] for k, v in plan_edges.items()),
               sorted([*k, v] for k, v in dev_edges.items() if k in plan_edges)),
        _check('autometa_rows', len(datasets), len(ams)),
        _check('processing_level_vs_plan', [], [
            [x['name'], plan_by_name[x['name']]['level'], x['processing_level']]
            for x in datasets if x['processing_level'] != plan_by_name[x['name']]['level']]),
        _check('project_vs_plan', [], [
            [x['name'], plan_by_name[x['name']]['project'], [p['name'] for p in x['projects']]]
            for x in datasets if [p['name'] for p in x['projects']] != [plan_by_name[x['name']]['project']]]),
        _check('body_files_vs_plan', [], [
            [x['name'], plan_by_name[x['name']]['expect_files'], n]
            for x in datasets
            if (n := sum(1 for f in x['files'] if f['kind'] == '본체')) != plan_by_name[x['name']]['expect_files']]),
        # The runner skips grid attachment when the screen judges the body file to carry its own
        # coordinates (runner.py do_grid 「격자 칸 미출현」). So a planned grid may be absent only
        # when the dataset's CRS came from the file itself, not from a reference grid file.
        _check('grid_absent_only_when_file_carries_crs', [], [
            [x['name'], crs]
            for x in datasets
            if plan_by_name[x['name']].get('grid_files')
            and not any(f['kind'] == GRID_KIND for f in by_id[x['id']]['files'])
            and ((crs := (x['autometa'] or {}).get('crs')) is None or GRID_KIND in crs)]),
        _check('grid_files_only_where_planned', [], [
            x['name'] for x in datasets
            if not plan_by_name[x['name']].get('grid_files')
            and any(f['kind'] == GRID_KIND for f in by_id[x['id']]['files'])]),
    ]
    return snapshot, idmap, checks


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True, help='new snapshot v2 path (must not exist)')
    ap.add_argument('--idmap', type=Path, required=True, help='new name->id JSON path (must not exist)')
    ap.add_argument('--checks', type=Path, help='optional path for validation checks JSON (must not exist)')
    args = ap.parse_args(argv)
    try:
        for out in (args.output, args.idmap, args.checks):
            if out is not None and out.exists():
                raise PreparationFailure(f'output already exists: {out}')
        host, key = _dev_env()
        plan = yaml.safe_load(PLAN_PATH.read_text(encoding='utf-8'))
        aux = json.loads(CANONICAL_PATH.read_text(encoding='utf-8'))['auxiliaryParents']
        raw = fetch_raw(host, key)
        snapshot, idmap, checks = build(raw, plan, aux, fetch_deployed_revision(host, key))
    except PreparationFailure as failure:
        print(f'Preparation failure: {failure}', file=sys.stderr)
        return 78
    args.output.write_text(_dump(snapshot), encoding='utf-8')
    args.idmap.write_text(_dump(idmap), encoding='utf-8')
    if args.checks is not None:
        args.checks.write_text(_dump(checks), encoding='utf-8')
    failed = [c['check'] for c in checks if not c['ok']]
    print(json.dumps({'counts': snapshot['counts'], 'failed_checks': failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
