"""Conservative condition checks over current, accessible, human-reviewed facts."""
from __future__ import annotations

import calendar
import datetime as dt
import re


def _compact(value):
    return re.sub(r'[\s·_-]+', '', str(value)).lower()


def parse(query: str) -> dict:
    q = _compact(query)
    for n, name in sorted(enumerate(('일월','이월','삼월','사월','오월','유월','칠월','팔월','구월','시월','십일월','십이월'),1), key=lambda x:-len(x[1])):
        q = q.replace('년'+name, f'년{n}월')
    topics = [topic for topic, pattern in (
        ('식생·NDVI', r'식생|ndvi|푸른'), ('강우·강수', r'강우|강수|레이더'),
        ('가뭄', r'가뭄|spei|spi')) if re.search(pattern,q)]
    criteria = {'topic': topics[0] if len(topics)==1 else None, 'unsupported': len(topics)>1}
    excluded_index = re.search(r'(spei|spi)말고(spi|spei)', q)
    remainder = re.sub(r'(spei|spi)말고(spi|spei)', '', q)
    if re.search(r'이면서|둘다|제외|빼줘|아닌|말고', remainder):
        criteria['unsupported'] = True
    roles=[]
    if re.search(r'예측|추정결과', q): roles.append('prediction')
    if re.search(r'보조|지형|토지피복', q): roles.append('auxiliary_input')
    if re.search(r'검증용|검증에쓴|검증자료|정답파일', q): roles.append('validation')
    if re.search(r'주입력|모델입력|학습용', q): roles.append('model_input')
    if roles: criteria['roles']=roles
    if 'unet' in q: criteria['model']='U-Net'
    if excluded_index: criteria['variable']=excluded_index[2].upper()
    elif 'spei' in q and 'spi' not in q.replace('spei',''): criteria['variable']='SPEI'
    elif 'spi' in q and 'spei' not in q: criteria['variable']='SPI'
    if '결측' in q or '0%' in q or re.search(r'품질|오차|정확도',q): criteria['quality']=True
    if '직접관측' in q:
        criteria['directObservation']=True
        resolution=re.search(r'(\d+(?:\.\d+)?)(km|m)',q)
        if resolution: criteria['nativeResolutionM']=float(resolution[1])*(1000 if resolution[2]=='km' else 1)
    if '보간' in q and re.search(r'하지않|안한|없는',q): criteria['interpolated']=False
    cadence=next((value for pattern,value in [('월평균|한달평균','monthly'),('일별|매일','daily'),('주간|매주','weekly')] if re.search(pattern,q)),None)
    if cadence: criteria['cadence']=cadence
    region=next((r for r in ['제주','한반도','서울','강원','전라','경상'] if r in q),None)
    if '경기' in q and '충청' in q: region='경기남부충청'
    elif '시군구' in q: region='대한민국시군구'
    elif '충청' in q: region='충청'
    if region: criteria['region']=region
    date=re.search(r'(20\d{2})년(\d{1,2})월(?:(\d{1,2})일)?',q)
    years=re.search(r'(\d{4})년부터(\d{4})년까지',q)
    try:
        if len(re.findall(r'20\d{2}년\d{1,2}월', q)) > 1 or (date and re.search(r'부터|까지|[~～–—]|[월일]\s*-\s*\d', query)):
            criteria['period']=None
        elif date:
            y,m=int(date[1]),int(date[2]); day=int(date[3]) if date[3] else None
            criteria['period']=(dt.date(y,m,day or 1).isoformat(),dt.date(y,m,day or calendar.monthrange(y,m)[1]).isoformat())
        elif years: criteria['period']=(f'{years[1]}-01-01',f'{years[2]}-12-31')
        elif re.search(r'\d{4}년',q): criteria['period']=None
    except ValueError:
        criteria['period']=None
    if re.search(r'wgs84|잘라|15분누적',q): criteria['processingUnknown']=True
    return criteria


