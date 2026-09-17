#!/usr/bin/env python3
"""Check the dedicated dev account in the real browser; never print credentials."""
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEV_URL = 'https://d31zgpff2091oh.cloudfront.net/'


def main():
    try:
        path = Path(os.environ.get('COLAB_DEV_TEST_CREDENTIALS_FILE', '~/.config/colab-platform/dev-test-admin.json')).expanduser()
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.getuid():
            raise ValueError('credential permissions')
        credentials = json.loads(path.read_text())
        if credentials.get('email') != 'test_admin@colab.invalid' or not isinstance(credentials.get('password'), str) or not credentials['password']:
            raise ValueError('credential format')
        session = os.environ.get('COLAB_DEV_BROWSER_SESSION', 'dev-test-admin')
        profile = os.environ.get('COLAB_DEV_BROWSER_AUTH_PROFILE', 'dev-test-admin')
        if not all(re.fullmatch(r'[A-Za-z0-9_-]+', value) for value in (session, profile)):
            raise ValueError('browser names')
        base = [sys.executable, str(ROOT / 'scripts/agent-bridge.py'), 'run-tool', 'browser', '--', '--session', session]

        def browser(*args, password=None):
            result = subprocess.run(base + list(args), input=password, text=True,
                                    capture_output=True, cwd=ROOT, timeout=60)
            if result.returncode:
                raise RuntimeError('browser command')
            return result.stdout

        def check_origin():
            url = urlsplit(browser('get', 'url').strip())
            expected = urlsplit(DEV_URL)
            if (url.scheme, url.netloc) != (expected.scheme, expected.netloc):
                raise ValueError('origin')

        browser('open', DEV_URL)
        check_origin()
        snapshot = browser('snapshot')
        if re.search(r'button "로그아웃"', snapshot):
            browser('find', 'role', 'button', 'click', '--name', '로그아웃', '--exact')
            browser('wait', '--text', '로그인')
            snapshot = browser('snapshot')
        check_origin()
        if not all(text in snapshot for text in ('heading "로그인"', 'textbox "이메일"', 'textbox "비밀번호"')):
            raise ValueError('login form')

        browser('auth', 'save', profile, '--url', DEV_URL, '--username', credentials['email'],
                '--password-stdin', password=credentials['password'] + '\n')
        browser('auth', 'login', profile)
        # auth login's success message only means the form was submitted.
        browser('wait', '--text', '로그아웃')
        snapshot = browser('snapshot')
        check_origin()
        header = browser('snapshot', '-s', 'header')
        if not re.search(r'button "로그아웃"', header) or not re.search(r'StaticText "test_admin"(?:\s|$)', header):
            raise ValueError('account UI')
        if any(text in snapshot for text in ('세션 저장소에 연결할 수 없다', '비밀번호 변경', 'heading "로그인"')):
            raise ValueError('login not complete')
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError, subprocess.SubprocessError):
        print('dev-browser-check: 준비 실패 — 보호 자격 또는 실제 dev 로그인 화면을 확인하지 못했습니다.')
        return 78
    print('dev-browser-check: 성공 — dev origin, test_admin 계정, 로그아웃 버튼 확인.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
