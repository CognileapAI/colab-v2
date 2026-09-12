"""Read-only dev keyword baseline, not a model/API/UI evaluation.

Exit 0: all automatic retrieval checks pass (semantic checks still pending).
Exit 1: at least one retrieval check fails. Exit 78: incomplete measurement.
Uses local LiteralInterpreter and deployed core search; never rewrites gold.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def expanded_cases(cases, responses):
    if [c['id'] for c in cases] != [r['id'] for r in responses]:
        raise ValueError('expansion case mismatch')
    result = []
    for c,r in zip(cases,responses):
        if r.get('degraded') is not False:
            raise ValueError('dictionary expansion degraded')
        parsed = r['interpretation']
        if not isinstance(parsed['terms'],list) or not all(isinstance(t,str) for t in parsed['terms']):
            raise ValueError('invalid expansion terms')
        result.append(dict(c,terms=parsed['terms'],topic=parsed['topic']))
    return result


AI_REMOTE = r'''
import dataclasses,hashlib,inspect,json,sys
from colab_ai.app import dictionaries,interpret
from colab_ai.domains import d9_ontology,d10_ai_services
from colab_ai.kernel.config import Settings
from colab_ai.kernel.db import make_engine
from pathlib import Path
p=json.loads(sys.stdin.readline())
settings=Settings.from_env()
assert settings.dict_db_url, 'dictionary connection missing'
source=dictionaries.SqlDictionaries(make_engine(settings.dict_db_url).execution_options(isolation_level='REPEATABLE READ'))
frozen=source._read()
class Frozen(dictionaries.SqlDictionaries):
 def __init__(self): pass
 def _read(self): return frozen
service=d10_ai_services.SearchService(interpreter=interpret.LiteralInterpreter(interpret.LiteralInterpreter.BY_DESIGN_REASON),dictionaries=Frozen())
responses=[]
for c in p['cases']:
 r=service.search(lab_id=p['subject']['labId'],lab_name='evaluation scope',query=c['query'],searched_count=0)
 responses.append(dict(id=c['id'],**r))
print(json.dumps({'responses':responses,'dictionary':dataclasses.asdict(frozen[0]),'graph':dataclasses.asdict(frozen[1]),'source_sha256':{m.__name__:hashlib.sha256(Path(inspect.getfile(m)).read_bytes()).hexdigest() for m in [dictionaries,interpret,d9_ontology,d10_ai_services]}},ensure_ascii=False))
'''


def assess(case, rows, total):
    ids = [r['dataset_id'] for r in rows]
    if total != len(ids) or len(ids) != len(set(ids)):
        raise ValueError('truncated or duplicate result set')
    scoped = [x for x in ids if x in case['scope']]
    if case['mode'] == 'manual':
        status = 'not_applicable'
    elif case['mode'] == 'empty':
        status = 'pass' if not scoped else 'fail'
    else:
        status = 'pass' if set(case['required']) <= set(scoped) else 'fail'
    return dict(id=case['id'], retrieval=status, semantic='unassessed',
                scoped_ids=scoped, outside_ids=[x for x in ids if x not in case['scope']],
                required_ranks={x: scoped.index(x)+1 if x in scoped else None
                                for x in case['required']})


REMOTE = r'''
import dataclasses,hashlib,inspect,json,os,sys,time
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import text
from colab_core.domains import d3_catalog
from colab_core.kernel.db import make_engine,make_session_factory
from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from colab_core.kernel.scope import read_only_scope

p=json.loads(sys.stdin.readline())
subject=p['subject']
known=json.loads(Path(os.environ['COLAB_CORE_SUBJECTS_FILE']).read_text())
assert subject in known.values(), 'subject absent'
url=Path(os.environ['COLAB_CORE_DATABASE_URL_FILE']).read_text().strip()
factory=make_session_factory(make_engine(url).execution_options(isolation_level='REPEATABLE READ'))
out={'captured_at':datetime.now(timezone.utc).isoformat(),'results':[]}
with read_only_scope(factory,Subject(account_id=Ulid(subject['accountId']),lab_id=Ulid(subject['labId']))) as s:
 out['read_only']=s.execute(text('SHOW transaction_read_only')).scalar()
 out['corpus']=[dict(r) for r in s.execute(text('SELECT d.id,dd.name,dd.topic,dd.summary,d.source_label,dd.search_vector::text AS description_vector,am.search_vector::text AS autometa_vector,d.search_vector::text AS source_vector FROM d3_dataset d JOIN d3_dataset_description dd ON dd.dataset_id=d.id LEFT JOIN d3_dataset_autometa am ON am.dataset_id=d.id WHERE d.deleted_at IS NULL ORDER BY d.id')).mappings()]
 ids={r['id'] for r in out['corpus']}
 assert set(p['expected_names']) <= ids, 'missing gold dataset'
 for r in out['corpus']:
  if r['id'] in p['expected_names']:
   assert r['name']==p['expected_names'][r['id']], 'gold name changed'
 for case in p['cases']:
  start=time.perf_counter()
  rows,total=d3_catalog.search_datasets(s,terms=tuple(case['terms']),topic=case.get('topic'),limit=100,offset=0)
  out['results'].append({'id':case['id'],'total':total,'rows':[dataclasses.asdict(r) for r in rows], 'sql_seconds':time.perf_counter()-start})
out['search_code_sha256']=hashlib.sha256(Path(inspect.getfile(d3_catalog)).read_bytes()).hexdigest()
print(json.dumps(out,ensure_ascii=False,default=str))
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--mode', choices=['literal','expanded','local-expanded'], default='literal')
    ap.add_argument('--frozen-expansion', type=Path,
                    help='Prior expansion report used by local-expanded; dictionary/graph remain frozen')
    ap.add_argument('--omit-topic-filter', action='store_true',
                    help='Diagnostic ablation only; no production configuration change')
    args = ap.parse_args()
    if args.output.exists():
        print('Preparation failure: output already exists; choose a new run path')
        return 78
    try:
        ssh_host = os.environ['COLAB_DEV_SSH']
        if args.omit_topic_filter and args.mode != 'expanded':
            raise ValueError('topic ablation requires expanded mode')
        ssh_key = os.environ['COLAB_DEV_KEY_FILE']
        case_path = HERE / 'golden-cases.json'
        suite = json.loads(case_path.read_text())
        if len(suite['cases']) != 12 or len({c['id'] for c in suite['cases']}) != 12:
            raise ValueError('unexpected case count')
        snapshot_path = ROOT / suite['snapshot']
        snapshot = json.loads(snapshot_path.read_text())
        expected = {d['id']: d['name'] for d in snapshot['datasets']}
        if len(expected) != 9:
            raise ValueError('expected nine datasets')
        for c in suite['cases']:
            if not c['scope'] or not set(c['scope']) <= set(expected):
                raise ValueError('invalid scope')
            if c['mode'] not in ('retrieval', 'empty', 'manual'):
                raise ValueError('unknown mode')
            if not set(c['required']) <= set(c['scope']):
                raise ValueError('gold outside scope')
            if c['mode'] == 'retrieval' and not c['required']:
                raise ValueError('empty retrieval gold')
        sys.path.insert(0, str(ROOT / 'services/ai-service/src'))
        from colab_ai.app.interpret import LiteralInterpreter
        import colab_ai.app.interpret as interpreter_module
        cases = [dict(c, terms=list(LiteralInterpreter().interpret(c['query']).terms))
                 for c in suite['cases']]
        expansion = None
        if args.mode == 'local-expanded':
            if not args.frozen_expansion:
                raise ValueError('local-expanded requires a frozen expansion report')
            from colab_ai.app import dictionaries
            from colab_ai.domains import d9_ontology, d10_ai_services
            prior = json.loads(args.frozen_expansion.read_text())['expansion']
            dictionary = d9_ontology.Dictionaries(**prior['dictionary'])
            graph = d9_ontology.ConceptGraph(
                nodes=tuple(d9_ontology.ConceptNode(**n) for n in prior['graph']['nodes']),
                edges=tuple(d9_ontology.ConceptEdge(**e) for e in prior['graph']['edges']))
            class FrozenLocal(dictionaries.SqlDictionaries):
                def __init__(self): pass
                def _read(self): return dictionary, graph
            service = d10_ai_services.SearchService(
                interpreter=LiteralInterpreter(LiteralInterpreter.BY_DESIGN_REASON), dictionaries=FrozenLocal())
            responses = [dict(id=c['id'], **service.search(lab_id=snapshot['subject']['labId'],
                         lab_name='evaluation scope', query=c['query'])) for c in cases]
            expansion = dict(responses=responses, dictionary=prior['dictionary'], graph=prior['graph'],
                fixture_sha256=hashlib.sha256(args.frozen_expansion.read_bytes()).hexdigest(),
                source_sha256={m.__name__:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                    for m in [dictionaries, interpreter_module, d9_ontology, d10_ai_services]})
            cases = expanded_cases(cases, responses)
        if args.mode == 'expanded':
            import shlex
            ai_cmd = 'docker exec -i colab_v2_dev_ai_service python -c ' + shlex.quote(AI_REMOTE)
            ai_proc = subprocess.run(['ssh','-i',ssh_key,'-o','BatchMode=yes','-o','ConnectTimeout=10',ssh_host,ai_cmd],
                                     input=json.dumps(dict(subject=snapshot['subject'],cases=cases)),text=True,capture_output=True,timeout=90)
            if ai_proc.returncode:
                raise RuntimeError('dictionary read failed')
            expansion = json.loads(ai_proc.stdout)
            cases = expanded_cases(cases,expansion['responses'])
            if args.omit_topic_filter:
                cases = [dict(c,topic=None) for c in cases]
        payload = dict(subject=snapshot['subject'],expected_names=expected,cases=cases)
        # Code and payload travel over stdin; authentication remains on the host.
        import shlex
        remote_cmd = 'docker exec -i colab_v2_dev_core_api python -c ' + shlex.quote(REMOTE)
        proc = subprocess.run(['ssh','-i',ssh_key,'-o','BatchMode=yes','-o',
                               'ConnectTimeout=10',ssh_host,remote_cmd],
                              input=json.dumps(payload),text=True,capture_output=True,timeout=90)
        if proc.returncode:
            raise RuntimeError('remote query failed (details withheld to protect connection secrets)')
        result = json.loads(proc.stdout)
        if result['read_only'] != 'on' or len(result['results']) != len(cases):
            raise ValueError('incomplete read-only run')
        if [r['id'] for r in result['results']] != [c['id'] for c in cases]:
            raise ValueError('case order mismatch')
        judgments = [assess(c, r['rows'], r['total']) for c,r in zip(cases,result['results'])]
        counts = dict(Counter(j['retrieval'] for j in judgments))
        result.update(mode=('literal-to-deployed-D3; no LLM/dictionary/graph/API/UI' if args.mode=='literal'
                            else 'local code+frozen dictionaries/graph-to-deployed-D3; no LLM/API/UI' if args.mode=='local-expanded'
                            else 'deployed literal+function-word-filter+dictionary+graph-to-D3; no LLM/API/UI'),
                      expansion=expansion,
                      diagnostic_omit_topic_filter=args.omit_topic_filter,
                      runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      oracle_sha256=hashlib.sha256((HERE/'golden-set.md').read_bytes()).hexdigest(),
                      suite_sha256=hashlib.sha256(case_path.read_bytes()).hexdigest(),
                      snapshot_sha256=hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
                      interpreter_sha256=hashlib.sha256(Path(interpreter_module.__file__).read_bytes()).hexdigest(),
                      local_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                      cases=cases,judgments=judgments,counts=counts,model_calls=0,
                      semantic_unassessed=len(cases))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'retrieval':counts,'semantic_unassessed':len(cases),'output':str(args.output)}))
        return 1 if counts.get('fail') else 0
    except Exception as exc:
        # Do not expose DB URLs or tokens in remote error traces.
        print('Preparation failure:', type(exc).__name__)
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
