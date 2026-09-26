"""실제 브라우저 · 실제 로컬 core-api(이 브랜치) · 실제 frontend(vite) 로 경로 1 조건 패널의 주기 상한 라벨을 본다.

intent `dev-package/intent/2026-09-26-cadence-range-predicate.md` 판정 6 — 패널이 `maxCadenceSeconds`·초 값이 아니라
「주기 1시간 이하」처럼 사람 말로 보여야 한다. 일회용 fixture DB 만 쓴다(운영·dev 무접속). 해석 서비스는
`eval/k4-search/search_journey.py` 의 HTTP 테스트 대역(loopback 43174 · 모델 호출 0)이다.

  E2E_PYTHON=services/core-api/.venv/bin/python E2E_FRONTEND_ROOT=frontend scripts/e2e-login.sh \
    --journey dev-package/reports/evidence-promotion/round-4-2026-09-26/cadence_panel_journey.py \
    --ai-base-url http://127.0.0.1:43174 --artifacts dev-package/reports/evidence-promotion/round-4-2026-09-26/browser
"""
import json
import urllib.parse

BASE = 'http://127.0.0.1:43173'
CASES = [
    ('panel-1h', '시간해상도 1시간 이하, 공간해상도 5 km 이하 한반도 강수자료', '1시간 이하'),
    ('panel-30min', '30분 이내, 공간해상도 5 km 이하 강수자료', '30분 이하'),
]


def run(command, args, session):
    if not args.artifacts:
        raise RuntimeError('artifact directory required')
    args.artifacts.mkdir(parents=True, exist_ok=True)
    seen = []
    for name, query, expected in CASES:
        command('open', BASE + '/datasets/search?q=' + urllib.parse.quote(query))
        command('wait', '[data-testid="search-assessment"]')
        command('wait', '--load', 'networkidle')
        panel = command('get', 'text', '[data-testid="search-assessment"]')
        assert '주기' in panel and expected in panel, panel
        assert 'maxCadenceSeconds' not in panel, panel
        assert '3600' not in panel and '1800' not in panel, panel
        (args.artifacts / f'{name}.txt').write_text(panel, encoding='utf-8')
        command('screenshot', str((args.artifacts / f'{name}.png').resolve()))
        seen.append(dict(name=name, query=query, expected=expected, panelText=panel))
    (args.artifacts / 'result.json').write_text(json.dumps(dict(
        passed=True, environment='disposable fixture DB · real local core-api (this branch) + vite frontend · agent-browser',
        interpreter='HTTP test double (eval/k4-search/search_journey.py) · no model call',
        checks=['login', 'path-1 condition panel shows 주기 + human limit', 'no raw key', 'no raw seconds'],
        cases=seen), ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: path-1 condition panel labels the cadence range in words')
