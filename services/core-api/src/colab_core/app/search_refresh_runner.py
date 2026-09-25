"""Bounded agent workflow. Network/model steps have no open DB transaction."""
from __future__ import annotations
import time


def run_batch(tools, *, max_jobs=100, synchronize=True, max_seconds=180):
    if type(max_jobs) is not int or not 1<=max_jobs<=1000:
        raise ValueError('max_jobs must be 1..1000')
    if type(max_seconds) not in (int,float) or not 0<max_seconds<=180:
        raise ValueError('max_seconds must be in (0,180]')
    if synchronize:
        tools.sync_manifest();tools.reconcile()
    summary={'processed':0,'ready':0,'candidate':0,'deleted':0,'failed':0}
    deadline=time.monotonic()+max_seconds
    for _ in range(max_jobs):
        if time.monotonic()>=deadline:break
        jobs=tools.claim(limit=1)
        if not jobs:break
        handle=jobs[0]['handle']
        try:
            data=tools.read(handle);source=data['source']
            if source.get('deleted') or source.get('status')=='candidate':
                result=tools.complete(handle,expected_version=data['ontology_version'],concept_ids=[])
            else:
                content=tools.lookup(handle)
                proposal=tools.propose(handle) if content['concepts'] else {'selections':[]}
                result=tools.complete(handle,expected_version=data['ontology_version'],
                    concept_ids=[p['node']['concept_id'] for p in content['concepts']],selections=proposal['selections'])
            summary[result['status']]+=1
        except Exception:
            # Only a closed error code is retained. Original text may contain data/secrets.
            summary['failed']+=1
            try:tools.fail(handle)
            except Exception:pass  # The persisted lease is the recovery path after process/DB loss.
        summary['processed']+=1
        if summary['failed']>=10:break
    return summary


def run_due(tools, *, max_jobs=100):
    from ..domains import d3_search_runs as runs
    with tools._scope() as s:generation=runs.claim_run(s)
    if generation is None:return {'status':'not_due'}
    summary={'processed':0,'ready':0,'candidate':0,'deleted':0,'failed':0}
    try:
        with tools._scope() as s:
            state=runs.status(s)
            initialized=runs.bootstrap_page(s,generation)
        if state['manifest_due']:
            tools.sync_manifest()
            with tools._scope() as s:runs.checkpoint(s,generation,manifest_checked=True)
        requeued=tools.reconcile()
        summary=run_batch(tools,max_jobs=max_jobs,synchronize=False)
        with tools._scope() as s:
            has_pending=not initialized or bool(runs.pending(s)) or requeued>=100
            if not runs.finish(s,generation,summary=summary,pending=has_pending,failed=bool(summary['failed'])):
                raise ValueError('refresh run lease expired')
            state=runs.status(s)
        return {'status':state['status'],**summary}
    except Exception:
        try:
            with tools._scope() as s:runs.finish(s,generation,summary=summary,pending=True,failed=True)
        except Exception:pass
        raise ValueError('search refresh run failed') from None
