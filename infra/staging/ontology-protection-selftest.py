#!/usr/bin/env python3
"""Real PostgreSQL deletion attempts, exclusively in a fresh no-port tmpfs container.

--baseline deliberately omits installation to demonstrate that the oracle catches
an unprotected deployment. It never selects an existing container or database.
"""
from pathlib import Path
import os
import subprocess
import sys
import time
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
NAME = 'colab_ontology_guard_test_' + uuid.uuid4().hex[:12]
TABLES = ('d9_method_term', 'd9_topic_synonym', 'd9_place_alias', 'd9_concept', 'd9_concept_edge')
BASELINE = sys.argv[1:] == ['--baseline']
if sys.argv[1:] not in ([], ['--baseline']):
    raise SystemExit('usage: ontology-protection-selftest.py [--baseline]')

def run(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, **kw)

def sql(statement, role='postgres', db='colab_ai'):
    return run(['docker', 'exec', '-i', NAME, 'psql', '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-U', role, '-d', db], input=statement)

def require(result, action):
    if result.returncode:
        raise RuntimeError(action + ': ' + result.stderr[-1200:])
    return result.stdout

failed = 0
checked = 0

def check(condition, label):
    global failed, checked
    checked += 1
    print(('PASS ' if condition else 'FAIL ') + label, flush=True)
    failed += not condition

