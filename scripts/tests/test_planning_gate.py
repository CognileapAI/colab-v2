"""원본을 복사하지 않고 기획 검사기의 실패 판정을 검증한다."""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("freshness", ROOT / "dev-package/tools/check-package-freshness.py")
freshness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freshness)


class PlanningGateTests(unittest.TestCase):
    def test_new_seam_citations_resolve_full_urls_not_legacy_tokens(self):
        spec = importlib.util.spec_from_file_location('seam_test', ROOT/'gates/tools/seam_consistency.py')
        seam = importlib.util.module_from_spec(spec); spec.loader.exec_module(seam)
        state = {'schema':'colab-work-state/1','issues':[{'id':'X','number':123,'state':'open','dependencies':[],
            'product': {'title':'X','owner':'test','status':'open','stage':'stage1','entry_conditions':[],
                        'completion_def_ref':'plan.md','evidence_ref':'','deadline':None,'required_gates':['fixture']}}]}
        path = self.root/'state.json'; path.write_text(json.dumps(state))
        with patch.dict(os.environ, {'COLAB_WORK_STATE_MODE':'work-state','COLAB_WORK_STATE_INPUT':str(path)}):
            valid = seam.citation_checker()
            self.assertTrue(valid('https://github.com/CognileapAI/colab-v2/issues/123'))
            for text in ('〈61〉 사용자 승인', '#123', 'https://github.com/CognileapAI/colab-v2/issues/999',
                         'https://github.com/other/repo/issues/123','https://github.com/CognileapAI/colab-v2/pull/123',
                         'docs/decisions/9999-missing.md'):
                self.assertFalse(valid(text),text)

    def test_new_applied_mode_rejects_unproved_merged(self):
        home = self.root/'home'; (home/'10_적용전').mkdir(parents=True)
        (home/'30_적용완료/R-X').mkdir(parents=True)
        (home/'10_적용전/source.md').write_text('same')
        (home/'30_적용완료/R-X/source.md').write_text('same')
        manifest = self.root/'applied.yaml'
        manifest.write_text('version: 1\nitems:\n- id: X\n  source: 10_적용전/source.md\n  status: merged\n  applied_round: R-X\n  applied_date: 2026-09-15\n')
        with patch.dict(os.environ, {'COLAB_WORK_STATE_MODE':'work-state'}, clear=True):
            rows, errors = freshness.check_applied(str(home), str(manifest))
            self.assertTrue(errors)

    def test_seam_ci_requires_fixed_event_base_not_head(self):
        env = dict(os.environ, CI='true'); env.pop('COLAB_SC_EVENT_BASE_SHA',None); env.pop('COLAB_SC_BASELINE',None)
        command = [sys.executable,str(ROOT/'gates/tools/seam_consistency.py'),'--check','citation']
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode,78,result.stdout+result.stderr)
        env['COLAB_SC_EVENT_BASE_SHA'] = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        self.assertEqual(subprocess.run(command,cwd=ROOT,env=env,capture_output=True).returncode,1)
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        epic = self.root / "에픽/E-00_fixture"
        (epic / "documents").mkdir(parents=True)
        (epic / "package").mkdir()
        self.source = epic / "documents/Policy_fixture.md"
        self.html = epic / "package/index.html"
        self.source.write_text("version: 1\n정책 원본\n", encoding="utf-8")
        self.html.write_text('<script type="text/markdown" id="md-policy">\nversion: 1\n정책 원본\n</script>', encoding="utf-8")

    def test_matching_source(self):
        rows, errors = freshness.check(str(self.root))
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][3], "MATCH")

    def test_tampered_embedded_text(self):
        self.html.write_text(self.html.read_text(encoding="utf-8").replace("정책 원본", "변조"), encoding="utf-8")
        rows, errors = freshness.check(str(self.root))
        self.assertTrue(errors)
        self.assertEqual(rows[0][3], "DIFFER")

    def test_missing_source_and_empty_root(self):
        self.source.unlink()
        self.assertTrue(freshness.check(str(self.root))[1])
        self.assertTrue(freshness.check(str(self.root / "missing"))[1])

    def test_read_failure_is_diagnosed(self):
        with patch.object(freshness, "read", side_effect=freshness.Unreadable("fixture")):
            self.assertIn("읽기 실패", " ".join(freshness.check(str(self.root))[1]))

    def test_applied_manifest_negative_cases(self):
        with contextlib.redirect_stdout(io.StringIO()):
            failures = freshness._selftest_applied(str(self.root))
        self.assertEqual(failures, [])
