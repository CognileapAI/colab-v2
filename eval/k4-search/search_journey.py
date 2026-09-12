"""Real local core/frontend journey; HTTP interpreter is an explicit test double.

Run this file as a process to provide interpretation on loopback port 43174.
Use scripts/e2e-login.sh --journey this-file --ai-base-url http://127.0.0.1:43174.
All database rows come from the disposable core fixture, not production data.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


def run(command, args, session):
    if not args.artifacts:
        raise RuntimeError('Persistent artifact directory required')
    args.artifacts.mkdir(parents=True, exist_ok=True)
    command('open', 'http://127.0.0.1:43173/lab')
    command('wait', '[aria-label="검색 질문"]')
    command('fill', '[aria-label="검색 질문"]', '강우 결측률 0% 검증용 자료')
    command('press', 'Enter')
    command('wait', '[data-testid="search-hit"]')
    text = command('get', 'text', 'body')
    assert '충족 여부를 확인하지 못했어요' in text, 'New server rationale not rendered'
    assert '파일 역할' in text and '품질' in text
    assert 'A 강우 원자료' in text
    assert 'B ' not in text, 'Other lab result leaked'
    command('screenshot', str((args.artifacts / 'search.png').resolve()))
    (args.artifacts / 'search.txt').write_text(text)
    command('click', '.hit:not(.is-locked) [data-testid="hit-name"]')
    actual_url = command('get', 'url').strip()
    assert actual_url.endswith('/datasets/0000000000000000000000DSA1'), actual_url
    command('reload')
    command('wait', '--text', 'A 강우 원자료')
    detail = command('get', 'text', 'body')
    assert 'A 강우 원자료' in detail
    (args.artifacts / 'detail.txt').write_text(detail)
    (args.artifacts / 'result.json').write_text(json.dumps(dict(
        passed=True, environment='disposable fixture DB, real local core + frontend',
        interpreter='HTTP test double; no LLM or live AI service evaluation',
        checks=['login', 'search input', 'rationale', 'lab boundary', 'detail navigation', 'reload']),
        ensure_ascii=False, indent=2))
    command('open', 'http://127.0.0.1:43173/lab')
    command('wait', '--text', '로그아웃')
    print('PASS: local search input -> scoped SQL results -> condition rationale -> detail -> reload')


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        query = body.get('query', '')
        response = dict(scope=body['scope'], isDataQuery=True, degraded=False,
                        interpretation=dict(terms=['강우'] if '강우' in query else [query],
                                            topic=None, source='literal'),
                        results=dict(items=[], totalCount=0, nextCursor=None))
        raw = json.dumps(response, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 43174), Handler).serve_forever()
