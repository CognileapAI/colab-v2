"""Real browser/core journey on the e2e-login disposable DB; no model call.

Synthetic file evidence is saved through the existing editor, reloaded, and used
by the new research form. Never run against a deployment or production account.
"""
import json
import urllib.parse


def fill_date(command, selector, value):
    # Native date input fill must notify React without updating its value tracker.
    # Only the visible form field changes; persistence still uses the UI button.
    command('eval', '(() => { const el=document.querySelector(' + json.dumps(selector) + ');'
            'Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(el,' + json.dumps(value) + ');'
            'el.dispatchEvent(new Event("input",{bubbles:true}));'
            'el.dispatchEvent(new Event("change",{bubbles:true})); return el.value; })()')
    assert value in command('get','value',selector)


def run(command,args,session):
    if not args.artifacts:
        raise RuntimeError('artifact directory required')
    args.artifacts.mkdir(parents=True,exist_ok=True)
    file_id='00000000000000000000000FA1'
    base='http://127.0.0.1:43173'
    command('open',base+'/datasets/0000000000000000000000DSA1')
    command('wait','[data-testid="dt-files-toggle"]')
    command('wait','--load','networkidle')
    command('focus','[data-testid="dt-files-toggle"]')
    command('press','Enter')
    command('wait','500')
    (args.artifacts/'file-list.txt').write_text(command('snapshot'))
    command('wait','button[aria-label="a1-body.csv 검색 근거"]')
    command('click','button[aria-label="a1-body.csv 검색 근거"]')
    command('wait',f'#se-label-{file_id}')
    for key,value in [('label','합성 LST 연구 검증 사양'),('locator','월평균·지역·기간 절'),
                      ('text','이 일회용 합성 CSV는 서울의 2025년 월평균 지표면 온도를 공간 좌표와 함께 기록한다.'),
                      ('start','2025-01-01'),('end','2025-12-31'),('region','서울'),('variable','지표면 온도')]:
        if key in ('start','end'):
            fill_date(command,f'#se-{key}-{file_id}',value)
        else:
            command('fill',f'#se-{key}-{file_id}',value)
    command('select',f'#se-representation-{file_id}','point_observations')
    command('select',f'#se-format-{file_id}','csv')
    command('get','text','body')
    (args.artifacts/'before-save.txt').write_text(command('snapshot'))
    command('focus','form .de-act button:last-child')
    command('press','Enter')
    command('wait','500')
    (args.artifacts/'after-save.txt').write_text(command('snapshot'))
    command('wait','--text','상태: 확인됨')
    command('reload')
    command('wait','[data-testid="dt-files-toggle"]')
    command('wait','--load','networkidle')
    command('focus','[data-testid="dt-files-toggle"]')
    command('press','Enter')
    command('wait','500')
    (args.artifacts/'file-list.txt').write_text(command('snapshot'))
    command('wait','button[aria-label="a1-body.csv 검색 근거"]')
    command('click','button[aria-label="a1-body.csv 검색 근거"]')
    command('wait','--text','상태: 확인됨')
    assert 'point_observations' in command('get','value',f'#se-representation-{file_id}')
    query='지표면 온도 자료 중 현재 내 연구에 가장 적합한 조건을 가진 건 무엇인지?'
    command('open',base+'/datasets/search?q='+urllib.parse.quote(query))
    command('wait','[data-testid="search-assessment"]')
    text=command('get','text','body')
    assert '먼저 확인할 내용' in text and '맞는 데이터를 못 찾았어요' not in text
    command('find','text','연구 조건 입력·변경','click','--exact')
    command('select','select[name="variable"]','land_surface_temperature')
    command('select','select[name="region"]','seoul')
    fill_date(command,'input[name="start"]','2025-01-01')
    fill_date(command,'input[name="end"]','2025-12-31')
    command('focus','[data-testid="search-assessment"] button[type="submit"]')
    command('press','Enter')
    command('wait','500')
    (args.artifacts/'after-search.txt').write_text(command('snapshot'))
    command('wait','[data-testid="search-hit"]')
    command('focus','[data-testid="search-assessment"] details:last-child > summary')
    command('press','Enter')
    text=command('get','text','body')
    assert '합성 LST 연구 검증 사양' in text and '공간 좌표가 있는 점 관측' in text
    assert 'a2-body' not in text and 'B ' not in text
    (args.artifacts/'research-result.txt').write_text(text)
    command('screenshot',str((args.artifacts/'research-result.png').resolve()))
    command('focus','[data-testid="hit-name"]')
    command('press','Enter')
    command('wait','[data-testid="dt-files-toggle"]')
    command('reload')
    command('wait','[data-testid="dt-files-toggle"]')
    (args.artifacts/'result.json').write_text(json.dumps({'passed':True,
        'environment':'disposable fixture DB + real core/frontend + agent-browser; synthetic evidence; no model',
        'checks':['evidence edit','review save','reload preserves spatial CSV','research clarification without false empty',
                  'research form submission','source comparison','locked file non-disclosure','detail navigation','detail reload']},ensure_ascii=False,indent=2))
    command('open',base+'/lab')
    command('wait','--text','로그아웃')
