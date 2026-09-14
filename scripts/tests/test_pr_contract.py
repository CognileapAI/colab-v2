import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/harness' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class HandoffContractTests(unittest.TestCase):
    def test_external_snapshot_uses_explicit_nondefault_config(self):
        module = load('agreement_snapshot')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); repo = root/'repo'; (repo/'.agents').mkdir(parents=True)
            (repo/'.agents/harness.yaml').write_text(json.dumps({'agreement_snapshot': {'deliverables_dir': 'views'}}))
            draft = root/'external'; (draft/'views').mkdir(parents=True)
            (draft/'plan.md').write_text('scope'); (draft/'views/result.html').write_text('actual view')
            with self.assertRaises(ValueError): module.freeze(draft, '001', 'reference')
            result = module.freeze(draft, '001', 'reference', repo=repo)
            self.assertEqual((result/'views/result.html').read_text(), 'actual view')
            with self.assertRaises(ValueError): module.freeze(draft, '001', 'reference', repo=repo)

    def test_verified_claim_consumes_registry_bundle_in_both_modes(self):
        ci = load('verify_evidence'); module = load('pr_contract'); cfg = module.configuration()
        self.assertEqual(len(cfg['required_sections']), 6)
        body = 'Plan-Ref: approved\nHead-SHA: '+'a'*40+'\n검증 상태: 검증됨\nEvidence-Ref: ci.json\nCI-Ref: local-run-1\n'
        body += ''.join('\n## '+section+'\nConcrete content.\n' for section in cfg['required_sections'])
        registry = ci.load_registry()
        filters = {key: 'false' for item in registry.values() for key in item['filters']}
        needs = {item['job']: {'result': 'skipped'} for item in registry.values()}
        needs.update({'changes': {'result': 'success'}, 'repo-hygiene': {'result': 'success'}})
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            for name, check in registry['repo-hygiene']['checks'].items():
                folder = bundle/name; folder.mkdir()
                record = {'schema': 'colab-ci-check/1', 'producer': 'repo-hygiene', 'check': name,
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
            for mode in ('draft', 'complete'):
                self.assertEqual(module.validate(body, 'a'*40, cfg, mode=mode, evidence=evidence, artifact_root=bundle), [])
            evidence['jobs'] = []
            for mode in ('draft', 'complete'):
                self.assertTrue(module.validate(body, 'a'*40, cfg, mode=mode, evidence=evidence, artifact_root=bundle))

    def test_snapshot_preserves_revision_and_detects_tamper_and_links(self):
        module = load('agreement_snapshot')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'plan.md').write_text('approved scope')
            with self.assertRaises(ValueError): module.freeze(root, '001', 'current conversation: user approval')
            snapshot = module.freeze(root, '001', 'current conversation: user approval', repo=ROOT)
            self.assertEqual(module.verify(snapshot), [])
            with self.assertRaises(ValueError): module.freeze(root, '001', 'same approval')
            (snapshot / 'plan.md').write_text('changed baseline')
            self.assertTrue(module.verify(snapshot))
            (snapshot / 'plan.md').unlink(); (snapshot / 'plan.md').symlink_to(root / 'plan.md')
            self.assertTrue(module.verify(snapshot))
            manifest=json.loads((snapshot/'snapshot.json').read_text())
            manifest['files']={'../plan.md':'bad'}
            (snapshot/'snapshot.json').write_text(json.dumps(manifest))
            self.assertTrue(module.verify(snapshot))
            alias=root/'alias'; alias.symlink_to(root,target_is_directory=True)
            with self.assertRaises(ValueError): module.freeze(alias,'002','prior approval')

    def test_adr_duplicate_and_broken_supersession_are_rejected(self):
        module = load('adr_gate')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-qm','initial'],check=True)
            (root / '.agents').mkdir(); (root / '.agents/harness.yaml').write_text((ROOT / '.agents/harness.yaml').read_text())
            folder = root / 'docs/decisions'; folder.mkdir(parents=True)
            text = '# ADR-0001: Example decision\n- 상태: proposed\n- 날짜: 2026-09-15\n- 대체함: 없음\n- 대체됨: 없음\n'
            cfg=json.loads((ROOT / '.agents/harness.yaml').read_text())['adr_gate']
            text+=''.join('\n## '+section+'\nConcrete rationale.\n' for section in cfg['required_sections'])
            (folder / '0001-example.md').write_text(text)
            self.assertEqual(module.validate(root,all_records=True),[])
            other=folder / '0001-duplicate.md';other.write_text(text)
            self.assertTrue(module.validate(root,all_records=True));other.unlink()
            (folder / '0001-example.md').write_text(text.replace('상태: proposed','상태: superseded').replace('대체됨: 없음','대체됨: [ADR-0002](0002-missing.md)'))
            self.assertTrue(module.validate(root,all_records=True))

    def test_pr_draft_and_completion_require_explicit_sha_and_evidence(self):
        module=load('pr_contract')
        cfg=module.configuration()
        body='Plan-Ref: approved-plan\nHead-SHA: '+'a'*40+'\n검증 상태: 미검증\n'
        body+=''.join('\n## '+section+'\nCurrent scope and evidence limitations.\n' for section in cfg['required_sections'])
        self.assertEqual(module.validate(body,'a'*40,cfg,mode='draft'),[])
        self.assertTrue(module.validate(body,'b'*40,cfg,mode='draft'))
        self.assertTrue(module.validate(body,'a'*40,cfg,mode='complete'))
        self.assertTrue(module.validate(body.replace('## 범위','## 기타'),'a'*40,cfg,mode='draft'))
        evidence={'schema':'colab-ci-evidence/1','commit':'a'*40,'counts':{'green':1,'red_judgment':0,'red_readiness':0,'not_applicable':0},
                  'jobs':[{'name':'check','state':'green'}]}
        completed=body.replace('검증 상태: 미검증','검증 상태: 검증됨')+'\nEvidence-Ref: ci-evidence.json\nCI-Ref: local-ci-evidence\n'
        self.assertTrue(module.validate(completed,'a'*40,cfg,mode='complete',evidence=evidence))
        self.assertTrue(module.validate(completed,'a'*40,cfg,mode='draft',evidence=evidence))
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            raw=json.dumps(evidence).encode(); evidence_path=folder/'ci.json'; evidence_path.write_bytes(raw)
            pr=folder/'pr.md'; pr.write_text(completed+'Evidence-SHA256: '+hashlib.sha256(raw).hexdigest()+'\n')
            command=[sys.executable,str(ROOT/'scripts/harness/pr_contract.py'),str(pr),'--head','a'*40,'--mode','complete','--evidence',str(evidence_path)]
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,1)
            evidence_path.write_bytes(raw+b' ')
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,1)
        evidence['commit']='c'*40
        self.assertTrue(module.validate(completed,'a'*40,cfg,mode='complete',evidence=evidence))


if __name__=='__main__': unittest.main()
