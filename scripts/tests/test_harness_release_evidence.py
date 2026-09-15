import copy
import json
import os
import subprocess
import sys
import tempfile
import types
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class ReleaseEvidenceTests(unittest.TestCase):
    def test_handwritten_post_checks_are_not_doctor_execution_evidence(self):
        post = {**self.pre, 'phase':'post', 'finished_at':'2026-09-15T00:01:00+00:00',
                'checks':[{'name':str(i),'exit':0} for i in range(1,16)]}
        with self.assertRaises(self.m.ReleaseEvidenceError): self.m.verify_post(self.pre,post)

    def setUp(self):
        spec = importlib.util.spec_from_file_location('release_evidence', ROOT / 'scripts/harness/release_evidence.py')
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.pre = {'schema': 'colab-release-evidence/1', 'sha': 'a'*40,
                    'environment': 'dev', 'release_id': 'release-1', 'run_id': 'run-1',
                    'pr': {'merged': True, 'merge_commit_sha': 'a'*40, 'base': 'develop', 'number': 1},
                    'ci': {}, 'artifact_root': '/fixture', 'started_at': '2026-09-15T00:00:00+00:00'}

    def test_missing_and_nonmain_fail_before_deploy(self):
        with self.assertRaises(self.m.ReadinessError): self.m.verify_pre({}, ROOT)
        with patch.object(self.m, 'git', side_effect=[0, 1]):
            with self.assertRaises(self.m.ReleaseEvidenceError): self.m.verify_pre(self.pre, ROOT)

    def test_environment_uses_its_source_branch_and_rejects_old_pr_base(self):
        for environment, branch in [('dev','develop'), ('prod','product')]:
            pre = copy.deepcopy(self.pre)
            pre['environment'] = environment
            pre['pr']['base'] = branch
            with self.subTest(environment=environment), patch.object(self.m,'git',return_value=0) as git:
                with self.assertRaisesRegex(self.m.ReleaseEvidenceError, 'required-gates'):
                    self.m.verify_pre(pre, ROOT)
                self.assertEqual(git.call_args_list[0].args[-1], 'refs/remotes/origin/'+branch)
                pre['pr']['base'] = 'main'
                with self.assertRaisesRegex(self.m.ReleaseEvidenceError,'merged PR'):
                    self.m.verify_pre(pre, ROOT)

    def test_post_requires_same_identity_and_exact_doctor_rows(self):
        post = {**self.pre, 'phase': 'post', 'finished_at': '2026-09-15T00:01:00+00:00',
                'checks': [{'name': str(i), 'exit': 0} for i in range(1,16)]}
        with self.assertRaises(self.m.ReleaseEvidenceError): self.m.verify_post(self.pre, post)
        for key, value in [('sha', 'b'*40), ('run_id', 'old'), ('environment', 'staging'),
                           ('release_id', 'old'), ('checks', post['checks'][:-1]),
                           ('finished_at', self.pre['started_at'])]:
            bad = copy.deepcopy(post); bad[key] = value
            with self.subTest(key=key), self.assertRaises(self.m.ReleaseEvidenceError):
                self.m.verify_post(self.pre, bad)

    def test_staging_uses_existing_two_checks_not_doctor(self):
        self.pre['environment'] = 'staging'
        post = {**self.pre, 'phase': 'post', 'finished_at': '2026-09-15T00:01:00+00:00',
                'checks': [{'name': name, 'exit': 0} for name in ['verify-deploy', 'verify-chains']]}
        self.m.verify_post(self.pre, post)

    def test_pre_consumes_real_registry_bundle_and_rejects_missing_artifact(self):
        spec = importlib.util.spec_from_file_location('release_test_ci', ROOT / 'scripts/harness/verify_evidence.py')
        ci = importlib.util.module_from_spec(spec); spec.loader.exec_module(ci)
        registry = ci.load_registry()
        filters = {key: 'false' for item in registry.values() for key in item['filters']}
        needs = {item['job']: {'result': 'skipped'} for item in registry.values()}
        needs.update({'changes': {'result': 'success'}, 'repo-hygiene': {'result': 'success'}, 'product-safety': {'result': 'success'}})
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            for producer in ('repo-hygiene','product-safety'):
                for name, check in registry[producer]['checks'].items():
                    folder = bundle / name; folder.mkdir()
                    record = {'schema': 'colab-ci-check/1', 'producer': producer, 'check': name,
                              'run_id': '1', 'run_attempt': 1, 'commit': 'a'*40, 'tree': 'b'*40,
                              'kind': check['kind'], 'command': check['command'], 'exit': 0,
                              'counts': {'green': 1, 'red_judgment': 0, 'red_readiness': 0}}
                    (folder/'evidence.json').write_text(json.dumps(record))
                    (folder/'gate-summary.json').write_text(json.dumps({'schema': 'colab-gate-summary/1',
                        'commit': 'a'*40, 'tree': 'b'*40, 'counts': {'green': len(check['gates']), 'red_판정': 0, 'red_준비': 0},
                        'gates': [{'name': g, 'status': 'green', 'state': 'green', 'exit': 0} for g in check['gates']]}))
            event = {'after': 'a'*40, 'before': 'c'*40}
            jobs = ci.collect_ci('1', 1, 'a'*40, 'b'*40, registry, needs, filters, bundle)
            evidence = ci.build_ci_evidence('1', 1, 'a'*40, 'b'*40, ci.event_shas('push', event, 'a'*40), jobs)
            evidence['inputs'] = {'event_name': 'push', 'event': event, 'needs': needs, 'filters': filters}
            self.pre.update(ci=evidence, artifact_root=str(bundle))
            with patch.object(self.m, 'git', return_value=0):
                self.m.verify_pre(self.pre, ROOT)
                next(bundle.rglob('evidence.json')).unlink()
                with self.assertRaises(self.m.ReadinessError): self.m.verify_pre(self.pre, ROOT)

    def test_shell_entries_fail_before_credentials_or_network_without_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'colab-v2-dev.sha').write_text('a'*40)
            env = dict(os.environ, COLAB_RELEASE_DRY_RUN='1')
            for key in ('COLAB_RELEASE_PRE_EVIDENCE', 'COLAB_RELEASE_POST_EVIDENCE', 'COLAB_DEV_SSH', 'COLAB_DEV_KEY_FILE'):
                env.pop(key, None)
            for script, args in [('ship.sh', [directory]), ('tag-release.sh', ['dev', directory])]:
                result = subprocess.run(['bash', str(ROOT/'infra/dev'/script), *args], cwd=ROOT, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 78, result.stderr)


