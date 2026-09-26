"""Conservative condition checks over current, accessible, human-reviewed facts."""
from __future__ import annotations

import calendar
import datetime as dt
import re

from ..kernel import cadence_scope
from ..kernel.region_scope import place_label, region_match
from ..kernel.search_semantics import SEMANTICS


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
    # 주기 상한(「1시간 이하」 = 산출 간격 ≤ 1시간 · Ted 2026-09-26) — 경로 1 과 같은 커널 파서로 원문에서 읽는다.
    # 범위 문구를 뗀 글에서 등호 주기를 찾는다(「10분 이내」의 「10분」은 등호가 아니다). 「15분 누적」은 누적
    # 기간이지 산출 간격이 아니라 주기로 읽지 않는다.
    limit=cadence_scope.parse_max_cadence_seconds(query)
    if limit: criteria['maxCadenceSeconds']=limit
    q_cadence=_compact(cadence_scope.strip_range(query))
    cadence=next((value for pattern,value in [('월평균|한달평균','monthly'),('일별|매일','daily'),('주간|매주','weekly'),('시간별|매시간|시간단위','hourly'),(r'(?<!\d)5\s*분','5min'),(r'(?<!\d)10\s*분','10min'),(r'(?<!\d)15분(?!누적)','15min'),('연평균|연단위|연 단위|매년|해마다','yearly')] if re.search(pattern,q_cadence)),None)
    if cadence: criteria['cadence']=cadence
    region=next((r for r in ['제주','한반도','서울','강원','전라','경상'] if r in q),None)
    # 「남한」은 표기 일치로만 맞춘다(의미 식별자가 아니라 넓히지 않는다 — 상향 금지).
    # 강·산 이름(남한강·남한산성)은 지역 조건이 아니다.
    if region is None and re.search(r'남한(?!강|산)',q): region='남한'
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


def _region_id(name: str) -> str | None:
    """파싱한 지역 이름 → 포함 관계 표(`regionWithin`)에 실린 의미 식별자. 아니면 None.

    표에 없는 지역은 종전대로 표기 일치만 본다 — 이 변경은 포함 관계 한 단계만 연다.
    """
    key=_compact(name)
    for rid in SEMANTICS.get('regionWithin',{}):
        if key in {_compact(rid),*(_compact(a) for a in SEMANTICS['regions'].get(rid,()))}:
            return rid
    return None


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
            display = cadence_scope.LABELS.get(actual,actual)
        checks[label]=('unknown' if actual is None else 'supported' if match else 'contradicted',display)
    if 'maxCadenceSeconds' in criteria:
        # 같은 커널 도우미로 판정한다(경로 1 `_predicate` 와 같은 표). 선언값 비교이며 연속 관측 보증이 아니다.
        actual=facts.get('cadence')
        within=cadence_scope.cadence_within(actual,criteria['maxCadenceSeconds'])
        limit=cadence_scope.limit_label(criteria['maxCadenceSeconds'])
        name=cadence_scope.LABELS.get(actual,actual)
        if actual is None: display='근거 없음'
        elif within is None: display=f'{actual} — 순서를 모르는 주기'
        elif within: display=f'{name} — {limit} 이하 · 등록 설명의 선언값, 파일 시간축 실측 아님'
        else: display=f'{name} — {limit} 초과 · 등록 설명의 선언값'
        checks['주기 범위']=('unknown' if within is None else 'supported' if within else 'contradicted',display)
    if criteria.get('roles'):
        actual=facts.get('roles')
        role_names={'model_input':'모델 입력','auxiliary_input':'보조 입력','validation':'검증 자료',
                    'prediction':'예측 결과','index':'지수 자료','documentation':'설명서','analysis_code':'분석 코드'}
        checks['파일 역할']=('unknown' if actual is None else 'supported' if set(actual)&set(criteria['roles']) else 'contradicted', ', '.join(role_names.get(r,r) for r in actual or []) or '근거 없음')
    if 'region' in criteria:
        actual=facts.get('region')
        wanted=_region_id(criteria['region'])
        if wanted is None:
            match,via=bool(actual) and _compact(actual)==_compact(criteria['region']),None
        else:
            # 의미 식별자면 직계 하위 한 단계까지 맞춘다(`kernel/region_scope.py` — 경로 1 과 같은 표).
            match,via=region_match(wanted,actual)
        display=actual or '근거 없음'
        if via is not None:
            display=f'{actual} — {place_label(wanted)} 안의 지역'
        # 모르는 지역을 지리적으로 배타라고 선언하지 않는다 — 불일치는 contradicted 가 아니라 unknown.
        checks['지역']=('supported' if match else 'unknown',display)
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


def supported_facts(criteria: dict, records: list[dict]) -> list[str]:
    """파일 근거 중 **확인(supported)된 조건만** 「파일 근거」 항목으로 적는다.

    Ted 2026-09-26 결정(intent `2026-09-25-search-rationale-separation.md` Q6) — 카드 근거는
    검색된 이유만 싣는다. 종전 `explain` 이 함께 적던 「불일치」·「미확인」 조각은 싣지 않는다.
    항목마다 한 줄이다(`AiRationale` 패턴 · 원문 글의 줄바꿈은 한 칸으로 접는다).
    """
    assessed=[(r,assess(criteria,r['facts'])) for r in records]
    assessed=[(r,c) for r,c in assessed if c]
    if not assessed: return []
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
    facts=[]
    for row,checks in assessed[:4]:
        # 지역은 포함 관계로 맞았을 때만 세부를 붙인다(「지역(남한 — 한반도 안의 지역)」 · intent
        # `2026-09-26-region-containment-expansion.md` 결정 2). 표기가 같으면 종전대로 「지역」만.
        names=[key+(f'({value[1]})' if key in ('기간','파일 역할','주기 범위')
                    or (key=='지역' and value[1].endswith(' 안의 지역')) else '')
               for key,value in checks.items() if value[0]=='supported']
        if not names: continue
        # 출처(설명서 이름·절)는 싣지 않는다 — 상세 「검색 근거」가 보인다
        # (intent `2026-09-26-rationale-facts-wording.md` ①).
        facts.append(re.sub(r'\s+',' ',f"{row['file_name']}에서 {', '.join(names)} 조건이 맞았어요").strip())
    return facts