try:
    restore=run(['bash', str(ROOT/'infra/staging/restore/restore-db.sh'), '--db','colab_ai','--owner','postgres','--dump','/nonexistent','--yes-drop-schema'])
    check(restore.returncode != 0 and 'ONTOLOGY_PROTECTED' in restore.stderr, 'destructive restore refused even with confirmation')
    with tempfile.TemporaryDirectory() as temp:
        fake=Path(temp)/'docker'
        marker=Path(temp)/'dangerous-call'
        fake.write_text('#!/bin/sh\nif [ "$1" = inspect ]; then echo bind; exit 0; fi\ntouch "'+str(marker)+'"\nexit 1\n')
        fake.chmod(0o755)
        fixture=run(['bash',str(ROOT/'services/ai-service/tests/fixtures/setup-db.sh')], env=dict(os.environ, PATH=temp+os.pathsep+os.environ['PATH'],CONTAINER='persistent-test-double'))
        check(fixture.returncode==65 and not marker.exists(), 'test setup refuses persistent mount before SQL execution')
    require(run(['docker', 'run', '--rm', '-d', '--name', NAME,
                 '--tmpfs', '/var/lib/postgresql/data', '-e', 'PGDATA=/var/lib/postgresql/data/pgdata',
                 '-e', 'POSTGRES_HOST_AUTH_METHOD=trust', 'postgres:16-alpine']), 'start disposable database')
    for _ in range(60):
        if run(['docker', 'exec', NAME, 'pg_isready', '-U', 'postgres']).returncode == 0:
            break
        time.sleep(0.5)
    else:
        raise RuntimeError('disposable postgres not ready')
    env = dict(os.environ, PG_CONTAINER=NAME, COLAB_OWNER_PASSWORD='test-owner', COLAB_APP_PASSWORD='test-app')
    env.pop('COLAB_PG_MASTER_URL_FILE', None)
    if BASELINE:
        require(sql('CREATE ROLE colab_owner LOGIN; CREATE DATABASE colab_ai OWNER colab_owner;',db='postgres'), 'unprotected baseline')
        require(sql('ALTER SCHEMA public OWNER TO colab_owner;'), 'baseline schema')
    else:
        require(run(['bash', str(ROOT/'infra/staging/db-bootstrap.sh'), 'roles'], env=env), 'bootstrap roles')
    for path in ['db/ai/schema.sql', 'db/ai/seed/k2_ontology_seed.sql', 'db/ai/seed/k2b_concept_graph_seed.sql']:
        require(sql((ROOT/path).read_text(), 'colab_owner'), path)
    require(sql('CREATE ROLE colab_ai_app LOGIN; GRANT CONNECT ON DATABASE colab_ai TO colab_ai_app; GRANT USAGE ON SCHEMA public TO colab_ai_app; GRANT SELECT ON ALL TABLES IN SCHEMA public TO colab_ai_app;'), 'app grants')
    if not BASELINE:
        for _ in range(2):
            require(run(['bash', str(ROOT/'infra/staging/db-bootstrap.sh'), 'protect-ontology'], env=env), 'install protection')
        require(run(['bash', str(ROOT/'infra/staging/db-bootstrap.sh'), 'roles'], env=env), 'repeat deployment bootstrap')
        verifier=['bash',str(ROOT/'infra/staging/verify/verify-ontology.sh')]
        verify_env=dict(os.environ,COLAB_STAGING_PG_CONTAINER=NAME)
        check(run(verifier,env=verify_env).returncode==0,'read-only verifier accepts installed protection')
        require(sql('GRANT DELETE ON d9_method_term TO colab_owner;'),'tamper disposable policy')
        check(run(verifier,env=verify_env).returncode==1,'verifier rejects a removed protection')
        require(run(['bash',str(ROOT/'infra/staging/db-bootstrap.sh'),'protect-ontology'],env=env),'repair disposable policy')
        require(sql('CREATE ROLE hidden_admin SUPERUSER; GRANT hidden_admin TO colab_owner;'),'inject disposable role escalation')
        check(run(verifier,env=verify_env).returncode==1,'verifier rejects inherited admin escalation')
        require(sql('REVOKE hidden_admin FROM colab_owner;'),'remove disposable escalation')
        require(sql('CREATE SCHEMA moved; ALTER TABLE d9_method_term SET SCHEMA moved; CREATE VIEW public.d9_method_term AS SELECT * FROM moved.d9_method_term;'),'inject view substitute')
        check(run(verifier,env=verify_env).returncode==1,'verifier rejects view replacing protected table')
        require(sql('DROP VIEW public.d9_method_term; ALTER TABLE moved.d9_method_term SET SCHEMA public;'),'restore disposable table')
        remote_env=dict(env,COLAB_PG_MASTER_URL_FILE='/nonexistent-remote-secret')
        r=run(['bash',str(ROOT/'infra/staging/db-bootstrap.sh'),'protect-ontology'],env=remote_env)
        check(r.returncode==78,'ST installer refuses unsupported AWS installation before connecting')


    for role in ('colab_ai_app', 'colab_owner'):
        for table in TABLES:
            for statement in (f'DELETE FROM public.{table}', f'TRUNCATE public.{table} CASCADE',
                              f'DROP TABLE public.{table} CASCADE', f'ALTER TABLE public.{table} DISABLE TRIGGER ALL'):
                r = sql('BEGIN; '+statement+'; ROLLBACK;', role)
                check(r.returncode != 0 and ('permission denied' in r.stderr or 'must be owner' in r.stderr), role+' rejects '+statement)
        r = sql('BEGIN; DROP SCHEMA public CASCADE; ROLLBACK;', role)
        check(r.returncode != 0 and ('permission denied' in r.stderr or 'must be owner' in r.stderr), role+' rejects DROP SCHEMA')
        check(sql('SELECT count(*) FROM d9_concept;', role).stdout.strip() == '49', role+' reads intact concepts')
        r=sql('SET ROLE colab_ontology_guardian;',role)
        check(r.returncode != 0, role+' cannot become guardian')
    require(sql("BEGIN; INSERT INTO d9_method_term(term,source_note) VALUES ('guard-test','test'); UPDATE d9_method_term SET source_note='updated' WHERE term='guard-test'; ROLLBACK;", 'colab_owner'), 'legitimate seed insert/update')
    check(True,'seed insert/update allowed')
    require(sql("BEGIN; INSERT INTO alembic_version_ai VALUES ('guard-test'); DELETE FROM alembic_version_ai WHERE version_num='guard-test'; ROLLBACK;",'colab_owner'), 'migration stamp stays writable')
    check(True,'migration stamp writable')
    for role in ('colab_ai_app','colab_owner'):
        r=sql('DROP DATABASE colab_ai;',role,db='postgres')
        check(r.returncode != 0 and ('permission denied' in r.stderr or 'must be owner' in r.stderr),role+' rejects DROP DATABASE')
    print(f'ontology-protection: {checked} checks, {failed} failures', flush=True)
    raise SystemExit(1 if failed else 0)
except RuntimeError as error:
    print('PREPARATION FAILURE: '+str(error),file=sys.stderr)
    raise SystemExit(78)
finally:
    run(['docker','rm','-f',NAME])
