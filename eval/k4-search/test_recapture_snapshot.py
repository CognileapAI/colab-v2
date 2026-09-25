import copy
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import recapture_snapshot as rs

A, B, C = '0' * 25 + 'A', '0' * 25 + 'B', '0' * 25 + 'C'
LAB, OWNER = 'L' * 26, 'O' * 26

PLAN = {
    'expected': {'datasets': 3, 'edges': 2},
    'projects': [{'key': 'p', 'name': 'p'}],
    'datasets': [
        {'seq': 1, 'project': 'p', 'name': 'raw', 'level': 'Lv0', 'expect_files': 2,
         'grid_files': ['g/LAT.npy', 'g/LON.npy'], 'parents': []},
        {'seq': 2, 'project': 'p', 'name': 'dem', 'level': 'Lv1', 'expect_files': 1,
         'grid_files': [], 'parents': []},
        {'seq': 3, 'project': 'p', 'name': 'pred', 'level': 'Lv2', 'expect_files': 1,
         'grid_files': [], 'parents': ['raw', 'dem']},
    ],
}
AUX = [{'child': 'pred', 'parent': 'dem', 'role': '보조입력'}]


def dataset(i, name, level, max_parent):
    return dict(id=i, lab_id=LAB, owner_account_id=OWNER, source_label='src', processing_level_user_set=level,
                max_primary_parent_level=max_parent, name=name, topic='t', summary='s', category=None,
                data_type=None, observation_interval_value=None, observation_interval_unit=None)


def raw():
    return {
        'read_only': 'on',
        'captured_at': '2026-09-25T00:00:00+00:00',
        'labs': [LAB],
        # deliberately unsorted: output order must not depend on query order
        'datasets': [dataset(C, 'pred', 'Lv2', 0), dataset(A, 'raw', 'Lv0', None), dataset(B, 'dem', 'Lv1', None)],
        'autometa': [
            dict(dataset_id=d, format='NetCDF' if d != B else None, variables=[], period_start='2020-01-01T00:00:00+00:00',
                 period_end='2020-02-01T00:00:00+00:00', period_granularity='일', file_extension='nc',
                 crs='WGS84' if d == A else None, grid='(2, 3)' if d == A else None, bundle_file_name='x.nc')
            for d in (C, A, B)],
        'variables': [dict(dataset_id=A, ordinal=2, name='v2', unit=None, value_range=None, missing_rate=None,
                           is_representative=False),
                      dict(dataset_id=A, ordinal=1, name='v1', unit='mm', value_range=None, missing_rate=None,
                           is_representative=True)],
        'files': [
            dict(dataset_id=A, id='F3', file_name='b.nc', kind='본체', size_bytes=3, relative_path=None,
                 carries_lat=False, carries_lon=False),
            dict(dataset_id=A, id='F1', file_name='LAT.npy', kind='기준 격자 파일', size_bytes=1, relative_path=None,
                 carries_lat=True, carries_lon=False),
            dict(dataset_id=A, id='F2', file_name='a.nc', kind='본체', size_bytes=2, relative_path=None,
                 carries_lat=False, carries_lon=False),
            dict(dataset_id=A, id='F0', file_name='LON.npy', kind='기준 격자 파일', size_bytes=1, relative_path=None,
                 carries_lat=False, carries_lon=True),
            dict(dataset_id=B, id='F4', file_name='dem.tif', kind='본체', size_bytes=4, relative_path=None,
                 carries_lat=False, carries_lon=False),
            dict(dataset_id=C, id='F5', file_name='p.npy', kind='본체', size_bytes=5, relative_path=None,
                 carries_lat=False, carries_lon=False),
        ],
        'edges': [dict(child_dataset_id=C, parent_dataset_id=B, parent_role='보조입력', method=None, origin='manual'),
                  dict(child_dataset_id=C, parent_dataset_id=A, parent_role='주입력', method=None, origin='manual')],
        'projects': [{'id': 'P1', 'name': 'p'}],
        'project_links': [{'project_id': 'P1', 'dataset_id': d} for d in (A, B, C)],
    }


def build(r=None):
    return rs.build(r or raw(), PLAN, AUX, deployed_revision='abc123')


