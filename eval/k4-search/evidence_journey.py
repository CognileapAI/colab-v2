"""Disposable browser journey: edit evidence -> persist -> search -> source."""
import json


def run(command,args,session):
    if not args.artifacts: raise RuntimeError('artifact directory required')
    args.artifacts.mkdir(parents=True,exist_ok=True)
    file_id='00000000000000000000000FA1'
    detail='http://127.0.0.1:43173/datasets/0000000000000000000000DSA1'
    command('open',detail)
    command('wait','--load','networkidle')
    command('wait','[data-testid="dt-files-toggle"]')
    command('focus','[data-testid="dt-files-toggle"]')
    command('press','Enter')
    try:
        command('wait','[aria-label="a1-body.csv 검색 근거"]')
    except Exception:
        (args.artifacts/'files-failure.txt').write_text(command('snapshot'))
        raise
    command('click','[aria-label="a1-body.csv 검색 근거"]')
    command('wait',f'#se-label-{file_id}')
    command('focus', 'form[aria-label="a1-body.csv 검색 근거"] fieldset label:nth-of-type(3) input')
    command('press','Space')
    command('fill',f'#se-label-{file_id}','로컬 검증 자료 설명서')
    command('fill',f'#se-locator-{file_id}','검증 파일 역할 절')
    command('fill',f'#se-text-{file_id}','a1-body.csv는 모델 검증에 사용하는 강우 자료입니다. 결측률 검증값은 없습니다.')
    (args.artifacts/'before-save.txt').write_text(command('snapshot'))
    command('focus','form .de-act button:first-child')
    command('press','Enter')
    command('wait','--text','상태: 초안')
    command('focus','form .de-act button:last-child')
    command('press','Enter')
    command('wait','--text','상태: 확인됨')
    command('screenshot',str((args.artifacts/'evidence-saved.png').resolve()))
    command('reload')
    command('wait','--load','networkidle')
    command('wait','[data-testid="dt-files-toggle"]')
    command('focus','[data-testid="dt-files-toggle"]')
    command('press','Enter')
    command('wait','[aria-label="a1-body.csv 검색 근거"]')
    command('click','[aria-label="a1-body.csv 검색 근거"]')
    command('wait','--text','상태: 확인됨')
    assert '로컬 검증 자료 설명서' in command('get','value',f'#se-label-{file_id}')
    command('open','http://127.0.0.1:43173/lab')
    command('wait','[aria-label="검색 질문"]')
    command('fill','[aria-label="검색 질문"]','강우 검증용 자료')
    command('press','Enter')
    command('wait','[data-testid="search-hit"]')
    text=command('get','text','body')
    assert '로컬 검증 자료 설명서' in text and '검증 자료' in text and 'a1-body.csv' in text
    assert 'a2-body.nc' not in text and 'B ' not in text
    command('screenshot',str((args.artifacts/'evidence-search.png').resolve()))
    (args.artifacts/'search.txt').write_text(text)
    command('click','.hit:not(.is-locked) [data-testid="hit-name"]')
    assert command('get','url').strip().endswith('/datasets/0000000000000000000000DSA1')
    (args.artifacts/'result.json').write_text(json.dumps(dict(passed=True,
        environment='disposable fixture DB, real core/frontend; HTTP interpreter double',
        checks=['draft save','explicit review','reload persistence','search evidence','locked file non-disclosure','detail navigation']),ensure_ascii=False,indent=2))
    command('open','http://127.0.0.1:43173/lab')
    command('wait','--text','로그아웃')