class DoctorEmitterTests(unittest.TestCase):
    def test_source_rejects_unlisted_old_file(self):
        (self.source/'old-migration.py').write_text('stale')
        with self.assertRaises(ValueError):self.m.source_snapshot(self.source,self.pre['sha'])

    def test_regular_probe_does_not_require_release_artifacts(self):
        probe=self.root/'deploy-verification.sh'
        probe.write_bytes((ROOT/'infra/ops/probes/deploy-verification.sh').read_bytes())
        docker=self.root/'docker';docker.write_text('#!/bin/sh\nexit 0\n');docker.chmod(0o755)
        runner=self.root/'docker-run.sh';runner.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n');runner.chmod(0o755)
        env=dict(os.environ,PATH=str(self.root)+':'+os.environ['PATH'],COLAB_DEV_STATE=str(self.state),COLAB_DEV_REPO=str(self.source))
        env.pop('COLAB_RELEASE_ARTIFACT_DIR',None);env.pop('COLAB_RELEASE_COLLECT',None)
        normal=subprocess.run(['bash',str(probe)],env=env,capture_output=True,text=True)
        self.assertEqual(normal.returncode,0,normal.stderr);self.assertIn('ops/deploy_doctor.py',normal.stdout)
        env['COLAB_RELEASE_COLLECT']='1'
        collect=subprocess.run(['bash',str(probe)],env=env,capture_output=True,text=True)
        self.assertEqual(collect.returncode,78)

    def setUp(self):
        spec=importlib.util.spec_from_file_location('doctor_emitter',ROOT/'services/core-api/ops/deploy_doctor_evidence.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.state=self.root/'state';self.state.mkdir();self.source=self.root/'source';self.source.mkdir()
        self.out=self.root/'artifacts';self.out.mkdir(mode=0o700)
        self.pre={'schema':'colab-release-evidence/1','sha':'a'*40,'environment':'dev','release_id':'release-1','run_id':'run-1','started_at':'2000-01-01T00:00:00+00:00'}
        self.pre_path=self.state/'RELEASE_PRE.json';self.pre_path.write_text(json.dumps(self.pre))
        for name,content in {'CURRENT_SHA':'a'*12,'CURRENT_FULL_SHA':'a'*40,'MAIN_SHA':'source_ref=develop source_sha='+('b'*40)+' candidate='+('a'*12)+' ancestor=yes'}.items():(self.state/name).write_text(content)
        lines=['# source_sha='+'a'*12,'# source_full_sha='+'a'*40]
        for name in ('deploy_doctor.py','deploy_doctor_evidence.py','s3_doctor.py'):
            p=self.source/'services/core-api/ops'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture source')
            lines.append(self.m.sha256(p.read_bytes())+'  ./'+str(p.relative_to(self.source)))
        (self.source/'OPS_SOURCE_MANIFEST').write_text('\n'.join(lines)+'\n')
        self.ctx=types.SimpleNamespace(env='dev',state_dir=str(self.state),allow_skip=False)
        self.calls=0
        def run(ctx,report=None):
            self.calls+=1;report.items=[(mark,'fixture','✓') for mark in '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮']
            print('postgresql://user:private-password@host/db https://host/file?X-Amz-Signature=private-signature token=private-token')
            print('Authorization: Bearer private-bearer',file=sys.stderr)
            return 0
        self.doctor=types.SimpleNamespace(DeployReport=lambda:types.SimpleNamespace(items=[]),run=run)

    def emit(self):
        return self.m.emit(self.ctx,self.pre_path,self.out/'post.json',self.source,doctor=self.doctor,test_injection=True)

    def test_one_run_emits_redacted_log_bound_evidence(self):
        self.assertEqual(self.emit(),0);self.assertEqual(self.calls,1)
        post=json.loads((self.out/'post.json').read_text())
        self.m.verify_emitted(self.pre,post,self.out)
        log=(self.out/'doctor.log').read_text()
        for secret in ('private-password','private-signature','private-token','private-bearer'):self.assertNotIn(secret,log)
        self.assertEqual((self.out/'doctor.log').stat().st_mode & 0o777,0o600)
        (self.out/'doctor.log').write_text('changed')
        with self.assertRaises(ValueError):self.m.verify_emitted(self.pre,post,self.out)

    def test_old_or_wrong_source_ancestry_is_rejected(self):
        for record in (
            'main='+('b'*12)+' candidate='+('a'*12)+' ancestor=yes',
            'source_ref=product source_sha='+('b'*40)+' candidate='+('a'*12)+' ancestor=yes',
        ):
            with self.subTest(record=record):
                (self.state/'MAIN_SHA').write_text(record)
                self.assertEqual(self.emit(),78)
                self.assertEqual(self.calls,0)

    def test_preexisting_output_and_missing_source_fail_before_doctor(self):
        (self.out/'post.json').write_text('{}')
        self.assertEqual(self.emit(),78);self.assertEqual(self.calls,0)
        (self.out/'post.json').unlink();(self.source/'services/core-api/ops/deploy_doctor.py').unlink()
        self.assertEqual(self.emit(),78);self.assertEqual(self.calls,0)

    def test_state_change_during_execution_cannot_emit_green(self):
        original=self.doctor.run
        def change(ctx,report=None):
            result=original(ctx,report);(self.state/'CURRENT_FULL_SHA').write_text('b'*40);return result
        self.doctor.run=change
        self.assertEqual(self.emit(),1)

    def test_post_rejects_missing_duplicate_skip_and_wrong_identity(self):
        self.assertEqual(self.emit(),0)
        post=json.loads((self.out/'post.json').read_text())
        changes=[('rows',post['rows'][:-1]),('rows',[post['rows'][0]]*15),
                 ('rows',[dict(row,status='─') for row in post['rows']]),
                 ('sha','b'*40),('run_id','other'),('environment','prod'),('allow_skip',True)]
        for key,value in changes:
            bad=copy.deepcopy(post);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.m.verify_emitted(self.pre,bad,self.out)

    def test_quoted_secrets_and_alternate_executable_rejected(self):
        for text in ('{"password": "secret-value"}', "{'token': 'secret-value'}", '{"AWS_SECRET_ACCESS_KEY": "secret-value"}'):
            self.assertNotIn('secret-value',self.m.redact(text))
        self.doctor.__file__=str(ROOT/'services/core-api/ops/deploy_doctor.py')
        self.assertEqual(self.m.emit(self.ctx,self.pre_path,self.out/'post.json',self.source,doctor=self.doctor),1)
        self.assertEqual(self.calls,0)

    def test_equal_but_invalid_snapshots_rejected(self):
        self.assertEqual(self.emit(),0);post=json.loads((self.out/'post.json').read_text())
        for missing in (True,False):
            bad=copy.deepcopy(post)
            for name in ('before','after'):
                if missing:bad[name].pop('source')
                else:bad[name]['state']['MAIN_SHA']='main='+('b'*12)+' candidate='+('a'*12)+' ancestor=bypass'
            with self.assertRaises(ValueError):self.m.verify_emitted(self.pre,bad,self.out)


if __name__ == '__main__': unittest.main()
