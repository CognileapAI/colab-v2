import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'dev-browser-check.py'


class BrowserCheckTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('dev_browser_check', PATH)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file = Path(self.tmp.name) / 'credentials.json'
        self.file.write_text(json.dumps({'email': 'test_admin@colab.invalid', 'password': 'SECRET-SENTINEL'}))
        self.file.chmod(0o600)
        self.env = patch.dict(os.environ, {'COLAB_DEV_TEST_CREDENTIALS_FILE': str(self.file)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_check(self, snapshot='- StaticText "test_admin"\n- button "로그아웃" [ref=e2]', url='https://d31zgpff2091oh.cloudfront.net/lab', failure=False, already=False):
        calls = []
        logged_in = already
        def run(argv, **kw):
            nonlocal logged_in
            calls.append((argv, kw))
            if failure:
                return subprocess.CompletedProcess(argv, 1, 'SECRET-SENTINEL', 'SECRET-SENTINEL')
            if 'click' in argv:
                logged_in = False
            if 'login' in argv:
                logged_in = True
            current = snapshot if logged_in else '- heading "로그인"\n- textbox "이메일"\n- textbox "비밀번호"'
            output = current if 'snapshot' in argv else url if argv[-2:] == ['get', 'url'] else 'Logged in'
            return subprocess.CompletedProcess(argv, 0, output, '')
        out = io.StringIO()
        with patch.object(self.mod.subprocess, 'run', side_effect=run), patch('sys.stdout', out):
            rc = self.mod.main()
        self.assertNotIn('SECRET-SENTINEL', out.getvalue())
        for argv, _ in calls:
            self.assertNotIn('SECRET-SENTINEL', argv)
            self.assertIn('agent-bridge.py', ' '.join(argv))
        return rc, calls

    def test_success_password_stdin_only(self):
        rc, calls = self.run_check()
        self.assertEqual(rc, 0)
        saves = [(a,k) for a,k in calls if 'save' in a]
        self.assertEqual(len(saves), 1)
        self.assertEqual(saves[0][1]['input'], 'SECRET-SENTINEL\n')
        self.assertIn('--password-stdin', saves[0][0])

    def test_login_message_alone_rejected(self):
        self.assertEqual(self.run_check(snapshot='Logged in')[0], 78)

    def test_wrong_identity_rejected(self):
        self.assertEqual(self.run_check(snapshot='- StaticText "other"\n- button "로그아웃"')[0], 78)

    def test_wrong_origin_rejected(self):
        self.assertEqual(self.run_check(url='https://www.colab-hydro.com/lab')[0], 78)

    def test_error_and_password_change_rejected(self):
        for text in ('세션 저장소에 연결할 수 없다.', '비밀번호 변경'):
            with self.subTest(text=text):
                self.assertEqual(self.run_check(snapshot='- StaticText "test_admin"\n- button "로그아웃"\n'+text)[0],78)

    def test_tool_failure_sanitized(self):
        self.assertEqual(self.run_check(failure=True)[0],78)

    def test_unprotected_or_missing_file_no_browser(self):
        self.file.chmod(0o644)
        rc,calls=self.run_check()
        self.assertEqual((rc,len(calls)),(78,0))
        self.file.unlink()
        rc,calls=self.run_check()
        self.assertEqual((rc,len(calls)),(78,0))

    def test_empty_password_no_browser(self):
        self.file.write_text('{"email":"test_admin@colab.invalid","password":""}')
        rc,calls=self.run_check()
        self.assertEqual((rc,len(calls)),(78,0))

    def test_wrong_email_no_browser(self):
        self.file.write_text('{"email":"other@colab.invalid","password":"SECRET-SENTINEL"}')
        rc,calls=self.run_check()
        self.assertEqual((rc,len(calls)),(78,0))

    def test_existing_session_logs_out_before_login(self):
        rc,calls=self.run_check(already=True)
        self.assertEqual(rc,0)
        actions=[a for a,k in calls]
        logout=next(i for i,a in enumerate(actions) if 'click' in a)
        login=next(i for i,a in enumerate(actions) if 'login' in a)
        self.assertLess(logout,login)

    def test_wrong_origin_never_enters_credentials(self):
        rc,calls=self.run_check(url='https://other.invalid/')
        self.assertEqual(rc,78)
        self.assertFalse(any('login' in a or 'save' in a for a,k in calls))
