"""Explicit worker entrypoint; no scheduler is started by the HTTP application.

Run with --once, --loop or --status. Configured login names identify the authorized
scope; the model cannot choose accounts. No credentials/source bodies are logged.
"""
from __future__ import annotations
import argparse
import json
import os
import signal
import threading

from ..kernel.config import load_settings, resolve_env_or_file
from ..kernel.db import make_engine, make_session_factory
from ..kernel.db_credentials import DatabaseCredentialStore
from .ontology_client import OntologyHttpClient
from .search_refresh_tools import SearchRefreshTools
from .search_refresh_runner import run_due
from ..domains import d3_search_runs as runs


def actor(store, login_name):
    credential=store.find(login_name)
    if credential is None or credential.status!='active' or credential.must_change_password:
        raise ValueError('refresh account is unavailable')
    subject=credential.subject
    identity=(subject.account_id,subject.lab_id,credential.session_version)
    def validate(current):
        latest=store.find(login_name)
        if (latest is None or latest.status!='active' or latest.must_change_password
            or (latest.subject.account_id,latest.subject.lab_id,latest.session_version)!=identity
            or (current.account_id,current.lab_id)!=identity[:2]):
            raise ValueError('refresh account authorization changed')
    return subject,validate


def configured_accounts(env):
    raw=resolve_env_or_file(env,'COLAB_SEARCH_REFRESH_ACCOUNTS')
    try:
        names=json.loads(raw or 'null')
        if not isinstance(names,list) or not 1<=len(names)<=100 or any(not isinstance(n,str) or not n.strip() for n in names):
            raise ValueError
        if len(names)!=len(set(names)):raise ValueError
        return names
    except (ValueError,TypeError):
        raise ValueError('configure 1..100 unique refresh login names') from None


def main(argv=None):
    parser=argparse.ArgumentParser(description='Scoped daily search refresh')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--once',action='store_true');mode.add_argument('--loop',action='store_true');mode.add_argument('--status',action='store_true')
    args=parser.parse_args(argv)
    engine=admin_engine=None
    try:
        settings=load_settings();names=configured_accounts(os.environ)
        if not settings.account_admin_database_url or not settings.ai_base_url or not settings.ai_service_token:
            raise ValueError('refresh runtime configuration missing')
        engine=make_engine(settings.database_url);admin_engine=make_engine(settings.account_admin_database_url)
        factory=make_session_factory(engine);store=DatabaseCredentialStore(make_session_factory(admin_engine))
        port=OntologyHttpClient(settings.ai_base_url,token=settings.ai_service_token)
        stop=threading.Event()
        if args.loop:
            for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
        while not stop.is_set():
            failed=False
            for index,name in enumerate(names):
                try:
                    subject,validate=actor(store,name)
                    tools=SearchRefreshTools(factory,subject,port,validate_subject=validate)
                    if args.status:
                        with tools._scope() as s:state=runs.status(s)
                        result={'status':'not_started'} if state is None else {
                            'status':state['status'],'next_run':state['next_run'].isoformat(),
                            'summary':state['summary'],'generation':state['generation']}
                    else:result=run_due(tools)
                    failed=failed or result['status']=='failed'
                except Exception:
                    failed=True;result={'status':'unavailable'}
                print(json.dumps({'account_index':index,**result},ensure_ascii=False),flush=True)
                if stop.is_set():break
            if not args.loop:return 1 if failed else 0
            stop.wait(30)
        return 0
    except Exception:
        print(json.dumps({'status':'configuration_unavailable'}),flush=True)
        return 78
    finally:
        if engine is not None:engine.dispose()
        if admin_engine is not None:admin_engine.dispose()


if __name__=='__main__':raise SystemExit(main())