class BuildTests(unittest.TestCase):
    def test_v2_keeps_every_v1_dataset_key_and_adds_processing_level_column(self):
        v1 = json.loads((Path(__file__).parent / 'fixtures/reference/dev-data-snapshot.json').read_text())
        snap, _, _ = build()
        for key in v1['datasets'][0]:
            self.assertIn(key, snap['datasets'][0])
        for key in v1['datasets'][0]['autometa']:
            self.assertIn(key, snap['datasets'][0]['autometa'])
        by_name = {d['name']: d for d in snap['datasets']}
        self.assertEqual(by_name['pred']['processing_level'], 'Lv2')
        self.assertEqual(by_name['pred']['processing_level_derived'], 1)
        # a dataset without a primary parent is Lv0 by the product rule, never the cap
        self.assertEqual(by_name['raw']['processing_level_derived'], 0)
        self.assertEqual(by_name['dem']['processing_level_derived'], 0)

    def test_derived_level_is_capped_like_the_product(self):
        r = raw()
        r['datasets'][0]['max_primary_parent_level'] = rs.LV_CAP
        snap, _, _ = build(r)
        self.assertEqual({d['name']: d['processing_level_derived'] for d in snap['datasets']}['pred'], rs.LV_CAP)
        self.assertEqual(snap['format_version'], 2)

    def test_output_is_deterministic_regardless_of_query_order(self):
        shuffled = raw()
        for k in ('datasets', 'autometa', 'files', 'edges', 'variables'):
            shuffled[k] = list(reversed(shuffled[k]))
        self.assertEqual(json.dumps(build()[0], ensure_ascii=False), json.dumps(build(shuffled)[0], ensure_ascii=False))
        snap = build()[0]
        self.assertEqual([d['id'] for d in snap['datasets']], [A, B, C])
        files = snap['datasets'][0]['files']
        self.assertEqual([f['kind'] for f in files], ['기준 격자 파일', '기준 격자 파일', '본체', '본체'])
        self.assertEqual([v['ordinal'] for v in snap['datasets'][0]['variable_rows']], [1, 2])
        self.assertEqual([p['parent_role'] for p in snap['datasets'][2]['parents']], ['주입력', '보조입력'])

    def test_projects_and_plan_seq_are_carried(self):
        snap, _, _ = build()
        self.assertEqual(snap['datasets'][0]['projects'], [{'id': 'P1', 'name': 'p'}])
        self.assertEqual([d['plan_seq'] for d in snap['datasets']], [1, 2, 3])
        self.assertEqual(snap['subject'], {'accountId': OWNER, 'labId': LAB})

    def test_idmap_contains_only_names_and_ids(self):
        _, idmap, _ = build()
        self.assertEqual(idmap, {'dem': B, 'pred': C, 'raw': A})

    def test_autometa_fill_counts_per_axis(self):
        snap, _, _ = build()
        fill = snap['counts']['autometa_fill']
        self.assertEqual(fill, {'rows': 3, 'format': 2, 'crs': 1, 'grid': 1, 'period_start': 3, 'period_end': 3,
                                'variables': 0, 'variable_rows_datasets': 1})


class ValidationTests(unittest.TestCase):
    def failed(self, r):
        _, _, checks = build(r)
        return {c['check'] for c in checks if not c['ok']}

    def test_clean_capture_passes_every_check(self):
        self.assertEqual(self.failed(raw()), set())

    def test_level_mismatch_is_a_judgement_failure(self):
        r = raw()
        r['datasets'][0]['processing_level_user_set'] = 'Lv1'
        self.assertIn('processing_level_vs_plan', self.failed(r))

    def test_missing_edge_and_wrong_role_fail(self):
        r = raw()
        r['edges'][0]['parent_role'] = '주입력'
        self.assertIn('edge_roles_vs_plan', self.failed(r))
        r = raw()
        r['edges'].pop()
        self.assertIn('edges_total', self.failed(r))

    def test_unlinked_dataset_and_extra_dev_dataset_fail(self):
        r = raw()
        r['project_links'].pop()
        self.assertIn('project_vs_plan', self.failed(r))
        r = raw()
        r['datasets'].append(dataset('0' * 25 + 'D', 'stray', 'Lv0', None))
        self.assertIn('datasets_total', self.failed(r))

    def test_grid_absent_is_accepted_only_when_the_file_carries_its_own_crs(self):
        plan = copy.deepcopy(PLAN)
        plan['datasets'][1]['grid_files'] = ['g/LAT.npy', 'g/LON.npy']
        failed = lambda r: {c['check'] for c in rs.build(r, plan, AUX)[2] if not c['ok']}
        self.assertIn('grid_absent_only_when_file_carries_crs', failed(raw()))
        r = raw()
        next(a for a in r['autometa'] if a['dataset_id'] == B)['crs'] = 'WGS84 (기준 격자 파일)'
        self.assertIn('grid_absent_only_when_file_carries_crs', failed(r))
        next(a for a in r['autometa'] if a['dataset_id'] == B)['crs'] = 'EPSG:4326'
        self.assertEqual(failed(r), set())

    def test_name_absent_or_duplicated_is_preparation_failure(self):
        r = raw()
        r['datasets'][1]['name'] = 'renamed'
        with self.assertRaises(rs.PreparationFailure):
            build(r)
        r = raw()
        r['datasets'].append(dataset('0' * 25 + 'D', 'raw', 'Lv0', None))
        with self.assertRaises(rs.PreparationFailure):
            build(r)

    def test_read_only_off_is_preparation_failure(self):
        r = raw()
        r['read_only'] = 'off'
        with self.assertRaises(rs.PreparationFailure):
            build(r)


class ReadOnlyContractTests(unittest.TestCase):
    def test_capture_sql_has_no_write_statement_and_is_wrapped_read_only(self):
        sql = rs.capture_sql()
        body = re.sub(r"'[^']*'", "''", sql)
        self.assertIsNone(re.search(r'\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|COPY|MERGE)\b',
                                    body, re.I))
        self.assertTrue(sql.lstrip().lower().startswith('begin read only;'))
        self.assertTrue(sql.rstrip().lower().endswith('rollback;'))

    def test_existing_output_is_preparation_failure_before_any_network(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'snap.json'
            out.write_text('{}')
            with mock.patch.object(rs, 'fetch_raw', side_effect=AssertionError('network touched')):
                code = rs.main(['--output', str(out), '--idmap', str(Path(d) / 'idmap.json')])
            self.assertEqual(code, 78)

    def test_missing_dev_environment_is_preparation_failure(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {}, clear=True):
            code = rs.main(['--output', str(Path(d) / 's.json'), '--idmap', str(Path(d) / 'i.json')])
            self.assertEqual(code, 78)


if __name__ == '__main__':
    unittest.main()