def assess(criteria: dict, facts: dict) -> dict:
    checks={}
    labels={'model':'모델','variable':'변수','cadence':'주기','directObservation':'직접 관측',
            'nativeResolutionM':'원관측 해상도','interpolated':'보간'}
    for key,label in labels.items():
        if key not in criteria: continue
        actual=facts.get(key)
        match=_compact(actual)==_compact(criteria[key])
        if key=='nativeResolutionM' and isinstance(actual,(int,float)): match=actual==criteria[key]
        display = str(actual) if actual is not None else '근거 없음'
        if key == 'directObservation' and actual is not None:
            display = '직접 관측' if actual else '직접 관측이 아닌 가공·예측 자료'
        elif key == 'interpolated' and actual is not None:
            display = '보간 적용' if actual else '보간 미적용'
        elif key == 'nativeResolutionM' and actual is not None:
            display = f'{actual:g}m'
        elif key == 'cadence' and actual is not None:
            display = {'daily':'일별','weekly':'주간','monthly':'월평균','15min':'15분'}.get(actual,actual)
        checks[label]=('unknown' if actual is None else 'supported' if match else 'contradicted',display)
    if criteria.get('roles'):
        actual=facts.get('roles')
        role_names={'model_input':'모델 입력','auxiliary_input':'보조 입력','validation':'검증 자료',
                    'prediction':'예측 결과','index':'지수 자료','documentation':'설명서','analysis_code':'분석 코드'}
        checks['파일 역할']=('unknown' if actual is None else 'supported' if set(actual)&set(criteria['roles']) else 'contradicted', ', '.join(role_names.get(r,r) for r in actual or []) or '근거 없음')
    if 'region' in criteria:
        actual=facts.get('region')
        checks['지역']=('supported' if actual and _compact(actual)==_compact(criteria['region']) else 'unknown',actual or '근거 없음')
    if 'period' in criteria:
        wanted=criteria['period']; actual=facts.get('period')
        status='unknown'
        if wanted and actual:
            if actual['start']<=wanted[0]<=wanted[1]<=actual['end']: status='supported'
            elif wanted[1]<actual['start'] or wanted[0]>actual['end']: status='contradicted'
        checks['기간']=(status, f"{actual['start']}~{actual['end']} (등록된 범위; 연속 관측 보증 아님)" if actual else '근거 없음')
    if criteria.get('quality'): checks['품질']=('unknown','품질 검증값을 수집하지 않음')
    if criteria.get('processingUnknown'): checks['가공·누적 간격']=('unknown','해당 조건은 현재 구조화 근거로 확인하지 못함')
    if criteria.get('unsupported'): checks['조건 조합']=('unknown','지원하지 않는 조건 조합')
    if checks and set(facts.get('roles',[])) & {'documentation','analysis_code'}:
        checks['자료 종류']=('contradicted','설명서·코드이며 관측·예측 자료 파일이 아님')
    return checks


def candidates(criteria: dict, records: list[dict], body_ids: dict[str,set[str]]) -> tuple[list[str],list[str]]:
    if not criteria.get('topic') or criteria.get('unsupported'): return [],[]
    grouped={}
    for record in records:
        if record.get('file_kind')=='본체': grouped.setdefault(record['dataset_id'],[]).append(record)
    included=[]; excluded=[]
    for dataset, rows in grouped.items():
        checks=[assess(criteria,r['facts']) for r in rows]
        if any(c and all(v[0]=='supported' for v in c.values()) for c in checks): included.append(dataset)
        # A partial set of annotations cannot establish absence. Related native
        # resolution products remain visible, explicitly marked as mismatches.
        if any(k in criteria for k in ('directObservation','nativeResolutionM','quality')): continue
        complete=body_ids.get(dataset) and body_ids[dataset]=={r['file_id'] for r in rows}
        if complete and all(any(v[0]=='contradicted' for v in c.values()) for c in checks): excluded.append(dataset)
    return included,excluded


def explain(base: str, criteria: dict, records: list[dict]) -> str:
    assessed=[(r,assess(criteria,r['facts'])) for r in records]
    assessed=[(r,c) for r,c in assessed if c]
    if not assessed: return base
    supported = [(r,c) for r,c in assessed if all(v[0]=='supported' for v in c.values())]
    if supported:
        assessed = supported
    else:
        related = [(r,c) for r,c in assessed if not any(v[0]=='contradicted' for v in c.values())]
        if related:
            assessed = related
    # Prefer files that satisfy the complete conjunction; do not assemble a
    # synthetic match from different files with individually matching fields.
    assessed.sort(key=lambda pair: (-sum(v[0]=='supported' for v in pair[1].values()),pair[0]['file_id']))
    pieces=[]
    for row,checks in assessed[:4]:
        states=[]
        for state,label in [('supported','확인'),('contradicted','불일치'),('unknown','미확인')]:
            names=[key+(f'({value[1]})' if state=='contradicted' or key in ('기간','파일 역할') else '')
                   for key,value in checks.items() if value[0]==state]
            if names: states.append(label+': '+', '.join(names))
        source=row['source']
        pieces.append(f"{row['file_name']} ({'; '.join(states)}; 출처 {source['label']} · {source['locator']})")
    return re.sub(r'\s+',' ',base.rstrip()+' 파일 근거 — '+' / '.join(pieces)+'.').strip()
