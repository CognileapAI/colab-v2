"""K4 interpreter probe — replays recorded model interpretations through the real search API.

Measurement, not a pass/fail gate: the retrieval half of `dev-package/intent/2026-09-22-k4-luna-interpreter-probe.md`.
Corpus = the reference snapshot v2 (28 datasets, fixed IDs) seeded by `seed_reference_corpus`, so the golden
IDs match without touching dev. No model is called here — the interpretations come from
`eval/k4-search/llm_interpreter_probe.py --skip-remote` output (env `COLAB_K4_PROBE_INTERP`).
The judgment JSON is written to `COLAB_K4_PROBE_OUT`. Both env values are required; missing → error, not skip.
"""
import copy
import json
import os
import statistics
from pathlib import Path

import pytest

from conftest import TOKEN_RES, auth
from test_search_relay import fake_ai  # noqa: F401
from test_search_reference_evidence import ROOT, seed_reference_corpus
from colab_core.app.main import API_PREFIX

pytestmark = pytest.mark.k4_probe


def _assess(case, ids_in_order):
    scoped = [x for x in ids_in_order if x in case['scope']]
    if case['mode'] == 'manual':
        status = 'not_applicable'
    elif case['mode'] == 'empty':
        status = 'pass' if not scoped else 'fail'
    else:
        status = 'pass' if set(case['required']) <= set(scoped) else 'fail'
    return dict(id=case['id'], retrieval=status, scoped_ids=scoped,
                outside_ids=[x for x in ids_in_order if x not in case['scope']],
                required_ranks={x: scoped.index(x) + 1 if x in scoped else None for x in case['required']})


def _run(client, fake_ai, cases, interps, source):
    out = []
    for case, interp in zip(cases, interps, strict=True):
        assert interp['id'] == case['id']
        fake_ai['body'] = {
            'degraded': False,
            'scope': {'labId': '0000000000000000000000000A', 'labName': 'evaluation scope', 'searchedCount': 0},
            'isDataQuery': True,
            'results': {'items': [], 'totalCount': 0, 'nextCursor': None},
            'interpretation': {'terms': list(interp['terms']), 'topic': interp['topic'], 'source': source},
        }
        response = client.post(f'{API_PREFIX}/dataset-searches', headers=auth(TOKEN_RES),
                               json={'query': case['query'], 'limit': 100})
        assert response.status_code == 200, response.text
        items = response.json()['items']
        j = _assess(case, [i['datasetId'] for i in items])
        j.update(terms=list(interp['terms']), topic=interp['topic'], total=len(items))
        out.append(j)
    return out


def _summary(judged):
    counted = [j for j in judged if j['retrieval'] != 'not_applicable']
    ranks = [r for j in judged for r in j['required_ranks'].values() if r is not None]
    return dict(passed=sum(j['retrieval'] == 'pass' for j in counted), judged=len(counted),
                failed=[j['id'] for j in counted if j['retrieval'] == 'fail'],
                rank_median=statistics.median(ranks) if ranks else None, ranks_found=len(ranks),
                required_total=sum(len(j['required_ranks']) for j in judged))


def test_k4_probe_replays_interpretations_on_reference_corpus(p2_client, sql, fake_ai):
    interp_path = Path(os.environ['COLAB_K4_PROBE_INTERP'])
    out_path = Path(os.environ['COLAB_K4_PROBE_OUT'])
    assert not out_path.exists(), 'output already exists; choose a new run path'
    recorded = json.loads(interp_path.read_text())
    cases = json.loads((ROOT / 'eval/k4-search/golden-cases.json').read_text())['cases']
    client, datasets = seed_reference_corpus(p2_client, sql, fake_ai)
    assert {d['id'] for d in datasets} >= {r for c in cases for r in c['required']}

    runs = {}
    for k, interps in enumerate(recorded['passes']):
        runs[f"{recorded['model']}#{k + 1}"] = _run(client, fake_ai, cases, interps, 'llm')
    runs['literal'] = _run(client, fake_ai, cases, recorded['literal'], 'literal')

    report = dict(kind='K4 retrieval half on reference corpus (9 datasets, fixed IDs); recorded interpretations replayed '
                       'through the real search API with a frozen AI double; no model call; not a gate',
                  model=recorded['model'], interp_source=str(interp_path.relative_to(ROOT)) if interp_path.is_relative_to(ROOT) else str(interp_path),
                  interp_runner_sha256=recorded.get('runner_sha256'), interp_local_sha=recorded.get('local_sha'),
                  corpus_size=len(datasets), judgments=runs,
                  summary={name: _summary(j) for name, j in runs.items()})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    # The measurement itself is the deliverable; only structural integrity is asserted.
    assert all(len(j) == len(cases) for j in runs.values())
