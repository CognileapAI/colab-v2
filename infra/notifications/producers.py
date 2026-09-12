from __future__ import annotations
import datetime as dt
from .events import make_event

def release_result(release_id:str,env:str,phase:str,exit_code:int,version:str,at:dt.datetime)->dict:
    if env not in {"dev","staging"}:raise ValueError("unknown release environment")
    kind="deploy.succeeded" if exit_code==0 else ("deploy.verification_failed" if phase=="verify" else "deploy.failed")
    severity="info" if exit_code==0 else "critical"
    return make_event(source="release",environment=env,severity=severity,channel="development",occurred_at=at,
                      event_id=f"release:{release_id}:{env}:{phase}:{exit_code}",
                      payload={"kind":kind,"release_id":release_id,"phase":phase,"exit_code":exit_code,"version":version})

def observe(state:dict,passed:bool,env:str,target:str,at:dt.datetime)->tuple[dict,list[dict]]:
    if env not in {"dev","staging"}:raise ValueError("unknown probe environment")
    state=dict(state);state.setdefault("failure_count",0);state.setdefault("active",False);state.setdefault("incident",0)
    events=[]
    if passed:
        state["failure_count"]=0
        if state["active"]:
            state["active"]=False
            events.append(make_event(source="probe",environment=env,severity="info",channel="development",occurred_at=at,
                event_id=f"probe:{env}:{target}:{state['incident']}:recovered",payload={"kind":"probe.recovered","target":target,"incident":state["incident"]}))
    else:
        state["failure_count"]+=1
        if state["failure_count"]>=2 and not state["active"]:
            state["active"]=True;state["incident"]+=1
            events.append(make_event(source="probe",environment=env,severity="critical",channel="development",occurred_at=at,
                event_id=f"probe:{env}:{target}:{state['incident']}:failed",payload={"kind":"probe.failed","target":target,"incident":state["incident"]}))
    state["observed_at"]=at.isoformat();return state,events


def heartbeat(state:dict, observed_at:dt.datetime, now:dt.datetime, env:str, target:str):
    if observed_at.tzinfo is None or now.tzinfo is None: raise ValueError("aware timestamp required")
    state=dict(state);events=[]
    stale=now-observed_at >= dt.timedelta(minutes=15)
    if stale != bool(state.get("unobservable",False)):
        state["unobservable"]=stale
        state["incident"]=state.get("incident",0)+(1 if stale else 0)
        events.append(make_event(source="probe-heartbeat",environment=env,severity="error" if stale else "info",channel="development",occurred_at=now,
            event_id=f"heartbeat:{env}:{target}:{state['incident']}:{'missing' if stale else 'resumed'}",
            payload={"kind":"probe.unobservable" if stale else "probe.recovered","target":target,"status":"15분 이상 관측 없음" if stale else "관측 재개 (서비스 복구 판정과 별개)"}))
    return state,events
